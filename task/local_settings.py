LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{name} | {levelname} | {asctime} | {module} | {process:d} | {thread:d} | {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "./logs/app.log",
            "formatter": "verbose",
        },
        "error": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "./logs/app_error.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file", "error"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}