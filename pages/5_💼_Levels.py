import streamlit as st
import pandas as pd

data = pd.read_excel('data/data_refined/vagas_full.xlsx')


st.markdown('# Levels')

df_seniority = ( data[['senioridade', 'link_site']]
                    .groupby('senioridade').count()
                    .reset_index()
                    .sort_values('link_site', ascending=False)
                    .rename(columns={'link_site': 'count'}) 
            )

st.bar_chart(data = df_seniority, x = 'senioridade', y = 'count')