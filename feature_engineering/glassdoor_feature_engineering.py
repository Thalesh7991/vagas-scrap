import re
import numpy as np
import pandas as pd

from unidecode import unidecode


def get_senioridade(df: pd.DataFrame) -> pd.DataFrame:

    df['senioridade'] = df['senioridade'].astype(str)

    mapa_senioridade = {
        'Júnior': ['Júnior', 'Junior', 'Jr', 'Estágio', 'Estagiário', 'Trainee', 'trainne'],
        'Pleno':  ['Pleno', 'Plena', 'Pl', 'Jr/Pl'],
        'Sênior': ['Sênior', 'Senior', 'Sr', 'Pl/Sr', 'Tech Lead', 'Líder']
    }

    for index, row in df.iterrows():
        for senioridade, termos in mapa_senioridade.items():
            for termo in termos:
                if re.search(r'\b' + termo + r'\b', row['titulo_da_vaga'], flags=re.IGNORECASE) or \
                   re.search(r'\b' + termo + r'\b', row['descricao'], flags=re.IGNORECASE):
                        df.loc[index, 'senioridade'] = senioridade

    return df


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
    'Vale-cultura':                          ['vale cultura', 'vale-cultura'],
    'Vale-refeição/alimentação':             ['refeicao', 'alimentacao','ticket', 'caju', 'alelo', 'flash'],
    'Vale-transporte':                       ['transporte'],
}

def format_benefits_list(description: str) -> list[str] | None:
    """Extrai e padroniza os benefícios a partir da descrição da vaga.

    Args:
        description (str): Descrição da vaga.

    Returns:
        list[str] | None: Lista com os benefícios padronizados, ou None se não forem encontrados.

    Exemplos:
    ---
    >>> format_benefits_list('Oferecemos vale-alimentação e plano de saúde.')
    ['Vale-alimentação', 'Plano de saúde']
    """

    try:
        # Inicializa uma lista para armazenar os benefícios extraídos
        extracted_benefits = []

        # Converte toda a descrição para minúsculas para facilitar a correspondência
        description_lower = unidecode(description).lower()

        # Percorre o mapa de benefícios para verificar a presença de cada benefício na descrição
        for benefit, synonyms in benefit_map.items():
            # Verifica se algum sinônimo do benefício está presente na descrição
            if any(synonym in description_lower for synonym in synonyms):
                extracted_benefits.append(benefit)

        # Retorna a lista de benefícios extraídos, removendo duplicatas e mantendo a ordem original
        if extracted_benefits:
            return list(dict.fromkeys(extracted_benefits))
        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


skills_map = {

    'Analytics':          ['Analytics', 'Data analysis skills'],
    'APIs':               ['APIs'],
    'Banco de dados':     ['Databases', 'Relational databases'],
    'Big data':           ['Big data'],
    'Cloud':              ['Azure', 'AWS', 'Google Cloud Platform'],
    'Dataviz':            ['Data visualization'],
    'Data mining':        ['Data mining'],
    'Deep Learning':      ['Deep learning', 'TensorFlow', 'Natural language processing'],
    'Docker':             ['Docker'],
    'Estatística':        ['Statistics', 'Statistical analysis'],
    'Excel':              ['Microsoft Excel'],
    'Git':                ['Git'],
    'Java':               ['Java'],
    'Linguagem R':        ['R'],
    'Machine Learning':   ['Machine learning', 'AI'],
    'Matlab':             ['MATLAB'],
    'Modelagem de dados': ['Data modeling'],
    'MongoDB':            ['MongoDB'],
    'MySQL':              ['MySQL'],
    'NoSQL':              ['NoSQL'],
    'Oracle':             ['Oracle'],
    'Pacote Office':      ['Microsoft Office'],
    'PostgreSQL':         ['PostgreSQL'],
    'Power BI':           ['Power BI'],
    'Python':             ['Python'],
    'Scala':              ['Scala'],
    'Spark':              ['Spark'],
    'SQL':                ['SQL'],
    'Tableau':            ['Tableau'],
    
}


def format_skills_list(skills_list: str):
    skills_list = re.findall(r'\'(.*?)\'', skills_list)

    formatted_skills = []

    for skill_name, match_words in skills_map.items():
        check_match = any( True if word in skills_list else False for word in match_words )

        if check_match:
            formatted_skills.append(skill_name)

    return formatted_skills


def search_job_modality(description: str) -> str:
    
    modality_search = {
        'Remoto':     ['remoto', 'home office', 'remota'],
        'Híbrido':    ['hibrido', 'hibrida'],
        'Presencial': ['presencial', 'escritorio', 'local de trabalho'],
    }

    description = unidecode(description).lower()

    for modality, search_words in modality_search.items():

        check_match = any( True if word in description else False for word in search_words )

        if check_match:
            return modality
        
    return 'Não informado'


def search_job_pcd(description: str) -> str:

    description = unidecode(description).lower()

    search_words = ['pcd', 'deficiente', 'deficiencia']

    check_match = any( True if word in description else False for word in search_words )

    if check_match:
        return 'Sim'
    
    return 'Não informado'



if __name__ == '__main__':

    df = pd.read_csv('data/data_raw/vagas_glassdoor_raw.csv')

    df = get_senioridade(df)


    df['regime'] = 'CLT'

    df['pcd'] = df['descricao'].apply(lambda description: search_job_pcd(description))

    df['skills'] = df['skills'].apply(lambda skills_list: format_skills_list(skills_list))

    df['beneficios'] = df['descricao'].apply(format_benefits_list)

    df['modalidade'] = df['descricao'].apply(lambda description: search_job_modality(description))

    df.loc[df['modalidade'] == 'Remoto', 'cidade'] = 'Não informado'
    df.loc[df['modalidade'] == 'Remoto', 'estado'] = 'Todo o Brasil'

    df['estado'] = df['estado'].replace('Distrito Federal', 'DF')



    df.rename(columns={'titulo_da_vaga': 'titulo_vaga'}, inplace=True)

    reordering_columns = [
            'site_da_vaga',
            'link_site',
            'link_origem',
            'data_publicacao',
            'data_expiracao',
            'data_coleta',
            'posicao',
            'titulo_vaga',
            'senioridade',
            'cidade',
            'estado',
            'modalidade',
            'nome_empresa',
            'contrato',
            'regime',
            'pcd',
            'beneficios',
            'skills',
            'codigo_vaga',
            'descricao'
    ]

    df[reordering_columns].to_excel('data/data_clean/vagas_glassdoor_clean.xlsx', index=False)