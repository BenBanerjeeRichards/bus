delete from live_location where ROWID in (select live_location.ROWID from live_location
	inner join service on service.id = live_location.service_id
	where service.service = 'MA1' or service.service = 'ET1' or service.service = 'CS1');