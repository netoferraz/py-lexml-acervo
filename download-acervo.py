from search_acervo_api import LexmlAcervo, XmlToJson
from pathlib import Path
#consulta a api e salva arquivos xml
dados_2019 = LexmlAcervo("date=2019")
dados_2019.automatic_pagination(1, 1000)
dados_2019.saveResults("./data/2019", "dados_2019")

#lê os arquivos xml e os salvo em formato json
xmlpath = Path("./data/xml/2019").glob("*.xml")
jsonFiles = [
    XmlToJson(xmlfile).parseToJson() for xmlfile in xmlpath 
]
XmlToJson.saveResults(jsonFiles, "./data/json", "2019")

