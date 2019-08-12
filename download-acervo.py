from search_acervo_api import LexmlAcervo

dados_2019 = LexmlAcervo("date=2019")
dados_2019.automatic_pagination(1, 1000)
dados_2019.saveResults("./data/2019", "dados_2019")
