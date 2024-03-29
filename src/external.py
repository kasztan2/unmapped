import requests
import requests_cache
import json
from src.logging import logging
import pygeohash as pgh
from bs4 import BeautifulSoup
import xmltodict
import pymongo

requests_cache.install_cache(
    ".cache/external_cache", backend="sqlite", expire_after=3600*24)


def external_request(obj_id: str, only_open_license: bool, mongo_client: pymongo.MongoClient) -> None:
    logging.info("External request: starting")
    logging.info(f"id: {obj_id}")

    f = open("lists/requests.json")
    requests_file = json.load(f)
    f.close()
    request_data = requests_file[obj_id]
    if isinstance(request_data, dict):
        request_data = [request_data]

    session = requests.Session()
    output_data = []

    # default user agent
    user_agent = {
        "User-Agent": "OSM Unmapped Project (https://osm-unmapped.eu)"}

    any_open_license = False

    for req in request_data:
        if "request_type" not in req:
            req["request_type"] = "get"
        try:
            if only_open_license and req["open_license"] == False:
                continue
            any_open_license = True

            if "headers" not in req["params"]:
                req["params"].update({"headers": user_agent})
            else:
                req["params"]["headers"].update(user_agent)

            if req["request_type"] == "post":
                res = session.post(**req["params"])
            else:
                res = session.get(**req["params"])
        except Exception as e:
            # if request failed, omit this entity (brand)
            logging.error(
                f"{obj_id}: External request error!\n{e}\nOmitting", exc_info=True)
            return

        # this is for cases when data is statically loaded (in some <script> tag or something similar)
        if "css_element_selector" in req:
            soup = BeautifulSoup(res.text, "html.parser")
            rtext = soup.select(req["css_element_selector"])[0].getText()
        else:
            rtext = res.text

        # ignore result if marked so, this is for pages later in list that require some cookies present
        if "ignore_result" in req and req["ignore_result"] == "yes":
            continue

        parsed_data = {}
        if "format" not in req or req["format"] == "json":
            try:
                parsed_data = json.loads(rtext)
            except Exception:
                logging.error(f"{obj_id}: error loading json", exc_info=True)
                return
        elif req["format"] == "xml":
            try:
                parsed_data = xmltodict.parse(rtext)
            except Exception:
                logging.error(f"{obj_id}: error loading xml", exc_info=True)
                return
        #! more formats to come
        else:
            logging.critical(f"Cannot handle \"{req['format']}\" format")
            raise Exception(
                f"\"{req['format']}\" format handling is not implemented!")

        for field in req["path"]["data_root"]:
            parsed_data = parsed_data[field]

        for obj in parsed_data:
            try:
                lat = 0
                lon = 0
                if "geohash" in req["path"]:
                    for field in req["path"]["geohash"]:
                        obj = obj[field]
                    (lat, lon) = pgh.decode(geohash=obj[:-1])
                else:
                    lat = obj
                    for field in req["path"]["lat"]:
                        lat = lat[field]

                    lon = obj
                    for field in req["path"]["lon"]:
                        lon = lon[field]

                lat = float(lat)
                lon = float(lon)

                output_data.append({"lat": lat, "lon": lon})
            except:
                pass

    # saving data to a database
    if len(output_data):
        mongo_client["external"][obj_id].insert_many(output_data)

    logging.info("External request: done")
