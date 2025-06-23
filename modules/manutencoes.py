import streamlit as st
from clientes import buscar_clientes
from veiculos import buscar_veiculos_do_cliente
import requests
import datetime

# === CONFIG JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net" 
JIRA_HEADERS = {
    "Authorization": "Basic ZGVnYW45MDZAZ21haWwuY29tOmdsVVFUTlpHMFYxdVlucldqcDl5QkIxNw==",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === FUNÇÕES AUXILIARES ===
def criar_os(cliente_nome, cliente_cpf, veiculo_key, km, data_entrada, data_saida, descricao):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10032"},
            "summary": f"OS - {cliente_nome} ({cliente_cpf}) - {veiculo_key}",
            "description": f"CPF: {cliente_cpf}\nPlaca: {veiculo_key}\nKM: {km}\n\nDescrição:\n{descricao}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code == 201:
        return r.json().get("key")
    st.error(f"Erro ao criar OS: {r.status_code} - {r.text}")
    return None

def criar_subtarefa(os_key, item):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10030"},
            "parent": {"key": os_key},
            "summary": item['descricao'],
            "description": f"Tipo: {item['tipo']}\nDescrição: {item['descricao']}\nQuantidade: {item['quantidade']}\nValor: R${item['valor']:.2f}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code != 201:
        st.error(f"Erro ao adicionar subtarefa: {r.status_code} - {r.text}")

def listar_itens_os(os_key):
    url = f"{JIRA_URL}/rest/api/2/issue/{os_key}"
    r = requests.get(url, headers=JIRA_HEADERS)
    if r.status_code == 200:
        fields = r.json().get("fields", {})
        return fields.get("subtasks", [])
    return []

def excluir_item(item_key):
    url = f"{JIRA_URL}/rest/api/2/issue/{item_key}"
    r = requests.delete(url, headers=JIRA_HEADERS)
    return r.status_code == 204

# === TELAS ===
def tela_consulta_os():
    st.title("🔍 Consultar Ordens de Serviço")

    jql = 'project = MC AND issuetype = "OS" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "summary,status"
    }
    r = requests.get(url, headers=JIRA_HEADERS, params=params)

    if r.status_code != 200:
        st.error("Erro ao buscar OS")
        return

    issues = r.json().get("issues", [])
    if not issues:
        st.info("Nenhuma OS encontrada.")
        return

    st.markdown("### 🗂 Lista de OS")
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"].get("summary", "-")
        status = issue["fields"].get("status", {}).get("name", "-")

        cliente_match = re.search(r"OS - (.*?) \(", summary)
        cliente = cliente_match.group(1) if cliente_match else "-"
        placa_match = re.search(r"\((.*?)\)", summary)
        placa = placa_match.group(1) if placa_match else "-"

        cols = st.columns([2, 4, 2, 2, 2])
        cols[0].markdown(f"**{key}**")
        cols[1].markdown(f"{cliente}")
        cols[2].markdown(f"{placa}")
        cols[3].markdown(f"📋 *{status}*")
        if cols[4].button("Editar", key=f"editar_{key}"):
            st.session_state.tela_atual = "editar_os"
            st.session_state.os_key = key
            st.rerun()

def tela_editar_os():
    st.title("\U0001F6E0️ Editar Ordem de Serviço")
    os_key = st.session_state.os_key

    # Buscar detalhes da OS
    url = f"{JIRA_URL}/rest/api/2/issue/{os_key}"
    r = requests.get(url, headers=JIRA_HEADERS)
    if r.status_code != 200:
        st.error("Erro ao carregar OS")
        return

    fields = r.json().get("fields", {})
    summary = fields.get("summary", "-")
    description = fields.get("description", "-")
    status = fields.get("status", {}).get("name", "-")

    st.subheader(f"OS: {summary}")
    st.write(f"Status: {status}")
    st.write(f"Descrição: {description}")

    # Listar itens da OS
    itens = listar_itens_os(os_key)
    if not itens:
        st.info("Esta OS não possui itens cadastrados.")
    else:
        st.markdown("### Itens da OS")
        for idx, item in enumerate(itens):
            item_key = item["id"]
            item_summary = item["fields"]["summary"]
            col1, col2 = st.columns([4, 1])
            col1.write(f"- {item_summary}")
            if col2.button("Excluir", key=f"excluir_{item_key}"):
                if excluir_item(item_key):
                    st.success("Item excluído com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao excluir item.")

    # Adicionar novos itens
    st.markdown("### Adicionar Novo Item")
    tipo = st.selectbox("Tipo", ["Serviço", "Peça"])
    descricao = st.text_input("Descrição")
    quantidade = st.number_input("Quantidade", step=1, min_value=1)
    valor = st.number_input("Valor R$", step=0.01, min_value=0.0)

    if st.button("Adicionar Item"):
        novo_item = {
            "tipo": tipo,
            "descricao": descricao,
            "quantidade": quantidade,
            "valor": valor
        }
        criar_subtarefa(os_key, novo_item)
        st.success("Item adicionado com sucesso!")
        st.rerun()

    # Botão para voltar
    if st.button("Voltar"):
        st.session_state.tela_atual = "consulta_os"
        st.rerun()

# === LÓGICA DE NAVEGAÇÃO ===
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "consulta_os"

if st.session_state.tela_atual == "consulta_os":
    tela_consulta_os()
elif st.session_state.tela_atual == "editar_os":
    tela_editar_os()
