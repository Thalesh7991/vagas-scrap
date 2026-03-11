import re
import folium
import branca
import pandas         as pd
import streamlit      as st
import geopandas      as gpd
import plotly.express as px

from PIL              import Image
from streamlit_folium import folium_static


st.set_page_config(page_title='Overview', page_icon='📊', layout='wide')


# =====================================================================================
# Helper functions
# =====================================================================================

def get_job_count_position(data: pd.DataFrame, position: str) -> int:

    if position in data['posicao'].unique():
        job_count = data.query('posicao == @position').shape[0]

        return job_count
    
    job_count = data.shape[0]

    return job_count


def platform_job_position_count(data: pd.DataFrame, platform: str) -> pd.DataFrame:
    df_platform = data.query('site_da_vaga == @platform')

    df_platform = ( df_platform[['posicao', 'site_da_vaga']]
                        .groupby('posicao')
                        .count()
                        .reset_index()
                        .rename(columns={'site_da_vaga': 'vagas'}) 
                    )
    return df_platform
    

def plot_bar_graph(data: pd.DataFrame, x: str, y: str, title: str, vertical: bool=False) -> None:

    if vertical:

        fig = px.bar( data, x=x, y=y, title=title, orientation='h', color=x)
        #fig.update_layout(coloraxis_showscale=False)
        fig.update_coloraxes(showscale=False)

    else:
        fig = px.bar( data, x=x, y=y, title=title)

    st.plotly_chart(fig, use_container_width=True)
    
    return None


def adjust_states_names(state_name: str) -> str:

    # adiciona espaço onde há letras maiusculas
    state_name = re.sub(r'(?<=\w)([A-Z])', r' \1', state_name)  # 'RioGrandedoSul' -> 'Rio Grandedo Sul'

    # adiciona espaço se as substring 'do'/'de' estão no final de uma palavra ( seguidas por espaço )
    state_name = re.sub(r'(d[oe])(?=\s)', r' \1', state_name)   # 'Rio Grandedo Sul' -> 'Rio Grande do Sul'

    return state_name


def get_geographical_data(data: pd.DataFrame) -> pd.DataFrame:

    geodata = gpd.read_file('data/data_raw/tmp/data_json/geo_data_brazil.json')

    geodata = geodata[['NAME_1', 'geometry']].rename(columns={'NAME_1': 'geo_state'})

    df_state = ( data[['estado', 'site_da_vaga']]
                        .groupby('estado')
                        .count()
                        .reset_index()
                        .rename(columns={'site_da_vaga': 'vagas'})
            )
    
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
    
    geodata['geo_state'] = geodata['geo_state'].apply(lambda state: adjust_states_names(state))

    geodata['uf'] = geodata['geo_state'].map( state_uf )


    df_map = pd.merge(left=geodata, right=df_state, how='left', left_on='uf', right_on='estado')

    df_map['percentage'] = 100 * df_map['vagas'] / df_map['vagas'].sum()

    return df_map


