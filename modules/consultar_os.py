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

    def buscar_todas_os():
        jql = 'project = MC AND issuetype = "OS" ORDER BY created DESC'
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 100, "fields": "summary,description,status"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        else:
            st.error(f"Erro ao buscar OS: {r.status_code}")
            return []

    def buscar_subtarefas(os_key):
        url = f"{JIRA_URL}/rest/api/2/search"
        jql = f'parent = {os_key}'
        params = {"jql": jql, "fields": "summary,description"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        return []

    # === BUSCA INICIAL ===
    with st.spinner("🔍 Carregando Ordens de Serviço..."):
        issues = buscar_todas_os()

    if not issues:
        st.warning("Nenhuma OS encontrada.")
        return

    # === MONTA DATAFRAME ===
    lista_os = []
    mapa_os = {}
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"].get("summary", "")
        status = issue["fields"].get("status", {}).get("name", "")
        descricao = issue["fields"].get("description", "")
        lista_os.append({
            "Key": key,
            "Resumo": summary,
            "Status": status,
            "Descrição": descricao
        })
        mapa_os[key] = issue  # salva para expanders

    df_os = pd.DataFrame(lista_os)

    # === CAMPO DE BUSCA LOCAL ===
    termo = st.text_input("🔎 Buscar OS por resumo ou status:")

    if termo:
        df_filtrado = df_os[df_os.apply(lambda row: termo.lower() in str(row["Resumo"]).lower() or termo.lower() in str(row["Status"]).lower(), axis=1)]
    else:
        df_filtrado = df_os

    st.success(f"✅ {len(df_filtrado)} OS encontrada(s)")
    st.dataframe(df_filtrado, use_container_width=True)

    # === EXPANSORES ===
    for _, row in df_filtrado.iterrows():
        key = row["Key"]
        resumo = row["Resumo"]
        status = row["Status"]
        descricao = row["Descrição"]
        issue = mapa_os[key]

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
