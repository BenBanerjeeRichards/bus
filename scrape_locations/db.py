import sqlite3
from datatypes import *
import logging 
import os 




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


def insert_live_locations(connection, live_locations: [LiveLocation]) -> int:
    cursor = connection.cursor()
    data = [(l.lat, l.lon, l.heading, l.timestamp, l.vehicle_id, l.speed, l.next_stop_id, 
        l.journey_id, l.service_id) for l in live_locations]
    cursor.executemany("insert or ignore into live_location values (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    connection.commit()
    return cursor.rowcount


def connect(path: str):
    return sqlite3.connect(path)
