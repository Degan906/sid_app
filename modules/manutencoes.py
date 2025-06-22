import streamlit as st
import requests
import base64
import unicodedata
import re
import datetime

# === CONFIG JIRA ===
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

def buscar_clientes():
    jql = 'project = MC AND issuetype = "Clientes" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 100, "fields": "summary,customfield_10040,customfield_10041,customfield_10042"}
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    if r.status_code == 200:
        return r.json().get("issues", [])
    return []

def buscar_veiculos_do_cliente(cpf):
    jql = f'project = MC AND issuetype = "Veículos" AND "CPF/CNPJ" ~ "{cpf}" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 50, "fields": "summary,customfield_10134"}
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    if r.status_code == 200:
        return r.json().get("issues", [])
    return []

def obter_foto_veiculo(issue_key):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}?fields=attachment"
    r = requests.get(url, headers=JIRA_HEADERS)
    if r.status_code == 200:
        attachments = r.json()["fields"].get("attachment", [])
        for a in attachments:
            if a.get("mimeType", "").startswith("image"):
                return a["content"]
    return None

def criar_os(cliente_nome, cliente_cpf, veiculo_key, km, descricao):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10030"},
            "summary": f"OS - {cliente_nome} ({cliente_cpf}) - {veiculo_key}",
            "description": f"CPF: {cliente_cpf}\nPlaca: {veiculo_key}\nKM: {km}\n\nDescrição:\n{descricao}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code == 201:
        return r.json().get("key")
    st.error(f"Erro ao criar OS: {r.status_code} - {r.text}")
    return None

def criar_subtarefa(os_key, descricao, tipo, quantidade, valor):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10031"},
            "parent": {"key": os_key},
            "summary": f"{tipo} - {descricao}",
            "description": f"{descricao}\nQuantidade: {quantidade}\nValor: R${valor}" 
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    return r.status_code == 201

# === TELA DE MANUTENÇÃO ===
def tela_manutencoes():
    st.header("🛠️ Abertura de Ordem de Serviço (OS)")

    st.subheader("👤 Selecionar Cliente")
    clientes = buscar_clientes()
    nomes = [f"{c['fields'].get('summary')} - {c['fields'].get('customfield_10041')}" for c in clientes]
    cliente_index = st.selectbox("Buscar por CPF ou Tel", nomes, index=0)
    cliente_escolhido = clientes[nomes.index(cliente_index)]
    cpf = cliente_escolhido['fields'].get('customfield_10040')
    nome_cliente = cliente_escolhido['fields'].get('summary')
    email_cliente = cliente_escolhido['fields'].get('customfield_10042')

    st.info(f"**Cliente:** {nome_cliente} | **CPF:** {cpf} | **Email:** {email_cliente}")

    st.subheader("🚗 Selecionar Veículo")
    veiculos = buscar_veiculos_do_cliente(cpf)
    if not veiculos:
        st.warning("Este cliente não possui veículos cadastrados.")
        return

    veiculo_opcoes = [f"{v['fields'].get('summary')} ({v['fields'].get('customfield_10134')})" for v in veiculos]
    veiculo_escolhido = st.selectbox("Selecione o Veículo:", veiculo_opcoes)
    veiculo_info = veiculos[veiculo_opcoes.index(veiculo_escolhido)]
    veiculo_key = veiculo_info["key"]

    st.markdown(f"**🔑 ID no Jira:** {veiculo_key}")
    st.markdown(f"**🚘 Identificação:** {veiculo_info['fields'].get('summary')}")
    st.markdown(f"**📍 Placa:** {veiculo_info['fields'].get('customfield_10134')}")

    foto_url = obter_foto_veiculo(veiculo_key)
    if foto_url:
        st.image(foto_url, width=300, caption="📸 Foto do Veículo")
    else:
        st.info("Nenhuma imagem encontrada para este veículo.")

    st.subheader("📋 Dados da OS")
    km = st.text_input("KM atual:")
    descricao_os = st.text_area("Descrição da OS:")

    st.subheader("🧾 Serviços e Peças")
    with st.form("form_subtarefas"):
        col1, col2 = st.columns([3, 1])
        descricao = col1.text_input("Descrição do item")
        tipo = col2.selectbox("Tipo", ["Serviço", "Peça"])
        quantidade = st.number_input("Quantidade", min_value=1, value=1)
        valor = st.number_input("Valor unitário (R$)", min_value=0.0, format="%.2f")
        adicionar_item = st.form_submit_button("➕ Adicionar Item")

    if "itens_os" not in st.session_state:
        st.session_state.itens_os = []

    if adicionar_item and descricao:
        st.session_state.itens_os.append({"descricao": descricao, "tipo": tipo, "quantidade": quantidade, "valor": valor})

    total = 0
    for i, item in enumerate(st.session_state.itens_os):
        total += item["quantidade"] * item["valor"]
        st.markdown(f"{i+1}. **{item['tipo']}** - {item['descricao']} | Qtd: {item['quantidade']} | Valor: R${item['valor']:.2f}")

    st.markdown(f"**💰 Total estimado:** R${total:.2f}")

    if st.button("🚀 Criar OS no Jira"):
        os_key = criar_os(nome_cliente, cpf, veiculo_key, km, descricao_os)
        if os_key:
            for item in st.session_state.itens_os:
                criar_subtarefa(os_key, item["descricao"], item["tipo"], item["quantidade"], item["valor"])
            st.success(f"✅ OS criada com sucesso: [{os_key}]({JIRA_URL}/browse/{os_key})")
            st.session_state.itens_os = []
