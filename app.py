# sid_app/app.py
import streamlit as st
from modules.clientes import tela_clientes, tela_busca_edicao_clientes
from modules.veiculos import tela_veiculos, cadastro_veiculo  # Importa a nova função de cadastro
from modules.manutencoes import tela_manutencoes

# Configuração inicial da página
st.set_page_config(page_title="SID - Sistema de Manutenção", layout="wide")
st.title("🚗 SID - Sistema de Manutenção de Veículos")

# Menu lateral
menu = st.sidebar.selectbox("Menu", [
    "Cadastro de Clientes",
    "Buscar/Editar Clientes",
    "Consulta de Veículos",
    "Cadastrar Novo Veículo",  # Nova opção para cadastro de veículos
    "Cadastro de Manutenções"
])

# Roteamento do menu
if menu == "Cadastro de Clientes":
    tela_clientes()
elif menu == "Buscar/Editar Clientes":
    tela_busca_edicao_clientes()
elif menu == "Consulta de Veículos":
    tela_veiculos()  # Tela para consulta e edição de veículos existentes
elif menu == "Cadastrar Novo Veículo":
    cadastro_veiculo()  # Tela dedicada ao cadastro de novos veículos
elif menu == "Cadastro de Manutenções":
    tela_manutencoes()
