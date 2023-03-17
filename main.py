from src.downloader import download
from src.compare import compare
import json
from src.logging import logging
import os
import sys

if __name__ == "__main__":
    only_open_licenses = False
    if len(sys.argv) > 1 and sys.argv[1] == "--open_license":
        only_open_licenses = True
    status_file = open("lists/status.json", "w+")
    if os.path.getsize("lists/status.json") == 0:
        status_file.write("{}")
    status_file.close()

    os.makedirs(os.path.dirname("data/external/"), exist_ok=True)
    os.makedirs(os.path.dirname("data/overpass/"), exist_ok=True)
    os.makedirs(os.path.dirname("geojson/"), exist_ok=True)
    download(only_open_licenses)

    f = open("lists/nsi.json")
    nsi_array = json.load(f)
    f.close()

    for obj in nsi_array:
        try:
            file_external = open(f"data/external/{obj['id']}.json")
            file_overpass = open(f"data/overpass/{obj['id']}.json")
            try:
                compare(obj["id"], json.load(file_external),
                        json.load(file_overpass))
            except Exception as e:
                logging.error(
                    f"{obj}: Error while comparing: {e}", exc_info=True)
            file_external.close()
            file_overpass.close()
        except Exception:
            pass