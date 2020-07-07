from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pathlib import Path
import json
import re
from loguru import logger
from time import sleep

sleep(90)
# connect to es
NDJSON = "./data/metadados_legislacao.json"
es = Elasticsearch(f"elk:9200")

@logger.catch
def get_legislation_keyword_type(urn: str) -> str:
    mapping = {
        'constituicao' : "Constituição",
        'decreto' : "Decreto",
        'decreto.legislativo' : "Decreto do Legislativo",
        'decreto.lei' : "Decreto-Lei",
        'emenda.constitucional' : "Emenda Constitucional",
        'lei' : "Lei",
        'lei.complementar' : "Lei Complementar",
        'lei.delegada' : "Lei Delegada",
        "medida.provisoria" : "Medida Provisória" 
    }
    pattern = "federal:.+:" 
    s = re.compile(pattern)
    match = s.search(urn)
    if match:
        return mapping[match.group(0).split(":")[1]]
    else:
        return None

if not es.ping():
    raise ValueError("Conexão falhou.")

if not es.indices.exists(index="normativos"):
    container_of_jsons = []
    with open(NDJSON, encoding="utf8") as _:
        for line in _:
            instance_data = json.loads(line)
            try:
                id_instance = instance_data["@id"]
            except KeyError:
                continue
            instance_data["legislationKeywordType"] = get_legislation_keyword_type(instance_data["@id"])
            del instance_data["@id"]
            reshape_data = {
                "_index": "normativos",
                "_type": "_doc",
                "_id": id_instance,
                "_source": instance_data,
            }
            container_of_jsons.append(reshape_data)

    helpers.bulk(es, container_of_jsons)
    logger.info("Finalizado a carga dos dados.")

