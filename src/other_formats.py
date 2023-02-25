import os
import json

def to_osm_xml():
    for filename in os.listdir("geojson/"):
        base_filename=filename.removesuffix(".geojson")
        with open(f"geojson/{filename}") as f:
            data=json.load(f)
        data=data["features"]

        xml_string="<?xml version=\"1.0\" encoding=\"UTF-8\"?><osm version=\"0.6\" generator=\"github.com/kasztan2/unmapped\">"

        count=-1
        for x in data:
            tags=x["properties"]["tags"]
            xml_string+=f"<node id=\"{count}\" lat=\"{x['geometry']['coordinates'][0]}\" lon=\"{x['geometry']['coordinates'][1]}\">"
            for key, value in tags.items():
                xml_string+=f"<tag k=\"{key}\" v=\"{value}\"/>"
            xml_string+="</node>"
            count-=1

        xml_string+="</osm>"

        f=open(f"osm/{base_filename}.osm", "w+")
        f.write(xml_string)
        f.close()