# from elasticsearch import Elasticsearch
# from elasticsearch import helpers
from pathlib import Path
import json

"""
ESSE SCRIPT DEVE SER EXECUTADO NO SERVIDOR
"""
# connect to es
es = Elasticsearch("localhost:9200")
# list files

ndjson = "./data/ndjson/metadados_legislacao.json"

container_of_jsons = []

with open(ndjson, encoding="utf8") as _:
    for line in _:
        # line = line.encode("utf8").decode("utf8")
        instance_data = json.loads(line)
        id_instance = instance_data["@id"]
        del instance_data["@id"]
        reshape_data = {
            "_index": "normativos",
            "_type": "_doc",
            "_id": id_instance,
            "_source": instance_data,
        }
        print(reshape_data)
        break
"""
for f in files:
    with open(f, "r", encoding='utf8') as _:
        print(f"inicio da carga de {f}.")
        instance_data_year = json.load(_)
        for instance_data in instance_data_year:
            id_instance = instance_data['@id']
            del instance_data['id']
            reshape_data = {
                "_index" : "normativos",
                "_type" : "_doc",
                "_id" : id_instance,
                "_source" : instance_data
            }
            container_of_jsons.append(reshape_data)

helpers.bulk(es, container_of_jsons)
print("Finalizado a carga dos dados.")

"""
