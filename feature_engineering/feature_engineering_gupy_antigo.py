import re
import pandas as pd
from unidecode import unidecode
from datetime import datetime


# função de faz matches com as senioridades das vagas
def busca_senioridade(titulo_vaga: str, match_list: list[str]) -> bool:
    """Identifica se a senioridade label está dentro do titulo da vaga

    Args:
        titulo_vaga (str): titulo da vaga
        match_list (list[str]): lista de substrings usadas para identificar um grau de senioridade

    Returns:
        bool: verifica se a vaga corresponde a senioridade

    Exemplos:
    ---
    >>> busca_seniorida('Analista de dados pleno', ['nivel ii', pleno])
    True
    """

    senioridade = False
    for sub_string in match_list:
        if sub_string in titulo_vaga:
            senioridade = True
    
    return senioridade

def get_benefits_list(description: str) -> list[str] | None:
    """Obtém a lista de benefícios a partir da descrição da vaga

    Args:
        description (str): descrição da vaga

    Returns:
        list[str] | None: lista com benefícios ou valor nulo

    Exemplos:
    ---
    >>> descricao = 'Nós oferecemos a você: Vale-Alimentação; Vale-Transporte; Gympass;'
    >>> get_benefits_list(descricao)
    ['Vale-Alimentação', 'Vale-Transporte', 'Gympass']
    """

    try:
        # na gupy a descricao geralmente é dividida em 4 seções: 0 -> 'JOB DESCRIPTION';                 1 -> 'RESPONSIBILITIES AND ASSIGNMENTS';
        #                                                        2 -> 'REQUIREMENTS AND QUALIFICATIONS'; 3 -> 'ADDITIONAL INFORMATION'
        # a lista de beneficios geralmente esta contida na seção 'ADDITIONAL INFORMATION' (existem alguns casos que isso não é verdade)
        
        # divide a descricao em seções
        description_sections = description.split('\n')
        
        # obtem o indice da seção 'ADDITIONAL INFORMATION' (geralmente é o terceiro indice mas existem paginas com menos seções)
        index_benefit = [ True if 'Informações adicionais' in section else False for section in description_sections ].index( True )

        # seleciona a seção 'ADDITIONAL INFORMATION'
        benefit_str = description_sections[index_benefit]

        # substitui multiplos espaços em sequência por apenas um
        benefit_str = re.sub(r'\s+', ' ', benefit_str)

        # adiciona um ponto-virgula ou ')' onde uma letra maiuscula é antecida por uma minuscula, precisamos dessa condição porque
        # em muitos casos não existe um caracter utilizado para deixar clara separação entre os benefícios dentro da string; nessa
        # situação, os beneficios estarão colados uns aos outros e a unica forma de diferenciá-los são os caracteres maiusculos.
        benefit_str = re.sub(r'(?<=[a-z]|\))([A-Z])', r';\1', benefit_str)  # Exemplo:  Gympass(ilimitado)Vale-TransporteConvenio
                                                                            #        -> Gympass(ilimitado);Vale-Transporte;Convenio
        
        # cria uma lista com substrings contendo uma letra maiúscula precedida e antecedida por um entre: ':', ';', '.', '•', '*'
        # esses simbolos geralmente antecedem / procedem os elementos da lista de beneficios dentro da string.
        benefit_list = re.findall(r'(?:(?<=[\:\;\.\•\*]).*?[A-Z].*?(?=[\.\;\•\*\)]))', benefit_str, flags=re.I)   # Exemplos: '* Gympass;' -> 'Gympass'
                                                                                                                #             '• PLR.'     -> 'PLR'
        
        # remove espaços vazios no final e inicio de cada elemento da lista
        benefit_list = list( map( lambda benefit: benefit.strip(), benefit_list ) )

        return benefit_list
    
    except:
        return None

