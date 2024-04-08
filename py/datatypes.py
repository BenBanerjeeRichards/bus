from dataclasses import dataclass


@dataclass
class ApiLiveLocation:
    lat: float
    lon: float
    heading: int
    last_fix_timestamp: int
    vehicle_id: str
    speed: int
    next_stop_id: str
    journey_id: str
    service_name: str
    destination: str


@dataclass
class LiveLocation:
    lat: float
    lon: float
    heading: int
    timestamp: int
    vehicle_id: str
    speed: int
    next_stop_id: str
    journey_id: str
    service_id: int


@dataclass
class Stop:
    id: str
    atco_code: str
    lat: float
    lon: float
    name: str
    orientation: int
    direction: str
    identifier: str
    locality: str


@dataclass
class Point:
    lat: float
    lon: float
    stop_id: int
    seq: int


@dataclass
class Route:
    service: str  # e.g. 35
    destination: str  # e.g. Ocean terminal
    points: list[Point]


@dataclass
class Marker:
    lat: float
    lon: float
    color: str
    shape: str
    message: str


@dataclass
class BusPosition:
    lat: float
    lon: float
    prev_stop: Point
    next_stop: Point
    # How far between prev_stop and next_stop are we 0 <= progress_prop <= 1
    progress_prop: float
