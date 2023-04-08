import numpy as np
from sklearn.neighbors import BallTree
from math import radians
import json
import os
from src.logging import logging
import time
import pymongo

earth_radius = 6378000


def init_tree(X: list[list[float]]) -> BallTree:
    X_rad = [[radians(x[0]), radians(x[1])] for x in X]
    tree = BallTree(X_rad, leaf_size=2, metric="haversine")
    return tree


def find_nearest(tree: BallTree, point: list[float]) -> tuple:
    point_rad = [[radians(point[0]), radians(point[1])]]
    dist, ind = tree.query(point_rad, k=1)
    ind = ind[0][0]
    dist = dist[0][0]*earth_radius
    return (ind, dist)


def compare(obj_id: str, mongo_client: pymongo.MongoClient, threshold_meters: float = 500.) -> None:
    logging.info(f"Comparing {obj_id}")

    overpass_data = list(mongo_client["overpass"][obj_id].find())
    external_data = list(mongo_client["external"][obj_id].find())

    if len(overpass_data) == 0:
        return

    overpass_tree = init_tree([[x["lat"], x["lon"]] for x in overpass_data])
    output = []

    with open("lists/nsi.json") as f:
        nsi_data = json.load(f)

    nsi_data = [x for x in nsi_data if x["id"] == obj_id][0]

    mongo_client["output"][obj_id].create_index([("geometry", pymongo.GEOSPHERE)])

    for obj in external_data:
        num, min_distance = find_nearest(
            overpass_tree, [obj["lat"], obj["lon"]])

        if min_distance > threshold_meters:
            x=mongo_client["output"][obj_id].insert_one({"type": "Feature", "properties": {
                **nsi_data["tags"]}, "geometry": {"coordinates": [obj["lon"], obj["lat"]], "type": "Point"}})
            print(x)
            x=mongo_client["output"]["all"].insert_one({"type": "Feature", "nsi_id": obj_id, "properties": {
                **nsi_data["tags"]}, "geometry": {"coordinates": [obj["lon"], obj["lat"]], "type": "Point"}})
            print(x)

    with open("lists/requests.json") as f:
        requests_data = json.load(f)

    request_data = requests_data[obj_id]
    if isinstance(request_data, dict):
        request_data = [request_data]

    external_urls = list(map(lambda x: x["params"]["url"], request_data))
    open_license = list(map(lambda x: x["open_license"], request_data))

    info_output = {
        "nsi_id": obj_id,
        "threshold_in_meters": threshold_meters,
        "comparison_timestamp": time.time(),
        "external_sources": external_urls,
        "data_length": len(output),
        "open_license": open_license
    }

    # full_output = {
    #    "type": "FeatureCollection",
    #    "info": info_output,
    #    "features": output
    # }

    mongo_client["status"]["status"].replace_one(
        {"nsi_id": obj_id}, info_output, upsert=True)

    logging.info(f"Output data length: {len(output)}")
    logging.info("Done")
