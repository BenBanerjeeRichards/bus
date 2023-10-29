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
