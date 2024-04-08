import sqlite3
from geopy import distance
import json
from py.db import *
from py.map.map import *
import time


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
            print(ts - prev_ts, dist.meters, point)
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


def _point_idx(point: Point, points: list[Point]) -> int | None:
    for i, p in enumerate(points):
        if p.lat == point.lat and p.lon == point.lon and p.stop_id == point.stop_id:
            return i
    return None


def _interpoint_distances(points: [Point]) -> list[float]:
    distances = []
    for i in range(1, len(points)):
        p1 = points[i - 1]
        p2 = points[i]
        distances.append(distance.distance((p1.lat, p1.lon), (p2.lat, p2.lon)).meters)
    return distances


def _next_stop(points: list[Point], current_idx: int, look_fwd: bool):
    dir = 1 if look_fwd else -1
    while points[current_idx].stop_id is None and 0 < current_idx < len(points) - 1:
        current_idx += dir
    return points[current_idx]


def _slow_get_nearest_point_index(points: list[Point], live_location: LiveLocation):
    distances = [distance.distance((p.lat, p.lon), (live_location.lat, live_location.lon)).meters for p in points]
    return distances.index(min(distances))


def _get_nearest_point_index(points: list[Point], live_location: LiveLocation):
    next_stops = [(i, stop) for i, stop in enumerate(points) if stop.stop_id == int(live_location.next_stop_id)]
    idx_next_stop = None if len(next_stops) == 0 else next_stops[0]
    idx, next_stop = idx_next_stop
    if distance.distance((live_location.lat, live_location.lon), (next_stop.lat, next_stop.lon)).meters > 200:
        # next stop is too far away - just check all points
        return _slow_get_nearest_point_index(points, live_location)
    # If we are close to the next_stop, just check 10 points in either direction - much faster than checking them all
    range_start, range_end = max(0, idx - 10), min(len(points), idx + 10)
    return _slow_get_nearest_point_index(points[range_start:range_end], live_location) + range_start


def _get_departed_point_index(points: list[Point], live_location: LiveLocation):
    nearest_point_idx = _get_nearest_point_index(points, live_location)
    nearest_point = points[nearest_point_idx]
    if nearest_point_idx == 0:
        return nearest_point_idx
    if nearest_point_idx == len(points) - 1:
        # Must have departed the previous point
        return nearest_point_idx - 1
    (lat, lon) = (live_location.lat, live_location.lon)
    # A: ----P1-----------P2--------*----P3--------------------P4------
    # B: ----P1-----------P2-------------P3---*----------------P4------
    # Now we know the closest point the location is near (P3), we must determine whether we are approaching
    # this point (e.g. case A) or have just departed the point (e.g. case B).
    # If d(P2, *) < d(P2, P3), then we know that we have departed P2, Otherwise we have departed P3
    prev_point = points[nearest_point_idx - 1]
    distance_p2_to_p3 = distance.distance((prev_point.lat, prev_point.lon), (nearest_point.lat, nearest_point.lon)).meters
    distance_p2_to_loc = distance.distance((prev_point.lat, prev_point.lon), (lat, lon)).meters
    is_arriving_at_nearest = distance_p2_to_loc < distance_p2_to_p3
    # If we are arriving at P3, we must go back one to get to last departed point
    return nearest_point_idx - 1 if is_arriving_at_nearest else nearest_point_idx


# Given a live location and a route that point is on, find the previous and next stop
# The live_location.next_stop_id can not be trusted as it is often delayed
def get_bus_position(points: list[Point], live_location: LiveLocation, point_distances: list[float]) \
        -> BusPosition | None:
    last_departed_point_idx = _get_departed_point_index(points, live_location)
    prev_stop = _next_stop(points, last_departed_point_idx, False)
    next_stop = _next_stop(points, last_departed_point_idx + 1, True)
    prev_stop_idx = _point_idx(prev_stop, points)
    next_stop_idx = _point_idx(next_stop, points)
    if prev_stop_idx is None or next_stop_idx is None:
        return None

    departed_point = points[last_departed_point_idx]
    inter_stop_distance = sum(point_distances[prev_stop_idx:next_stop_idx])
    if inter_stop_distance == 0:
        return None
    up_to_nearest_point_distance = sum(point_distances[prev_stop_idx:last_departed_point_idx])
    nearest_point_to_current_pos = distance.distance((live_location.lat, live_location.lon),
                                                     (departed_point.lat, departed_point.lon)).meters
    progress = (nearest_point_to_current_pos + up_to_nearest_point_distance) / inter_stop_distance
    return BusPosition(live_location.lat, live_location.lon, prev_stop, next_stop, progress)


def main():
    connection = connect("db.sqlite")
    points = get_service_points(connection, 1)
    point_distances = _interpoint_distances(points)
    skipped = 0
    markers = []
    i = 0
    for batch in paginated_get_live_locations_by_service_id(connection, 1, batch_size=1000):
        start = time.time()
        for live_location in batch:
            i += 1
            res = get_bus_position(points, live_location, point_distances)
            if res is None:
                skipped += 1
                continue

            prev_stop, next_stop = res.prev_stop, res.next_stop
            print(i, prev_stop.stop_id, next_stop.stop_id, res.progress_prop)
            color = rand_color()
            markers.append(Marker(prev_stop.lat, prev_stop.lon, color, 'diamond', f"{i}:{prev_stop.stop_id}:prev"))
            markers.append(Marker(next_stop.lat, next_stop.lon, color, 'diamond', f"{i}:{next_stop.stop_id}:next"))
            markers.append(Marker(live_location.lat, live_location.lon, color, None, f"{i}:{int(100*res.progress_prop)}%"))

        duration = 1000 * (time.time() - start)
        print(f"Done: {duration}ms, {duration / i}ms/record ")
        open_map(markers)
        break
    print(skipped)


if __name__ == '__main__':
    main()
