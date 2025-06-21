import streamlit as st
import requests
from datetime import datetime
import unicodedata
import re
import base64

# === CONFIGURAÇÕES DO JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === FUNÇÕES AUXILIARES ===
def corrige_abnt(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    texto = ' '.join(word.capitalize() for word in texto.split())
    return texto

def buscar_endereco(cep):
    try:
        resposta = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        if resposta.status_code == 200:
            return resposta.json()
    except:
        return None
    return None

def criar_issue_jira(nome, cpf, empresa, telefone, email, cep, numero, complemento, endereco_formatado):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "summary": nome,
            "issuetype": {"name": "Clientes"},
            "customfield_10038": nome,
            "customfield_10040": cpf,
            "customfield_10051": empresa,
            "customfield_10041": telefone,
            "customfield_10042": email,
            "customfield_10133": cep,
            "customfield_10039": "",
            "customfield_10044": complemento,
            "customfield_10139": numero,
            "description": endereco_formatado
        }
    }

    response = requests.post(f"{JIRA_URL}/rest/api/2/issue", json=payload, headers=JIRA_HEADERS)
    if response.status_code == 201:
        return response.json().get("key")
    else:
        st.error(f"Erro ao criar cliente: {response.text}")
        return None

def anexar_foto(issue_key, imagem):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    headers = {
        "Authorization": JIRA_HEADERS["Authorization"],
        "X-Atlassian-Token": "no-check"
    }
    files = {"file": (imagem.name, imagem.getvalue())}
    response = requests.post(url, headers=headers, files=files)
    return response.status_code == 200

# === TELA DE CLIENTES ===
def tela_clientes():
    st.header("👤 Cadastro de Clientes")

    with st.form("form_cliente"):
        nome = st.text_input("Nome do Cliente:")
        cpf = st.text_input("CPF/CNPJ:")
        empresa = st.text_input("Empresa:")
        telefone = st.text_input("Telefone:")
        email = st.text_input("E-mail:")
        cep = st.text_input("CEP:")
        numero = st.text_input("Nº")
        complemento = st.text_input("Complemento")
        imagem = st.file_uploader("Foto do cliente:", type=["png", "jpg", "jpeg"])

        buscar = st.form_submit_button("🔍 Buscar Endereço")

        endereco_formatado = ""
        endereco_obj = None

        if buscar and cep:
            endereco_obj = buscar_endereco(cep)
            if endereco_obj:
                endereco_formatado = f"{endereco_obj['logradouro']} - {endereco_obj['bairro']} - {endereco_obj['localidade']}/{endereco_obj['uf']}, nº {numero}"
                st.success(f"Endereço encontrado: {endereco_formatado}")
            else:
                st.error("CEP não encontrado")

        confirmar = st.form_submit_button("✅ Confirmar cadastro")

        if confirmar:
            nome_abnt = corrige_abnt(nome)
            empresa_abnt = corrige_abnt(empresa)
            endereco_formatado = endereco_formatado or f"CEP: {cep}, Nº: {numero}, Compl: {complemento}"

            st.markdown("""
            ### 📄 Resumo do cadastro gerado
            **Nome:** {0}  
            **CPF/CNPJ:** {1}  
            **Empresa:** {2}  
            **Telefone:** {3}  
            **E-mail:** {4}  
            **Endereço:** {5}  
            """.format(nome_abnt, cpf, empresa_abnt, telefone, email, endereco_formatado))

            if imagem:
                st.image(imagem, width=160, caption="Foto selecionada")

            enviar = st.form_submit_button("🚀 Enviar para o Jira")

            if enviar:
                issue_key = criar_issue_jira(nome_abnt, cpf, empresa_abnt, telefone, email, cep, numero, complemento, endereco_formatado)
                if issue_key and imagem:
                    anexar_foto(issue_key, imagem)
                if issue_key:
                    st.success(f"Cliente criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")

