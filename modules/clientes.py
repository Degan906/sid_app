import streamlit as st
import requests
import base64
import json
import unicodedata
import re

# === CONFIG JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === CAMPOS PERSONALIZADOS ===
CAMPOS_JIRA = {
    "nome": "customfield_10038",
    "cpf_cnpj": "customfield_10040",
    "empresa": "customfield_10051",
    "contato": "customfield_10041",
    "email": "customfield_10042",
    "cep": "customfield_10133",
    "complemento": "customfield_10044",
    "numero": "customfield_10139"
}

# === FUNÇÕES ===
def corrige_abnt(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    return ' '.join(word.capitalize() for word in texto.split())

def buscar_cep(cep):
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        if resp.status_code == 200:
            return resp.json()
    except:
        return None
    return None

def cadastrar_cliente(payload):
    response = requests.post(
        f"{JIRA_URL}/rest/api/2/issue",
        headers=JIRA_HEADERS,
        json=payload
    )
    if response.status_code == 201:
        return response.json().get("key")
    else:
        return None

# === INTERFACE ===
def tela_clientes():
    st.markdown("""
        <h3 style='display: flex; align-items: center;'>
            <span style="font-size: 1.6em; margin-right: 0.3em;">👤</span> Cadastro de Clientes
        </h3>
    """, unsafe_allow_html=True)

    with st.form(key="form_cliente"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome do Cliente *")
            cpf_cnpj = st.text_input("CPF ou CNPJ *")
            telefone = st.text_input("Telefone *", placeholder="(00) 00000-0000")
            email = st.text_input("E-mail *")
            empresa = st.text_input("Empresa")

        with col2:
            cep = st.text_input("CEP *")
            numero = st.text_input("Número")
            complemento = st.text_input("Complemento")
            foto = st.file_uploader("Foto do cliente", type=["jpg", "jpeg", "png"])

        confirmar = st.form_submit_button("✅ Confirmar dados")

    if confirmar:
        erros = []
        if not nome: erros.append("Nome")
        if not cpf_cnpj: erros.append("CPF/CNPJ")
        if not telefone: erros.append("Telefone")
        if not email: erros.append("E-mail")
        if not cep: erros.append("CEP")

        if erros:
            st.error("Preencha os campos obrigatórios: " + ", ".join(erros))
            return

        cep_limpo = re.sub(r'\D', '', cep)
        endereco = buscar_cep(cep_limpo) if len(cep_limpo) == 8 else None

        if endereco:
            endereco_str = f"{endereco.get('logradouro', '')} - {endereco.get('bairro', '')} - {endereco.get('localidade', '')}/{endereco.get('uf', '')}, nº {numero}"
        else:
            endereco_str = "Não encontrado"

        st.markdown("""
        <div style="border:1px solid #ccc; padding:1em; border-radius:10px;">
        <h4>📋 Confirme os dados abaixo</h4>
        <b>Nome:</b> {0}  
        <b>CPF/CNPJ:</b> {1}  
        <b>Empresa:</b> {2}  
        <b>Telefone:</b> {3}  
        <b>E-mail:</b> <a href='mailto:{4}'>{4}</a>  
        <b>Endereço:</b> {5}
        </div>
        """.format(nome, cpf_cnpj, empresa, telefone, email, endereco_str), unsafe_allow_html=True)

        if st.button("🚀 Deseja realmente cadastrar este cliente?"):
            payload = {
                "fields": {
                    "project": {"key": "MECANICA"},
                    "summary": nome,
                    "issuetype": {"name": "Clientes"},
                    CAMPOS_JIRA["nome"]: nome,
                    CAMPOS_JIRA["cpf_cnpj"]: cpf_cnpj,
                    CAMPOS_JIRA["empresa"]: empresa,
                    CAMPOS_JIRA["contato"]: telefone,
                    CAMPOS_JIRA["email"]: email,
                    CAMPOS_JIRA["cep"]: cep,
                    CAMPOS_JIRA["complemento"]: complemento,
                    CAMPOS_JIRA["numero"]: numero
                }
            }
            issue_key = cadastrar_cliente(payload)

            if issue_key:
                st.success(f"✅ Cliente criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
            else:
                st.error("Erro ao criar cliente. Verifique os dados e tente novamente.")
