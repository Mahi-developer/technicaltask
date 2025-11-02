import os
import logging
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task.settings")
django.setup()

from django.utils import timezone
from taskiq import TaskiqMiddleware, TaskiqMessage
from taskiq_redis import ListQueueBroker

from .config import curr_config
from .models import JobTracker
from task.settings import BROKER_BACKEND_URL

logger = logging.getLogger(__name__)


# custom timeout middleware
class TimeoutMiddleware(TaskiqMiddleware):
    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    async def on_task_execute(self, task_func, message):
        return await asyncio.wait_for(task_func(), timeout=self.timeout)

# define taskiq broker
broker = ListQueueBroker(BROKER_BACKEND_URL)
broker.add_middlewares(TimeoutMiddleware(timeout=curr_config.WORKER_TIMEOUT))


@broker.task
async def process_w2_forms(job_id: str, filepath: str):
    try:
        logger.info("Job - '%s', Processing file from path - %s", job_id, filepath)
        job = await JobTracker.objects.filter(id=job_id).afirst()
        await job.amark(status=job.Status.IN_PROGRESS)
        logger.info("Completed the task successfully.")
    except Exception as exc:
        logger.exception("Error occurred while processing w2 forms...") 
