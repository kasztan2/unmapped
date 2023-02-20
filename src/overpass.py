import requests
import json
from string import Template
import time
import os
from datetime import datetime, timedelta
from src.logging import logging

overpass_endpoint="https://overpass-api.de/api/interpreter"

def overpass_request(obj_id: str, names: list, sleep: int=120)->None:
    logging.info("Overpass request: starting")
    logging.info(f"id: {obj_id}")

    file_modification_time=0
    try:
        file_modification_time=datetime.fromtimestamp(os.path.getmtime(f"data/overpass/{obj_id}.json"))
    except:
        file_modification_time=datetime.fromtimestamp(0)
    
    current_time=datetime.now()

    if file_modification_time>current_time-timedelta(days=1):
        logging.info("Same overpass request made less than 1 day ago, using saved version")
        return

    #dealing with overpass request template
    template_file=open("src/overpass_template", "r")
    template_src=Template(template_file.read())
    template_file.close()

    names_string=""
    for x in names:
        names_string+=f"nwr[\"name\"=\"{x}\"];\nnwr[\"brand\"=\"{x}\"];\n"

    req=template_src.safe_substitute(names=names_string)

    params={"data": req}

    #making request
    try:
        res=requests.get(url=overpass_endpoint, params=params)
        res.raise_for_status()
        res=res.text
    except Exception:
        logging.error("Overpass request error!")
        return
    
    #loading json into dictionary
    try:
        res=json.loads(res)
    except Exception:
        if "too busy to handle your request" in res:
            if sleep>1000:
                raise SystemExit("Overpass server repeatedly too busy! Exiting")
            logging.warning(f"Overpass server too busy! Waiting {sleep/60} minutes...")
            time.sleep(sleep)
            overpass_request(obj_id, names, sleep*2)
            return
        elif "rate_limited" in res:
            if sleep>1000:
                raise SystemExit("Overpass quota repeatedly exceeded! Exiting")
            logging.warning(f"Overpass quota per IP address exceeded! Waiting {sleep/60} minutes...")
            time.sleep(sleep)
            overpass_request(obj_id, names, sleep)
            return
        else:
            print(res)
            logging.critical("Unidentified error parsing overpass response! (Response is not in json format) Exiting")
            raise SystemExit("Unidentified error parsing overpass response! (Response is not in json format) Exiting")
        
    res=res["elements"]

    #handling data to be in a unified format
    for i, x in enumerate(res):
        if "center" in x:
            res[i]["lat"]=x["center"]["lat"]
            res[i]["lon"]=x["center"]["lon"]
            del res[i]["center"]
        del res[i]["id"]
        del res[i]["type"]
        if "nodes" in x:
            del res[i]["nodes"]
        if "tags" in x:
            del res[i]["tags"]
    
    #checking if response array is empty
    if len(res)==0:
        logging.critical("Overpass query returned no results")
        raise Exception("Overpass query returned no results!")

    #saving data to a file
    output_file=open(f"data/overpass/{obj_id}.json", "w")
    output_file.write(json.dumps(res))
    output_file.close()

    logging.info("Overpass request: done")