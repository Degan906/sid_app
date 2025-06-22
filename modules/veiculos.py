
import streamlit as st
import requests
import base64
import unicodedata
import re
from io import BytesIO
import pandas as pd

# === CONFIG JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === UTILITÁRIOS ===
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
    params = {"jql": jql, "maxResults": 1}
    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    if response.status_code == 200:
        issues = response.json().get("issues", [])
        if issues:
            fields = issues[0]["fields"]
            return {
                "nome": fields.get("customfield_10038", ""),
                "telefone": fields.get("customfield_10041", "")
            }
    return None

def criar_issue_veiculo(placa, modelo, marca, cor, ano, resumo, cpf_cliente=None):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10031"},
            "summary": resumo,
            "customfield_10134": placa,
            "customfield_10136": modelo,
            "customfield_10140": {"value": marca},
            "customfield_10137": cor,
            "customfield_10138": ano,
            "customfield_10040": cpf_cliente
        }
    }
    response = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
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

# === TELA DE CADASTRO DE VEÍCULOS ===
def tela_veiculos():
    st.header("🚘 Cadastrar Novo Veículo")

    if "veiculo_confirmado" not in st.session_state:
        st.session_state.veiculo_confirmado = False
    if "veiculo_dados" not in st.session_state:
        st.session_state.veiculo_dados = {}

    marcas = get_marcas()

    with st.form("form_veiculo"):
        placa = st.text_input("Placa:")
        modelo = st.text_input("Modelo:")
        marca = st.selectbox("Marca:", marcas)
        cor = st.text_input("Cor:")
        ano = st.text_input("Ano:")
        cpf_cliente = st.text_input("CPF/CNPJ do Cliente:")
        imagem = st.file_uploader("Foto do veículo:", type=["jpg", "jpeg", "png"])
        confirmar = st.form_submit_button("✅ Confirmar Dados")

    if confirmar:
        resumo = f"{corrige_abnt(marca)} / {corrige_abnt(modelo)} / {corrige_abnt(cor)} / {placa.upper()}"
        st.session_state.veiculo_confirmado = True
        st.session_state.veiculo_dados = {
            "placa": placa.upper(),
            "modelo": corrige_abnt(modelo),
            "marca": marca,
            "cor": corrige_abnt(cor),
            "ano": ano,
            "resumo": resumo,
            "imagem": imagem,
            "cpf_cliente": cpf_cliente
        }
        st.success("✅ Dados confirmados! Verifique abaixo antes de enviar.")

    if st.session_state.veiculo_confirmado:
        dados = st.session_state.veiculo_dados
        st.markdown("### 📄 Resumo do veículo")
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
            st.warning("Cliente não encontrado.")

        if dados.get("imagem"):
            st.image(dados["imagem"], width=200, caption="📸 Foto selecionada")

        if st.button("🚀 Enviar para o Jira"):
            with st.spinner("Enviando para o Jira..."):
                key = criar_issue_veiculo(
                    dados["placa"], dados["modelo"], dados["marca"],
                    dados["cor"], dados["ano"], dados["resumo"], dados["cpf_cliente"]
                )
                if key:
                    if dados["imagem"]:
                        sucesso_foto = anexar_foto(key, dados["imagem"])
                        if not sucesso_foto:
                            st.warning("⚠️ Veículo criado, mas falha ao anexar foto.")
                    st.success(f"✅ Veículo criado com sucesso: [{key}]({JIRA_URL}/browse/{key})")
                    st.session_state.veiculo_confirmado = False
                    st.session_state.veiculo_dados = {}
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
            image_url = attachments[0]["content"]
            image_resp = requests.get(image_url, headers=JIRA_HEADERS)
            if image_resp.status_code == 200:
                return BytesIO(image_resp.content)
    return None

def buscar_veiculos_jira(termo_busca):
    jql = f'project = MC AND issuetype = "Veículos" AND (summary ~ "{termo_busca}" OR customfield_10134 ~ "{termo_busca}") ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": 50,
        "fields": "summary,customfield_10134,customfield_10136,customfield_10140,customfield_10137,customfield_10138"
    }
    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        st.error(f"Erro ao buscar veículos: {response.text}")
        return []

