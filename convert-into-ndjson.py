import json
from pathlib import Path
from json.decoder import JSONDecodeError

json_folder = Path("./data/metadados/")
json_folder.mkdir(exist_ok=True, parents=True)
ndjson_folder = Path("./pyes/data/ndjson/") / "ndjson"
ndjson_folder.mkdir(exist_ok=True, parents=True)
files = json_folder.rglob("*.json")
with open(ndjson_folder / "metadados_legislacao.json", "w", encoding="utf8") as _:
    for f in files:
        with open(f, "r", encoding="utf8") as jfile:
            try:
                json_metadado = json.load(jfile)[0]
            except JSONDecodeError:
                print(f"Erro no arquivo {f}.")
                continue
            else:
                ndjson = "\r\n".join([json.dumps(json_metadado, ensure_ascii=False)])
                _.write(ndjson)
                _.write("\n")
