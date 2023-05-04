from src.downloader import download
from src.compare import compare
import json
from src.logging import logging
import sys
import pymongo

if __name__ == "__main__":
    only_open_licenses = False
    if len(sys.argv) > 1 and sys.argv[1] == "--open_license":
        only_open_licenses = True

    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

    mongo_client.drop_database("external")
    mongo_client.drop_database("overpass")
    mongo_client.drop_database("output")

    download(only_open_licenses, mongo_client)

    f = open("lists/nsi.json")
    nsi_array = json.load(f)
    f.close()

    collection_names = list(set(mongo_client["external"].list_collection_names(
    )).intersection(set(mongo_client["overpass"].list_collection_names())))

    mongo_client["output"]["all"].create_index([("geometry", pymongo.GEOSPHERE)])

    for obj in nsi_array:
        if obj["id"] not in collection_names:
            continue
        try:
            compare(obj["id"], mongo_client=mongo_client)
        except Exception as e:
            logging.error(
                f"{obj}: Error while comparing: {e}", exc_info=True)