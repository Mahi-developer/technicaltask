import pytest
import copy
import asyncio
from unittest.mock import patch

from django.urls import reverse

from conftest import TestBase
from _test_utils import mock_args_async
from _test_constants import (
    sample_movie_search_response,
    sample_movie_search_error_response,
    sample_movie_director_fetch_response,
)

from app.connector import BaseRedis


@pytest.mark.asyncio
class TestMoviesSearch(TestBase):
    """Testcases related to W2 Get API"""

    def setUp(self):
        super().setUp()
        self.url = reverse("movies")
        self.cached_keys = []
        self.redis = BaseRedis()
        
    def tearDown(self):
        super().tearDown()

    async def cleanup_redis(self):
        async with self.redis.connect() as redis_conn:
            tasks = [redis_conn.delete(key) for key in self.cached_keys]
            await asyncio.gather(*tasks)
            await redis_conn.close()

    async def test_movies_empty_search_param(self):
        """Testing Movies Search API with empty search param"""
        # mocks

        params = {
            "q": ""
        }
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["results"], [])
        self.assertEqual(response["total_results"], 0)
        self.assertEqual(response["total_pages"], 0)

    @patch("app.views.OMDBConnector.process_request")
    async def test_no_movies_from_search(self, mock_process_request):
        """Testing Movies Search API validations"""
        # mocks
        mock_process_request.side_effect = mock_args_async(
            return_val=({}, 400),
        )
        
        params = {
            "q": "adfklsdkf"
        }
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 400)
        response = response.json()
        self.assertEqual(response["status"], "failed")
        self.assertEqual(response["status_code"], 400)
        self.assertEqual(response["error"]["message"], "Error response from provider, try again later.")

    @patch("app.views.OMDBConnector.process_request")
    async def test_movies_unexpected_error(self, mock_process_request):
        """Testing Movies Search API unexpected error"""
        # mocks
        mock_process_request.side_effect = mock_args_async(
            return_val=Exception("Unit Testing excpetion"), _is_exp=True,
        )

        params = {
            "q": "afkaldkfa"
        }
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 500)
        response = response.json()
        self.assertEqual(response["status"], "unexpected error")
        self.assertEqual(response["status_code"], 500)
        self.assertEqual(response["error"]["message"], "Unexpected error occurred.")

    @patch("app.views.OMDBConnector.process_request")
    @patch("app.views.OMDBConnector.get_directors")
    async def test_movies_pagination(self, mock_get_directors, mock_process_request):
        """Testing Movies Search API pagination check"""
        # mocks
        page = 0
        movies=copy.deepcopy(sample_movie_search_response)
        mock_process_request.side_effect = mock_args_async(
            return_val=(movies[page], 200),
        )
        directors = copy.deepcopy(sample_movie_director_fetch_response)
        dir_response = {dir["imdbID"]: dir["Director"] for dir in directors}
        mock_get_directors.side_effect = mock_args_async(
            return_val=dir_response,
        )
        
        page += 1  # list index 0 resp mapped to page 1
        params = {
            "q": "Spider+Man",
            "page": page
        }
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["total_results"], 20)
        self.assertEqual(response["total_pages"], 2)
        self.assertEqual(len(response['results']), 10)
        first_results = response['results']
        
        self.cached_keys.append(f"{params["q"]}_{page}")
         
        mock_process_request.side_effect = mock_args_async(
            return_val=(movies[page], 200),
        )
        mock_get_directors.side_effect = mock_args_async(
            return_val=dir_response,
        )
        page += 1 # list index 1 resp mapped to page 2
        params.update({"page": page})

        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["total_results"], 20)
        self.assertEqual(response["total_pages"], 2)
        self.assertEqual(len(response['results']), 10)
        self.assertNotEqual(response['results'], first_results)
        
        # cleanup
        self.cached_keys.append(f"{params["q"]}_{page}")
        await self.cleanup_redis()
        
    @patch("app.views.OMDBConnector.process_request")
    @patch("app.views.OMDBConnector.get_directors")
    async def test_movies_success_verify_cache(self, mock_get_directors, mock_process_request):
        """Testing Movies Search API cache result verify"""
        # mocks
        page = 0
        movies=copy.deepcopy(sample_movie_search_response)
        mock_process_request.side_effect = mock_args_async(
            return_val=(movies[page], 200),
        )
        directors = copy.deepcopy(sample_movie_director_fetch_response)
        dir_response = {dir["imdbID"]: dir["Director"] for dir in directors}
        mock_get_directors.side_effect = mock_args_async(
            return_val=dir_response,
        )
        
        page += 1
        params = {
            "q": "Unit Testing"
        }
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["total_results"], 20)
        self.assertEqual(response["total_pages"], 2)
        self.assertEqual(len(response['results']), 10)
        first_results = response['results']
        
        # verify in redis cache
        
        async with self.redis.connect() as redis_conn:
            self.assertIsNotNone(await redis_conn.get(f"{params["q"]}_{page}"))
        
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 200)
        response = response.json()
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["total_results"], 20)
        self.assertEqual(response["total_pages"], 2)
        self.assertEqual(len(response['results']), 10)
        self.assertEqual(response['results'], first_results)

        # cleanup
        self.cached_keys.append(f"{params["q"]}_{page}")
        await self.cleanup_redis()
    
    @patch("app.views.OMDBConnector.process_request")
    async def test_movies_api_error(self, mock_process_request):
        """Testing Movies Search API Error response"""
        # mocks
        movies=copy.deepcopy(sample_movie_search_error_response)
        mock_process_request.side_effect = mock_args_async(
            return_val=(movies, 400),
        )
        
        params = {
            "q": "askfmlad"
        }
        response = await self.client.get(self.url, query_params=params)
        self.assertEqual(response.status_code, 400)
        response = response.json()
        self.assertEqual(response["status"], "failed")
        self.assertEqual(response["status_code"], 400)
        self.assertEqual(response["error"]["message"], "Error response from provider, try again later.")
        resp_keys = response["error"].keys()
        [self.assertIn(key, resp_keys) for key in movies.keys()]