def replace_va_vr_substrings(benefits_str: str) -> str:
    """Verifica se as substrings VA e/ou VR estão dentro string de benefícios e substitui
    por Vale alimentação e Vale refeição respectivamente. 

    Args:
        benefits_str (str): string contendo os benefícios encontrados separados virgula e espaço.

    Returns:
        str: string contendo as substituições caso elas sejam encontradas.

    Exemplos:
    ---
    >>> benefits_str = 'Convênio médico, VA, VR, Gympass'
    >>> replace_va_vr_substrings(benefits_str)
    'Convênio médico, Vale alimentação, Vale refeição, Gympass'
    """

    va_vr_matches = re.findall(r'V[R|A]\b', benefits_str)

    va_vr_map = zip(['Vale refeição', 'Vale alimentação'], ['VR', 'VA'])

    for va_vr_full, va_vr_short in va_vr_map:

        if va_vr_short in va_vr_matches:
            benefits_str = benefits_str.replace(va_vr_short, va_vr_full)

    return benefits_str

def format_benefits_list(benefit_list: list[str]) -> list[str] | None:
    """Padroniza os elementos da lista de beneficios.

    Args:
        benefit_list (list[str]): lista com beneficios extraídos da descrição.

    Returns:
        list[str] | None: lista com os beneficios padronizados.

    Exemplos:
    ---
    >>> format_benefits_list(['Gympass', 'VR'])
    ['Auxílio academia', 'Vale refeição']
    >>> format_benefits_list(['Total pass', 'VA'])
    ['Auxílio academia', 'Vale alimentação']
    """

    try:
        benefit_list_formatted = []

        # junta os beneficios em uma string separada por vírgula e espaço
        benefits_str = ', '.join(benefit_list)

        # substitui as substrings 'VA' / 'VR' por 'Vale alimentação' / 'Vale refeição'
        benefits_str = replace_va_vr_substrings(benefits_str)

        # remove acentos e deixa a string em lowercase
        benefits_str = unidecode(benefits_str).lower()

        for benefit_key, benefit_matches in benefit_map.items():

            # verifica se o beneficio está presente dentro da string
            match_look = any( True if benefit_word in benefits_str else False for benefit_word in benefit_matches )

            if match_look:
                benefit_list_formatted.append(benefit_key)
            else:
                continue
        
        # se nenhum match é encontrado retona 'None' ao invés de uma lista vazia
        if len(benefit_list_formatted) == 0:
            return None

        return benefit_list_formatted
    
    except:
        return None

# Loading Dataframe
df_gupy = pd.read_excel('../data/data_raw/vagas_gupy_raw.xlsx')

df_vagas = df_gupy.copy()

## Tratamento de Dados
df_vagas['site_da_vaga'] = 'Gupy'
df_vagas['data_publicacao'] = df_vagas['data_publicacao'].apply(lambda x: datetime.strptime(x.replace('Publicada em: ', '').replace('/', '-'),'%d-%m-%Y').strftime('%Y-%m-%d'))
df_vagas['data_coleta'] = df_vagas['data_coleta']
df_vagas['pcd'] = df_vagas['pcd'].apply(lambda x: 'Sim' if x == 'Também p/ PcD' else 'Não informado')


# Senioridade

# matches para as senioridades
junior_matches = ['junior', ' jr'  , ' i', ' l ']
pleno_matches  = ['pleno', ' pl', ' ii', ' ll ']
senior_matches = ['senior', ' sr', ' iii', ' lll ']

# removendo acentos e deixando letras minúsculas
df_vagas['titulo_vaga_tratado'] = df_vagas['titulo_da_vaga'].apply(lambda x: x if pd.isnull(x) else unidecode(x.lower()))

# aplicando função
df_vagas['senioridade_junior'] = df_vagas['titulo_vaga_tratado'].apply(lambda titulo_vaga: busca_senioridade(titulo_vaga, junior_matches))
df_vagas['senioridade_pleno']  = df_vagas['titulo_vaga_tratado'].apply(lambda titulo_vaga: busca_senioridade(titulo_vaga, pleno_matches))
df_vagas['senioridade_senior'] = df_vagas['titulo_vaga_tratado'].apply(lambda titulo_vaga: busca_senioridade(titulo_vaga, senior_matches))

