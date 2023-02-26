import requests
import json
import os
from datetime import datetime, timedelta
from src.logging import logging
import pygeohash as pgh
from bs4 import BeautifulSoup

def external_request(obj_id: str, only_open_licence: bool)->None:
    logging.info("External request: starting")
    logging.info(f"id: {obj_id}")

    file_modification_time=0
    try:
        file_modification_time=datetime.fromtimestamp(os.path.getmtime(f"data/external/{obj_id}.json"))
    except:
        file_modification_time=datetime.fromtimestamp(0)
    
    current_time=datetime.now()

    if file_modification_time>current_time-timedelta(days=1):
        logging.info("Same external request made less than 1 day ago, using saved version")
        return

    f=open("lists/requests.json")
    requests_file=json.load(f)
    f.close()
    request_data=requests_file[obj_id]
    if isinstance(request_data, dict):
        request_data=[request_data]

    session=requests.Session()
    output_data=[]

    #TODO make default user agent

    any_open_licence=False

    for req in request_data:
        if "request_type" not in req:
            req["request_type"]="get"
        try:
            if only_open_licence and req["open_licence"]==False:
                continue
            any_open_licence=True
            if req["request_type"]=="post":
                res=session.post(**req["params"])
            else:
                res=session.get(**req["params"])
        except Exception as e:
            #if request failed, omit this entity (brand)
            logging.error(f"{obj_id}: External request error!\n{e}\nOmitting", exc_info=True)
            return

        #this is for cases when data is statically loaded (in some <script> tag or something similar)
        if "css_element_selector" in req:
            soup=BeautifulSoup(res.text, "html.parser")
            res.text=str(soup.select(req["css_element_selector"]).string)
        
        #ignore result if marked so, this is for pages later in list that require some cookies present
        if "ignore_result" in req and req["ignore_result"]=="yes":
            continue

        parsed_data={}
        if "format" not in req or req["format"]=="json":
            try:
                parsed_data=json.loads(res.text)
            except Exception:
                print(res.text)
                logging.error(f"{obj_id}: error loading json")
                return
        #! more formats to come
        else:
            logging.critical(f"Cannot handle \"{req['format']}\" format")
            raise Exception(f"\"{req['format']}\" format handling is not implemented!")
        
        for field in req["path"]["data_root"]:
            parsed_data=parsed_data[field]
        
        for obj in parsed_data:
            try:
                lat=0
                lon=0
                if "geohash" in req["path"]:
                    for field in req["path"]["geohash"]:
                        obj=obj[field]
                    (lat, lon)=pgh.decode(geohash=obj[:-1])
                else:
                    lat=obj
                    for field in req["path"]["lat"]:
                        lat=lat[field]
                    
                    lon=obj
                    for field in req["path"]["lon"]:
                        lon=lon[field]
                
                lat=float(lat)
                lon=float(lon)

                output_data.append({"lat": lat, "lon": lon})
            except:
                pass
    
    #saving data to a file
    if any_open_licence:
        output_file=open(f"data/external/{obj_id}.json", "w")
        output_file.write(json.dumps(output_data))
        output_file.close()

    logging.info("External request: done")
