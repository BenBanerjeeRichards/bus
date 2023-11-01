from py.db import *
from py.datatypes import *
from py.util import *
import requests


def _get_stops() -> [Stop]:
    res = requests.get("https://tfe-opendata.com/api/v1/stops")
    res.raise_for_status()
    return [Stop(j["stop_id"], j["atco_code"], j["latitude"], j["longitude"], j["name"], j["orientation"],
                 j["direction"], j["identifier"], j["locality"]) for j in res.json()["stops"]]


def sync_stops(conn):
    stops = _get_stops()
    return save_stops(conn, stops)


def _get_routes() -> [Route]:
    res = requests.get("https://tfe-opendata.com/api/v1/services")
    res.raise_for_status()
    routes = []
    for service in res.json()["services"]:
        for route in service["routes"]:
            points = []
            for point in route["points"]:
                points.append(Point(point["latitude"], point["longitude"], point["stop_id"]))
            routes.append(Route(service["name"], route["destination"], points))
    return routes


def _normalise_destination(d: str) -> str:
    return (d.lower().replace("'", "").replace("-", "")
            .replace("infirmary", "infirmry")
            .replace("uni", "").replace("university", "")
            .replace("granton harbour", "granton")
            .replace("edinburgh airport", "airport")
            .replace(" ", "")
            .replace("buildings", "buildngs"))


def _destination_to_service_id(service_mapping: dict, service: str, destination: str):
    # Some special cases
    if service == "124" and destination == "West End":
        destination = "Edinburgh"
    s = service_mapping.get((service, destination))
    if s:
        return s
    for (service_code, service_destination), s_id in service_mapping.items():
        if service_code != service:
            continue
        if _normalise_destination(destination) == _normalise_destination(service_destination):
            return s_id
    return None


def sync_routes(conn):
    routes = _get_routes()
    services = get_services(conn)
    for route in routes:
        service_id = _destination_to_service_id(services, route.service, route.destination)
        if not service_id:
            logging.error("Failed to find existing service %s %s", route.service, route.destination)
            continue

        inserted = save_route(conn, service_id, route)
        logging.info("Inserted %s records for service %s %s", inserted, route.service, route.destination)


def main():
    log_path = os.environ.get("LOG_PATH")
    if not log_path:
        print("Missing configuration environment LOG_PATH")
        sys.exit(1)
    setup_logging(log_path)
    db_path = get_required_env("SQLITE_PATH")
    connection = connect(db_path)

    num_stops_saved = sync_stops(connection)
    if num_stops_saved > 0:
        logging.info("Saved %s stops", num_stops_saved)
    sync_routes(connection)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        logging.fatal("Error:", exc_info=e)
        sys.exit(1)