# categorizando senioridades
df_vagas['senioridade'] = df_vagas[['senioridade_junior', 
                                    'senioridade_pleno', 
                                    'senioridade_senior']].apply(lambda x:  'Pleno/Sênior' if (x['senioridade_pleno']) and (x['senioridade_senior']) else
                                                                            'Júnior/Pleno' if (x['senioridade_junior']) and (x['senioridade_pleno']) else
                                                                            'Júnior' if x['senioridade_junior'] else 
                                                                            'Pleno' if x['senioridade_pleno'] else
                                                                            'Sênior' if x['senioridade_senior'] else
                                                                            'Não informado'
                                                                    , axis = 1
                                                            )

# Localidade

df_vagas['cidade'] = df_vagas['local'].apply(lambda x: 'Não informado' if x == 'Não informado' else x.split(' - ')[0])
df_vagas['estado'] = df_vagas['local'].apply(lambda x: 'Não informado' if x == 'Não informado' else x.split(' - ')[1])

df_vagas['estado'] = df_vagas.apply( lambda column: 'Todo o Brasil' if ( column['estado'] == 'Não informado' and column['modalidade'] == 'Remoto' ) else
                                                    column['estado'],
                                    axis=1
                            )

# Beneficios

benefit_map = {
    'Assistência médica':                    ['medica', 'saude', 'medico'],
    'Assistência odontológica':              ['odonto', 'dentista'],
    'Assistência psicológia':                ['psicolog', 'saude mental'],
    'Auxílio academia':                      ['academia', 'gympass', 'gym', 'total pass'],
    'Auxílio combustível':                   ['combustivel'],
    'Auxílio creche':                        ['creche'],
    'Auxílio desenvolvimento':               ['desenvolvimento'],
    'Auxílio estacionamento':                ['estacionamento'],
    'Auxílio farmácia':                      ['farmacia', 'medicamento'],
    'Auxílio fretado':                       ['fretado'],
    'Auxílio home office':                   ['auxilio home', 'custo home'],
    'Bicicletário':                          ['bicleta'],
    'Bolsa auxílio':                         ['bolsa auxilio'],
    'Café da manhã':                         ['cafe da manha'],
    'Cesta básica':                          ['cesta basica'],
    'Cesta de natal':                        ['natal'],
    'Clube de vantagens':                    ['vantagens'],
    'Consignado':                            ['consignado'],
    'Convênio com empresas parceiras':       ['convenio'],
    'Cooperativa de crédito':                ['cooperativa de credito'],
    'Day off aniversário':                   ['aniversario'],
    'Desconto em produtos':                  ['desconto em produtos'],
    'Ginástica laboral':                     ['ginastica laboral'],
    'Horário flexível':                      ['horario flexivel', 'flexibilidade'],
    'Massoterapia':                          ['massoterapia', 'massagem'],
    'Participação nos Lucros ou Resultados': ['lucros', 'plr', 'ppr'],
    'Plano de Aquisição de Ações':           ['aquisicao de acoes'],
    'Previdência privada':                   ['previdencia'],
    'Programa de remuneração variável':      ['remuneracao variavel', 'bonificac', 'premiac'],
    'Programa de treinamentos':              ['treinamento', 'capacitacao'],
    'Refeitório':                            ['refeitorio'],
    'Restaurante interno':                   ['restaurante'],
    'Sala de Jogos':                         ['jogos'],
    'Seguro de vida':                        ['vida'],
    'Vale-alimentação':                      ['alimentacao'],
    'Vale-cultura':                          ['vale cultura', 'vale-cultura'],
    'Vale-refeição':                         ['refeicao', 'ticket'],
    'Vale-transporte':                       ['transporte'],
}

df_vagas['beneficios'] = df_vagas['descricao'].apply( lambda descricao: format_benefits_list(get_benefits_list(descricao)) )

## Skills

