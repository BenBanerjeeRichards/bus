import logging
import sqlite3
from py.datatypes import *


def insert_services(connection, services: [(str, str)]):
    cursor = connection.cursor()
    cursor.executemany("insert or ignore into service (service, destination) values (?, ?)", services)


def get_services(connection):
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
    insert_data = [(service_id, p.lat, p.lon, p.stop_id) for p in route.points]
    cursor.executemany("insert or ignore into route_point values (?, ?, ?, ?)", insert_data)
    connection.commit()
    return cursor.rowcount



def connect(path: str):
    return sqlite3.connect(path)
