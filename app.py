# sid_app/app.py
import streamlit as st
from modules.clientes import tela_clientes
from modules.veiculos import tela_veiculos
from modules.manutencoes import tela_manutencoes

st.set_page_config(page_title="SID - Sistema de Manutenção", layout="wide")
st.title("🚗 SID - Sistema de Manutenção de Veículos")

menu = st.sidebar.selectbox("Menu", [
    "Cadastro de Clientes",
    "Cadastro de Veículos",
    "Cadastro de Manutenções"
])

if menu == "Cadastro de Clientes":
    tela_clientes()
elif menu == "Cadastro de Veículos":
    tela_veiculos()
elif menu == "Cadastro de Manutenções":
    tela_manutencoes()
