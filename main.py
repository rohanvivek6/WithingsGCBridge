import logging
import os
import time

from config import load_config
from bridge import WithingsGCBridge

UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 0))
PORT = int(os.getenv("WITHINGS_PORT", 5681))
log_level = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=logging._nameToLevel[log_level])
logger = logging.getLogger("wt_gc_bridge")

if __name__ == "__main__":
    logger.info("Starting WithingsGCBridge")
    config = load_config(PORT)
    bridge = WithingsGCBridge(config)
    if UPDATE_INTERVAL > 0:
        while True:
            try:
                bridge.sync()
            except Exception:
                logger.exception("Sync failed; will retry next interval")
            time.sleep(UPDATE_INTERVAL)
    else:
        bridge.sync()
