# Full documentation for this API can be found on Gallica's site: http://api.bnf.fr/api-gallica-de-recherche
import requests
import xml.etree.ElementTree as ET
import xml
import sys


class lexmlAcervo(object):
    def __init__(self):
        self.RECHERCHE_BASEURL = "https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&version=1.1&query="
        self.START_REC = "&startRecord="
        self.MAXIMUM_REC = "&maximumRecords="

    def query(self, startRecord: int, maximumRecords: int, query_string: str):
        search_string = query_string.replace(" ", "%20")
        url = "".join(
            [
                self.RECHERCHE_BASEURL,
                search_string,
                self.START_REC,
                str(startRecord),
                self.MAXIMUM_REC,
                str(maximumRecords),
            ]
        )
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"Ocorreu um erro na requisição a API: {err}")
            tree = self.loadIntoXml(r)
            if "diagnostics" in tree.getroot().tag:
                diagnosticoErro = self.parseError(tree)
                print(diagnosticoErro)
                return None
        else:
            tree = self.loadIntoXml(r)
            # verifica se foi uma query válida
            if "diagnostics" in tree.getroot().tag:
                diagnosticoErro = self.parseError(tree)
                print(diagnosticoErro)
                return None
            # verifica se a query retornou algum resultado
            numeroObjetos = int(list(tree.getroot())[1].text)
            if numeroObjetos == 0:
                print(f"A query {search_string} não retornou nenhum resultado.")
            else:
                print(f"Há {numeroObjetos} objetos retornados pela query: {url}.")
            return tree

    def parseError(self, tree: xml.etree.ElementTree.ElementTree):
        # verifica se foi uma query válida
        if "diagnostics" in tree.getroot().tag:
            try:
                type_error, message_error = (
                    tree.getiterator()[3].text,
                    tree.getiterator()[4].text,
                )
            except IndexError:
                message_error = tree.getiterator()[3].text
                return f"Messagem de Erro: {message_error}"
            else:
                return f"Messagem de Erro: {type_error}: {message_error}"

    def loadIntoXml(
        self, response: requests.models.Response
    ) -> xml.etree.ElementTree.ElementTree:
        contents = response.content.decode("utf8")
        root = ET.fromstring(contents)
        tree = ET.ElementTree(root)
        return tree
