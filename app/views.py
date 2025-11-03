import os
import math
import json
import uuid
import logging
import aiofiles

from django.core import exceptions
from django.http import HttpResponse, JsonResponse
from django.views import View
from task.settings import TMP_DIR
from .config import curr_config
from .workers import process_w2_forms, form_error_response
from .models import JobTracker
from .connector import BaseRedis, OMDBConnector

logger = logging.getLogger(__name__)
# common redis for cache
redis = BaseRedis()


async def ping(request):
    return HttpResponse("Hey, There!!")


def form_json_response(status, status_code=200, addl_resp=None, error_message=None):
    response = {"status": status, "status_code": status_code}
    if addl_resp and not isinstance(addl_resp, dict):
        addl_resp = {"response": str(addl_resp)}

    if isinstance(error_message, str):
        error_resp = form_error_response(error_message, json_type=False)
        error_resp["error"].update(addl_resp) if addl_resp else ...
        response.update(error_resp)
    elif addl_resp:
        response.update(addl_resp)
    return JsonResponse(response, status=status_code)


class W2Intelligence(View):
    """
    Class view to handle W2 form parsing.
    """

    async def get(self, request, job_id):
        """Get details from w2 form, returns job status once till completion

        Args:
            request (HttpRequest): Http GET Request
            job_id (str): Processing Job Id

        Returns:
            JsonReponse: W-2 form details / status of the job
        """
        try:
            logger.info("Fetching details for job id - %s", job_id)
            invalid_resp = form_json_response(
                "failed",
                status_code=400,
                error_message="Invalid Job id, Provide a valid Job Id to get results.",
            )
            if not job_id:
                return invalid_resp
            try:
                job = await JobTracker.objects.filter(id=job_id).afirst()
            except exceptions.ValidationError:
                return invalid_resp
            if job:
                logger.info("Successfully fetched job details - %s", job)
                return form_json_response(
                    job.status, status_code=200, addl_resp=job.to_dict()
                )
            return invalid_resp
        except Exception:
            logger.exception("Error occurred while fetching job status")
            return form_json_response(
                "unexpected error", 500, error_message="Unexpected error occurred."
            )

    async def post(self, request):
        """Gets Input W-2 file as request and pushes it to queue for processing.

        Args:
            request (HttpRequest): Http POST Request

        Returns:
            JsonResponse: Status & queued Job Id.
        """
        job = None
        try:
            logger.info("Processing recieved w2 form request")
            w2_form = request.FILES["file"]
            mime_type = w2_form.content_type
            if mime_type not in curr_config.ALLOWED_FILE_TYPES:
                logger.info("invald w2 form recieved in the request - %s", mime_type)
                return form_json_response(
                    "failed",
                    400,
                    error_message="Invalid file format, Allowed Types (.png, .jpeg, .pdf).",
                )

            job_id = uuid.uuid4().hex
            unique_file_name = f"{job_id[:6]}_{w2_form.name}"
            tmp_path = os.path.join(TMP_DIR, unique_file_name)

            logger.info("Saving W2 form - '%s' in path '%s'", unique_file_name, TMP_DIR)
            # save file in temporary path
            async with aiofiles.open(tmp_path, "wb+") as destination:
                for chunk in w2_form.chunks():
                    await destination.write(chunk)

            job_obj = JobTracker(id=job_id, status=JobTracker.Status.QUEUED)
            job = await job_obj.asave()
            await process_w2_forms.kiq(job_id, tmp_path, mime_type)
            logger.info(
                "Successfully pushed W2 form to job que, filename - %s | job_id - %s",
                unique_file_name,
                job_id,
            )
            return form_json_response("queued", 201, addl_resp={"job_id": job_id})
        except KeyError:
            logger.warning("W-2 form is missing in the request.")
            return form_json_response(
                "failed",
                400,
                error_message="W-2 form missing in request, Upload form to proceed.",
            )
        except Exception as exc:
            logger.exception(
                "Exception occurred while processing the input form request."
            )
            if job:
                await job.amark(
                    status=job.Status.Failed, _task_result=form_error_response(str(exc))
                )
            return form_json_response(
                "unexpected error", 500, error_message="Unexpected error occurred."
            )


class Movies(View):
    """
    View for movies Search API
    """

    # /api/movies?q=<keyword>&page=<n>

    @staticmethod
    def form_movies_result(movies, directors, total_results: str):
        """Forms dict response based on movies & directors

        Args:
            movies (list): List of movies based on search term.
            directors (list): List of direcors based on movie ids.
            total_results (str): Integer string of total results from API.
        returns:
            movies_dirs (list): List of movie with director
            [
                {
                    "title": "Movie Name",
                    "director": "Director Name"
                }
            ]
        """
        results = []
        total_results = int(total_results)
        response = {
            "total_results": total_results,
            "total_pages": math.ceil(total_results / curr_config.OMDB_RESULT_PER_PAGE),
        }
        for movie in movies:
            results.append(
                {
                    "title": movie["Title"],
                    "director": directors.get(movie["imdbID"], "N/A"),
                }
            )
        response.update({"results": results})
        return response

    async def get(self, request):
        """Search movies API

        Args:
            request (HttpRequest): Http GET Request with query params

        Returns:
            JsonResponse:
        """
        try:
            query_params = request.GET
            logger.info("Searching movies for query search param - %s", query_params)
            search_param = query_params.get("q")
            page = query_params.get("page", 1)

            if not search_param:
                logger.info("No search params given, returning empty result - '%s'", search_param)
                resp = self.form_movies_result(
                    movies=[], directors={}, total_results="0"
                )
                return form_json_response("success", 200, addl_resp=resp)

            async with redis.connect() as redis_conn:
                cache_key = f"{search_param}_{page}"
                cached_resp = await redis_conn.get(cache_key)
                if cached_resp:
                    logger.info("Response available in cache, returning cached response.")
                    return form_json_response(
                        "success", 200, addl_resp=json.loads(cached_resp)
                    )

            request_data = {"params": {"s": search_param, "page": page}}
            logger.info("Fetching movies for request - %s", request_data)
            response, status_code = await OMDBConnector(request_data).process_request()
            logger.info("Recieved movies details with status code - %s", status_code)
            movies = response.get("Search")
            if status_code != 200 or not movies:
                logger.info("Invalid response recieved from OMDB API - %s", response)
                return form_json_response(
                    "failed",
                    status_code or 400,
                    addl_resp=response,
                    error_message="Error response from provider, try again later.",
                )

            m_ids = [movie["imdbID"] for movie in movies]
            directors = await OMDBConnector({}).get_directors(movies=m_ids)
            resp = self.form_movies_result(
                movies=movies,
                directors=directors,
                total_results=response["totalResults"],
            )
            # set response to redis cache
            async with redis.connect() as redis_conn:
                await redis_conn.set(
                    cache_key, json.dumps(resp), ex=curr_config.MOVIES_CACHE_TTL
                )
            return form_json_response("success", 200, addl_resp=resp)
        except Exception:
            logger.exception("Exception occurred while fetching movies")
            return form_json_response(
                "unexpected error", 500, error_message="Unexpected error occurred."
            )
