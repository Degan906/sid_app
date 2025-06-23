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
        params = {
            "jql": jql,
            "maxResults": 100,
            "fields": "summary,description,status,customfield_10134,customfield_10041,customfield_10140,customfield_10136,customfield_10138"
        }
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

    with st.spinner("🔍 Carregando Ordens de Serviço..."):
        issues = buscar_todas_os()

    if not issues:
        st.warning("Nenhuma OS encontrada.")
        return

    # === MONTA DATAFRAME COMPLETO ===
    lista_os = []
    mapa_os = {}
    for issue in issues:
        fields = issue["fields"]
        key = issue["key"]
        resumo = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        descricao = fields.get("description", "")
        placa = fields.get("customfield_10134", "")
        telefone = fields.get("customfield_10041", "")
        marca = fields.get("customfield_10140", {}).get("value", "") if fields.get("customfield_10140") else ""
        modelo = fields.get("customfield_10136", "")
        ano = fields.get("customfield_10138", "")

        lista_os.append({
            "Key": key,
            "Resumo": resumo,
            "Descrição": descricao,
            "Status": status,
            "Placa": placa,
            "Telefone": telefone,
            "Marca": marca,
            "Modelo": modelo,
            "Ano": ano
        })
        mapa_os[key] = issue

    df_os = pd.DataFrame(lista_os)

    # === BUSCA LOCAL POR QUALQUER CAMPO ===
    termo = st.text_input("🔎 Buscar por Resumo, Descrição, Placa, Telefone, Marca, Modelo ou Ano:")

    if termo:
        termo_lower = termo.lower()
        df_filtrado = df_os[df_os.apply(
            lambda row: any(termo_lower in str(value).lower() for value in [
                row["Resumo"], row["Descrição"], row["Placa"], row["Telefone"], row["Marca"], row["Modelo"], row["Ano"]
            ]),
            axis=1
        )]
    else:
        df_filtrado = df_os

    st.success(f"✅ {len(df_filtrado)} OS encontrada(s)")
    st.dataframe(df_filtrado, use_container_width=True)

    # === EXPANSORES COM DETALHES ===
    for _, row in df_filtrado.iterrows():
        key = row["Key"]
        resumo = row["Resumo"]
        status = row["Status"]
        descricao = row["Descrição"]
        placa = row["Placa"]
        telefone = row["Telefone"]
        marca = row["Marca"]
        modelo = row["Modelo"]
        ano = row["Ano"]

        with st.expander(f"🔧 {resumo} ({key})"):
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Descrição:** {descricao}")
            st.markdown(f"**Placa:** {placa}")
            st.markdown(f"**Telefone:** {telefone}")
            st.markdown(f"**Marca:** {marca}")
            st.markdown(f"**Modelo:** {modelo}")
            st.markdown(f"**Ano:** {ano}")

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
