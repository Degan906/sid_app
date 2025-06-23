import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

from modules.clientes import tela_clientes, tela_busca_edicao_clientes
from modules.veiculos import tela_veiculos, tela_busca_edicao_veiculos
from modules.manutencoes import tela_manutencoes, tela_consulta_os

st.set_page_config(page_title="SID - Sistema de Manutenção", layout="wide")
st.title("🚗 SID - Sistema de Manutenção de Veículos")

# --- Inicialização do Firebase ---
def initialize_firebase():
    try:
        if "firebase_credentials" in st.secrets:
            creds_dict = st.secrets["firebase_credentials"]
        else:
            st.error("Credenciais do Firebase não encontradas nos segredos do Streamlit. Carregue seu arquivo serviceAccount.json.")
            st.stop()

        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
        st.session_state.firebase_initialized = True
        return firestore.client()

    except ValueError as e:
        if "The default Firebase app already exists" not in str(e):
            st.error(f"Erro ao inicializar o Firebase: {e}")
            st.stop()
        return firestore.client()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado na inicialização do Firebase: {e}")
        st.stop()

# --- Lógica Principal do App ---
# Inicializa o Firebase e o armazena no estado da sessão
if 'firebase_initialized' not in st.session_state:
    st.session_state.db = initialize_firebase()

# --- Menu de Navegação ---
menu = st.sidebar.selectbox("Menu", [
    "Cadastro de Clientes",
    "Buscar/Editar Clientes",
    "Cadastro de Veículos",
    "Buscar/Editar Veículos",
    "Cadastro de Manutenções",
    "Consultar OS"
])

# --- Roteamento de Página ---
if menu == "Cadastro de Clientes":
    tela_clientes()
elif menu == "Buscar/Editar Clientes":
    tela_busca_edicao_clientes()
elif menu == "Cadastro de Veículos":
    tela_veiculos()
elif menu == "Buscar/Editar Veículos":
    tela_busca_edicao_veiculos()
elif menu == "Cadastro de Manutenções":
    # Quando a opção "Cadastro de Manutenções" é selecionada, 
    # garantimos que não há OS selecionada para entrar no modo de criação.
    if 'os_id_selecionada' in st.session_state:
        del st.session_state.os_id_selecionada
    if 'loaded_os_id' in st.session_state:
        del st.session_state.loaded_os_id
    tela_manutencoes()
elif menu == "Consultar OS":
    # Quando a opção "Consultar OS" é selecionada, 
    # garantimos que não há OS selecionada para exibir a tabela completa.
    if 'os_id_selecionada' in st.session_state:
        del st.session_state.os_id_selecionada
    if 'loaded_os_id' in st.session_state:
        del st.session_state.loaded_os_id
    tela_consulta_os()