def tela_busca_edicao_veiculos():
    st.header("🔍 Buscar e Editar Veículos")

    termo = st.text_input("Buscar por placa ou modelo:")

    jql = 'project = MC AND issuetype = "Veículos" ORDER BY created DESC'
    if termo:
        jql = f'project = MC AND issuetype = "Veículos" AND (summary ~ "{termo}" OR customfield_10134 ~ "{termo}") ORDER BY created DESC'

    with st.spinner("Buscando veículos..."):
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {
            "jql": jql,
            "maxResults": 50,
            "fields": "summary,customfield_10134,customfield_10136,customfield_10140,customfield_10137,customfield_10138,customfield_10040"
        }
        response = requests.get(url, headers=JIRA_HEADERS, params=params)

    if response.status_code == 200:
        issues = response.json().get("issues", [])
        if issues:
            st.success(f"{len(issues)} veículo(s) encontrado(s)")

            data = []
            for issue in issues:
                fields = issue["fields"]
                data.append({
                    "Key": issue["key"],
                    "Resumo": fields.get("summary"),
                    "Placa": fields.get("customfield_10134", "—"),
                    "Modelo": fields.get("customfield_10136", "—"),
                    "Marca": fields.get("customfield_10140", {}).get("value", "—"),
                    "Cor": fields.get("customfield_10137", "—"),
                    "Ano": fields.get("customfield_10138", "—"),
                    "CPF/CNPJ": fields.get("customfield_10040", "")
                })

            df = pd.DataFrame(data)
            st.dataframe(df.drop(columns=["Key"]), use_container_width=True)

            for item in data:
                key = item["Key"]
                if f"editar_{key}" not in st.session_state:
                    st.session_state[f"editar_{key}"] = False

                with st.expander(f"🚗 {item['Placa']} - {item['Modelo']} ({key})"):
                    st.markdown(f"**Marca:** {item['Marca']}")
                    st.markdown(f"**Cor:** {item['Cor']}")
                    st.markdown(f"**Ano:** {item['Ano']}")

                    # 🔍 Buscar dados do cliente
                    cpf_cliente = item.get("CPF/CNPJ")
                    cliente = buscar_cliente_por_cpf(cpf_cliente)
                    if cliente:
                        st.markdown("#### 👤 Cliente Associado")
                        st.markdown(f"- **Nome:** {cliente.get('nome', '—')}")
                        st.markdown(f"- **Telefone:** {cliente.get('telefone', '—')}")
                        st.markdown(f"- **CPF/CNPJ:** {cpf_cliente}")
                    else:
                        st.warning("Cliente não encontrado no Jira.")

                    # 🖼️ Mostrar foto (se houver)
                    imagem = get_attachments(key)
                    if imagem:
                        st.image(imagem, width=200, caption="📸 Foto do veículo")

                    # Botão editar
                    if st.button(f"✏️ Editar {key}", key=f"btn_{key}"):
                        st.session_state[f"editar_{key}"] = True

                    if st.session_state.get(f"editar_{key}"):
                        with st.form(f"form_edicao_{key}"):
                            placa = st.text_input("Placa:", value=item["Placa"])
                            modelo = st.text_input("Modelo:", value=item["Modelo"])
                            marca = st.text_input("Marca:", value=item["Marca"])
                            cor = st.text_input("Cor:", value=item["Cor"])
                            ano = st.text_input("Ano:", value=item["Ano"])
                            salvar = st.form_submit_button("💾 Salvar alterações")

                        if salvar:
                            resumo = f"{corrige_abnt(marca)} / {corrige_abnt(modelo)} / {corrige_abnt(cor)} / {placa.upper()}"
                            atualizado = atualizar_veiculo(key, {
                                "placa": placa.upper(),
                                "modelo": corrige_abnt(modelo),
                                "marca": marca,
                                "cor": corrige_abnt(cor),
                                "ano": ano,
                                "resumo": resumo
                            })
                            if atualizado:
                                st.success("✅ Veículo atualizado com sucesso!")
                                st.session_state[f"editar_{key}"] = False
                            else:
                                st.error("❌ Falha ao atualizar veículo.")
        else:
            st.warning("Nenhum veículo encontrado.")
    else:
        st.error("Erro na requisição ao Jira.")

