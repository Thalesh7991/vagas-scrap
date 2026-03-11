import streamlit as st
import pandas as pd
from PIL import Image


st.set_page_config(page_title='Welcome', page_icon='👋', layout='wide')


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

with st.container():
    
    cols = st.columns([10, 1, 4])
    
    with cols[0]:
 
        st.markdown('### Bem-vindo ao dashboard de monitoramento de vagas')
        st.markdown('#### Aqui você encontra oportunidades na área de dados')

        st.write("""

            Nosso objetivo é simplificar o processo de busca de emprego, fornecendo a você uma plataforma intuitiva e eficiente para explorar 
            oportunidades de carreira em todo o país. Se você estiver procurando por uma oportunidade na área de dados, nosso dashboard está aqui 
            para ajudá-lo a encontrar a oportunidade certa para você.

            Explore, filtre e descubra novas oportunidades de carreira com nosso dashboard.
            
            Estamos aqui para ajudá-lo a dar o próximo passo em sua jornada profissional.

        """)

    with cols[1]:
        st.empty()  # adiciona espaço entre a descricao e a imagem

    with cols[2]:
        st.markdown(3*'<br>', unsafe_allow_html=True)  # <br><br><br> pula de linha 3 vezes

        image = Image.open('img/job-search.jpg')
        st.image(image)


st.markdown('#')
st.markdown('#### Coletamos dados nas seguintes plataformas:')

with st.container():
    
    cols = st.columns(3, gap='large')

    with cols[0]:
        st.image('img/glassdoor_logo.png', width=200)

    with cols[1]:
        st.image('img/gupy_logo.png', width=200)
    
    with cols[2]:
        st.image('img/vagas_logo.png', width=200)