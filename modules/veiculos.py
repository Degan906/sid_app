# modules/veiculos.py
import streamlit as st
import requests
import base64
import unicodedata
import re
from io import BytesIO
import pandas as pd

# === CONFIGURAÇÕES JIRA ===
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
    return ' '.join(word.capitalize() for word in texto.split())

def get_marcas():
    url = f"{JIRA_URL}/rest/api/2/issue/createmeta"
    params = {
        "projectKeys": "MC",
        "issuetypeIds": "10031",
        "expand": "projects.issuetypes.fields"
    }
    resp = requests.get(url, headers=JIRA_HEADERS, params=params)
    try:
        campos = resp.json()["projects"][0]["issuetypes"][0]["fields"]
        return [op["value"] for op in campos["customfield_10140"]["allowedValues"]]
    except:
        return []

def buscar_cliente_por_cpf(cpf):
    if not cpf:
        return None
    jql = f'project = MC AND issuetype = "Clientes" AND "CPF/CNPJ" ~ "{cpf}"'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "fields": "customfield_10038,customfield_10040,customfield_10041",
        "maxResults": 1
    }
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    if r.status_code == 200:
        issues = r.json().get("issues", [])
        if issues:
            f = issues[0]["fields"]
            return {
                "nome": f.get("customfield_10038", ""),
                "cpf": f.get("customfield_10040", ""),
                "telefone": f.get("customfield_10041", "")
            }
    return None

def buscar_veiculos():
    jql = 'project = MC AND issuetype = "Veículos" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "fields": "summary,customfield_10134,customfield_10136,customfield_10140,customfield_10137,customfield_10138,customfield_10040",
        "maxResults": 100
    }
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    veiculos = []
    if r.status_code == 200:
        for issue in r.json()["issues"]:
            f = issue["fields"]
            cpf = f.get("customfield_10040")
            cliente = buscar_cliente_por_cpf(cpf)
            veiculos.append({
                "Key": issue["key"],
                "Resumo": f.get("summary"),
                "Placa": f.get("customfield_10134"),
                "Modelo": f.get("customfield_10136"),
                "Marca": f.get("customfield_10140", {}).get("value"),
                "Cor": f.get("customfield_10137"),
                "Ano": f.get("customfield_10138"),
                "CPF/CNPJ": cpf,
                "Cliente": cliente["nome"] if cliente else "",
                "Telefone": cliente["telefone"] if cliente else ""
            })
    return veiculos

def criar_issue_veiculo(placa, modelo, marca, cor, ano, resumo, cpf_cliente):
    fields = {
        "project": {"key": "MC"},
        "issuetype": {"id": "10031"},
        "summary": resumo,
        "customfield_10134": placa,
        "customfield_10136": modelo,
        "customfield_10140": {"value": marca} if marca else None,
        "customfield_10137": cor,
        "customfield_10138": ano,
        "customfield_10040": cpf_cliente
    }
    payload = {"fields": {k: v for k, v in fields.items() if v}}
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code == 201:
        return r.json()["key"]
    st.error(f"Erro ao criar veículo: {r.status_code} - {r.text}")
    return None

def anexar_foto(issue_key, imagem):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    headers = {
        "Authorization": JIRA_HEADERS["Authorization"],
        "X-Atlassian-Token": "no-check"
    }
    files = {"file": ("veiculo.jpg", imagem.getvalue())}
    r = requests.post(url, headers=headers, files=files)
    return r.status_code == 200

# === TELA PRINCIPAL ===
def tela_veiculos():
    st.header("🚘 Consulta de Veículos")
    filtro = st.text_input("Buscar por placa, modelo, marca ou cor:")
    veiculos = buscar_veiculos()
    if filtro:
        veiculos = [v for v in veiculos if filtro.lower() in str(v).lower()]
    if veiculos:
        df = pd.DataFrame(veiculos)
        st.dataframe(df, use_container_width=True)
        indice = st.selectbox("Selecione um veículo:", df.index, format_func=lambda i: f"{df.loc[i, 'Placa']} - {df.loc[i, 'Modelo']}")
        if indice is not None:
            selecionado = df.loc[indice]
            st.subheader("📋 Detalhes do Veículo")
            st.markdown(f"""
            **Resumo:** {selecionado['Resumo']}
            **Placa:** {selecionado['Placa']}
            **Marca:** {selecionado['Marca']}
            **Modelo:** {selecionado['Modelo']}
            **Cor:** {selecionado['Cor']}
            **Ano:** {selecionado['Ano']}
            **CPF:** {selecionado['CPF/CNPJ']}
            """)
            cliente = buscar_cliente_por_cpf(selecionado["CPF/CNPJ"])
            if cliente:
                st.markdown(f"""
                **👤 Cliente:** {cliente['nome']}
                📞 {cliente['telefone']}
                """)
            else:
                st.warning("⚠️ Cliente não encontrado.")
    else:
        st.info("Nenhum veículo encontrado.")

# === TELA DE CADASTRO ===
def cadastro_veiculo():
    st.header("📝 Cadastro de Novo Veículo")
    with st.form("form_novo_veiculo"):
        placa = st.text_input("Placa").upper()
        modelo = st.text_input("Modelo")
        marcas = get_marcas()
        marca = st.selectbox("Marca", marcas)
        cor = st.text_input("Cor")
        ano = st.text_input("Ano")
        cpf = st.text_input("CPF/CNPJ do Cliente")
        img_up = st.file_uploader("Foto do veículo", type=["jpg", "jpeg", "png"])
        imagem = BytesIO(img_up.read()) if img_up else None
        confirmar = st.form_submit_button("✅ Cadastrar Veículo")
    
    if confirmar:
        if not all([placa, modelo, marca, cor, ano, cpf]):
            st.error("Por favor, preencha todos os campos obrigatórios.")
            return
        
        resumo = f"{corrige_abnt(marca)} / {corrige_abnt(modelo)} / {corrige_abnt(cor)} / {placa}"
        key = criar_issue_veiculo(placa, modelo, marca, cor, ano, resumo, cpf)
        if key:
            if imagem:
                anexar_foto(key, imagem)
            st.success(f"✅ Veículo cadastrado com sucesso! [{key}]({JIRA_URL}/browse/{key})")
        else:
            st.error("Erro ao cadastrar veículo.")
