from apis.acervo import LexmlAcervo, XmlToJson
from pathlib import Path
import gc

years = reversed(list(range(2000,2010)))
for year in years:
    # consulta a api e salva arquivos xml
    dados = LexmlAcervo(f"date={year}")
    dados.automatic_pagination(1, 1000)
    dados.saveResults(f"./data/xml/{year}", f"{year}")

    # lê os arquivos xml e os salvo em formato json
    xmlpath = Path(f"./data/xml/{year}").glob("*.xml")
    jsonFiles = [XmlToJson(xmlfile).parseToJson() for xmlfile in xmlpath]
    if jsonFiles:
        XmlToJson.saveResults(jsonFiles, f"./data/json/{year}", f"{year}")
    del jsonFiles
    del dados
    gc.collect()