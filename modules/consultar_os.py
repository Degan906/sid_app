import streamlit as st
import requests
import base64
import pandas as pd

# === CONFIGURAÇÃO JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
EMAIL = "degan906@gmail.com"
TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{EMAIL}:{TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def tela_consulta_os():
    st.title("🔧 SID - Consulta de Ordens de Serviço (OS)")

    def buscar_issues():
        jql = 'project = MC AND issuetype = "OS" ORDER BY created DESC'
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 100, "fields": "summary,description,customfield_10134,customfield_10140,customfield_10136,customfield_10138,status,customfield_10041"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        return []

    def buscar_subtarefas(issue_key):
        url = f"{JIRA_URL}/rest/api/2/search"
        jql = f"parent = {issue_key}"
        params = {"jql": jql, "fields": "summary,description"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        return []

    def aplicar_transicao(issue_key, transition_id):
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}
        return requests.post(url, headers=HEADERS, json=payload).status_code == 204

    def buscar_transicoes(issue_key):
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.json().get("transitions", [])
        return []

    def atualizar_os(issue_key, campos):
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
        payload = {"fields": campos}
        return requests.put(url, headers=HEADERS, json=payload).status_code == 204

    issues = buscar_issues()

    if not issues:
        st.warning("Nenhuma OS encontrada.")
        return

    st.success(f"{len(issues)} OS encontradas.")

    busca = st.text_input("🔎 Buscar por qualquer campo (placa, resumo, marca...)")

    linhas = []
    for i, issue in enumerate(issues):
        key = issue["key"]
        f = issue["fields"]
        resumo = f.get("summary", "")
        descricao = f.get("description", "")
        placa = f.get("customfield_10134", "")
        marca = f.get("customfield_10140", {}).get("value", "")
        modelo = f.get("customfield_10136", "")
        ano = f.get("customfield_10138", "")
        telefone = f.get("customfield_10041", "")
        status = f.get("status", {}).get("name", "")

        if busca:
            termo = busca.lower()
            if not any(termo in str(v).lower() for v in [resumo, descricao, placa, telefone, marca, modelo, ano]):
                continue

        col1, col2 = st.columns([6, 1])
        with col1:
            with st.expander(f"🔧 {key} - {resumo} [{status}]"):
                st.markdown(f"**Placa:** {placa}  ")
                st.markdown(f"**Telefone:** {telefone}")
                st.markdown(f"**Marca:** {marca}")
                st.markdown(f"**Modelo:** {modelo}")
                st.markdown(f"**Ano:** {ano}")
                st.markdown("---")
                st.markdown("### 🧾 Itens/Subtarefas")
                subtarefas = buscar_subtarefas(key)
                if not subtarefas:
                    st.warning("Nenhuma subtarefa encontrada.")
                else:
                    for item in subtarefas:
                        st.markdown(f"**{item['key']} - {item['fields']['summary']}**")
                        desc = item["fields"].get("description", "")
                        st.markdown(f"> {desc}")
                        st.markdown("---")

        with col2:
            if st.button("✏️ Editar", key=f"edit_{i}"):
                st.session_state["os_editando"] = issue
                st.rerun()

    if "os_editando" in st.session_state:
        issue = st.session_state["os_editando"]
        key = issue["key"]
        f = issue["fields"]

        st.markdown("---")
        st.header(f"🛠️ Editar OS {key}")

        resumo = st.text_input("Resumo", value=f.get("summary", ""))
        descricao = st.text_area("Descrição", value=f.get("description", ""))
        placa = st.text_input("Placa", value=f.get("customfield_10134", ""))
        telefone = st.text_input("Telefone", value=f.get("customfield_10041", ""))
        marca = st.text_input("Marca", value=f.get("customfield_10140", {}).get("value", ""))
        modelo = st.text_input("Modelo", value=f.get("customfield_10136", ""))
        ano = st.text_input("Ano", value=f.get("customfield_10138", ""))

        transicoes = buscar_transicoes(key)
        opcoes_status = {t["name"]: t["id"] for t in transicoes}
        status_atual = f.get("status", {}).get("name", "")
        novo_status = st.selectbox("Status", options=list(opcoes_status.keys()), index=list(opcoes_status).index(status_atual) if status_atual in opcoes_status else 0)

        if st.button("💾 Salvar alterações"):
            campos = {
                "summary": resumo,
                "description": descricao,
                "customfield_10134": placa,
                "customfield_10041": telefone,
                "customfield_10140": {"value": marca},
                "customfield_10136": modelo,
                "customfield_10138": ano,
            }
            ok = atualizar_os(key, campos)
            status_ok = aplicar_transicao(key, opcoes_status[novo_status]) if novo_status != status_atual else True

            if ok and status_ok:
                st.success("OS atualizada com sucesso.")
                del st.session_state["os_editando"]
                st.rerun()
            else:
                st.error("Erro ao atualizar OS. Verifique os campos e tente novamente.")

