import time
import requests
import json

import pandas as pd

from datetime import datetime
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys


def get_job_position_data_web(position: str) -> str:
    """Retorna uma string com o html da página

    Args:
        position (str): nome da vaga a ser buscada

    Returns:
        str: html com página com a lista de vagas encontradas
    """

    opts = Options()

    # uma sessão do navegador é criada quando instanciamos a classe 'Driver'. Em alguns casos seria necessario incluir
    # o caminho para o driver do navegador como parâmetro, mas como incluímos esse arquivo dentro em um dos diretórios
    # da variável $PATH (/usr/local/bin) isso não será necessário.
    driver = webdriver.Firefox(options=opts)

    # acessa a pagina dada pela URL
    driver.get('https://www.vagas.com.br')

    driver.implicitly_wait(5)

    # o método '.find_element()' localiza os elementos da página atual da sessão, baseado no tipo de elemento/ID que o
    # objeto possui e pelo nome da classe dado ao elemento do HTML. Após selecionarmos esse objeto, podemos passar
    # uma string usando o método '.send_keys()' que simula as teclas pressionadas no teclado.
    search_bar = driver.find_element(by=By.ID, value='nova-home-search')
    search_bar.send_keys(position + Keys.ENTER)


    driver.implicitly_wait(10)

    prev_height = -1

    # laço para rolar até o final da página
    while True:
        
        time.sleep(4)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # rola até o final da página - (x-coord, y-coord)
        new_height = driver.execute_script("return document.body.scrollHeight")  # retona a posição atual em pixels
        
        if new_height == prev_height:
            break

        prev_height = new_height

        try:
            # nessa pagina o "botão" 'maisVagas' não foi configurado usando o elemento <button> do html mas sim um anchor
            # element <a>, o qual possui uma ação configurada via javascript. Para executar a ação atribuída a esse elemento
            # usamos o método '.execute_script()' e passamos como argumentos uma string contendo com script para executar a ação
            # e um argumento que contém os dados da tag html.
            see_more = driver.find_element(By.ID, 'maisVagas')
            driver.execute_script('arguments[0].click()', see_more) # executa a ação que simula o clique de um botão
            
            time.sleep(3)

        except:
            time.sleep(1)

    # html da página
    page_source = driver.page_source

    driver.quit()

    return page_source


def get_job_opportunity_info(job_url: str, position: str) -> dict:
    """Retona um dicionário contendo as infomações da vaga.

    Args:
        job_url (str): url da vaga
        position (str): nome da vaga buscada

    Returns:
        dict: dicionário com os atributos da vaga
    """

    r = requests.get('https://www.vagas.com.br' + job_url)

    job_page = BeautifulSoup(r.content, 'html.parser')


    # obtem os dados do JSON
    try:
        string_json = job_page.find_all('script', {'type': 'application/ld+json'})[-1].text.strip()
        request_json = json.loads(string_json)
    except:
        request_json = None
    

    
    job_info = {}

    job_info['site_da_vaga'] = 'Vagas.com'
    job_info['link_site'] = 'https://www.vagas.com.br' + job_url
    job_info['link_origem'] = None

    try:
        job_info['data_publicacao'] = job_page.select('.job-breadcrumb li')[0].text.strip()
    except:
        job_info['data_publicacao'] = None

    try:
        job_info['data_expiracao'] = request_json.get('validThrough')
    except:
        job_info['data_expiracao'] = None

    
    job_info['data_coleta'] = datetime.today().strftime('%Y-%m-%d')
    job_info['posicao'] = position
    

    try:
        job_info['senioridade'] = job_page.select('.job-hierarchylist')[0].select_one('span').get('aria-label')
    except:
        job_info['senioridade'] = None


    try:
        job_info['titulo_vaga'] = job_page.select('.job-shortdescription__title')[0].text.strip()
    except:
        job_info['titulo_vaga'] = None


    try:
        job_info['nome_empresa'] = job_page.select('.job-shortdescription__company')[0].text.strip()
    except:
        job_info['nome_empresa'] = None


    try:
        job_info['cidade'] = request_json['jobLocation']['address'].get('addressLocality')
        job_info['estado'] = request_json['jobLocation']['address'].get('addressRegion')
    except:
        job_info['cidade'] = None
        job_info['estado'] = job_page.select('.info-localizacao')[0].text.strip()


    job_info['modalidade'] = None

    job_info['contrato'] = None


    try:
        job_info['regime'] = job_page.select('.info-modelo-contratual')[0].text.strip()
    except:
        job_info['regime'] = 'Não informado'


    job_info['pcd'] = None


    try:
        job_info['beneficios'] = []
        benefits = job_page.select('.job-benefits__list')[0].find_all('span')

        for benefit in benefits:
            job_info['beneficios'].append(benefit.text.strip())

    except:
        job_info['beneficios'] = None
    

    job_info['skills'] = None


    try:
        job_info['codigo_vaga'] = job_page.select('.job-breadcrumb li')[1].text.strip()
    except:
        job_info['codigo_vaga'] = None


    try:
        job_info['descricao'] = job_page.select('.job-tab-content.job-description__text.texto')[0].text.strip()
    except:
        job_info['descricao'] = None
        

    return job_info