def plot_brazil_map(data_map: pd.DataFrame) -> None:

    colormap = branca.colormap.LinearColormap(
                    vmin=data_map['percentage'].quantile(0.0),
                    vmax=data_map['percentage'].quantile(1),
                    colors=["red", "orange", "lightblue", "green", "darkgreen"],
                    caption="Porcentagem de vagas no estado (%)",
                )
    
    m = folium.Map([-15, -50], zoom_start=4)

    popup = folium.GeoJsonPopup(
                    fields=['geo_state', 'vagas', 'percentage'],
                    aliases=['Estado', 'Vagas', 'Porcentagem (%)'],
                    localize=True,
                    labels=True,
                    style='background-color: yellow',
                )

    tooltip = folium.GeoJsonTooltip(
                    fields=['geo_state', 'vagas', 'percentage'],
                    aliases=['State:', 'Vagas:', 'Porcentagem (%):'],
                    localize=True,
                    sticky=False,
                    labels=True,
                    style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                    """,
                    max_width=800,
                )

    g = folium.GeoJson(
                    data=data_map,
                    style_function=lambda x:{
                        'fillColor': colormap(x['properties']['percentage'])
                        if x['properties']['percentage'] is not None
                        else 'transparent',
                        'color': 'black',
                        'fillOpacity': 0.4,
                    },
                    popup=popup,
                    tooltip=tooltip,
            ).add_to(m)

    colormap.add_to(m)

    folium_static(m, width=900, height=500)

    return None


def get_skills_list(data: pd.DataFrame) -> list:
    unique_skills = set()

    for _, row in data.iterrows():
        
        try:
            skills_list = re.findall(r'\'(.*?)\'', row['skills'])
            
            unique_skills.update(skills_list)
        except:
            continue

    return list( unique_skills )


def get_skills_dataframe(data: pd.DataFrame) -> pd.DataFrame:

    skills_list = get_skills_list(data)
    skills_list.sort()

    data_list = []

    for _, row in data.iterrows():
        row_skills = []

        try:
            for skill in skills_list:
                if skill in row['skills']:
                    row_skills.append(True)
                else:
                    row_skills.append(False)
        except:
            pass
        
        data_list.append(row_skills)


    skills_df = pd.DataFrame(data=data_list, columns=skills_list)


    skills_df = ( skills_df
                    .sum()
                    .sort_values(ascending=False)
                    .reset_index(name='count')
                    .rename(columns={'index': 'skill'})
                )


    return skills_df



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


df_raw = pd.read_excel('data/data_refined/vagas_full.xlsx')


st.markdown('# Overview')

# --------------------------- Sessão Métricas ------------------------

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric('Analista',   get_job_count_position(df_raw, 'Analista de dados'),   'X novas vagas')
metric2.metric('Cientista',  get_job_count_position(df_raw, 'Cientista de dados'),  'X novas vagas')
metric3.metric('Engenheiro', get_job_count_position(df_raw, 'Engenheiro de dados'), 'X novas vagas')
metric4.metric('Total',      get_job_count_position(df_raw, 'Total'),               'X novas vagas')


# ----------------- Distribuição vagas por plataforma ------------------------

glassdor_tab, gupy_tab, vagascom_tab = st.tabs(['Glassdoor', 'Gupy', 'Vagas.com'])

with glassdor_tab:

    cols = st.columns([3, 7])
    with cols[0]:
        st.markdown('#')
        st.markdown('## Plataforma')
        st.image('img/glassdoor_logo.png', width=200)

        df_platform = platform_job_position_count(df_raw, 'Glassdoor')
        st.dataframe(df_platform)

    with cols[1]:
        plot_bar_graph(df_platform, x='posicao', y='vagas', title='Vagas por posição')
        

with gupy_tab:
    cols = st.columns([3, 7])
    with cols[0]:
        st.markdown('#')
        st.markdown('## Plataforma')
        st.image('img/gupy_logo.png', width=200)

        df_platform = platform_job_position_count(df_raw, 'Gupy')
        st.dataframe(df_platform)
        
    with cols[1]:
        plot_bar_graph(df_platform, x='posicao', y='vagas', title='Vagas por posição')
        

with vagascom_tab:
    cols = st.columns([3, 7])

    with cols[0]:
        st.markdown('#')
        st.markdown('## Plataforma')
        st.image('img/vagas_logo.png', width=200)

        df_platform = platform_job_position_count(df_raw, 'Vagas.com')
        st.dataframe(df_platform)

    with cols[1]:
        plot_bar_graph(df_platform, x='posicao', y='vagas', title='Vagas por posição')
        

# --------------------------- Mapa do Brasil ------------------------

st.markdown('#')
st.markdown('# Visão Geral Brasil')

df_map = get_geographical_data(df_raw)

plot_brazil_map(df_map)


# --------------------------- Sessão Skills ------------------------

st.markdown('#')
st.markdown('# Skills')

cols = st.columns([1, 10])

with cols[0]:
    st.markdown(4*'<br>', unsafe_allow_html=True)
    top_skills = st.radio(label='**Data Skills**', options=['top 15', 'top 20', 'top 25', 'todas'])

with cols[1]:

    skills_df = get_skills_dataframe(df_raw)

    try:
        top = int( re.findall(r'\d+', top_skills)[0] )
        skills_df = skills_df.loc[:top]

    except:
        pass
    
    skills_df['count'] = skills_df['count'].astype(float)
    skills_df = skills_df.sort_values('count', ascending=True)

    plot_bar_graph(skills_df, x='count', y='skill', title='Most common skills', vertical=True)
