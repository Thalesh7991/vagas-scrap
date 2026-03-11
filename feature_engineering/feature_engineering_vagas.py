import re
import pandas as pd

from unidecode import unidecode
from datetime  import datetime, timedelta


def clean_publish_date(date_string: str) -> str | int:

    if 'dias' in date_string:
        days = re.findall(r'\d+', date_string)[0]
        return int(days)
    
    elif 'ontem' in date_string:
        return 1
    
    elif 'hoje' in date_string:
        return 0
    
    else:

        date = date_string.split(' ')[-1]

        date = date.split('/')
        date.reverse()

        formatted_date = '-'.join(date)

        return formatted_date


def subtract_date(date: str, days: int) -> str:
    
    real_date_datetime = datetime.strptime(date, '%Y-%m-%d') - timedelta(days)
    real_date_string = real_date_datetime.strftime('%Y-%m-%d')

    return real_date_string


def get_state_uf(state: str) -> str:
    
    state_uf = {
            'Acre': 'AC',
            'Alagoas': 'AL',
            'Amazonas': 'AM',
            'Amapá': 'AP',
            'Bahia': 'BA',
            'Ceará': 'CE',
            'Distrito Federal': 'DF',
            'Espírito Santo': 'ES',
            'Goiás': 'GO',
            'Maranhão': 'MA',
            'Mato Grosso': 'MT',
            'Mato Grosso do Sul': 'MS',
            'Minas Gerais': 'MG',
            'Pará': 'PA',
            'Paraíba': 'PB',
            'Paraná': 'PR',
            'Pernambuco': 'PE',
            'Piauí': 'PI',
            'Rio de Janeiro': 'RJ',
            'Rio Grande do Norte': 'RN',
            'Rio Grande do Sul': 'RS',
            'Rondônia': 'RO',
            'Roraima': 'RR',
            'Santa Catarina': 'SC',
            'São Paulo': 'SP',
            'Sergipe': 'SE',
            'Tocantins': 'TO'
    }

    if state_uf.get(state) is None:
        return state
    else:
        return state_uf.get(state)


def search_description_regex(search_words: list[str], job_description: str) -> list[str]:
    
    search_mask = rf'({"|".join(search_words)})'

    matches = re.findall(search_mask, job_description, flags=re.I)

    matches = list( map( str.lower, matches ) )

    return matches


def fill_modality_column(search_words: list[str], job_description: str) -> str:

    matched_words = search_description_regex(search_words, job_description)
    
    search_words = search_words[:]      # cria uma copia da lista (não afeta a variável global passada como referência)
    search_words.remove('Presencial')

    if 'híbrido' in matched_words:
        return 'Híbrido'
    
    elif any( True if word.lower() in matched_words else False for word in search_words):
        return 'Remoto'
    
    else:
        return 'Presencial'
    

def fill_pcd_column(search_words: list[str], job_description: str) -> str:
    
    matched_words = search_description_regex(search_words, job_description)

    search_condition = any( True if pcd_word.lower() in matched_words else False for pcd_word in search_words )

    if search_condition:
        return 'Sim'
    else:
        return 'Não informado'


def get_skills_list(description: str) -> list[str]:

    # adiciona o ponto-virgula onde havia uma quebra de linha seguida por letra maiuscula
    description = re.sub(r'(;?\n)(?=[A-Z])', r';', description)

    # substitui múltiplos espaços por apenas um ('\t' e '\n' são substituidos)
    description = re.sub(r'\s+', ' ', description)

    # cria uma lista com elementos separados pelos simbolos: '-', ';', '*' etc
    skills_list = re.findall(r'(?:(?<=[-\*\;\•\.]).*?(?=[-\;\•\.]))', description)

    # remove items vazios da lista
    skills_list = list( filter(None, skills_list) )


    return skills_list


