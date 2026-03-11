from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime
import requests
import json

def vitrine_vagas_gupy(LINK, nome_vaga):

    driver = webdriver.Chrome()
    driver.get(LINK)
    time.sleep(3)
    driver.maximize_window()
    try:
        cuidado_golpes = driver.find_element(By.XPATH, '//*[@id="radix-0"]/div[2]/button')
        cuidado_golpes.click()
    except:
        pass
    search = driver.find_element(By.XPATH, '//*[@id="undefined-input"]')
    search.send_keys(nome_vaga)
    search.send_keys(Keys.ENTER)

    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    driver.quit()

    return soup

def coleta_dados_vagas(soup, nome_vaga):

    lista_de_vagas = soup.find_all('ul', {'class':'ssc-a01de6b-0 ypLsU'})

    list_columns = [
            'site_da_vaga',
            'link_site',
            'link_origem',
            'data_publicacao',
            'data_expiracao',
            'data_coleta',
            'posicao',
            'titulo_da_vaga',
            'local',
            'modalidade',
            'nome_empresa',
            'contrato',
            'regime',
            'pcd',
            'beneficios',
            'codigo_vaga',
            'descricao'
    ]

    df_vagas = pd.DataFrame(
            columns = list_columns
        )

    for vaga in lista_de_vagas:

        df_aux = pd.DataFrame(
            columns = list_columns
        )

        ## Buscando informações na própria página de pesquisa da Gupy

        df_aux.loc[0,'site_da_vaga'] = 'Gupy'

        df_aux.loc[0,'link_site'] = vaga.findAll('a')[0]['href']

        df_aux.loc[0,'link_origem'] = vaga.findAll('a')[0]['href']

        df_aux.loc[0,'data_publicacao'] = vaga.findAll('p', {'class':'sc-dPyBCJ kyoAxx sc-1db88588-0 inqtnx'})[0].text

        df_aux.loc[0,'data_coleta'] = datetime.datetime.today().strftime('%Y-%m-%d')

        df_aux.loc[0,'posicao'] = nome_vaga

        df_aux.loc[0,'titulo_vaga'] = vaga.findAll('h2')[0].text

        df_aux.loc[0,'nome_empresa'] = vaga.findAll('p', {'class':'sc-dPyBCJ kyoAxx sc-a3bd7ea-6 cQyvth'})[0].text

        try: 
            df_aux.loc[0,'local'] = vaga.findAll('span', {'class',"sc-23336bc7-1 cezNaf"})[0].text
        except:
            df_aux.loc[0,'local'] = np.nan

        try:
            df_aux.loc[0,'modalidade'] = vaga.findAll('span', {'class',"sc-23336bc7-1 cezNaf"})[1].text
        except:
            df_aux.loc[0,'modalidade'] = np.nan

        try:
            df_aux.loc[0,'contrato'] = vaga.findAll('span', {'class',"sc-23336bc7-1 cezNaf"})[2].text
        except:
            df_aux.loc[0,'contrato'] = np.nan

        df_aux.loc[0, 'regime'] = np.nan

        try:
            df_aux.loc[0,'pcd'] = vaga.findAll('span', {'class',"sc-23336bc7-1 cezNaf"})[3].text
        except:
            df_aux.loc[0,'pcd'] = np.nan

        df_aux.loc[0,'beneficios'] = np.nan

        ## Request da página da vaga

        try:
            response = requests.get(vaga.findAll('a')[0]['href']) # link da vaga
            time.spleep(5)
            page = BeautifulSoup(response.text, 'html.parser')

            try:
                lista_descricao_em_texto = [page.findAll('div', {'data-testid':'text-section'})[i].text for i in range(len(page.findAll('div', {'data-testid':'text-section'})))]
                descricao_completa = '\n'.join(lista_descricao_em_texto)
                df_aux.loc[0,'descricao'] = descricao_completa
            except:
                df_aux.loc[0,'descricao'] = np.nan

            try:
                df_aux.loc[0,'codigo_vaga'] = json.loads(page.findAll('script', {'id':'__NEXT_DATA__'})[0].get_text())['props']['pageProps']['job']['id']
            except:
                df_aux.loc[0,'codigo_vaga'] = np.nan

            try:
                df_aux.loc[0,'data_expiracao'] = json.loads(page.findAll('script', {'id':'__NEXT_DATA__'})[0].get_text())['props']['pageProps']['job']['expiresAt']
            except:
                df_aux.loc[0,'data_expiracao'] = np.nan
        except:
            df_aux.loc[0,'descricao'] = np.nan
            df_aux.loc[0,'codigo_vaga'] = np.nan
            df_aux.loc[0,'data_expiracao'] = np.nan
        
        df_vagas = pd.concat([df_vagas, df_aux], axis=0, ignore_index=True)
        
    df_vagas = df_vagas.reset_index(drop=True)

    nome_vaga = nome_vaga.replace(' ', '_').lower()

    # df_vagas.to_excel(f'../data/data_raw/tmp/data_csv/{nome_vaga}_gupy.xlsx', index=False)

    return df_vagas

def busca_vagas(nome_vaga):

    LINK = 'https://portal.gupy.io/'

    vagas_gupy_page = vitrine_vagas_gupy(LINK,nome_vaga)

    df_vagas_gupy = coleta_dados_vagas(vagas_gupy_page, nome_vaga)

    return df_vagas_gupy

if __name__ == '__main__':

    lista_posicoes = ['Cientista de Dados'] #, 'Cientista de Dados', 'Engenheiro de Dados']
    df_vagas_full = pd.DataFrame()

    for posicao in lista_posicoes:
        
        df_vagas_aux = busca_vagas(posicao)
        df_vagas_aux.shape
        
        df_vagas_full = pd.concat([df_vagas_full, df_vagas_aux], axis = 0)
        
    df_vagas_full.reset_index()

    df_vagas_full.to_excel('../data/data_raw/vagas_gupy_raw.xlsx', index=False)
    df_vagas_full.shape