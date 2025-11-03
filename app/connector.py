import copy
import json
import logging
import aiofiles
import aiohttp
import asyncio
import redis.asyncio as redis

from contextlib import asynccontextmanager
from google.genai import Client
from .config import curr_config
from task.settings import REDIS_HOST

logger = logging.getLogger(__name__)


class ExternalConnector:
    """
    Connector class to connect to the external APIs
    """

    def __init__(self, request, retry_config=None):
        """Initialize function for external connector

        Args:
            request (dict): Follow the format
            {
                "method": "",
                "url": "",
                "headers": {},  # Request Headers
                "params": {},  # Query params
                "json": {},  # for json request body
                "data": "", # for other type of form / file inputs
                "timeout": 30  # request timeout in seconds
            }
            retry_config (dict): Following format
            {
                "max_attempts": 0, # Integer for timeout retry attempts
                "exceptions": []  # list of exceptions to be retried
            }
        """
        self.request = request
        self.retry_config = retry_config or {}
        self.retry_attempts = self.retry_config.get("max_attempts", 0)

    async def process_request(self, fmt="json"):
        response, status_code = {}, None
        try:
            logger.info(
                "Posting External API with request | URL - %s | METHOD - %s | PARAMS - %s",
                self.request.get("url"),
                self.request.get("method"),
                self.request.get("params"),
            )
            async with aiohttp.ClientSession() as session:
                async with session.request(**self.request) as resp:
                    status_code = resp.status
                    response = await getattr(resp, fmt)()
            logger.info(
                "External API '%s' completed with status - %s",
                self.request.get("url"),
                status_code,
            )
        except tuple(self.retry_config.get("exceptions", [])) as error:
            if self.retry_attempts > 0:
                logger.warning("%s - error occurred, retrying", str(error))
                self.retry_attempts -= 1
                return await self.process_request(fmt)
            else:
                logger.exception(
                    "Max Retries exceeded, Error occurred while porcessing the request"
                )
        except Exception:
            logger.exception(
                "Error occurred while posting request to third party service - %s",
                self.url,
            )
        return response, status_code


class OMDBConnector(ExternalConnector):
    """OMDB Connector for movies search"""

    def __init__(self, data):
        if not data.get("params"):
            data["params"] = {}

        # update default required params
        data["params"].update({"apikey": curr_config.OMDB_API_KEY, "type": "movie"})

        request = {
            "method": data.pop("method", "GET"),
            "url": curr_config.OMDB_URL,
            "headers": data.pop("headers", {}),
            "params": data.pop("params"),
            "timeout": data.pop("timeout", 30),
        }
        retry_config = {"max_attempts": 3, "exceptions": [asyncio.TimeoutError]}
        super().__init__(request, retry_config=retry_config)

    async def _fetch_director(self, session, movie_id, sem):
        response = {}
        try:
            logger.info("Fetching director for movie - %s", movie_id)
            request = copy.deepcopy(self.request)
            request["params"]["i"] = movie_id
            async with sem:
                async with session.request(**request) as resp:
                    resp.raise_for_status()
                    response = await resp.json()
                    logger.info("Response for movie director id - %s, response - %s", movie_id, response)
        except Exception:
            logger.exception("Unable to get director for movie - %s", movie_id)

        return {"id": movie_id, "director": response.get("Director", "N/A")}

    async def get_directors(self, movies):
        results = {}
        try:
            logger.info("Fetching directors for requested movies")
            sem = asyncio.Semaphore(curr_config.MAX_CONCURRENCY)
            async with aiohttp.ClientSession() as session:
                tasks = [self._fetch_director(session, _id, sem) for _id in movies]
                responses = await asyncio.gather(*tasks)
            results = {
                response["id"]: response["director"]
                for response in responses
                if isinstance(response, dict)
            }
            logger.info("Successfully fetched director details for requested movies")
        except Exception:
            logger.exception("Error while fetching directors for movies - %s", movies)

        return results


class GeminiConnector:
    """Connector with Gemini client"""

    def __init__(self):
        self.client = Client(api_key=curr_config.GEMINI_API_KEY).aio

    async def file_upload(self, filepath, file_type):
        try:
            logger.info("Uploading file to Gemini client")
            file = await self.client.files.upload(
                file=filepath, config={"mime_type": file_type}
            )
            logger.info("Successfully uploaded the file to Gemini client")
            return True, file
        except Exception as error:
            logger.exception("Error while uploading file to Gemini client")
            return False, str(error)

    async def process_request(self, prompt, data=None):
        try:
            logger.info("Processing GEN AI request with Gemini...")
            contents = [prompt]
            contents.append(data) if data else ...
            response = await self.client.models.generate_content(
                model=curr_config.GEMINI_MODEL_ID,
                contents=contents,
            )
            response = response.text
            if "error" in response:
                return False, response

            logger.info("Successfully processed the w2 form.")
            return True, response
        except Exception as error:
            logger.exception("Error occurred while processing the GEN AI request")
            return False, str(error)

    async def close_connections(self):
        try:
            await self.client.close()
        except Exception:
            logger.exception("Error while closing Gemini connection")


class BaseRedis:
    """Base Redis connector class
    """

    @asynccontextmanager
    async def connect(self):
        conn = redis.Redis(host=REDIS_HOST, port=6379, db=0)
        try:
            yield conn
        finally:
            try:
                await conn.aclose()
            except RuntimeError:
                pass