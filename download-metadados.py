import bs4
import requests
from requests.exceptions import ConnectionError
from pathlib import Path
import json
from json.decoder import JSONDecodeError
from time import sleep
import re
from loguru import logger

BASE_URL = "https://www.lexml.gov.br/urn"
urns = Path("./data/federal/")
urns = urns.rglob("*.json")
LOG_FILE = "./log/coleta_metadados_normativos.log"
logger.add(
    LOG_FILE, format="{time:YYYY-MM-DD HH:mm:ss} | {file} {level} | {line} | {message}"
)


def get_metadata(urn: str, **kwargs):
    global urn_retry
    if urn not in urn_retry:
        urn_retry[urn] = 0
    foldername = kwargs.get("foldername")
    index = kwargs.get("index")
    sleep(0.5)
    try:
        urn_retry[urn] += 1
        r = requests.get(f"{BASE_URL}/{urn}")
    except ConnectionError:
        sleep(30)
        if urn_retry[urn] > 5:
            logger.critical(
                f"O programa será encerrrado por excesso de requests para a mesma urn."
            )
            exit()
        else:
            get_metadata(urn=urn, **{"foldername": file_, "index": index})
    else:
        if r.status_code == 200:
            soup = bs4.BeautifulSoup(r.text, features="html.parser")
            scripts = soup.find_all("script")
            tag_script = [
                str(s) for s in scripts if re.search("application\/ld\+json", str(s))
            ]
            if tag_script:
                tag_script = tag_script[0]
                first_slice = tag_script.find("[")
                last_slice = tag_script.find("</script>")
                try:
                    metadata = json.loads(tag_script[first_slice:last_slice])
                except JSONDecodeError:
                    try:
                        first_slice = tag_script.find("{")
                        last_slice = tag_script.find("</script>")
                        metadata = json.loads(
                            "[" + tag_script[first_slice:last_slice] + "]"
                        )
                    except JSONDecodeError:
                        logger.error(f"Erro na conversão em JSON da urn {urn}.")
                        pass
                    else:
                        save_file(
                            data=metadata,
                            filename=index,
                            foldername=foldername,
                            **{"urn": urn},
                        )
                else:
                    save_file(
                        data=metadata,
                        filename=index,
                        foldername=foldername,
                        **{"urn": urn},
                    )

            else:
                logger.info(f"A urn {urn} não possui metadados.")
        else:
            logger.error(f"Requisição para urn {urn} com status code {r.status_code}.")


def save_file(data, filename, foldername, **kwargs):
    urn = kwargs.get("urn")
    get_year_folder = str(foldername).split("_")[-1].split(".")[0]
    BASE_PATH = Path(f"./data/metadados/{get_year_folder}")
    BASE_PATH.mkdir(parents=True, exist_ok=True)
    BASE_PATH = BASE_PATH / f"{get_year_folder}_{filename}.json"
    try:
        with open(BASE_PATH, mode="w", encoding="utf8") as _:
            json.dump(data, _, ensure_ascii=False)
    except ValueError:
        logger.error(f"Erro no dump para urn {urn}.")
    else:
        logger.success(f"Metadados da urn {urn} salvo com sucesso.")


urn_retry = {}
for file_ in urns:
    with open(file_, encoding="utf8") as f:
        dados_acervo = json.load(f)
        lista_urns = [u.get("urn") for u in dados_acervo]
        for index, urn in enumerate(lista_urns):
            get_metadata(urn=urn, **{"foldername": file_, "index": index})
