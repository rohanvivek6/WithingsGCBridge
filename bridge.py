import datetime
import logging
import urllib.parse
from pathlib import Path

from config import Config, DEFAULT_TOKENSTORE
from withings.auth import WithingsAuth, start_callback_server
from withings.client import WithingsClient
from garmin.client import GarminClient

logger = logging.getLogger("wt_gc_bridge")


class WithingsGCBridge:
    def __init__(self, config: Config) -> None:
        self.config = config
        parsed_uri = urllib.parse.urlparse(config.withings_callback_uri)
        logger.debug(f"Running flask endpoint {parsed_uri}")
        start_callback_server(parsed_uri.port)

    def sync(self) -> None:
        garmin_client = GarminClient(
            tokenstore=DEFAULT_TOKENSTORE,
            email=self.config.garmin_email,
            password=self.config.garmin_password,
        )
        garmin = garmin_client.login()
        logger.info("Logged into Garmin Connect")

        withings_auth = WithingsAuth(
            client_id=self.config.withings_client_id,
            client_secret=self.config.withings_client_secret,
            callback_uri=self.config.withings_callback_uri,
            tokenstore=DEFAULT_TOKENSTORE,
        )
        access_token = withings_auth.init()

        last_sync_path = Path("/data/.last_sync.txt")
        if not last_sync_path.exists():
            logger.info("Could not determine last sync date. Syncing last 7 days.")
            last_sync = datetime.datetime.now() - datetime.timedelta(days=7)
        else:
            with last_sync_path.open("r") as f:
                last_sync = datetime.datetime.fromisoformat(f.read().strip())

        withings_client = WithingsClient(access_token)
        measurements = withings_client.get_measurements(last_sync)

        if garmin_client.upload_body_composition(garmin, measurements):
            with last_sync_path.open("w") as f:
                f.write(datetime.datetime.now().isoformat())
        else:
            logger.error("Could not upload weights to Garmin Connect")
