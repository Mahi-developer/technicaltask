import os
from task.settings import CURR_ENV

class Config:
    ALLOWED_FILE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'application/pdf']
    WORKER_TIMEOUT = 120
    GEMINI_MODEL_ID = "gemini-2.5-flash"
    OMDB_URL = "https://www.omdbapi.com/"
    GEMINI_API_KEY = os.getenv("GEMINI_API_X", "")
    OMDB_API_KEY = os.getenv("OMDB_API_X", "")
    OMDB_RESULT_PER_PAGE = 10
    REDIS_CACHE_DEFAULT_TTL = 300

class LocalConfig(Config):
    MAX_CONCURRENCY = 5
    MOVIES_CACHE_TTL = 300  # 5 minutes

class TestConfig(Config):
    MAX_CONCURRENCY = 10
    MOVIES_CACHE_TTL = 600

class ProdConfig(Config):
    MAX_CONCURRENCY = 20
    MOVIES_CACHE_TTL = 600

env_config = {
    "local": LocalConfig,
    "test": TestConfig,
    "prod": ProdConfig
}
curr_config = env_config[CURR_ENV]