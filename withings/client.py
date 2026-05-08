import datetime
import logging
from typing import Any

import requests

from models import Measurement

_TIMEOUT = (10, 30)  # (connect seconds, read seconds)

logger = logging.getLogger("wt_gc_bridge")


class WithingsClient:
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def get_measurements(self, last_sync: datetime.datetime) -> list[Measurement]:
        headers = {"Authorization": "Bearer " + self.access_token}
        payload: dict[str, Any] = {
            "action": "getmeas",
            "meastypes": "1,6,76,88",
            "category": 1,
            "lastupdate": int(last_sync.timestamp()),
        }
        logger.debug("Requesting measurements from Withings...")
        result = requests.get(
            "https://wbsapi.withings.net/v2/measure", headers=headers, params=payload,
            timeout=_TIMEOUT
        ).json()
        logger.debug(f"Withings response: {result}")

        try:
            measurement_groups = result["body"]["measuregrps"]
        except KeyError:
            logger.error(f"Could not retrieve measurements from Withings. Response:\n{result}")
            raise KeyError

        logger.info(f"Retrieved {len(measurement_groups)} measurements from Withings")
        return [self._to_measurement(m) for m in measurement_groups]

    @staticmethod
    def _to_measurement(payload: dict) -> Measurement:
        def standardize(measure: dict) -> float:
            return measure["value"] * 10 ** measure["unit"]

        date = datetime.datetime.fromtimestamp(payload["date"])
        by_type = {m["type"]: standardize(m) for m in payload["measures"]}
        return Measurement(
            datetime=date,
            weight=by_type.get(1),
            percent_fat=by_type.get(6),
            muscle_mass=by_type.get(76),
            bone_mass=by_type.get(88),
        )
