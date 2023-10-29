import logging
import os
import sys


def setup_logging(path: str):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(path)
        ]
    )


def get_required_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        logging.fatal("Missing configuration environment %s", name)
        sys.exit(1)
    return v