def get_skills_list(description: str) -> list[str] | None:
    '''
    Separa palavras que eventualmente podem estar juntas
    Na descrição, palavras podem estar juntas, por isso essa função separa palavras chave que possam estar unidas
    Ajuste de formatação dos dados
    '''
    try:
        # na gupy a descricao geralmente é dividida em 4 seções: 0 -> 'JOB DESCRIPTION';                 1 -> 'RESPONSIBILITIES AND ASSIGNMENTS';
        #                                                        2 -> 'REQUIREMENTS AND QUALIFICATIONS'; 3 -> 'ADDITIONAL INFORMATION'
        # a lista de beneficios geralmente esta contida na seção 'ADDITIONAL INFORMATION' (existem alguns casos que isso não é verdade)
        
        # divide a descricao em seções
        skills_sections = description.split('\n')
        
        # obtem o indice da seção 'ADDITIONAL INFORMATION' (geralmente é o terceiro indice mas existem paginas com menos seções)
        index_benefit = [ True if 'Requisitos e qualificações' in section else False for section in skills_sections ].index( True )

        # seleciona a seção 'ADDITIONAL INFORMATION'
        skills_str = skills_sections[index_benefit]

        # substitui multiplos espaços em sequência por apenas um
        skills_str = re.sub(r'\s+', ' ', skills_str)

        # adiciona um ponto-virgula ou ')' onde uma letra maiuscula é antecida por uma minuscula, precisamos dessa condição porque
        # em muitos casos não existe um caracter utilizado para deixar clara separação entre os benefícios dentro da string; nessa
        # situação, os beneficios estarão colados uns aos outros e a unica forma de diferenciá-los são os caracteres maiusculos.
        skills_str = re.sub(r'(?<=[a-z]|\))([A-Z])', r';\1', skills_str)  # Exemplo:  Gympass(ilimitado)Vale-TransporteConvenio
                                                                            #        -> Gympass(ilimitado);Vale-Transporte;Convenio
        
        # cria uma lista com substrings contendo uma letra maiúscula precedida e antecedida por um entre: ':', ';', '.', '•', '*'
        # esses simbolos geralmente antecedem / procedem os elementos da lista de beneficios dentro da string.
        skills_list = re.findall(r'(?:(?<=[\:\;\.\•\*]).*?[A-Z].*?(?=[\.\;\•\*\)]))', skills_str, flags=re.I)   # Exemplos: '* Gympass;' -> 'Gympass'
                                                                                                                #             '• PLR.'     -> 'PLR'
        
        # remove espaços vazios no final e inicio de cada elemento da lista
        skills_list = list( map( lambda skill: skill.strip(), skills_list ) )

        return skills_list
    
    except:
        return None
    
def replace_specifics_substrings(benefits_str: str) -> str:

    va_vr_matches = re.findall(r'V[R|A]\b', benefits_str)

    va_vr_map = zip(['Vale refeição', 'Vale alimentação'], ['VR', 'VA'])

    for va_vr_full, va_vr_short in va_vr_map:

        if va_vr_short in va_vr_matches:
            benefits_str = benefits_str.replace(va_vr_short, va_vr_full)

    return benefits_str

def format_skills_list(skills_list: list[str], skills_map: dict[str, list]) -> list[str] | None:

    '''
    Verifica o match entre a lista de skills e as palavras chave
    '''

    try:
        skills_list_formatted = []

        # junta os beneficios em uma string separada por vírgula e espaço
        skills_str = ', '.join(skills_list)

        # # substitui as substrings 'VA' / 'VR' por 'Vale alimentação' / 'Vale refeição'
        skills_str = replace_specifics_substrings(skills_str)

        # remove acentos e deixa a string em lowercase
        skills_str = unidecode(skills_str).lower()

        for skills_key, skills_matches in skills_map.items():

            # verifica se o beneficio está presente dentro da string
            match_look = any( True if skill_word in skills_str else False for skill_word in skills_matches )

            if match_look:
                skills_list_formatted.append(skills_key)
            else:
                continue
        
        # se nenhum match é encontrado retona 'None' ao invés de uma lista vazia
        if len(skills_list_formatted) == 0:
            return None

        return skills_list_formatted
    
    except:
        return None

