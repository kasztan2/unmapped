import numpy as np
from sklearn.neighbors import BallTree
from math import radians
import json
import os
from src.logging import logging
import time

earth_radius=6378000

def init_tree(X: list[list[float]])->BallTree:
    X_rad=[[radians(x[0]), radians(x[1])] for x in X]
    tree=BallTree(X_rad, leaf_size=2, metric="haversine")
    return tree

def find_nearest(tree: BallTree, point: list[float])->tuple:
    point_rad=[[radians(point[0]), radians(point[1])]]
    dist, ind=tree.query(point_rad, k=1)
    ind=ind[0][0]
    dist=dist[0][0]*earth_radius
    return (ind, dist)

def compare(obj_id: str, external_data: list, overpass_data: list, threshold_meters: float=500.)->None:
    logging.info(f"Comparing {obj_id}")

    overpass_tree=init_tree([[x["lat"], x["lon"]] for x in overpass_data])
    output=[]
    for obj in external_data:
        num, min_distance=find_nearest(overpass_tree, [obj["lat"], obj["lon"]])
        
        if min_distance>threshold_meters:
            output.append({"type": "Feature", "properties": {}, "geometry":{"coordinates": [obj["lon"], obj["lat"]], "type": "Point"}})
    
    with open("lists/requests.json") as f:
        requests_data=json.load(f)
    
    request_data=requests_data[obj_id]
    if isinstance(request_data, dict):
        request_data=[request_data]
    
    external_urls=list(map(lambda x: x["params"]["url"], request_data))
    open_licence=list(map(lambda x: x["open_licence"], request_data))
    
    info_output={
            "external_request_timestamp": os.path.getmtime(f"data/external/{obj_id}.json"),
            "overpass_request_timestamp": os.path.getmtime(f"data/overpass/{obj_id}.json"),
            "nsi_id": obj_id,
            "threshold_in_meters": threshold_meters,
            "comparison_timestamp": time.time(),
            "external_sources": external_urls,
            "data_length": len(output),
            "open_licence": open_licence
        }

    full_output={
        "type": "FeatureCollection",
        "info": info_output,
        "features": output
    }

    with open("lists/status.json") as f:
        arr=json.load(f)
    arr.update({f"{obj_id}": info_output})
    with open("lists/status.json", "w") as f:
        json.dump(arr, f)

    logging.info(f"Output data length: {len(output)}")
    os.makedirs(os.path.dirname(f"geojson/{obj_id}.geojson"), exist_ok=True)
    f=open(f"geojson/{obj_id}.geojson", "w")
    logging.info("Saving")
    f.write(json.dumps(full_output))
    f.close()
    logging.info("Done")