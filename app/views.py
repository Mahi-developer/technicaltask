import os
import uuid
import logging

from django.http import HttpResponse, JsonResponse
from django.views import View
from task.settings import TMP_DIR
from .config import curr_config
from .workers import process_w2_forms
from .models import JobTracker
from .helper import create_record

logger = logging.getLogger(__name__)
async def ping(request):
    return HttpResponse("Hey, There!!")


def form_json_response(status, status_code=200, addl_resp=None, error_message=None):
    response = {
        "status": status,
        "status_code": status_code
    }
    if isinstance(error_message, str):
        response.update({"error": {"message": error_message}})
    if isinstance(addl_resp, dict):
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
        return form_json_response("in-progress")
    
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
            w2_form = request.FILES['file']
            mime_type = w2_form.content_type
            if mime_type not in curr_config.ALLOWED_FILE_TYPES:
                logger.info("invald w2 form recieved in the request - %s", mime_type)
                return form_json_response(
                    "failed", 400, error_message="Invalid file format, Allowed Types (.png, .jpeg, .pdf)."
                )

            job_id = uuid.uuid4().hex
            unique_file_name = f"{job_id[:6]}_{w2_form.name}"
            tmp_path = os.path.join(TMP_DIR, unique_file_name)

            logger.info("Saving W2 form - '%s' in path '%s'", unique_file_name, TMP_DIR)
            # save file in temporary path
            with open(tmp_path, 'wb+') as destination:
                for chunk in w2_form.chunks():
                    destination.write(chunk)

            job = await create_record(model=JobTracker, id=job_id, status=JobTracker.Status.QUEUED)
            await process_w2_forms.kiq(job_id, tmp_path)
            logger.info("Successfully pushed W2 form to job que, filename - %s | job_id - %s", unique_file_name, job_id)
            return form_json_response("queued", 201, addl_resp={"job_id": job_id})
        except KeyError:
            logger.warning("W-2 form is missing in the request.")
            return form_json_response(
                "failed", 400, error_message="W-2 form missing in request, Upload form to proceed."
            )
        except Exception as exc:
            logger.exception("Exception occurred while processing the input form request.")
            if job:
                await job.amark(status=job.Status.Failed, task_result=str(exc))
            return form_json_response(
                "unexpected error", 500, error_message="Unexpected error occurred."
            )



class Movies(View):
    
    async def get(self, request):
        return JsonResponse({"status": "Searching", "status_code": 200})