import streamlit as st
import requests
import base64
import unicodedata
import re
import pandas as pd
from io import BytesIO

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
    texto = re.sub(r'[^a-zA-Z0-9\\s]', '', texto)
    texto = ' '.join(word.capitalize() for word in texto.split())
    return texto

def buscar_dados_por_placa(placa):
    try:
        resp = requests.get(f"https://placafipe.com/api/v1/{placa}")
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {}

def get_marcas():
    url = f"{JIRA_URL}/rest/api/2/issue/createmeta"
    params = {
        "projectKeys": "MC",
        "issuetypeIds": "10031",
        "expand": "projects.issuetypes.fields"
    }
    resp = requests.get(url, headers=JIRA_HEADERS, params=params)
    if resp.status_code == 200:
        data = resp.json()
        try:
            campos = data["projects"][0]["issuetypes"][0]["fields"]
            opcoes = campos["customfield_10140"]["allowedValues"]
            return [op["value"] for op in opcoes]
        except (KeyError, IndexError):
            return []
    else:
        st.warning("⚠️ Não foi possível obter a lista de marcas do Jira.")
        return []

def criar_issue_veiculo(placa, modelo, marca, cor, ano, resumo, cpf_cliente=None):
    payload = {
        "fields": {
            "project": { "key": "MC" },
            "issuetype": { "id": "10031" },
            "summary": resumo,
            "customfield_10134": placa,
            "customfield_10136": modelo,
            "customfield_10140": { "value": marca } if marca else None,
            "customfield_10137": cor,
            "customfield_10138": ano,
            "customfield_10040": cpf_cliente
        }
    }
    payload["fields"] = {k: v for k, v in payload["fields"].items() if v not in [None, ""]}
    response = requests.post(f"{JIRA_URL}/rest/api/2/issue", json=payload, headers=JIRA_HEADERS)
    if response.status_code == 201:
        return response.json().get("key")
    else:
        st.error(f"Erro ao criar veículo: {response.status_code} - {response.text}")
        return None

def anexar_foto(issue_key, imagem):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    headers = {
        "Authorization": JIRA_HEADERS["Authorization"],
        "X-Atlassian-Token": "no-check"
    }
    files = { "file": (imagem.name, imagem.getvalue()) }
    response = requests.post(url, headers=headers, files=files)
    return response.status_code == 200

# === TELA PRINCIPAL ===
def tela_veiculos():
    st.header("🚘 Cadastro de Veículos")

    marcas = get_marcas()
    st.write("✅ Marcas disponíveis:", marcas)  # ← linha temporária para verificação

    if "veiculo_confirmado" not in st.session_state:
        st.session_state.veiculo_confirmado = False
    if "veiculo_dados" not in st.session_state:
        st.session_state.veiculo_dados = {}

    with st.form("form_veiculo"):
        placa = st.text_input("Placa:").upper()
        modelo = st.text_input("Modelo:")
        marca = st.selectbox("Marca:", marcas) if marcas else st.text_input("Marca:")
        cor = st.text_input("Cor:")
        ano = st.text_input("Ano:")
        resumo = st.text_input("Identificação (nome resumido):")
        cpf_cliente = st.text_input("CPF/CNPJ do Cliente vinculado:")
        imagem = st.file_uploader("Foto do veículo:", type=["jpg", "jpeg", "png"])
        confirmar = st.form_submit_button("✅ Confirmar Dados")

    if confirmar:
        resumo_abnt = corrige_abnt(resumo)
        st.session_state.veiculo_confirmado = True
        st.session_state.veiculo_dados = {
            "placa": placa,
            "modelo": corrige_abnt(modelo),
            "marca": marca,
            "cor": corrige_abnt(cor),
            "ano": ano,
            "resumo": resumo_abnt,
            "imagem": imagem,
            "cpf_cliente": cpf_cliente
        }
        st.success("✅ Dados confirmados! Verifique abaixo antes de enviar.")

    if st.session_state.veiculo_confirmado:
        dados = st.session_state.veiculo_dados
        st.markdown("### 📄 Resumo do cadastro do veículo")
        st.markdown(f"**Placa:** {dados['placa']}")
        st.markdown(f"**Modelo:** {dados['modelo']}")
        st.markdown(f"**Marca:** {dados['marca']}")
        st.markdown(f"**Cor:** {dados['cor']}")
        st.markdown(f"**Ano:** {dados['ano']}")
        st.markdown(f"**Identificação:** {dados['resumo']}")
        st.markdown(f"**CPF/CNPJ do Cliente:** {dados['cpf_cliente']}")
        if dados["imagem"]:
            st.image(dados["imagem"], width=200, caption="📸 Foto selecionada")

        if st.button("🚀 Enviar para o Jira"):
            with st.spinner("Enviando para o Jira..."):
                issue_key = criar_issue_veiculo(
                    dados["placa"], dados["modelo"], dados["marca"],
                    dados["cor"], dados["ano"], dados["resumo"], dados["cpf_cliente"]
                )
                if issue_key:
                    if dados["imagem"]:
                        sucesso = anexar_foto(issue_key, dados["imagem"])
                        if not sucesso:
                            st.warning("⚠️ Veículo criado, mas não foi possível anexar a foto.")
                    st.success(f"✅ Veículo criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
                    st.session_state.veiculo_confirmado = False
                    st.session_state.veiculo_dados = {}
