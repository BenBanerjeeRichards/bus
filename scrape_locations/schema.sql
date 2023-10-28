-- The purpose of this is really to allow the very large live_location table to refer 
-- to services by a small number to keep disk use low 
create table if not exists service (
	id integer primary key autoincrement,
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
	primary key (vehicle_id, timestamp),
	foreign key (service_id) references service(id)
)

-- TODO indexex for live_location