# sid_app/app.py
import streamlit as st
from modules.clientes import tela_clientes, tela_busca_edicao_clientes
from modules.veiculos import tela_veiculos, tela_busca_edicao_veiculos
from modules.manutencoes import tela_manutencoes, tela_consulta_os  # ⬅️ IMPORTANTE

st.set_page_config(page_title="SID - Sistema de Manutenção", layout="wide")
st.title("🚗 SID - Sistema de Manutenção de Veículos")

# === MENU ===
menu = st.sidebar.selectbox("Menu", [
    "Cadastro de Clientes",
    "Buscar/Editar Clientes",
    "Cadastro de Veículos",
    "Buscar/Editar Veículos",
    "Cadastro de Manutenções",
    "Consultar OS"
])

# === ROTEAMENTO POR MENU ===
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
    tela_consulta_os()

# === REDIRECIONAMENTO PARA TELA DE OS ABERTA ===
if st.session_state.get("tela_atual") == "manutencoes":
    tela_manutencoes()
