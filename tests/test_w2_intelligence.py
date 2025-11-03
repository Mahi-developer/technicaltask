import os
import uuid
import pytest
from unittest.mock import patch
from parameterized import parameterized

from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from conftest import TestBase
from _test_utils import mock_args, mock_args_async, mock_execute
from _test_constants import sample_w2_success_response, sample_w2_error_response

from app.models import JobTracker
from app.workers import process_w2_forms


@pytest.mark.asyncio
class TestW2Get(TestBase):
    """Testcases related to W2 Get API"""

    def setUp(self):
        super().setUp()
        self.url = reverse("w2_response", args=[uuid.uuid4().hex])

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tracker_ids = []

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if cls.tracker_ids:
            JobTracker.objects.filter(id__in=cls.tracker_ids).delete()
        cls.cleanup()

    @parameterized.expand(
        [
            ("no_job_id", {"job_id": None}),
            ("invalid_job_id", {"job_id": f"{uuid.uuid4().hex}123"}),
            ("no_results", {"job_id": uuid.uuid4().hex}),
        ]
    )
    async def test_w2_get_validation(self, name, kwargs):
        """Testing W2 GET API validations"""
        url = reverse("w2_response", kwargs=kwargs)
        response = await self.client.get(url)
        self.assertEqual(response.status_code, 400)
        response = response.json()
        self.assertEqual(response["status"], "failed")
        self.assertEqual(response["status_code"], 400)
        self.assertEqual(
            response["error"]["message"],
            "Invalid Job id, Provide a valid Job Id to get results.",
        )

    @patch("app.models.JobTracker.objects.filter")
    async def test_w2_get_unexpected_error(self, mock_filter):
        """Testing W2 GET Unexpected Error"""
        mock_filter.side_effect = mock_args(
            Exception("Sample Testing Exception"), _is_exp=True
        )

        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        response = response.json()
        self.assertEqual(response["status"], "unexpected error")
        self.assertEqual(response["status_code"], 500)
        self.assertEqual(response["error"]["message"], "Unexpected error occurred.")

    @patch("app.views.process_w2_forms.kiq")
    @patch("app.workers.GeminiConnector.file_upload")
    @patch("app.workers.GeminiConnector.process_request")
    async def test_w2_get_success(
        self, mock_process_request, mock_file_upload, mock_kiq
    ):
        """Testing W2 GET API Success case"""

        # mocks
        mock_kiq.side_effect = mock_execute(executable_func=process_w2_forms)
        mock_file_upload.side_effect = mock_args_async(return_val=(True, "Mock"))
        mock_process_request.side_effect = mock_args_async(
            return_val=(True, sample_w2_success_response)
        )

        # sample file
        sample_file = SimpleUploadedFile(
            "sample.pdf", b"sample file content", content_type="application/pdf"
        )

        # post doc and mock gemini response to create entry
        post_url = reverse("w2_process")
        post_response = await self.client.post(post_url, {"file": sample_file})
        self.assertEqual(post_response.status_code, 201)
        post_response = post_response.json()
        self.assertEqual(post_response["status"], "queued")

        # verify entry in backend
        job = await JobTracker.objects.filter(id=post_response["job_id"]).afirst()
        self.assertEqual(job.id.hex, post_response["job_id"])

        url = reverse("w2_response", kwargs={"job_id": post_response["job_id"]})
        response = await self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = response.json()

        self.assertEqual(response["status"], job.Status.SUCCESS)
        self.assertEqual(response["status_code"], 200)
        self.assertIsNotNone(response["meta"]["created_time"])
        self.assertIsNotNone(response["meta"]["start_time"])
        self.assertIsNotNone(response["meta"]["end_time"])
        self.assertEqual(response["result"], job.to_dict()["result"])
        [self.assertIn(key, response["result"]["model_assessment"].keys()) for key in ["missing_fields", "warnings"]]

        # verify masked info
        # MASKED_KEYS = ["employee_info.ssn", "employer_info.ein"]
        ssn = response["result"]["employee_info"]["ssn"]
        ein = response["result"]["employer_info"]["ein"]
        self.assertTrue(ssn[:-4] == "X" * (len(ssn) - 4))
        self.assertTrue(ein[:-4] == "X" * (len(ein) - 4))

        # clean up
        self.tracker_ids.append(job.id)

    @patch("app.views.process_w2_forms.kiq")
    @patch("app.workers.GeminiConnector.file_upload")
    @patch("app.workers.GeminiConnector.process_request")
    async def test_w2_get_error_from_gemini(
        self, mock_process_request, mock_file_upload, mock_kiq
    ):
        """Testing W2 GET API Success case"""

        # mocks
        mock_kiq.side_effect = mock_execute(executable_func=process_w2_forms)
        mock_file_upload.side_effect = mock_args_async(return_val=(True, "Mock"))
        mock_process_request.side_effect = mock_args_async(
            return_val=(False, sample_w2_error_response)
        )

        # sample file
        sample_file = SimpleUploadedFile(
            "sample.pdf", b"sample file content", content_type="application/pdf"
        )

        # post doc and mock gemini response to create entry
        post_url = reverse("w2_process")
        post_response = await self.client.post(post_url, {"file": sample_file})
        self.assertEqual(post_response.status_code, 201)
        post_response = post_response.json()
        self.assertEqual(post_response["status"], "queued")

        # verify entry in backend
        job = await JobTracker.objects.filter(id=post_response["job_id"]).afirst()
        self.assertEqual(job.id.hex, post_response["job_id"])

        url = reverse("w2_response", kwargs={"job_id": post_response["job_id"]})
        response = await self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = response.json()

        self.assertEqual(response["status"], job.Status.FAILED)
        self.assertEqual(response["status_code"], 200)
        self.assertIsNotNone(response["meta"]["created_time"])
        self.assertIsNotNone(response["meta"]["start_time"])
        self.assertIsNotNone(response["meta"]["end_time"])
        self.assertEqual(response["result"], job.to_dict()["result"])

        # clean up
        self.tracker_ids.append(job.id)


