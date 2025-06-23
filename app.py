# sid_app/app.py
import streamlit as st
from modules.clientes import tela_clientes, tela_busca_edicao_clientes
from modules.veiculos import tela_veiculos, tela_busca_edicao_veiculos
from modules.manutencoes import tela_manutencoes

st.set_page_config(page_title="SID - Sistema de Manutenção", layout="wide")
st.title("🚗 SID - Sistema de Manutenção de Veículos")

menu = st.sidebar.selectbox("Menu", [
    "Cadastro de Clientes",
    "Buscar/Editar Clientes",
    "Cadastro de Veículos",
    "Buscar/Editar Veículos",
    "Cadastro de Manutenções",
    "Consultar OS"
])

if menu == "Cadastro de Clientes":
    tela_clientes()
elif menu == "Buscar/Editar Clientes":
    tela_busca_edicao_clientes()
elif menu == "Cadastro de Veículos":
    tela_veiculos()
elif menu == "Buscar/Editar Veículos":
    tela_busca_edicao_veiculos()
elif menu == "Cadastro de Manutenções":
    tela_manutencoes()
elif menu == "Consultar OS":
    st.subheader("🔍 Consulta de Ordens de Serviço")
    st.info("Clique no botão abaixo para abrir a tela de consulta de OS em uma nova aba.")
    
    # 🔗 Altere esta URL para a real do seu app quando publicado
    url_consulta = "https://seu-app.streamlit.app/consultar_os"
    
    st.markdown(f"""
        <a href="{url_consulta}" target="_blank">
            <button style='padding:10px 20px; font-size:16px;'>Abrir Consulta de OS 🔎</button>
        </a>
    """, unsafe_allow_html=True)
