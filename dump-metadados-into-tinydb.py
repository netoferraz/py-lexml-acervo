from pathlib import Path
from tinydb import TinyDB
import json
from typing import Iterable
import gc

db_metadados = TinyDB("./data/db/metadados.json")
db_acervo = TinyDB("./data/db/acervo.json")

files_metadados = Path("./data/metadados/")
files_metadados = files_metadados.rglob("*.json")

files_acervo = Path("./data/json/")
files_acervo = files_acervo.rglob("*.json")
params = {
    # "metadados": (db_metadados, files_metadados),
    "acervo": (db_acervo, files_acervo)
}


def insert_into_db(list_of_files: Iterable, db: TinyDB, key: str) -> None:
    container = []
    list_of_files = list(list_of_files)
    list_of_files.sort()
    for f in list_of_files:
        if len(container) > 5000:
            db.insert_multiple(container)
            container = []
            gc.collect()
        with open(f, "r", encoding="utf8") as _:
            data = json.load(_)
            for d in data:
                if key == "metadados":
                    try:
                        d["keywords"] = d["keywords"].split(",")
                    except KeyError:
                        print(
                            f"Não foi possível encontrar o campo keywords no arquivo {f}."
                        )

                container.append(d)

    db.insert_multiple(container)


for k, v in params.items():
    insert_into_db(list_of_files=v[1], db=v[0], key=k)

