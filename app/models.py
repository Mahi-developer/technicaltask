import uuid
import json
import copy
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

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
    _task_result = models.JSONField(null=True, db_column="task_result")

    class Meta:
        db_table = "job_tracker"
        
    MASKED_KEYS = ["employee_info.ssn", "employer_info.ein"]

    @staticmethod
    def _mask_nested_keys(key, data):
        nested_keys = key.split(".")
        _d = data
        for curr_key in nested_keys:
            if curr_key not in _d:
                break
            if isinstance(_d[curr_key], dict):
                _d = _d[curr_key]
            else:
                val = _d[curr_key]
                _d[curr_key] = "*" * (len(val) - 4) + val[-4:]

    @cached_property
    def task_result(self):
        """Return masked details for app-level access."""
        data = {}
        if self._task_result:
            data = copy.deepcopy(self._task_result)
            data = json.loads(self._task_result)
            for key in self.MASKED_KEYS:
                self._mask_nested_keys(key, data)
        return data

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
        return f"{self.id} ({self.status})"
    
    def to_dict(self):
        result = self.task_result or {}
        return {
            "status": self.status,
            "meta": {
                "job_id": self.id.hex,
                "created_time": self.created_dtm,
                "start_time": self.started_at,
                "end_time": self.finished_at
            },
            "result": result,
        }
