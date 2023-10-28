create table if not exists tmp_service (
	id integer primary key,
	service text not null, -- e.g. '26' or 'X26',
	destination text not null   -- e.g. 'Seton Sands'
);

insert into tmp_service(id, service, destination)
select id, service, destination
from service;

drop table service;
alter table tmp_service RENAME TO service;

create unique index if not exists service_name_destination on service (service, destination);
