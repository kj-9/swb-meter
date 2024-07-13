import logging
import os
from logging.config import dictConfig

SWB_METER_LOG_LEVEL = os.getenv("SWB_METER_LOG_LEVEL", "INFO").upper()

# ロギング設定
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": SWB_METER_LOG_LEVEL,
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # 標準出力へログを出力
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": SWB_METER_LOG_LEVEL,
            "propagate": True,
        }
    },
}

dictConfig(logging_config)

logger = logging.getLogger(__name__)
