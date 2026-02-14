import json
import os
from dataclasses import dataclass
from typing import Dict, Any

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(BASE_DIR, "config")


@dataclass
class EmailConfig:
    host: str
    port: int
    user: str
    password: str
    sender: str
    recipient: str


@dataclass
class AppConfig:
    datafiniti_api_key: str
    estated_api_key: str
    data_dir: str
    db_path: str
    criteria: Dict[str, Any]
    email: EmailConfig


def _resolve_path(path_value: str) -> str:
    if not path_value:
        return path_value
    if os.path.isabs(path_value):
        return path_value
    return os.path.abspath(os.path.join(BASE_DIR, path_value))


def load_criteria() -> Dict[str, Any]:
    criteria_path = os.path.join(CONFIG_DIR, "criteria.json")
    with open(criteria_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> AppConfig:
    load_dotenv(os.path.join(CONFIG_DIR, ".env"))

    data_dir = _resolve_path(os.getenv("DATA_DIR", "./data"))
    db_path = _resolve_path(os.getenv("DB_PATH", "./data/app.db"))

    email = EmailConfig(
        host=os.getenv("EMAIL_SMTP_HOST", ""),
        port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
        user=os.getenv("EMAIL_SMTP_USER", ""),
        password=os.getenv("EMAIL_SMTP_PASS", ""),
        sender=os.getenv("EMAIL_FROM", ""),
        recipient=os.getenv("EMAIL_TO", ""),
    )

    return AppConfig(
        datafiniti_api_key=os.getenv("DATAFINITI_API_KEY", ""),
        estated_api_key=os.getenv("ESTATED_API_KEY", ""),
        data_dir=data_dir,
        db_path=db_path,
        criteria=load_criteria(),
        email=email,
    )


def ensure_data_dirs(config: AppConfig) -> None:
    if config.data_dir:
        os.makedirs(config.data_dir, exist_ok=True)