class TestW2Process(TestBase):
    """Testcases related to W2 Process (POST) API"""

    def setUp(self):
        super().setUp()
        self.url = reverse("w2_process")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tracker_ids = []
        cls.files = []
        cls.pdf_file = SimpleUploadedFile(
            "sample.pdf", b"sample pdf content", content_type="application/pdf"
        )
        cls.img_file = SimpleUploadedFile(
            "sample.png", b"sample img content", content_type="image/png"
        )
        cls.csv_file = SimpleUploadedFile(
            "sample.csv", b"sample,pdf,content", content_type="text/csv"
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if cls.tracker_ids:
            JobTracker.objects.filter(id__in=cls.tracker_ids).delete()
        cls.cleanup()

    @parameterized.expand(
        [
            ("no_file", None, "W-2 form missing in request, Upload form to proceed."),
            (
                "invalid_filetype",
                "csv_file",
                "Invalid file format, Allowed Types (.png, .jpeg, .pdf).",
            ),
        ]
    )
    async def test_w2_post_validations(self, name, file, expected_message):
        """Testing W2 POST API Success case"""
        if file:
            file_param = {"file": getattr(self, file)}
            post_response = await self.client.post(self.url, file_param)
        else:
            post_response = await self.client.post(self.url)

        self.assertEqual(post_response.status_code, 400)
        post_response = post_response.json()
        self.assertEqual(post_response["status_code"], 400)
        self.assertEqual(post_response["status"], "failed")
        self.assertEqual(post_response["error"]["message"], expected_message)

    @patch("app.views.process_w2_forms.kiq")
    async def test_w2_post_unexpected_error(self, mock_kiq):
        """Testing W2 POST API Success case"""

        # mocks
        mock_kiq.side_effect = mock_args_async(
            Exception("Unit Testing Exception"), _is_exp=True
        )

        post_response = await self.client.post(self.url, {"file": self.pdf_file})
        self.assertEqual(post_response.status_code, 500)
        post_response = post_response.json()
        self.assertEqual(post_response["status_code"], 500)
        self.assertEqual(post_response["status"], "unexpected error")
        self.assertEqual(
            post_response["error"]["message"], "Unexpected error occurred."
        )

    @patch("app.views.process_w2_forms.kiq")
    async def test_w2_post_success(self, mock_kiq):
        """Testing W2 POST API Success case"""

        # mocks
        mock_kiq.return_value = None

        post_response = await self.client.post(self.url, {"file": self.img_file})
        self.assertEqual(post_response.status_code, 201)
        post_response = post_response.json()
        self.assertEqual(post_response["status_code"], 201)
        self.assertEqual(post_response["status"], "queued")

        # verify entry in backend
        job = await JobTracker.objects.filter(id=post_response["job_id"]).afirst()
        self.assertEqual(job.status, job.Status.QUEUED)

        # clean up
        self.tracker_ids.append(job.id)
