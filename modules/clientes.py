# sid_app/modules/clientes.py
import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import re

# === CONFIG JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_API = f"{JIRA_URL}/rest/api/2"
PROJECT_KEY = "MC"
ISSUE_TYPE = "Clientes"
AUTH = HTTPBasicAuth("degan906@gmail.com", "glUQTNZG0V1uYnrRjp9yBB17")
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# === CAMPOS CUSTOMIZADOS ===
CAMPOS = {
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
def corrigir_nome_abnt(nome):
    nome = nome.strip().lower()
    return re.sub(r"\b(\w)", lambda m: m.group(1).upper(), nome)

def criar_cliente(data, foto=None):
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": data["nome"],
            "issuetype": {"name": ISSUE_TYPE},
            CAMPOS["nome"]: data["nome"],
            CAMPOS["cpf_cnpj"]: data["cpf_cnpj"],
            CAMPOS["empresa"]: data["empresa"],
            CAMPOS["contato"]: data["contato"],
            CAMPOS["email"]: data["email"],
            CAMPOS["cep"]: data["cep"],
            CAMPOS["complemento"]: data["complemento"],
            CAMPOS["numero"]: data["numero"]
        }
    }
    res = requests.post(f"{JIRA_API}/issue", json=payload, headers=HEADERS, auth=AUTH)
    if res.status_code == 201:
        key = res.json()["key"]
        if foto:
            files = {"file": (foto.name, foto.read(), foto.type)}
            headers = {"X-Atlassian-Token": "no-check"}
            upload_url = f"{JIRA_API}/issue/{key}/attachments"
            requests.post(upload_url, files=files, headers=headers, auth=AUTH)
        return True, key
    return False, res.text

def buscar_clientes():
    jql = f'project = {PROJECT_KEY} AND issuetype = "{ISSUE_TYPE}" ORDER BY created DESC'
    res = requests.get(f"{JIRA_API}/search?jql={jql}&maxResults=100", headers=HEADERS, auth=AUTH)
    if res.status_code == 200:
        issues = res.json()["issues"]
        lista = []
        for issue in issues:
            f = issue["fields"]
            lista.append({
                "Key": issue["key"],
                "Nome": f.get(CAMPOS["nome"], ""),
                "CPF/CNPJ": f.get(CAMPOS["cpf_cnpj"], ""),
                "Contato": f.get(CAMPOS["contato"], ""),
                "E-mail": f.get(CAMPOS["email"], ""),
                "Empresa": f.get(CAMPOS["empresa"], ""),
                "CEP": f.get(CAMPOS["cep"], ""),
                "Número": f.get(CAMPOS["numero"], ""),
                "Complemento": f.get(CAMPOS["complemento"], "")
            })
        return lista
    return []

def tela_clientes():
    st.header("👤 Cadastro de Clientes (Jira)")

    with st.expander("➕ Novo Cliente"):
        with st.form("form_cliente"):
            nome = st.text_input("Nome completo")
            cpf = st.text_input("CPF/CNPJ")
            empresa = st.text_input("Empresa")
            contato = st.text_input("Telefone")
            email = st.text_input("E-mail")
            cep = st.text_input("CEP")
            numero = st.text_input("Número")
            complemento = st.text_input("Complemento")
            foto = st.file_uploader("Foto do cliente", type=["jpg", "png", "jpeg"])
            submitted = st.form_submit_button("Salvar")

        if submitted:
            nome = corrigir_nome_abnt(nome)
            cliente = {
                "nome": nome,
                "cpf_cnpj": cpf,
                "empresa": empresa,
                "contato": contato,
                "email": email,
                "cep": cep,
                "numero": numero,
                "complemento": complemento
            }
            ok, msg = criar_cliente(cliente, foto)
            if ok:
                st.success(f"Cliente '{nome}' criado com sucesso (issue {msg})")
            else:
                st.error(f"Erro ao criar cliente: {msg}")

    st.subheader("📋 Clientes cadastrados")
    data = buscar_clientes()
    if data:
        st.dataframe(pd.DataFrame(data))
    else:
        st.info("Nenhum cliente encontrado.")
