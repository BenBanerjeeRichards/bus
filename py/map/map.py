import json
from py.datatypes import *
import tempfile
import webbrowser
import uuid

import random


def rand_color():
    chars = '0123456789ABCDEF'
    return '#' + ''.join(random.sample(chars, 6))


def jitter(lat, lon):
    # Add jitter so we can see when points overlayed
    lat_jitter = random.randint(1, 9) * 1 / 100000 * (1 if random.choice([True, False]) else -1)
    lon_jitter = random.randint(1, 9) * 1 / 1000000 * (1 if random.choice([True, False]) else -1)
    return lat + lat_jitter, lon + lon_jitter


def generate_data(markers: list[Marker]) -> str:
    res = []
    for m in markers:
        lat, lon = jitter(m.lat, m.lon)
        res.append({"lat": lat, "lon": lon, "color": m.color,
                    "shape": m.shape, "message": m.message})
    return json.dumps(res)


def generate_index(out: str, markers: list[Marker]):
    marker_json = generate_data(markers)
    with open("py/map/index.html") as f:
        html = f.read().replace("{markers}", marker_json)
        with open(out, 'w+') as f2:
            f2.write(html)


def open_map(markers: list[Marker]):
    temp_path = f"{tempfile.gettempdir()}/{str(uuid.uuid4())}.html"
    generate_index(temp_path, markers)
    webbrowser.open("file://" + temp_path)
