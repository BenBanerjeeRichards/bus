from py.db import *
from py.datatypes import *
from py.util import *
import requests


def _get_stops() -> [Stop]:
    res = requests.get("https://tfe-opendata.com/api/v1/stops")
    res.raise_for_status()
    return [Stop(j["stop_id"], j["atco_code"], j["latitude"], j["longitude"], j["name"], j["orientation"],
                 j["direction"], j["identifier"], j["locality"]) for j in res.json()["stops"]]


def sync_stops(conn):
    stops = _get_stops()
    return save_stops(conn, stops)


def main():
    log_path = os.environ.get("LOG_PATH")
    if not log_path:
        print("Missing configuration environment LOG_PATH")
        sys.exit(1)
    setup_logging(log_path)
    db_path = get_required_env("SQLITE_PATH")
    connection = connect(db_path)

    num_stops_saved = sync_stops(connection)
    if num_stops_saved > 0:
        logging.info("Saved %s stops", num_stops_saved)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        logging.fatal("Error:", exc_info=e)
        sys.exit(1)
