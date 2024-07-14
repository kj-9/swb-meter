import os
from datetime import datetime
from pathlib import Path

from sqlite_utils import Database


def get_db():
    db_path = Path(os.getenv("SWB_METER_DB_PATH", "./swb_meter.db"))

    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch()

    db = Database(db_path)

    return db


def get_temperature_table():
    db = get_db()
    t = db["Temperature"]

    return t


def get_meter_table():
    db = get_db()
    t = db["Meter"]

    return t


TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def datetime_to_str(datetime_obj: datetime) -> str:
    return datetime_obj.strftime(TIMESTAMP_FORMAT)


def str_to_datetime(datetime_str: str) -> datetime:
    return datetime.strptime(datetime_str, TIMESTAMP_FORMAT)