def format_skills_list(skills_list: list[str]) -> list[str]:
    skills_str = ', '.join(skills_list)
    
    skills_str = unidecode(skills_str).lower()

    micro_skills = []
    macro_skills = set()

    for skill_map in skills_map_list:

        macro, micro, lookup_string = skill_map.values()

        skill_matches = lookup_string.split(', ')
        match_lookup = any( True if skill in skills_str else False for skill in skill_matches )

        if match_lookup:
            micro_skills.append(micro)
            macro_skills.add(macro)
        else:
            continue
    
    macro_skills = sorted(macro_skills)
    macro_skills = list(macro_skills)

    return micro_skills, macro_skills


def get_capabilities(description: str) -> list[str]:

    description = unidecode(description).lower()

    capability_list = []

    for capability_map in capabilities_map_list:
        capability, lookup_string = capability_map.values()
        capability_matches = lookup_string.split(', ')

        match_lookup = any( True if word in description else False for word in capability_matches )

        if match_lookup:
            capability_list.append(capability)

    return capability_list


def clean_vagas_dataframe(df_vagas: pd.DataFrame) -> pd.DataFrame:

    df_vagas['data_publicacao'] = df_vagas['data_publicacao'].apply( lambda date: clean_publish_date(date) )

    df_vagas['estado'] = df_vagas['estado'].apply( lambda state: get_state_uf(state) )

    df_vagas['contrato'] = df_vagas['regime'].apply( lambda regime: 'Efetivo'    if regime == 'Regime CLT'      else
                                                                    'Associado'  if regime == 'Pessoa Jurídica' else
                                                                    'Estágio'    if regime == 'Estágio'         else
                                                                    'Temporário' if regime == 'Temporário'      else
                                                                    'Não informado'
                                                        )


    df_vagas['data_publicacao'] = df_vagas.apply( 
                                            lambda x: 
                                                subtract_date(x['data_coleta'], x['data_publicacao']) 
                                                if isinstance(x['data_publicacao'], int) else 
                                                x['data_publicacao'], axis=1 
                                            )



    modalidade_search = ['Híbrido', 'Remoto', 'Home Office', 'Presencial']

    df_vagas['modalidade'] = df_vagas.apply( lambda columns: 'Remoto' if columns['estado'] == 'Todo o Brasil' else 
                                                            fill_modality_column(modalidade_search, columns['descricao']), 
                                            axis=1
                                    )


    pcd_search = ['PcD', 'deficiência', 'deficiente']

    df_vagas['pcd'] = df_vagas['descricao'].apply( lambda description: fill_pcd_column(pcd_search, description) )


    df_vagas['skills'] = df_vagas['descricao'].apply( lambda description: get_skills_list(description) )

    df_vagas['habilidades_micro'] = df_vagas['skills'].apply( lambda skills_list: format_skills_list(skills_list)[0] )
    df_vagas['habilidades_macro'] = df_vagas['skills'].apply( lambda skills_list: format_skills_list(skills_list)[1] )

    df_vagas['competencias'] = df_vagas['descricao'].apply( lambda description: get_capabilities(description) )


    return df_vagas



df_vagas = pd.read_excel('data/data_raw/vagas_vagas_raw.xlsx')

df_skills = pd.read_excel('data/dicionario-skills.xlsx', sheet_name='Habilidades')

skills_map_list = df_skills.to_dict('records')

df_capabilities = pd.read_excel('data/dicionario-skills.xlsx', sheet_name='Competencias')

capabilities_map_list = df_capabilities.to_dict('records')


df_vagas = clean_vagas_dataframe(df_vagas)

features_selected = [
    'site_da_vaga',
    'link_site',
    'link_origem',
    'data_publicacao',
    'data_expiracao',
    'data_coleta',
    'posicao',
    'senioridade',
    'titulo_vaga',
    'nome_empresa',
    'cidade',
    'estado',
    'modalidade',
    'contrato',
    'regime',
    'pcd',
    'beneficios',
    'habilidades_macro',
    'habilidades_micro',
    'competencias',
    'codigo_vaga',
    'descricao'
]

df_vagas[features_selected].to_excel('data/data_clean/vagas_vagas_clean.xlsx', index=False)
