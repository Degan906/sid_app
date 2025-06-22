import streamlit as st
import requests
import base64
import pandas as pd
from datetime import datetime

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
def buscar_clientes():
    jql = 'project = MC AND issuetype = Clientes ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 100, "fields": "summary,customfield_10040,customfield_10041,customfield_10042"}
    resp = requests.get(url, headers=JIRA_HEADERS, params=params)
    if resp.status_code == 200:
        return resp.json().get("issues", [])
    return []

def buscar_veiculos_do_cliente(cpf):
    jql = f'project = MC AND issuetype = Veículos AND "CPF/CNPJ" ~ "{cpf}"'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 100, "fields": "summary,customfield_10134,customfield_10136"}
    resp = requests.get(url, headers=JIRA_HEADERS, params=params)
    if resp.status_code == 200:
        return resp.json().get("issues", [])
    return []

# === TELA DE MANUTENÇÃO ===
def tela_manutencoes():
    st.header("🧰 Abertura de Ordem de Serviço (OS)")

    st.subheader("🔍 Buscar Cliente")
    clientes = buscar_clientes()
    opcoes = {f"{c['fields']['summary']} ({c['fields'].get('customfield_10040', '')})": c for c in clientes}
    cliente_nome = st.selectbox("Selecione um cliente:", list(opcoes.keys()))

    if cliente_nome:
        cliente = opcoes[cliente_nome]
        cpf = cliente["fields"].get("customfield_10040", "")
        telefone = cliente["fields"].get("customfield_10041", "")
        email = cliente["fields"].get("customfield_10042", "")

        st.markdown(f"**📌 CPF/CNPJ:** {cpf}")
        st.markdown(f"**📞 Telefone:** {telefone}")
        st.markdown(f"**📧 E-mail:** {email}")

        st.subheader("🚗 Veículo do Cliente")
        veiculos = buscar_veiculos_do_cliente(cpf)
        if veiculos:
            veiculo_opcoes = {f"{v['fields'].get('customfield_10134', '')} - {v['fields'].get('customfield_10136', '')}": v for v in veiculos}
            veiculo_escolhido = st.selectbox("Escolha um veículo:", list(veiculo_opcoes.keys()))
            veiculo_key = veiculo_opcoes[veiculo_escolhido]["key"]
        else:
            st.warning("Nenhum veículo encontrado para esse cliente.")
            return

        st.subheader("📋 Dados da Ordem de Serviço")
        km_atual = st.text_input("KM Atual:")
        data_entrada = st.date_input("Data de Entrada:", value=datetime.today())
        previsao_saida = st.date_input("Previsão de Saída:")
        observacoes = st.text_area("Observações:")

        st.subheader("🛠️ Itens da Manutenção (Subtarefas)")
        st.info("Essa área exibirá os serviços adicionados após salvar a OS principal.")

        if st.button("🚀 Criar Ordem de Serviço"):
            with st.spinner("Criando OS no Jira..."):
                payload = {
                    "fields": {
                        "project": {"key": "MC"},
                        "issuetype": {"id": "10030"},  # OS
                        "summary": f"OS - {cliente['fields']['summary']} - {veiculo_escolhido}",
                        "customfield_10040": cpf,
                        "customfield_10134": veiculo_escolhido,
                        "description": f"KM: {km_atual}\nEntrada: {data_entrada}\nSaída: {previsao_saida}\nObservações: {observacoes}"
                    }
                }
                res = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
                if res.status_code == 201:
                    os_key = res.json().get("key")
                    st.success(f"✅ OS criada com sucesso: [{os_key}]({JIRA_URL}/browse/{os_key})")
                else:
                    st.error(f"Erro ao criar OS: {res.status_code} - {res.text}")
