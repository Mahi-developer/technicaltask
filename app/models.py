import uuid
from django.db import models
from django.utils import timezone

class JobTracker(models.Model):
    """
    Stores background job details — status, timing, and result/exception info.
    """

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In-Progress"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    created_dtm = models.DateTimeField(auto_now_add=True)
    modified_dtm = models.DateTimeField(auto_now=True)
    task_result = models.TextField(null=True)

    class Meta:
        db_table = "job_tracker"

    async def amark(self, status: str, **fields):
        """
        Async-safe status updater for async tasks.
        """
        self.status = status
        if status == self.Status.IN_PROGRESS:
            self.started_at = timezone.now()
        elif status in [self.Status.SUCCESS, self.Status.FAILED, self.Status.CANCELLED]:
            self.finished_at = timezone.now()

        for key, value in fields.items():
            setattr(self, key, value)

        await self.asave(update_fields=["status", "started_at", "finished_at", *fields.keys()])

    def __str__(self):
        return f"{self.name} ({self.status})"