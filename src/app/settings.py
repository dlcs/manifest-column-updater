import json
import os


def _get_boolean(env_name: str, fallback: str) -> bool:
    return os.environ.get(env_name, fallback).lower() in ("true", "t", "1")


# Database
DRY_RUN = _get_boolean("DRY_RUN", "False")
CONNECTION_TIMEOUT = os.environ.get("CONNECTION_TIMEOUT")
ASSET_SPLIT_SIZE = os.environ.get("ASSET_SPLIT_SIZE", 100)

PRESENTATION_CONNECTION_STRING = os.environ.get("PRESENTATION_CONNECTION_STRING")

PROTAGONIST_BASE_URL = os.environ.get("PROTAGONIST_BASE_URL")

DLCS_API_AUTH = os.environ.get("DLCS_API_AUTH")
EXIT_ON_ERROR = _get_boolean("EXIT_ON_ERROR", "False")