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
    st.header("🔧 Consultar Ordens de Serviço (OS)")

    def buscar_os_por_placa(placa):
        jql = f'project = MC AND issuetype = "OS" AND description ~ "{placa}" ORDER BY created DESC'
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 50, "fields": "summary,description,status"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        return []

    def buscar_subtarefas(os_key):
        url = f"{JIRA_URL}/rest/api/2/search"
        jql = f'parent = {os_key}'
        params = {"jql": jql, "fields": "summary,description"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        return []

    placa = st.text_input("🔍 Buscar OS por placa (campo descrição):")

    if placa and st.button("Buscar OS"):
        with st.spinner("🔎 Buscando Ordens de Serviço..."):
            issues = buscar_os_por_placa(placa)

        if issues:
            st.success(f"✅ {len(issues)} OS encontrada(s)")

            # Tabela de resumo
            dados = []
            for issue in issues:
                fields = issue["fields"]
                dados.append({
                    "Key": issue["key"],
                    "Resumo": fields.get("summary", "—"),
                    "Status": fields.get("status", {}).get("name", "—"),
                    "Descrição": fields.get("description", "—")
                })
            df = pd.DataFrame(dados)
            st.dataframe(df, use_container_width=True)

            # Expanders com detalhes
            for issue in issues:
                key = issue["key"]
                fields = issue["fields"]
                resumo = fields.get("summary", "—")
                status = fields.get("status", {}).get("name", "—")
                descricao = fields.get("description", "—")

                with st.expander(f"🔧 {resumo} ({key})"):
                    st.markdown(f"**Status:** {status}")
                    st.markdown(f"**Descrição:** {descricao}")

                    subtarefas = buscar_subtarefas(key)
                    if subtarefas:
                        st.markdown("### 🧾 Subtarefas:")
                        for item in subtarefas:
                            st.markdown(f"- **{item['key']}**: {item['fields']['summary']}")
                            desc = item["fields"].get("description", "")
                            if desc:
                                st.markdown(f"  > {desc}")
                    else:
                        st.info("Nenhuma subtarefa encontrada.")
        else:
            st.warning("Nenhuma OS encontrada com essa placa.")
