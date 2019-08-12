import requests
import xml.etree.ElementTree as ET
import xml
import sys
from pathlib import Path
import os


class lexmlAcervo(object):
    __overall_query_objects_tracker = 0
    __total_objects_of_query = None
    __completed_query = False

    def __init__(self, query_string: str):
        self.__BASE_URL = "https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&version=1.1&query="
        self.__START_REC = "&startRecord="
        self.__MAXIMUM_REC = "&maximumRecords="
        self.containerOfXmlFiles = []
        self.__query_string = query_string

    def addToContainerOfXmlFiles(self, tree: xml.etree.ElementTree.ElementTree):
        self.containerOfXmlFiles.append(tree)
        return None

    def query(self, startRecord: int, maximumRecordsPerPage: int):
        if self.__completed_query:
            print(
                f"Todos os objetos para a query {self.__query_string} foram consumidos."
            )
        search_string = self.__query_string.replace(" ", "%20")
        url = "".join(
            [
                self.__BASE_URL,
                search_string,
                self.__START_REC,
                str(startRecord),
                self.__MAXIMUM_REC,
                str(maximumRecordsPerPage),
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
            if not self.__total_objects_of_query:
                self.__total_objects_of_query = numeroObjetos
            if numeroObjetos == 0:
                print(f"A query {search_string} não retornou nenhum resultado.")
            self.addToContainerOfXmlFiles(tree)
            # calcula o número de objetos ainda há serem consultados
            self.__overall_query_objects_tracker += maximumRecordsPerPage
            remain_objects = numeroObjetos - self.__overall_query_objects_tracker
            if self.__overall_query_objects_tracker >= numeroObjetos:
                print("Todos os objetos foram consultados.")
                print("Finalizado a paginação da query.")
                self.__completed_query = True
            if not self.__completed_query:
                print(
                    f"Retornando objetos de {startRecord} a {self.__overall_query_objects_tracker}."
                )
                print(f"Restam {remain_objects} a serem consultados pela query: {url}")
            start_record_next_query = self.__overall_query_objects_tracker + 1
            return tree, start_record_next_query, maximumRecordsPerPage

    def automatic_pagination(self, startRecord, maximumRecordsPerPage):
        while not self.__completed_query:
            tree, startRecord, maximumRecordsPerPage = self.query(
                startRecord, maximumRecordsPerPage
            )
            self.automatic_pagination(startRecord, maximumRecordsPerPage)

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

    def saveResults(self, path: str, filename: str):
        path_to_save = Path(path)
        path_to_save.mkdir(parents=True, exist_ok=True)
        for index, xmlfile in enumerate(self.containerOfXmlFiles):
            aggName = f"{index}_{filename}.xml"
            full_xml_filename = path_to_save / aggName
            print(full_xml_filename)
            xmlfile.write(full_xml_filename, encoding="utf-8")
