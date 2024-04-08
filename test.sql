select distinct live_location.service_id, service.* from live_location 
	inner join service on service.id = live_location.service_id
	where service_id not in (select distinct service_id from route_point)
	order by service.service asc;