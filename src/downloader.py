import json
import requests
from src.external import external_request
from src.overpass import overpass_request
from datetime import datetime, timedelta
import os
from src.logging import logging

nsi_list_url = "https://cdn.jsdelivr.net/npm/name-suggestion-index@6.0.20230206/dist/nsi.min.json"


def download(only_open_licence: bool) -> None:
    file_modification_time = 0
    try:
        file_modification_time = datetime.fromtimestamp(
            os.path.getmtime(f"lists/nsi.json"))
    except:
        file_modification_time = datetime.fromtimestamp(0)

    current_time = datetime.now()

    if file_modification_time > current_time-timedelta(days=1):
        logging.info(
            "NSI data downloaded less than 1 day ago, using saved version")
    else:
        try:
            res = requests.get(nsi_list_url).text
            nsi_list = json.loads(res)
            nsi_list = nsi_list["nsi"]

            nsi_array = []
            for ind, x in nsi_list.items():
                if "brands/" not in ind:
                    continue
                nsi_array.extend(x["items"])

            output_file = open("lists/nsi.json", "w")
            output_file.write(json.dumps(nsi_array))
            output_file.close()
        except Exception:
            logging.warning(
                "Error downloading NSI data, trying to use saved version")

    f = open("lists/nsi.json")
    nsi_array = json.load(f)
    f.close()

    f = open("lists/requests.json")
    request_list = json.load(f)
    f.close()

    for obj in nsi_array:
        if obj["id"] not in request_list.keys():
            continue

        try:
            external_request(obj["id"], only_open_licence)
        except Exception as e:
            logging.error(
                f"{obj}: Error during external request: {e}", exc_info=True)

    for obj in nsi_array:
        if obj["id"] not in request_list.keys():
            continue

        names = [obj["displayName"]]
        if "brand" in obj["tags"]:
            names.append(obj["tags"]["brand"])
        if "name" in obj["tags"]:
            names.append(obj["tags"]["name"])

        any_open_license = not only_open_licence
        for req in request_list[obj["id"]]:
            if req["open_licence"]:
                any_open_license = True
                break

        if any_open_license == False:
            continue

        try:
            overpass_request(obj["id"], names, only_open_licence)
        except Exception as e:
            logging.error(f"{obj}: Error during overpass request: {e}")
