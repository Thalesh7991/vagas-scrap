import csv
import json
import os
from datetime import datetime
from random import randint
from time import sleep

import psutil
from bs4 import BeautifulSoup
from job_scraper import JobScraper
from selenium import webdriver
from selenium.common.exceptions import (ElementNotInteractableException,
                                        InvalidSessionIdException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class GlassdoorScraper(JobScraper):

    def __init__(self) -> None:
        super().__init__('Glassdoor')
        self.cookie = {"name": "at", "value": "Vffs0MlCIDEfflQ11OInCvejLSP2LJcus1xBWozC4laeA4Xfzb6pv7qDZ_nwxqGx8vddl85T-AGlsgrFvWOm3fmwDp5hZoRrXCoQlk2Xvune7iwSoRLLsAB3X0SorZbu9v_SHQtJ3TH-8DeJGhIUNDFe7nbcqLIDnERzKYMblmuGV7vjGilr4kCHdQsm_TxJu2t9KW2a10gCKYDmmtefQp3RY5JaWyGuy1rFiAbYDs3OnryED52XCKCW-gcOGwrz1mHg6DWAqo87ZwLESUOWplI6L8WSW-F2-K9Z199grBuAb3MLwFokvYoBjWrS8EwgcF0w_cpo3rX9zifSNrvXyp5aFjLXX6gqwbGx5DCikwD423oWNinJ1GC-pZVni0VNPpcJaAy6aIPehY9E0n1c-Fj64lSudtDotmVv1vc5Y7DYjGyCdq2OI24rwf_8We9hupYU9R_45EN869hsAmc57uAG1OXm_AoRH93wbxMxfZSPa2ZBubcFr6UWeGOWM0JLifZjn5ZPmRqBLvNBhfk0V6H9zBsIB8glha60m73wEIBDnxjBc6ysk0JUj6ngOEA9ULt6vtV1_i9dzm3sw4nDaPlJNE7bFNAWX1o0j76pjHRr4ZzWjr52MnqlqcLE3AkMtsStwFGPOjwOny01p-JwXnR7AfmS3dzPgOBdWiDtt-uIATlpy00nZO6azbxMATcPtLj--nrciT6pfzwIUpcMg45SEgbI4qiQnH9RAgw3BiEgXrXDruDhWAdljwePDGJb7GwHUkYGBcgWIqsxah2tRHafGKoBEDLPMV8__Nknbr-OJ-2ppMnCK1jPuR7r9viJUHVEdyCrwpszdwYDe2dvlsGNtIYbDbSGdVk_LaiZscvWdK0EVyHliqxxPQ"}

    def pesquisa_chave(self, dictionario, chave):
        for key, value in dictionario.items():
            if key == chave:
                return value
            elif isinstance(value, dict):
                result = self.pesquisa_chave(value, chave)
                if result is not None:
                    return result
        return None

    def clean_tags(self, text):

        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        return clean_text

    def __get_job_urls(self, xpath, cargo):

        job_elements = self.driver.find_elements('xpath', xpath)

        job_urls = dict()

        for element in job_elements:
            href = element.get_attribute('href')
            job_id = href.split('=')[-1]
            if href:
                job_urls[job_id] = [href, cargo]

        return job_urls

    def __verify_json(self) -> bool:

        wait = WebDriverWait(self.driver, 50)

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//script[@id and contains(text(), "props")]')
            )
        )

        script_tag = self.driver.find_element(
            'xpath', '//script[@id and contains(text(), "props")]'
        ).get_attribute('innerHTML')
        data = json.loads(script_tag)
        job_json = self.pesquisa_chave(data, 'job')
        header_json = self.pesquisa_chave(data, 'header')

        if job_json is None or header_json is None:
            return True

        return False

    def __delete_json(self, filepath, key):

        with open(filepath, 'r') as arquivo:
            dados = json.load(arquivo)

        if key in dados:
            del dados[key]
        else:
            return

        with open(filepath, 'w') as arquivo:
            json.dump(dados, arquivo, indent=4)

        if not dados:
            os.remove(filepath)

    def __create_json(self, dictionary, filepath):

        if os.path.exists(filepath):

            with open(filepath, 'r') as f:
                dados_json = json.load(f)

                for chave in dictionary:
                    if chave not in dados_json:
                        dados_json.update(dictionary)

        else:
            dados_json = dictionary

        with open(filepath, 'w') as f:
            json.dump(dados_json, f, indent=4)

    def __browser_refresh(self):
        if self.driver is not None:
            self.driver.quit()
            sleep(3)
            self.driver = self._init_selenium(False)

    def __close_modal(self):
        try:

            close_modal = self.driver.find_element(
                'xpath',
                '//span[@class="SVGInline modal_closeIcon"]'
            )
            close_modal.click()

        except (StaleElementReferenceException, NoSuchElementException):
            try:

                self.driver.find_element(
                    'xpath',
                    '//button[@data-test="job-alert-modal-close"]'
                ).click()
            except (StaleElementReferenceException, NoSuchElementException):
                pass

    def __exists_xpath(self, xpath):

        try:
            self.driver.find_element(
                'xpath',
                xpath
            )

            return True
        except:
            return False

    def __seleciona_filtro(self, idx_option):
        self.driver.find_element(
            'xpath',
            '//button[@data-test="expand-filters"]'
        ).click()

        sleep(1)

        self.driver.find_element(
            'xpath',
            '//button[@data-test="clear-search-filters"]'
        ).click()

        sleep(1)

        self.driver.find_element(
            'xpath',
            '//button[@data-test="expand-filters"]'
        ).click()

        sleep(1)

        expand_city = self.driver.find_element(
            'xpath',
            '//button[@data-test="cityId"]'
        )
        expand_city.click()
        aria_expanded = expand_city.get_attribute('aria-expanded')

        if aria_expanded == 'false':
            expand_city.click()

        sleep(3)

        #! verificar se o filtro de cidades está aberto
        cidades = self.driver.find_elements(
            'xpath', '//button[@data-test="cityId-option"]')

        sleep(3)

        next_city = cidades[idx_option]
        next_city.click()

        sleep(2)

        self.driver.find_element(
            'xpath',
            '//button[@data-test="apply-search-filters"]'
        ).click()

    def get_links(self):
        links = ['https://www.glassdoor.com.br/Vaga/brasil-engenheiro-agrimensor-vagas-SRCH_IL.0,6_IN36_KO7,28.htm', 
                 'https://www.glassdoor.com.br/Vaga/brasil-top%C3%B3grafo-vagas-SRCH_IL.0,6_IN36_KO7,16.htm',
                'https://www.glassdoor.com.br/Vaga/brasil-geoprocessamento-vagas-SRCH_IL.0,6_IN36_KO7,23.htm'
                ]
        i = 0
        for link in links:
            job_title = ['engenheiro agrimensor', 'topografo', 'geoprocessamento']
            self.driver = self._init_selenium(False)

            self.driver.get(link)
            self.driver.add_cookie(self.cookie)
            self.driver.refresh()

            wait = WebDriverWait(self.driver, 20)

            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//input[@id="searchBar-jobTitle"]')
                )
            )

            # # Preenche o campo de pesquisa do título de trabalho
            # barra_pesquisa = WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH, '//input[@id="searchBar-jobTitle"]'))
            # )
            # barra_pesquisa.send_keys(job_title)

            # # Preenche o campo de localização
            # barra_location = WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH, '//input[@id="searchBar-location"]'))
            # )
            # barra_location.send_keys('Brasil')

            # # Após preencher os campos, envie com ENTER
            # barra_location.send_keys(Keys.ENTER)

            sleep(10)

            #self.__close_modal()

            # qnt_vagas = self.driver.find_element(
            #     'xpath',
            #     '//h1[@data-test="search-title"]').get_attribute(
            #         'innerHTML').split()[0].replace('.', '')

            #if int(qnt_vagas) > 870:
            if 1 > 2:
                self.driver.find_element(
                    'xpath',
                    '//button[@data-test="expand-filters"]'
                ).click()

                self.driver.find_element(
                    'xpath',
                    '//button[@data-test="cityId"]'
                ).click()

                num_cidades = len(
                    self.driver.find_elements(
                        'xpath', '//button[@data-test="cityId-option"]')
                ) - 1

                self.driver.find_element(
                    'xpath',
                    '//button[@data-test="expand-filters"]'
                ).click()

                idx_option = 0

                while True:

                    if idx_option > num_cidades:
                        break

                    self.__close_modal()

                    self.__seleciona_filtro(idx_option)

                    filtro_data = self.driver.find_element(
                        'xpath',
                        '//button[@data-test="fromAge"]'
                    )

                    filtro_data.click()

                    filtro_data.find_element(
                        'xpath',
                        '//button[@data-test="fromAge-option"]/div[contains(text(), "Última semana")]'
                    ).click()

                    self.driver.refresh()

                    sleep(2)

                    self.__close_modal()

                    if self.driver.title.split()[0] == '0':
                        back_url = self.driver.current_url.split('?')[0]
                        self.driver.get(back_url)
                        idx_option += 1
                        sleep(3)
                        continue

                    sleep(2)

                    # qnt_vagas = self.driver.find_element(
                    #     'xpath',
                    #     '//h1[@data-test="search-title"]'
                    # ).get_attribute(
                    #     'innerHTML').split()[0].replace('.', '')

                    i = 0

                    while True:
                        sleep(1)

                        jobs_antes = len(
                            self.driver.find_elements(
                                'xpath',
                                './/a[contains(@id, "job-title")]'
                            )
                        )

                        if self.__exists_xpath(
                                '//button[@data-test="load-more"]'):

                            try:

                                load_button = wait.until(
                                    EC.presence_of_element_located(
                                        (By.XPATH,
                                         '//button[@data-test="load-more"]')
                                    )
                                )
                                load_button.click()

                                sleep(3)

                                self.__close_modal()

                                sleep(3)

                            except NoSuchElementException:
                                self.__close_modal()

                            jobs_depois = len(
                                self.driver.find_elements(
                                    'xpath',
                                    './/a[contains(@id, "job-title")]'
                                )
                            )

                            if jobs_antes == jobs_depois:
                                qnt_jobs = jobs_depois
                                break

                        else:
                            qnt_jobs = len(self.driver.find_elements(
                                'xpath', './/a[contains(@id, "job-title")]'))
                            break

                    filepath = '../data/data_raw/tmp/glassdoor.json'
                    print('FILEEEEE')
                    links_json = self.__get_job_urls(
                        './/a[contains(@id, "job-title")]', job_title[i])
                    self.__create_json(links_json, filepath)

                    idx_option += 1

                    sleep(5)
            # TODO: Criar um else para quando não tiver que filtrar por cidades
            else:
                while True:
                    sleep(1)

                    try:
                        load_button = wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH,
                                    '//button[@data-test="load-more"]')
                            )
                        )
                        load_button.click()

                        sleep(3)

                        self.__close_modal()

                        sleep(3)

                        wait.until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR,
                                    'button[data-test="load-more"][data-loading="false"]')
                            )
                        )
                    except:
                        self.__close_modal()

                    qnt_jobs = len(self.driver.find_elements(
                        'xpath', './/a[contains(@id, "job-title")]'))

                    # ! Coloquei uma condição para que não pegue mais de 870 jobs
                    # if qnt_jobs >= int(qnt_vagas) or \
                    #         int(qnt_vagas) - qnt_jobs < 10 or \
                    #     qnt_jobs >= 870:
                    filepath = '../data/data_raw/tmp/glassdoor.json'

                    links_json = self.__get_job_urls(
                    './/a[contains(@id, "job-title")]', job_title[i])
                    self.__create_json(links_json, filepath)
                    break
            i = i +1
            self.driver.quit()

    def get_json_file(self, filepath):
        with open(filepath, 'r') as file:
            dados_json = json.load(file)

        return dados_json

    def __get_expired_date(self):
        if self.__exists_xpath('//div[@data-test="expired-job-notice"]'):
            return datetime.now().date()
        return

    def scrape_jobs(self):

        while os.path.exists('../data/data_raw/tmp/glassdoor.json'):
            print('aaaaa')
            job_urls = self.get_json_file(
                '../data/data_raw/tmp/glassdoor.json')

            urls_processadas = 1

            self.driver = self._init_selenium(False)

            for key, list_jobs in job_urls.items():
                print('bbbbb')
                url, job_title = list_jobs

                if urls_processadas % 5 == 0:

                    memory_use = psutil.virtual_memory().used / (1024 * 1024)
                    print(f"Uso de memória: {memory_use:.2f} MB")

                    self.__browser_refresh()
                    sleep(3)

                try:
                    self.driver.get(url)
                    self.driver.refresh()
                    sleep(3)

                    i = 0
                    while True:

                        if not self.__verify_json():
                            break
                        elif i == 10:
                            self.driver.refresh()
                            sleep(5)

                        i += 1

                    if self.__verify_json():
                        self.driver.refresh()
                        wait.until(
                            lambda driver: driver.execute_script(
                                "return document.readyState") == "complete"
                        )

                    script_tag = self.driver.find_element(
                        'xpath',
                        '//script[@id and contains(text(), "props")]'
                    ).get_attribute('innerHTML')
                    data = json.loads(script_tag)
                    job_json = self.pesquisa_chave(data, 'job')
                    header_json = self.pesquisa_chave(data, 'header')
                    map_json = self.pesquisa_chave(data, 'map')
                    modalidade = self.driver.find_element(
                        'xpath', '//div[@data-test="location"]').text.lower()

                except (TimeoutException, StaleElementReferenceException):
                    self.driver.close()
                    continue
                except InvalidSessionIdException:
                    sleep(5)
                    print('Erro InvalidSessionIdException')
                    self.__browser_refresh()
                    continue

                try:
                    dados = {
                        'site_da_vaga': self.site_name,
                        'link_site': url,
                        'link_origem': 'www.glassdoor.com.br/Vaga/index.htm'
                        + header_json['applyUrl'],
                        'data_publicacao': datetime.strptime(job_json['discoverDate'], '%Y-%m-%dT%H:%M:%S').date(),
                        'data_expiracao': '',
                        'data_coleta': datetime.now().date(),
                        'posicao': job_title.capitalize(),
                        'senioridade': '',
                        'titulo_da_vaga': header_json['jobTitleText'],
                        'nome_empresa': header_json['employerNameFromSearch'],
                        'cidade': map_json['cityName'],
                        'estado': map_json['stateName'],
                        'modalidade': modalidade.capitalize()
                        if 'remoto' in modalidade else '',
                        'contrato': '',
                        'regime': '',
                        'pcd': '',
                        'codigo_vaga': job_json['listingId'],
                        'descricao': self.clean_tags(job_json['description']),
                        'skills': header_json['indeedJobAttribute']['skillsLabel'] if header_json['indeedJobAttribute'] != None else ''
                    }
                except TypeError:

                    if self.__exists_xpath(
                            '//div[@data-test="expired-job-notice"]'):
                        filepath = '../data/data_raw/tmp/glassdoor.json'
                        #self.__delete_json(filepath, key)

                        continue

                self.save_csv(dados)

                filepath = '../data/data_raw/tmp/glassdoor.json'

                self.__delete_json(filepath, key)

                sleep(randint(1, 15))

                urls_processadas += 1

        sleep(5)
        self.driver.quit()


def main():

    scraper = GlassdoorScraper()
    if not os.path.exists('../data/data_raw/tmp/glassdoor.json'):
        print('AAAAAAAAAAAA')
        scraper.get_links()
    scraper.scrape_jobs()


if __name__ == '__main__':
    main()
