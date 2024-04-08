import logging
import sqlite3
from py.datatypes import *


def insert_services(connection, services: [(str, str)]):
    cursor = connection.cursor()
    cursor.executemany("insert or ignore into service (service, destination) values (?, ?)", services)


def get_services(connection) -> dict[tuple[str, str], int]:
    cursor = connection.cursor()
    records = cursor.execute("select * from service").fetchall()
    res = {}
    for record in records:
        res[(record[1], record[2])] = record[0]

    return res


def insert_live_locations(connection, live_locations: list[LiveLocation]) -> int:
    cursor = connection.cursor()
    data = [(l.lat, l.lon, l.heading, l.timestamp, l.vehicle_id, l.speed, l.next_stop_id,
             l.journey_id, l.service_id) for l in live_locations]
    cursor.executemany("insert or ignore into live_location values (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    connection.commit()
    return cursor.rowcount


def save_stops(connection, stops: list[Stop]) -> int:
    cursor = connection.cursor()
    data = [(s.id, s.atco_code, s.lat, s.lon, s.name, s.orientation, s.direction, s.identifier, s.locality)
            for s in stops]
    cursor.executemany("insert or ignore into stop values (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    connection.commit()
    return cursor.rowcount


def save_route(connection, service_id: int, route: Route) -> int:
    cursor = connection.cursor()
    insert_data = [(service_id, p.lat, p.lon, p.stop_id, p.seq) for p in route.points]
    cursor.executemany("insert or ignore into route_point values (?, ?, ?, ?, ?)", insert_data)
    connection.commit()
    return cursor.rowcount


def get_service_stops(connection, service_id: int) -> [Point]:
    cursor = connection.cursor()
    res = cursor.execute("select lat, lon, stop_id, sequence from route_point where service_id = ? and stop_id is not null order by seq asc",
                             (str(service_id),)).fetchall()
    return [Point(*p) for p in res]


def get_service_points(connection, service_id: int) -> [Point]:
    cursor = connection.cursor()
    res = cursor.execute("select lat, lon, stop_id, sequence from route_point where service_id = ? order by sequence asc",
                             (str(service_id),)).fetchall()
    return [Point(*p) for p in res]


def paginated_get_live_locations_by_service_id(connection, service_id, batch_size=1000):
    return _paginated_query(connection, "select * from live_location where service_id = ?",
                            (service_id,), lambda r: LiveLocation(*r), batch_size)


def _paginated_query(connection, query: str, params: tuple, mapping, count: int):
    cursor = connection.cursor()
    current_offset = 0
    result = None
    while result is None or len(result) > 0:
        result = cursor.execute(query + " limit ? offset ?", (*params, count, current_offset)).fetchall()
        yield [mapping(r) for r in result]
        current_offset += count


def connect(path: str):
    return sqlite3.connect(path)
