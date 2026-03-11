import re
import folium
import branca
import numpy as np
import pandas as pd
import streamlit as st
import geopandas as gpd
import plotly.express as px

from PIL import Image
from streamlit_folium import folium_static

import warnings

st.set_page_config(page_title='Localidade', page_icon='📍', layout='wide')


# =====================================================================================
# Helper functions
# =====================================================================================

def adjust_states_names(state_name: str) -> str:

    # adiciona espaço onde há letras maiusculas
    state_name = re.sub(r'(?<=\w)([A-Z])', r' \1', state_name)  # 'RioGrandedoSul' -> 'Rio Grandedo Sul'

    # adiciona espaço se as substring 'do'/'de' estão no final de uma palavra ( seguidas por espaço )
    state_name = re.sub(r'(d[oe])(?=\s)', r' \1', state_name)   # 'Rio Grandedo Sul' -> 'Rio Grande do Sul'

    return state_name


def get_geographical_data(data: pd.DataFrame, region: str) -> gpd.GeoDataFrame:

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


    df_map = df_map[ df_map['uf'].isin(country_regions.get(region)) ]

    df_map['percentage'] = round( 100 * df_map['vagas'] / df_map['vagas'].sum(), 2 )

    return df_map


def plot_brazil_map(data_map: gpd.GeoDataFrame) -> None:

    # ignora aviso sobre possíveis erros de projeção
    warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")

    centroid_region = data_map['geometry'].centroid

    # reativa os avisos após o bloco acima
    warnings.filterwarnings("default", message="Geometry is in a geographic CRS")

    x_coords = [point.x for point in centroid_region]
    y_coords = [point.y for point in centroid_region]

    mean_long = np.mean(x_coords)
    mean_lat  = np.mean(y_coords)

    colormap = branca.colormap.LinearColormap(
                    vmin=data_map['percentage'].quantile(0.0),
                    vmax=data_map['percentage'].quantile(1),
                    colors=["red", "orange", "green", "darkgreen", "darkblue"],
                    caption="Porcentagem de vagas no estado (%)",
                )
    
    m = folium.Map([mean_lat, mean_long], zoom_start=5)

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

    folium_static(m, width=500, height=500)

    return None


def plot_sunburst(data: pd.DataFrame, region: str) -> None:
    df_sunburst = data[ data['estado'].isin(country_regions.get(region)) ]
    df_sunburst.loc[:, 'posicao'] = df_sunburst.loc[:, 'posicao'].apply(lambda x: x.split(' ')[0])

    fig = px.sunburst(df_sunburst, path=['estado', 'posicao'], height=550)
    st.plotly_chart(fig, use_container_width=True)

    return None


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


st.markdown('# Localidades')


country_regions = {
        'Norte':        ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
        'Nordeste':     ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'Centro-oeste': ['DF', 'GO', 'MS', 'MT'],
        'Sudeste':      ['ES', 'MG', 'RJ', 'SP'],
        'Sul':          ['PR', 'RS', 'SC']
    }

cols = st.columns([5, 5])

with cols[0]:
    region = st.radio(
        label='#### Selecione a região do Brasil', 
        options=['Norte', 'Nordeste', 'Centro-oeste', 'Sudeste', 'Sul'],
        index=3,
        horizontal=True
    )
    df_map = get_geographical_data(df_raw, region)

    plot_brazil_map(df_map)


with cols[1]:
    
    st.markdown('#### Distribuição de vagas nos estado da região')

    plot_sunburst(df_raw, region)
