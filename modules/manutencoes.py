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

def criar_os(cliente_nome, cliente_cpf, veiculo_key, km, data_entrada, data_saida, descricao):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10030"},
            "summary": f"OS - {cliente_nome} ({cliente_cpf}) - {veiculo_key}",
            "description": f"CPF: {cliente_cpf}\nPlaca: {veiculo_key}\nKM: {km}\n\nDescrição:\n{descricao}",
            "customfield_10065": data_entrada,
            "customfield_10066": data_saida
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
            "description": f"{descricao}\nQuantidade: {quantidade}\nValor: R${valor:.2f}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    return r.status_code == 201

# === TELA DE MANUTENÇÃO ===
def tela_manutencoes():
    st.header("\U0001F6E0️ Abertura de Ordem de Serviço (OS)")

    st.subheader("👤 Selecionar Cliente")
    clientes = buscar_clientes()
    nomes = [f"{c['fields'].get('summary')} - {c['fields'].get('customfield_10041')}" for c in clientes]
    cliente_index = st.selectbox("Buscar por CPF ou Tel", nomes)
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

    # Formulário da OS
    st.subheader("📋 Detalhes da OS")
    km = st.text_input("Quilometragem atual do veículo (KM):")
    data_entrada = st.date_input("Data de Entrada", value=datetime.date.today())
    data_saida = st.date_input("Data Prevista de Saída", value=datetime.date.today())
    descricao = st.text_area("Descrição geral do problema ou solicitação:")

    if st.button("✅ Criar Ordem de Serviço"):
        os_key = criar_os(nome_cliente, cpf, veiculo_key, km, str(data_entrada), str(data_saida), descricao)
        if os_key:
            st.success(f"Ordem de Serviço criada com sucesso! ID: {os_key}")

            # Adicionar serviços ou peças
            st.subheader("🧾 Adicionar Serviços ou Peças")
            st.markdown("Você pode adicionar múltiplos serviços ou peças abaixo:")

            with st.form(key="form_subtarefas"):
                col1, col2 = st.columns(2)
                with col1:
                    tipo = st.selectbox("Tipo", ["Serviço", "Peça"])
                    descricao_sub = st.text_input("Descrição do item")
                with col2:
                    quantidade = st.number_input("Quantidade", min_value=1, step=1)
                    valor = st.number_input("Valor unitário (R$)", min_value=0.0, step=0.01)

                enviar = st.form_submit_button("➕ Adicionar Subtarefa")
                if enviar:
                    sucesso = criar_subtarefa(os_key, descricao_sub, tipo, quantidade, valor)
                    if sucesso:
                        st.success("Subtarefa adicionada com sucesso.")
                    else:
                        st.error("Erro ao adicionar subtarefa.")
