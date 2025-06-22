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
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
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

def criar_issue_veiculo(placa, modelo, marca, cor, ano, resumo):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"name": "Veiculos"},
            "summary": resumo,
            "customfield_10134": placa,
            "customfield_10136": modelo,
            "customfield_10140": {"value": marca} if marca else None,
            "customfield_10137": cor,
            "customfield_10138": ano
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
    files = {"file": (imagem.name, imagem.getvalue())}
    response = requests.post(url, headers=headers, files=files)
    return response.status_code == 200

def buscar_veiculos_jira(termo):
    jql = f'project = MC AND issuetype = Veiculos AND summary ~ "{termo}" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 100}
    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        st.error(f"Erro ao buscar veículos: {response.text}")
        return []

# === TELA DE VEÍCULOS ===
def tela_veiculos():
    st.header("🚘 Cadastro e Edição de Veículos")

    aba = st.radio("Escolha a ação:", ["Cadastrar Veículo", "Buscar e Editar Veículo"])

    if aba == "Cadastrar Veículo":
        if "veiculo_confirmado" not in st.session_state:
            st.session_state.veiculo_confirmado = False
        if "veiculo_dados" not in st.session_state:
            st.session_state.veiculo_dados = {}

        with st.form("form_veiculo"):
            placa = st.text_input("Placa:").upper()
            buscar = st.form_submit_button("🔍 Buscar dados pela placa")

            if buscar and placa:
                dados = buscar_dados_por_placa(placa)
                if dados:
                    st.success("✅ Dados encontrados pela placa.")
                else:
                    st.warning("⚠️ Nenhum dado encontrado.")

            modelo = st.text_input("Modelo:")
            marca = st.text_input("Marca:")
            cor = st.text_input("Cor:")
            ano = st.text_input("Ano:")
            resumo = st.text_input("Identificação (nome resumido):")
            imagem = st.file_uploader("Foto do veículo:", type=["jpg", "jpeg", "png"])
            confirmar = st.form_submit_button("✅ Confirmar Dados")

        if confirmar:
            resumo_abnt = corrige_abnt(resumo)
            st.session_state.veiculo_confirmado = True
            st.session_state.veiculo_dados = {
                "placa": placa,
                "modelo": corrige_abnt(modelo),
                "marca": corrige_abnt(marca),
                "cor": corrige_abnt(cor),
                "ano": ano,
                "resumo": resumo_abnt,
                "imagem": imagem
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
            if dados["imagem"]:
                st.image(dados["imagem"], width=200, caption="📸 Foto selecionada")

            if st.button("🚀 Enviar para o Jira"):
                with st.spinner("Enviando para o Jira..."):
                    issue_key = criar_issue_veiculo(
                        dados["placa"], dados["modelo"], dados["marca"],
                        dados["cor"], dados["ano"], dados["resumo"]
                    )
                    if issue_key:
                        if dados["imagem"]:
                            sucesso = anexar_foto(issue_key, dados["imagem"])
                            if not sucesso:
                                st.warning("⚠️ Veículo criado, mas não foi possível anexar a foto.")
                        st.success(f"✅ Veículo criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
                        st.session_state.veiculo_confirmado = False
                        st.session_state.veiculo_dados = {}

    else:
        termo = st.text_input("🔎 Buscar veículo por nome, placa ou modelo:")
        if termo:
            with st.spinner("🔍 Buscando veículos..."):
                resultados = buscar_veiculos_jira(termo)
            if resultados:
                st.success(f"✅ {len(resultados)} veículo(s) encontrado(s)")
                for issue in resultados:
                    key = issue["key"]
                    f = issue["fields"]
                    with st.expander(f"🚗 {f.get('summary', key)} ({key})"):
                        st.markdown(f"**Placa:** {f.get('customfield_10134', '-')}")
                        st.markdown(f"**Modelo:** {f.get('customfield_10136', '-')}")
                        st.markdown(f"**Marca:** {f.get('customfield_10140', {}).get('value', '-') if f.get('customfield_10140') else '-'}")
                        st.markdown(f"**Cor:** {f.get('customfield_10137', '-')}")
                        st.markdown(f"**Ano:** {f.get('customfield_10138', '-')}")
                        if st.button(f"✏️ Editar {key}", key=f"editar_{key}"):
                            with st.form(f"form_edicao_{key}"):
                                novo_resumo = st.text_input("Identificação:", value=f.get("summary", ""))
                                nova_placa = st.text_input("Placa:", value=f.get("customfield_10134", ""))
                                novo_modelo = st.text_input("Modelo:", value=f.get("customfield_10136", ""))
                                nova_marca = st.text_input("Marca:", value=f.get("customfield_10140", {}).get("value", ""))
                                nova_cor = st.text_input("Cor:", value=f.get("customfield_10137", ""))
                                novo_ano = st.text_input("Ano:", value=f.get("customfield_10138", ""))
                                salvar = st.form_submit_button("💾 Salvar alterações")

                            if salvar:
                                payload = {
                                    "fields": {
                                        "summary": novo_resumo,
                                        "customfield_10134": nova_placa,
                                        "customfield_10136": novo_modelo,
                                        "customfield_10140": {"value": nova_marca},
                                        "customfield_10137": nova_cor,
                                        "customfield_10138": novo_ano
                                    }
                                }
                                update_url = f"{JIRA_URL}/rest/api/2/issue/{key}"
                                r = requests.put(update_url, headers=JIRA_HEADERS, json=payload)
                                if r.status_code == 204:
                                    st.success("✅ Veículo atualizado com sucesso!")
                                else:
                                    st.error(f"Erro ao atualizar: {r.text}")
            else:
                st.warning("Nenhum veículo encontrado.")
