import os
from task.settings import CURR_ENV

class Config:
    ALLOWED_FILE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'application/pdf']
    WORKER_TIMEOUT = 120

class LocalConfig(Config):
    GEMINI_API_KEY = os.getenv("GEMINI_API_X", "")

class TestConfig(Config):
    GEMINI_API_KEY = os.getenv("GEMINI_API_X", "")

class ProdConfig(Config):
    GEMINI_API_KEY = os.getenv("GEMINI_API_X", "")


env_config = {
    "local": LocalConfig,
    "test": TestConfig,
    "prod": ProdConfig
}
curr_config = env_config[CURR_ENV]