def build_skills_map(data, macro:bool = False):
    dict_micro_tema = {}
    dict_macro_tema = {}

    for index, row in data[['micro','palavras_chave']].iterrows():
        dict_micro_tema[row['micro']] = row['palavras_chave'].split(', ')

    if macro:
        df_macro_temas = data[['macro','micro']].groupby('macro').agg(palavras_chave = ('micro',lambda x: ', '.join(x.str.lower()))).reset_index()
        for index, row in df_macro_temas.iterrows():
            dict_macro_tema[row['macro']] = row['palavras_chave'].split(', ')
        return dict_macro_tema, dict_micro_tema
    else:
        return dict_micro_tema

dict_skills = pd.read_excel('../dicionario-skills.xlsx', sheet_name='Habilidades')

skills_map_macro, skills_map_micro = build_skills_map(dict_skills, macro=True)

# skills_map = {
#     'Analytics':          ['kpi', 'metricas', 'indicadores', 'analise de dados'],
#     'Banco de dados':     ['bancos de dados', 'banco de dados', 'relacion'],
#     'Big data':           ['big data'],
#     'Clickview':          ['clickview'],
#     'Cloud':              ['azure', 'aws', 'gcp', 'nuvem', 'cloud'],
#     'Databricks':         ['databricks'],
#     'Data Mining':        ['mining'],
#     'Data Warehouse':     ['warehouse', 'datawarehouse'],
#     'Dataviz':            ['dashboard', 'relatorio'],
#     'Docker':             ['docker', 'container'],
#     'ETL':                ['etl'],
#     'Estatística':        ['estatistica'],
#     'Excel':              ['excel'],
#     'Git':                ['git', 'versionamento'],
#     'Java':               ['java'],
#     'Linguagem R':        [' r ', ' r,'],
#     'Linux':              ['linux'],
#     'Machine Learning':   ['machine'],
#     'Matlab':             ['matlab'],
#     'Modelagem de dados': ['modelagem', 'modelos de dados'],
#     'MongoDB':            ['mongodb'],
#     'MySQL':              ['mysql'],
#     'NoSQL':              ['no sql'],
#     'Oracle':             ['oracle'],
#     'Pacote Office':      ['pacote office', 'office'],
#     'PostgreSQL':         ['postgres'],
#     'Power BI':           ['power bi', 'pbi', 'powerbi', 'dax'],
#     'Pós-graduação':      ['pos-graduacao', 'mestrado', 'doutorado'],
#     'Python':             ['python', 'phython'],
#     'Scala':              [' scala'],
#     'Spark':              ['spark'],
#     'SQL':                ['sql'],
#     'Storytelling':       ['storytelling'],
#     'Tableau':            ['tableau'],
# }

# df_vagas['skills_micro'] = df_vagas['descricao'].apply(lambda descricao: format_skills_list(get_skills_list(descricao), skills_map_micro))
# df_vagas['skills_macro'] = df_vagas['descricao'].apply(lambda descricao: format_skills_list(get_skills_list(descricao), skills_map_macro))

## Contrato
df_vagas['contrato'] = df_vagas['contrato'].apply(lambda x: 'Autônomo' if x == 'Pessoa Jurídica' else x )

## Regime
df_vagas['regime'] = df_vagas['contrato'].apply(lambda x: 'PJ' if x == 'Autônono' else 'CLT')

# Save Dataframe

columns_selected = [
            'site_da_vaga',
            'link_site',
            'link_origem',
            'data_publicacao',
            'data_expiracao',
            'data_coleta',
            'posicao',
            'titulo_da_vaga',
            'senioridade',
            'cidade',
            'estado',
            'modalidade',
            'nome_empresa',
            'contrato',
            'regime',
            'pcd',
            'beneficios',
            # 'skills_macro',
            # 'skills_micro',
            'codigo_vaga',
            'descricao'
]

df_vagas[columns_selected].to_excel('../data/data_clean/vagas_gupy_clean.xlsx', index=False)

print(df_vagas.shape)
