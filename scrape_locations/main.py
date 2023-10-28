import os 
import datetime 
import requests 
import json
import db 
from datatypes import *
import logging 
import sys



def get_vehicle_locations() -> [ApiLiveLocation]:
    r = requests.get("https://tfe-opendata.com/api/v1/vehicle_locations")
    r.raise_for_status()
    return [ApiLiveLocation(l["latitude"], l["longitude"], l["heading"], l["last_gps_fix"], 
        l["vehicle_id"], l["speed"], l["next_stop_id"],l["journey_id"], l["service_name"], 
        l["destination"]) for l in r.json()["vehicles"] if l["service_name"] != None]


def scrape_locations(conn):

    locations = get_vehicle_locations()

    # First insert any services that don't already exist
    services = []
    live_locations = []
    for loc in locations:
        s = (loc.service_name, loc.destination)
        if s not in services:
            services.append(s)
    logging.info("Got %s live vehicle locations from open-tfe API", len(locations))
    db.insert_services(conn, services)
    service_mapping = db.get_services(conn)

    for l in locations:
        sid = service_mapping[(l.service_name, l.destination)]
        live_locations.append(LiveLocation(l.lat, l.lon, l.heading, l.last_fix_timestamp, l.vehicle_id, l.speed, 
            l.next_stop_id, l.journey_id, sid))

    num_inserted = db.insert_live_locations(conn, live_locations)
    logging.info("Inserted %s live_locations", num_inserted)



def main():
    log_path = os.environ.get("LOG_PATH")
    if not log_path:
        print("Missing configuration environment LOG_PATH")
        sys.exit(1)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  
            logging.FileHandler(log_path) 
        ]
    )

    db_path = get_required_env("SQLITE_PATH")
    conn = db.connect(db_path)
    scrape_locations(conn)

def get_required_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        logging.fatal("Missing configuration environment %s", name)
        sys.exit(1)
    return v 


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        logging.fatal("Error occured", exc_info=e)
        sys.exit(1)
