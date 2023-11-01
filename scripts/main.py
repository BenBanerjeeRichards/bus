import sqlite3
from geopy import distance
import json


# How far apart are the timestamps
# Answer: time: 30-40s distance: < 800m
def interpoint_distances():
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    res = cursor.execute("select * from live_location where journey_id=4356").fetchall()
    prev = None
    prev_ts = None
    for r in res:
        point = (r[0], r[1])
        ts = r[3]
        if prev is not None:
            dist = distance.distance(point, prev)
            print(ts-prev_ts, dist.meters, point)
        prev = point
        prev_ts = ts


def service_info():
    services = json.load(open("data/services.json"))
    total = len(services["services"])
    multiple_dests = 0

    for service in services["services"]:
        routes = service["routes"]
        if len(routes) > 2:
            multiple_dests += 1
            dests = [r["destination"] for r in routes]
            print(service["name"], dests)
        elif len(routes) == 2:
            stops_r1 = set(routes[0]["stops"])
            stops_r2 = set(routes[1]["stops"])
            print(service["name"], len(stops_r1.intersection(stops_r2)))

    print(total, multiple_dests)

def main():
    service_info()

if __name__ == '__main__':
    main()
