from dataclasses import dataclass
import datetime 


@dataclass
class Departure:
    stop_id: str
    service_id: str 
    date_time: datetime.datetime


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
