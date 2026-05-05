import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger("wt_gc_bridge")

SECRETS_PATH = Path("/data/secrets.yaml")
DEFAULT_TOKENSTORE = "/data/.tokenstore"


@dataclass
class Config:
    withings_client_id: str
    withings_client_secret: str
    withings_callback_uri: str
    garmin_email: str
    garmin_password: str


def load_config(port: int) -> Config:
    try:
        with SECRETS_PATH.open() as f:
            secrets = yaml.safe_load(f)
    except Exception as err:
        logger.error("Could not load secrets.yaml")
        raise err

    try:
        withings_client_id = secrets["withings"]["client_id"]
        withings_client_secret = secrets["withings"]["secret"]
        garmin_email = secrets["garmin"]["email"]
        garmin_password = secrets["garmin"]["password"]
    except KeyError as err:
        logger.error("Could not load secrets.yaml")
        raise err

    callback_uri = secrets["withings"].get(
        "callback_uri", f"http://127.0.0.1:{port}"
    )

    return Config(
        withings_client_id=withings_client_id,
        withings_client_secret=withings_client_secret,
        withings_callback_uri=callback_uri,
        garmin_email=garmin_email,
        garmin_password=garmin_password,
    )
