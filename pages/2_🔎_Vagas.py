import pandas    as pd
import streamlit as st
from PIL import Image

st.set_page_config(page_title='Vagas', page_icon='🔎', layout='wide')


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

data = pd.read_excel('data/data_refined/vagas_full.xlsx')

st.markdown('# Vagas')

senioridade_option = st.multiselect(label = 'Senioridade',options = data['senioridade'].unique())
cidade_option = st.multiselect(label = 'Cidade', options = data['cidade'].unique())
estado_option = st.multiselect(label = 'Estado', options = data['estado'].unique())
modalidade_option = st.multiselect(label = 'Modalidade', options = data['modalidade'].unique())
contrato_option = st.multiselect(label = 'Contrato', options = data['contrato'].unique())


dict_filter = {
        'senioridade': senioridade_option,
        'modalidade': modalidade_option,
        'contrato': contrato_option,
        'cidade': cidade_option,
        'estado': estado_option
    }

for column_name, selected_option in dict_filter.items():
    if selected_option:
        data = data.loc[data[column_name] == selected_option[0]]


st.dataframe(data, height=500)

