import requests
from py import db
from py.datatypes import *
from py.util import *
import logging
import sys

TOUR_BUS_SERVICES = ["CS1", "MA1", "ET1"]


# Filter out any locations we don't want
# TODO this should also include buses still at a depot
def _filter_live_locations(locations: list[ApiLiveLocation]) -> list[ApiLiveLocation]:
    return [loc for loc in locations if loc.service_name is not None and loc.service_name not in TOUR_BUS_SERVICES]


def get_vehicle_locations() -> [ApiLiveLocation]:
    r = requests.get("https://tfe-opendata.com/api/v1/vehicle_locations")
    r.raise_for_status()
    locs = [ApiLiveLocation(l["latitude"], l["longitude"], l["heading"], l["last_gps_fix"],
                            l["vehicle_id"], l["speed"], l["next_stop_id"], l["journey_id"], l["service_name"],
                            l["destination"]) for l in r.json()["vehicles"]]
    return _filter_live_locations(locs)


def scrape_locations(conn):
    locations = get_vehicle_locations()

    # First insert any services that don't already exist
    services = []
    live_locations = []
    for loc in locations:
        destination = "" if loc.destination is None else loc.destination  # e.g. CS1
        s = (loc.service_name, destination)
        if s not in services:
            services.append(s)
    logging.info("Got %s live vehicle locations from open-tfe API", len(locations))
    db.insert_services(conn, services)
    service_mapping = db.get_services(conn)

    for l in locations:
        service_key = (l.service_name, "" if l.destination is None else l.destination)
        if service_key not in service_mapping:
            logging.warn("Service %s not found in database", service_key)
            continue
        sid = service_mapping[service_key]
        live_locations.append(LiveLocation(l.lat, l.lon, l.heading, l.last_fix_timestamp, l.vehicle_id, l.speed,
                                           l.next_stop_id, l.journey_id, sid))

    num_inserted = db.insert_live_locations(conn, live_locations)
    logging.info("Inserted %s live_locations", num_inserted)


def main():
    log_path = os.environ.get("LOG_PATH")
    if not log_path:
        print("Missing configuration environment LOG_PATH")
        sys.exit(1)
    setup_logging(log_path)

    db_path = get_required_env("SQLITE_PATH")
    conn = db.connect(db_path)
    scrape_locations(conn)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        logging.fatal("Error:", exc_info=e)
        sys.exit(1)
