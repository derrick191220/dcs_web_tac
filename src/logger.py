import logging
import sys

# Configure structured logging for the project
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/app.log")
        ]
    )
    return logging.getLogger("dcs_web_tac")

logger = setup_logging()