def get_job_list_info(position: str, verbose: bool = True) -> list[dict]:
    """Retorna uma lista de dicionários com as vagas encontradas para a posição.

    Args:
        position (str): nome da vaga buscada
        verbose (bool, optional): exibe progresso a cada 20 vagas adicionadas. Defaults to True.

    Returns:
        list[dict]: lista de dicionários no padrão json com as informações das vagas
    """

    page_source = get_job_position_data_web(position)

    soup = BeautifulSoup(page_source, 'html.parser')

    job_opportunities = soup.select('.link-detalhes-vaga')

    job_list = []

    print(f'Collectando dados para {position} ')

    for index, job in enumerate(job_opportunities):
        
        if verbose == True and index % 20 == 0:
            print(f'{index} vagas coletadas')
            
        job_url = job['href']
        job_info = get_job_opportunity_info(job_url, position)

        job_list.append(job_info)

    return job_list


def saving_data(position: str, job_list: list) -> None:
    """Salva os dados obtidos em arquivos JSON e excel

    Args:
        position (str): nome da posição
        job_list (list): lista com as informações das vagas

    Returns:
        None
    """

    position = position.replace(' ', '_').lower()

    with open(f'data/data_raw/tmp/data_json/{position}_vagas.json', 'w', encoding='utf8') as file:
        json.dump(job_list, file, ensure_ascii=False, indent=4)

    df_position = pd.DataFrame(job_list)

    df_position.to_excel(f'data/data_raw/tmp/data_csv/{position}_vagas.xlsx', index=False)

    return None

# obtem os dados das vagas
analista_vagas = get_job_list_info('"Analista de Dados"', True)
cientista_vagas = get_job_list_info('"Cientista de Dados"', True)
engenharia_vagas = get_job_list_info('"Engenharia de Dados"', True)


# salva as mudanças feitas na coleta atual dentro da pasta 'tmp'
saving_data('Analista de Dados', analista_vagas)
saving_data('Cientista de Dados', cientista_vagas)
saving_data('Engenharia de Dados', engenharia_vagas)


# concatena os dados da coleta atual
full_data = analista_vagas + cientista_vagas + engenharia_vagas
df_vagas = pd.DataFrame(full_data)

try:
    # tenta concatenar novos dados extraidos com os dados existentes salvos
    df_saved = pd.read_excel('data/data_raw/vagas_vagas_raw.xlsx')
    df_vagas = pd.concat([df_saved, df_vagas], axis=0)

    df_vagas.to_excel('data/data_raw/vagas_vagas_raw.xlsx', index=False)

except:
    # cria o arquivo 'vagas_vagas_raw.xlsx' se ele não existir (primeira execução do código)
    df_vagas.to_excel('data/data_raw/vagas_vagas_raw.xlsx', index=False)