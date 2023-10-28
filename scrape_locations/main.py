import os 
import datetime 
import hashlib
import requests 
import json
import pytz
import db 
from datatypes import *
import logging 

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  
        logging.FileHandler('log.log') 
    ]
)


def get_key():
    date = datetime.datetime.now(datetime.timezone.utc)
    postfix = f"{date.year}{str(date.month).rjust(2,'0')}{str(date.day).rjust(2,'0')}{str(date.hour).rjust(2,'0')}"
    code = os.environ["LOTHIAN_BUSTRACKER_KEY"]
    return hashlib.md5(f"{code}{postfix}".encode("utf-8")).hexdigest()


def get_journey_times(stop_id: str, journey_id: str | None, bus_id: str | None):
    params["stopId"] = stop_id
    if journey_id is not None:
        params["journeyId"] = journey_id
    if bus_id is not None:
        params["busId"] = bus_id
    return _api_request("getJourneyTimes", params)


def get_bus_times(num_departures, time_requests):
    params = {}
    for i, req in enumerate(time_requests):
        n = i + 1
        if "stopId" in req:
            params[f"stopId{n}"] = req["stopId"]
        if "refService" in req:
            params[f"refService{n}"] = req["refService"]
        if "refDest" in req:
            params[f"refDest{n}"] = req["refDest"]
        params[f"operatorId{n}"] = "LB"
    params["nb"] = num_departures
    return _api_request("getBusTimes", params)


def get_realtime_departures(stop_ids: [str]) -> dict[str, Departure]:
    reqs = [{"stopId": sid for sid in stop_ids}]
    services = get_bus_times(1, reqs)["busTimes"]
    res = {}
    now = datetime.datetime.now()
    uktz = pytz.timezone('Europe/London')
    for service in services:
        time_data = service["timeDatas"][0]# TODO error handling
        if not is_realtime(time_data["reliability"]):
            continue
        local_time = time_data["time"] 
        parts = local_time.split(":")
        dt = uktz.localize(datetime.datetime(now.year, now.month, now.day, int(parts[0]), int(parts[1])))
        res[service["refService"]] = Departure(service["stopId"], service["refService"], dt)
    return res 


def get_bus_stops():
    return _api_request("getBusStops")


def get_services():
    return _api_request("getServices")


def is_realtime(status: str):
    # H = realtime low floor, F = realtime non-low floor (I don't think F exists anymore in practise)
    return status == "H" or status == "F"


def _api_request(function: str, params={}):
    params["function"] = function
    params["key"] = get_key()

    r = requests.get("http://ws.mybustracker.co.uk/?module=json", params=params)
    r.raise_for_status()
    return r.json()

def get_vehicle_locations() -> [ApiLiveLocation]:
    r = requests.get("https://tfe-opendata.com/api/v1/vehicle_locations")
    r.raise_for_status()
    return [ApiLiveLocation(l["latitude"], l["longitude"], l["heading"], l["last_gps_fix"], 
        l["vehicle_id"], l["speed"], l["next_stop_id"],l["journey_id"], l["service_name"], 
        l["destination"]) for l in r.json()["vehicles"] if l["service_name"] != None]


def scrape_locations():

    locations = get_vehicle_locations()

    # First insert any services that don't already exist
    services = []
    live_locations = []
    for loc in locations:
        s = (loc.service_name, loc.destination)
        if s not in services:
            services.append(s)
    logging.info("Got %s live vehicle locations from open-tfe API", len(locations))
    db.insert_services(services)
    service_mapping = db.get_services()

    for l in locations:
        sid = service_mapping[(l.service_name, l.destination)]
        live_locations.append(LiveLocation(l.lat, l.lon, l.heading, l.last_fix_timestamp, l.vehicle_id, l.speed, 
            l.next_stop_id, l.journey_id, sid))

    num_inserted = db.insert_live_locations(live_locations)
    logging.info("Inserted %s live_locations", num_inserted)


if __name__=="__main__":
    scrape_locations()