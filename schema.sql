-- The purpose of this is really to allow the very large live_location table to refer 
-- to services by a small number to keep disk use low 
create table if not exists service (
	id integer primary key,
	service text not null, -- e.g. '26' or 'X26',
	destination text not null   -- e.g. 'Seton Sands'
);

create unique index if not exists service_name_destination on service (service, destination);

create table if not exists live_location (
	lat real,
	lon real,
	heading int, -- 90 = East
	timestamp int,
	vehicle_id text, -- lothian vehicle id (same as number on front of bus )
	speed int, -- mph
	next_stop_id text,
	journey_id text,
	service_id int,
	run_id int,  -- Set when route processing completed. No FK to keep migration simple
	primary key (vehicle_id, timestamp),
	foreign key (service_id) references service(id)
);

create index if not exists live_loc_timestamp on live_location (timestamp);

create table if not exists stop (
    id text primary key, -- Naptan code
    atco_code text not null unique,
    lat real not null,
    lon real not null,
    name text not null,
    orientation real, -- bearing e.g. 128
    direction text, -- N, E, S, W, NE, SW, ...
    identifier text, -- code for dense locations - e.g. PX, PT, ...
    locality text -- Broad area stop is located in - Edinburgh (for centre), Holyrood, West End etc
);

create table if not exists route_point (
    service_id int,
    lat int not null,
    lon int not null,
    stop_id int,
    sequence int not null, -- order of points
    primary key (service_id, lat, lon),
    foreign key (stop_id) references stop (id)
);

-- Concept of a specific bus carrying out a bus run on a service
create table if not exists run (
    route_id int primary key,
    service_id int not null,
    vehicle_id int not null,
    start_timestamp int not null,
    end_timestamp int,
    start_stop_id int,
    end_stop_id int,
    journey_id int, -- lothian journey id - not sure exactly what this is for
    unique (service_id, vehicle_id, start_timestamp),
    foreign key (service_id) references service (id),
    foreign key (start_stop_id) references stop (id),
    foreign key (end_stop_id) references stop (id)
);

-- Result of processing live_location with route information
-- Adds stop info and distance
-- Denormalized for easy of future processing
create table if not exists bus_position (
    run_id int,
    timestamp int,
    lat float not null,
    lon float not null,
    prev_stop_id int not null, --if at start, equals first stop (progress_prop = 0)
    next_stop_id int not null, -- if at end, equals last stop (progress_prop = 1)
    inter_stop_distance_metres float not null,
     -- 0 <= progress_prop <= 1. Distance from first stop = progress_prop * inter_stop_distance_metres
    progress_prop float not null,
    primary key (run_id, timestamp),
    foreign key (prev_stop_id) references stop (id),
    foreign key (next_stop_id) references stop (id),
    foreign key (run_id) references run(id)
);