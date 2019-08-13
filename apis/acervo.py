import requests
import xml.etree.ElementTree as ET
import xml
import sys
import unicodedata
import xmltodict
from pathlib import Path
from typing import Union, Tuple
import os
import json


class LexmlAcervo(object):
    """
    Classe para realizar consultas ao acervo do Portal LexML (https://www12.senado.leg.br/dados-abertos/conjuntos?grupo=legislacao&portal=legislativo)
    A API do LexML permite realizar pesquisas por meio de URLs e receber o resultado no formato XML. 
    A API segue o padrão definido pelo Biblioteca do Congresso Nova-americano no projeto Search/Retrieval via URL (SRU).
    Documentação do padrão SRU: http://www.loc.gov/standards/sru/
    """

    def __init__(self, query_string: str):
        """
        A string de consulta a API faz uso do padrão CQL (Contextual Query Language).
        A especificação da query CQL pode ser encontrada em https://www.loc.gov/standards/sru/cql/spec.html
        
        Parâmetros:
            query_string: string de consulta no padrão CQL
        
        Exemplo: "date=2019"
        """
        self.__BASE_URL = "https://www.lexml.gov.br/busca/SRU?operation=searchRetrieve&version=1.1&query="
        self.__START_REC = "&startRecord="
        self.__MAXIMUM_REC = "&maximumRecords="
        # inicializa o container que armazenará o resultado das querys
        self.containerOfXmlFiles = []
        self.__query_string = query_string
        self.__overall_query_objects_tracker = 0
        self.__total_objects_of_query = None
        self.__completed_query = False

    def __addToContainerOfXmlFiles(self, tree: xml.etree.ElementTree.ElementTree):
        """
        Adiciona o resultado de uma paginação da query ao container de dados.
        """
        self.containerOfXmlFiles.append(tree)
        return None

    def query(
        self, startRecord: int, maximumRecordsPerPage: int
    ) -> Tuple[xml.etree.ElementTree.ElementTree, int, int]:
        """
        Realiza uma query a partir da query string definida na inicialização da instância.

        Parâmetros:
            startRecord: posição inicial no set de resultado da query
            maximumRecordsPerPage: número máximo de resultados por paginação.
        """
        #identificar querys sem resultado.
        non_zero_results = True
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
                non_zero_results = False
            if non_zero_results:
                self.__addToContainerOfXmlFiles(tree)
            # calcula o número de objetos ainda há serem consultados
            self.__overall_query_objects_tracker += maximumRecordsPerPage
            remain_objects = numeroObjetos - self.__overall_query_objects_tracker
            if self.__overall_query_objects_tracker >= numeroObjetos:
                if non_zero_results:
                    print(f"Todos os {numeroObjetos} objetos foram consultados.")
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
        """
        Realiza paginação automática até consumir todos os resultados
        da query string definida na inicialização do instância.

        Parâmetros:
        startRecord: posição inicial no set de resultado da query
        maximumRecordsPerPage: número máximo de resultados por paginação.
        """
        while not self.__completed_query:
            tree, startRecord, maximumRecordsPerPage = self.query(
                startRecord, maximumRecordsPerPage
            )
            self.automatic_pagination(startRecord, maximumRecordsPerPage)

    def parseError(self, tree: xml.etree.ElementTree.ElementTree) -> str:
        """
        Avalia se a query string retorna uma resposta válida.

        Parâmetros:
        tree: objeto do parser de xml
        """
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
        """
        Recebe a resposta do request a API e o carrega no parser de XML

        Parâmetros:
            response: reposta do request GET feito a API.
        """
        contents = unicodedata.normalize("NFKD", response.content.decode("utf-8"))
        root = ET.fromstring(contents)
        tree = ET.ElementTree(root)
        return tree

    def saveResults(self, path: str, filename: str):
        """
        Itera sobre o container de objetos XML coletados da API e os persiste em arquivos
        XML.

        Parâmetros:
            path: Path para salvar os arquivos XML
            filename: nome base dos arquivos a serem salvos.
        """
        #identifica se há arquivos a serem salvos
        if self.containerOfXmlFiles:
            path_to_save = Path(path)
            try:
                path_to_save.mkdir(parents=True, exist_ok=True)
            except FileNotFoundError:
                raise FileNotFoundError()
            for index, xmlfile in enumerate(self.containerOfXmlFiles):
                aggName = f"{index}_{filename}.xml"
                full_xml_filename = path_to_save / aggName
                try:
                    xmlfile.write(full_xml_filename, encoding="utf-8")
                except FileNotFoundError:
                    raise FileNotFoundError()


class XmlToJson(object):
    """
    Classe para transformar arquivos XML em JSON.
    """

    __BASE_URL = "https://www.lexml.gov.br/urn/"

    def __init__(self, xmlfile, encoding="utf8"):
        with open(xmlfile, "r", encoding=encoding) as f:
            self.xml = f.read()
            self.container_of_json = []

    def __parseXml(self, _, document):
        """
        Função de callback para ser utilizada pela biblioteca xmltodict para parsear
        os arquivos XML
        """
        tipoDocumento = document.get("tipoDocumento", None)
        facet_tipoDocumento = document.get("facet-tipoDocumento", None)
        data = document.get("dc:date", None)
        urn = document.get("urn", None)
        url = f"{self.__BASE_URL}{urn}"
        localidade = document.get("localidade", None)
        facet_localidade = document.get("facet-localidade", None)
        autoridade = document.get("autoridade", None)
        facet_autoridade = document.get("facet-autoridade", None)
        title = document.get("dc:title", None)
        description = document.get("dc:description", None)
        type_ = document.get("dc:type", None)
        identifier = document.get("dc:identifier", None)
        data = {
            "tipoDocumento": tipoDocumento,
            "facet-tipoDocumento": facet_tipoDocumento,
            "data": data,
            "urn": urn,
            "url": url,
            "localidade": localidade,
            "facet-localidade": facet_localidade,
            "autoridade": autoridade,
            "facet-autoridade": facet_autoridade,
            "title": title,
            "description": description,
            "type": type_,
            "identifier": identifier,
        }
        self.container_of_json.append(data)
        return True

    def parseToJson(self):
        """
        Executa o parser dos arquivos XML
        """
        xmltodict.parse(self.xml, item_depth=5, item_callback=self.__parseXml)
        return self.container_of_json

    @staticmethod
    def saveResults(container: list, path: str, filename: str):
        """
        Itera sobre o container de dicionários e os persiste em arquivos JSON.

        Parâmetros:
            path: Path para salvar os arquivos XML
            filename: nome base dos arquivos a serem salvos.
        """
        path_to_save = Path(path)
        try:
            path_to_save.mkdir(parents=True, exist_ok=True)
        except FileNotFoundError:
            raise FileNotFoundError()
        for index, file_ in enumerate(container):
            aggName = f"{index}_{filename}.json"
            full_filename = path_to_save / aggName
            with open(full_filename, "w", encoding="utf8") as f:
                json.dump(file_, f, ensure_ascii=False)
