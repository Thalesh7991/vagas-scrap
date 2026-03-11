import re
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image


st.set_page_config(page_title='Beneficios', page_icon='⛑️', layout='wide')


# =====================================================================================
# Sidebar (Barra Lateral)
# =====================================================================================

st.sidebar.markdown('# Monitoramento de Vagas')
st.sidebar.markdown('### Aqui você não perde nada!')

cds_logo = Image.open('img/cds.png')
st.sidebar.image(cds_logo, width=150)

st.sidebar.markdown('''---''')

powered_cds_logo = Image.open('img/comunidade_ds_logo.png')
st.sidebar.image(powered_cds_logo, width=250)
st.sidebar.markdown('### Powered by Comunidade DS')


# =====================================================================================
# Layout streamlit
# =====================================================================================

def get_benefits_list(data: pd.DataFrame) -> set:
    unique_benefits = set()

    for _, row in data.iterrows():
        
        try:
            lista_beneficios = re.findall(r'\'(.*?)\'', row['beneficios'])
            
            unique_benefits.update(lista_beneficios)
        except:
            continue

    return unique_benefits


def get_benefits_dataframe(data: pd.DataFrame, benefits_list: list, columns: list) -> pd.DataFrame:
    data_list = []

    for _, row in data.iterrows():
        row_benefits = []

        try:
            for benefit in benefits_list:
                if benefit in row['beneficios']:
                    row_benefits.append(True)
                else:
                    row_benefits.append(False)
        except:
            pass

        row_benefits = [row['codigo_vaga'], row['site_da_vaga']] + row_benefits
        
        data_list.append(row_benefits)

    return pd.DataFrame(data=data_list, columns=columns)


def filter_benefits(data: pd.DataFrame, filter_list: list) -> pd.DataFrame:

    count_benefit_series = data.loc[:, filter_list].sum(axis=1)
    match_vaga_indices = count_benefit_series[ count_benefit_series.values == len(filter_list) ].index

    df_filtered = df_raw[ df_raw.index.isin( match_vaga_indices ) ]

    return df_filtered


def plot_bar_graph(data: pd.DataFrame, top_benefits: int) -> None:

    series_aux = ( data.drop(['codigo_vaga', 'site_da_vaga'], axis=1)
                    .sum()
                    .sort_values(ascending=False)
            )
    
    series_aux = series_aux.iloc[:top_benefits] 

    fig = px.bar(
            x=series_aux.index,
            y=series_aux.values,
            labels={'x': 'Benefícios', 'y': 'Número de Vagas'},
            title=f'Top {top_benefits} Beneficios por Vagas'
        )

    st.plotly_chart(fig, use_container_width=True)

    return None


st.markdown('# Benefícios')


df_raw = pd.read_excel('data/data_refined/vagas_full.xlsx')

benefits = list( get_benefits_list(df_raw) )
benefits.sort()

columns = ['codigo_vaga', 'site_da_vaga'] + benefits

df_benefits = get_benefits_dataframe(df_raw, benefits, columns)


selected_benefits = st.multiselect(
                            label='Selecione os benefícios da vaga buscada', 
                            options=benefits,
                            default=['Assistência médica', 'Vale-refeição', 'Auxílio academia']
                        )

df_filtered_benefits = filter_benefits(df_benefits, selected_benefits)


st.dataframe(df_filtered_benefits[['titulo_vaga', 'data_publicacao', 'senioridade', 'estado', 'modalidade', 'link_site']])



st.markdown('# Gráfico de Barras')

plot_bar_graph(df_benefits, 15)