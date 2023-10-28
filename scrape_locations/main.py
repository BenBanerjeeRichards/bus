import os 
import datetime 
import requests 
import json
import db 
from datatypes import *
import logging 
import sys


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  
        logging.FileHandler('log.log') 
    ]
)



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
    db_path = os.environ.get("SQLITE_PATH")
    if not db_path:
        logging.fatal("Missing configuration environment SQLITE_PATH")
        sys.exit(1)
    conn = db.connect(db_path)
    scrape_locations(conn)

if __name__ == "__main__":
    main()
