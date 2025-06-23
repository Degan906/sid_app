import streamlit as st
import requests
import base64
import re

# === CONFIG JIRA (ajuste para centralizar depois) ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
EMAIL = "degan906@gmail.com"
TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{EMAIL}:{TOKEN}'.encode()).decode()}",
    "Accept": "application/json"
}

def tela_consulta_os():
    st.header("🔎 Consulta de Ordens de Serviço")

    jql = 'project = MC AND issuetype = "OS" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "summary,status,description"
    }

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        st.error("Erro ao buscar OS.")
        return

    issues = r.json().get("issues", [])
    if not issues:
        st.info("Nenhuma OS encontrada.")
        return

    st.markdown("### 📋 Lista de Ordens de Serviço")
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"].get("summary", "")
        status = issue["fields"]["status"]["name"]
        descricao = issue["fields"].get("description", "")

        # Extrair cliente e placa do summary
        cliente = re.search(r"OS - (.*?) \(", summary)
        cliente = cliente.group(1) if cliente else "-"
        placa = re.search(r"\((.*?)\)", summary)
        placa = placa.group(1) if placa else "-"

        cols = st.columns([1.5, 3, 2, 2, 1])
        cols[0].markdown(f"**{key}**")
        cols[1].markdown(f"🧑 {cliente}")
        cols[2].markdown(f"🚘 {placa}")
        cols[3].markdown(f"📄 *{status}*")
        with cols[4]:
            if st.button("Abrir", key=f"abrir_{key}"):
                st.session_state.tela_atual = "manutencoes"
                st.session_state.os_key = key
                st.session_state.itens = []
                st.session_state.confirmado = False
                st.rerun()
