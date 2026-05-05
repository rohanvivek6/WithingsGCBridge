import datetime
import logging
from pathlib import Path

import requests
import yaml
import garminconnect
from garth.exc import GarthHTTPError

from models import Measurement

logger = logging.getLogger("wt_gc_bridge")


class GarminClient:
    def __init__(self, tokenstore: str, email: str, password: str) -> None:
        self.tokenstore = tokenstore
        self.email = email
        self.password = password

    def login(self) -> garminconnect.Garmin:
        try:
            garmin = garminconnect.Garmin()
            garmin.login(self.tokenstore)
        except (FileNotFoundError, GarthHTTPError, garminconnect.GarminConnectAuthenticationError):
            logger.debug("Generating tokenstore...")
            try:
                garmin = garminconnect.Garmin(self.email, self.password)
                garmin.login()
                garmin.garth.dump(self.tokenstore)
            except (
                FileNotFoundError,
                GarthHTTPError,
                garminconnect.GarminConnectAuthenticationError,
                requests.exceptions.HTTPError,
            ) as err:
                logger.error("Could not login to Garmin Connect")
                raise err
        logger.debug("Logged into Garmin Connect")
        return garmin

    def upload_body_composition(
        self, garmin: garminconnect.Garmin, measurements: list[Measurement]
    ) -> bool:
        try:
            for measurement in measurements:
                if measurement.weight is None:
                    logger.debug(f"Skipping weightless measurement {measurement}")
                    continue
                timestamp = measurement.datetime
                timestamp = datetime.datetime(
                    year=timestamp.year,
                    month=timestamp.month,
                    day=timestamp.day,
                    hour=timestamp.hour,
                    minute=timestamp.minute,
                    second=timestamp.second,
                    microsecond=123456,  # fake microseconds required by garminconnect
                )
                garmin.add_body_composition(
                    weight=measurement.weight,
                    percent_fat=measurement.percent_fat,
                    muscle_mass=measurement.muscle_mass,
                    timestamp=timestamp.isoformat(),
                )
                logger.info(f"added {measurement} to Garmin Connect")
        except (
            garminconnect.GarminConnectConnectionError,
            garminconnect.GarminConnectAuthenticationError,
            garminconnect.GarminConnectTooManyRequestsError,
            requests.exceptions.HTTPError,
            GarthHTTPError,
        ) as err:
            logger.error(err)
            return False
        return True
