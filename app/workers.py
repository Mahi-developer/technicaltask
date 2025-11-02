import os
import json
import django
import logging
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task.settings")
django.setup()

from django.utils import timezone
from taskiq import TaskiqMiddleware, TaskiqMessage
from taskiq_redis import ListQueueBroker
from asgiref.sync import sync_to_async

from .config import curr_config
from .models import JobTracker
from .prompts import W2_FORM_PROMPT
from .connector import GeminiConnector
from task.settings import BROKER_BACKEND_URL

logger = logging.getLogger(__name__)

def form_error_response(message, json_type: bool=True):
    try:
        message = json.loads(message)
    except (TypeError, json.decoder.JSONDecodeError):
        pass
    if not isinstance(message, dict):
        message = {"error": {"message": str(message)}}
    return message if not json_type else json.dumps(message)


# custom timeout middleware
class TimeoutMiddleware(TaskiqMiddleware):
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        
    async def on_timeout(**kwargs):
        logger.warning("Task timeout exceeded, exiting task...")
        job = await JobTracker.objects.filter(id=kwargs['job_id']).afirst()
        await job.amark(
            status=job.Status.CANCELLED,
            _task_result=form_error_response(f"Task running longer than expected. Tiemout - {curr_config.WORKER_TIMEOUT}")
        )

    async def on_task_execute(self, task_func, message):
        try:
            return await asyncio.wait_for(task_func(), timeout=self.timeout)
        except asyncio.TimeoutError:
            await on_timeout(**message.kwargs)

# define taskiq broker
broker = ListQueueBroker(BROKER_BACKEND_URL)
broker.add_middlewares(TimeoutMiddleware(timeout=curr_config.WORKER_TIMEOUT))


@sync_to_async
def cleanup(filepath: str):
    try:
        os.remove(filepath)
        logger.info("Successfully removed w2 form from file path - %s", filepath)
    except Exception:
        logger.exception("Error occurred while cleaning up file in filepath - %s", filepath)


@broker.task
async def process_w2_forms(job_id: str, filepath: str, mime_type: str):
    try:
        logger.info("Job - '%s', Processing file from path - %s", job_id, filepath)
        job = await JobTracker.objects.filter(id=job_id).afirst()
        await job.amark(status=job.Status.IN_PROGRESS)
        gen_ai = GeminiConnector()
        status, file_response = await gen_ai.file_upload(filepath, mime_type)
        if status:
            status, response = await gen_ai.process_request(prompt=W2_FORM_PROMPT, data=file_response)
            if status:
                await job.amark(status=job.Status.SUCCESS, _task_result=response)
            else:
                await job.amark(status=job.Status.FAILED, _task_result=form_error_response(response))
        else:
            await job.amark(status=job.Status.FAILED, _task_result=form_error_response(file_response))
        await cleanup(filepath)
        logger.info("Successfully completed the w2 processing, job - %s", job_id)
    except Exception as exc:
        logger.exception("Error occurred while processing w2 forms...") 
        await job.amark(status=job.Status.FAILED, _task_result=form_error_response(str(exc)))
