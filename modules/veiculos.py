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

def corrige_abnt(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    texto = ' '.join(word.capitalize() for word in texto.split())
    return texto

def get_marcas():
    url = f"{JIRA_URL}/rest/api/2/issue/createmeta"
    params = {
        "projectKeys": "MC",
        "issuetypeIds": "10031",
        "expand": "projects.issuetypes.fields"
    }
    resp = requests.get(url, headers=JIRA_HEADERS, params=params)
    if resp.status_code == 200:
        try:
            campos = resp.json()["projects"][0]["issuetypes"][0]["fields"]
            opcoes = campos["customfield_10140"]["allowedValues"]
            return [op["value"] for op in opcoes]
        except (KeyError, IndexError):
            return []
    else:
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
    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    if response.status_code == 200:
        issues = response.json().get("issues", [])
        if issues:
            fields = issues[0]["fields"]
            return {
                "nome": fields.get("customfield_10038", ""),
                "cpf": fields.get("customfield_10040", ""),
                "telefone": fields.get("customfield_10041", "")
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
    resp = requests.get(url, headers=JIRA_HEADERS, params=params)
    if resp.status_code == 200:
        issues = resp.json().get("issues", [])
        veiculos = []
        for issue in issues:
            fields = issue["fields"]
            cpf = fields.get("customfield_10040")
            cliente = buscar_cliente_por_cpf(cpf)
            veiculos.append({
                "Key": issue["key"],
                "Resumo": fields.get("summary"),
                "Placa": fields.get("customfield_10134"),
                "Modelo": fields.get("customfield_10136"),
                "Marca": fields.get("customfield_10140", {}).get("value"),
                "Cor": fields.get("customfield_10137"),
                "Ano": fields.get("customfield_10138"),
                "CPF/CNPJ": cpf,
                "Cliente": cliente["nome"] if cliente else "",
                "Telefone": cliente["telefone"] if cliente else ""
            })
        return veiculos
    else:
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

def atualizar_veiculo(issue_key, dados):
    payload = {
        "fields": {
            "summary": dados["resumo"],
            "customfield_10134": dados["placa"],
            "customfield_10136": dados["modelo"],
            "customfield_10140": { "value": dados["marca"] } if dados["marca"] else None,
            "customfield_10137": dados["cor"],
            "customfield_10138": dados["ano"]
        }
    }
    payload["fields"] = {k: v for k, v in payload["fields"].items() if v not in [None, ""]}
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    response = requests.put(url, json=payload, headers=JIRA_HEADERS)
    return response.status_code == 204

def get_attachments(issue_key):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}?fields=attachment"
    response = requests.get(url, headers=JIRA_HEADERS)
    if response.status_code == 200:
        attachments = response.json()["fields"].get("attachment", [])
        if attachments:
            first = attachments[0]
            image_url = first["content"]
            image_resp = requests.get(image_url, headers=JIRA_HEADERS)
            if image_resp.status_code == 200:
                return BytesIO(image_resp.content)
    return None

def anexar_foto(issue_key, imagem):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    headers = {
        "Authorization": JIRA_HEADERS["Authorization"],
        "X-Atlassian-Token": "no-check"
    }
    files = { "file": ("veiculo.jpg", imagem.getvalue()) }
    response = requests.post(url, headers=headers, files=files)
    return response.status_code == 200

def tela_veiculos():
    st.set_page_config(page_title="Cadastro de Veículos", layout="wide")
    st.header("🚘 Cadastro de Veículos")

    if "veiculo_confirmado" not in st.session_state:
        st.session_state.veiculo_confirmado = False
    if "veiculo_dados" not in st.session_state:
        st.session_state.veiculo_dados = {}
    if "modo_novo" not in st.session_state:
        st.session_state.modo_novo = False

    if st.button("➕ Cadastrar novo veículo"):
        st.session_state.veiculo_dados = {}
        st.session_state.veiculo_confirmado = False
        st.session_state.modo_novo = True

    st.subheader("🔍 Buscar veículos já cadastrados")
    filtro = st.text_input("Buscar por placa, modelo, marca ou cor:")
    veiculos = buscar_veiculos()
    if filtro:
        veiculos = [v for v in veiculos if filtro.lower() in str(v).lower()]
    if veiculos:
        df = pd.DataFrame(veiculos)
        st.dataframe(df, use_container_width=True)
        indice = st.selectbox("Selecione um veículo:", df.index, format_func=lambda i: f"{df.loc[i, 'Placa']} - {df.loc[i, 'Modelo']}")
        if indice is not None and not st.session_state.modo_novo:
            selecionado = df.loc[indice]
            st.session_state.veiculo_dados = {
                "key": selecionado["Key"],
                "placa": selecionado["Placa"],
                "modelo": selecionado["Modelo"],
                "marca": selecionado["Marca"],
                "cor": selecionado["Cor"],
                "ano": selecionado["Ano"],
                "resumo": selecionado["Resumo"],
                "cpf_cliente": selecionado["CPF/CNPJ"],
                "imagem": get_attachments(selecionado["Key"])
            }
            st.session_state.veiculo_confirmado = True
            st.session_state.modo_novo = False

    st.divider()
    st.subheader("📥 Cadastro / Edição de Veículo")

    with st.form("form_veiculo"):
        dados = st.session_state.veiculo_dados
        placa = st.text_input("Placa:", value=dados.get("placa", "")).upper()
        modelo = st.text_input("Modelo:", value=dados.get("modelo", ""))
        marcas = get_marcas()
        marca = st.selectbox("Marca:", marcas, index=marcas.index(dados.get("marca")) if dados.get("marca") in marcas else 0)
        cor = st.text_input("Cor:", value=dados.get("cor", ""))
        ano = st.text_input("Ano:", value=dados.get("ano", ""))
        cpf_cliente = st.text_input("CPF/CNPJ do Cliente:", value=dados.get("cpf_cliente", ""))
        imagem_up = st.file_uploader("Foto do veículo:", type=["jpg", "jpeg", "png"])
        imagem = BytesIO(imagem_up.read()) if imagem_up else dados.get("imagem")
        confirmar = st.form_submit_button("✅ Confirmar Dados")

    if confirmar:
        resumo = f"{corrige_abnt(marca)} / {corrige_abnt(modelo)} / {corrige_abnt(cor)} / {placa}"
        st.session_state.veiculo_confirmado = True
        st.session_state.modo_novo = False
        st.session_state.veiculo_dados = {
            "key": dados.get("key"),
            "placa": placa,
            "modelo": corrige_abnt(modelo),
            "marca": marca,
            "cor": corrige_abnt(cor),
            "ano": ano,
            "resumo": resumo,
            "cpf_cliente": cpf_cliente,
            "imagem": imagem
        }
        st.success("✅ Dados confirmados! Verifique abaixo antes de enviar.")

    if st.session_state.veiculo_confirmado:
        dados = st.session_state.veiculo_dados
        st.markdown("### 📄 Resumo")
        st.markdown(f"**Placa:** {dados['placa']}")
        st.markdown(f"**Modelo:** {dados['modelo']}")
        st.markdown(f"**Marca:** {dados['marca']}")
        st.markdown(f"**Cor:** {dados['cor']}")
        st.markdown(f"**Ano:** {dados['ano']}")
        st.markdown(f"**Resumo:** {dados['resumo']}")
        st.markdown(f"**CPF/CNPJ do Cliente:** {dados['cpf_cliente']}")

        cliente = buscar_cliente_por_cpf(dados["cpf_cliente"])
        if cliente:
            st.markdown(f"**👤 Cliente:** {cliente['nome']}")
            st.markdown(f"**📞 Telefone:** {cliente['telefone']}")
        else:
            st.warning("Cliente não localizado.")

        if dados.get("imagem"):
            st.image(dados["imagem"], width=200, caption="📸 Foto")

        if st.button("🚀 Enviar para o Jira"):
            with st.spinner("Enviando..."):
                if dados.get("key"):
                    ok = atualizar_veiculo(dados["key"], dados)
                    if ok:
                        st.success(f"✅ Atualizado: [{dados['key']}]({JIRA_URL}/browse/{dados['key']})")
                    else:
                        st.error("Erro ao atualizar.")
                else:
                    key = criar_issue_veiculo(
                        dados["placa"], dados["modelo"], dados["marca"],
                        dados["cor"], dados["ano"], dados["resumo"], dados["cpf_cliente"]
                    )
                    if key:
                        if dados.get("imagem"):
                            anexar_foto(key, dados["imagem"])
                        st.success(f"✅ Criado: [{key}]({JIRA_URL}/browse/{key})")
            st.session_state.veiculo_dados = {}
            st.session_state.veiculo_confirmado = False
            st.session_state.modo_novo = False
