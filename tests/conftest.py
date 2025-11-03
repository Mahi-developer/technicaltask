import pytest
from pathlib import Path
from django.test import AsyncClient, TestCase

from task.settings import TMP_DIR


@pytest.fixture
async def async_client():
    return AsyncClient()


class TestBase(TestCase):

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Runs automatically before each test in this class."""
        self.client = AsyncClient()

    @classmethod
    def cleanup(cls):
        try:
            tmp_dir = Path(TMP_DIR)
            for extension in ["*.pdf", "*.png", "*.webp", "*.jpg"]:
                for file_path in tmp_dir.glob(extension):
                    file_path.unlink()
        except Exception:
            pass
