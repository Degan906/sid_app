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
    st.header("🔧 Consultar e Editar Ordens de Serviço (OS)")

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

    def buscar_transicoes(issue_key):
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.json().get("transitions", [])
        return []

    def aplicar_edicao(issue_key, campos):
        payload = {"fields": campos}
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
        r = requests.put(url, headers=HEADERS, json=payload)
        return r.status_code == 204

    def aplicar_transicao(issue_key, transition_id):
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}
        r = requests.post(url, headers=HEADERS, json=payload)
        return r.status_code == 204

    with st.spinner("🔍 Carregando OS..."):
        issues = buscar_todas_os()

    if not issues:
        st.warning("Nenhuma OS encontrada.")
        return

    lista_os = []
    mapa_os = {}
    for issue in issues:
        fields = issue["fields"]
        key = issue["key"]
        lista_os.append({
            "Key": key,
            "Resumo": fields.get("summary", ""),
            "Status": fields.get("status", {}).get("name", ""),
            "Descrição": fields.get("description", ""),
            "Placa": fields.get("customfield_10134", ""),
            "Telefone": fields.get("customfield_10041", ""),
            "Marca": fields.get("customfield_10140", {}).get("value", "") if fields.get("customfield_10140") else "",
            "Modelo": fields.get("customfield_10136", ""),
            "Ano": fields.get("customfield_10138", "")
        })
        mapa_os[key] = issue

    df_os = pd.DataFrame(lista_os)
    termo = st.text_input("🔎 Buscar por qualquer campo da OS:")

    if termo:
        termo_lower = termo.lower()
        df_filtrado = df_os[df_os.apply(
            lambda row: any(termo_lower in str(val).lower() for val in row), axis=1
        )]
    else:
        df_filtrado = df_os

    st.success(f"✅ {len(df_filtrado)} OS encontrada(s)")
    st.dataframe(df_filtrado, use_container_width=True)

    for _, row in df_filtrado.iterrows():
        key = row["Key"]
        issue = mapa_os[key]
        fields = issue["fields"]

        with st.expander(f"🔧 {row['Resumo']} ({key})"):
            with st.form(f"form_{key}"):
                resumo = st.text_input("Resumo", value=row["Resumo"])
                descricao = st.text_area("Descrição", value=row["Descrição"], height=150)
                placa = st.text_input("Placa", value=row["Placa"])
                telefone = st.text_input("Telefone", value=row["Telefone"])
                marca = st.text_input("Marca", value=row["Marca"])
                modelo = st.text_input("Modelo", value=row["Modelo"])
                ano = st.text_input("Ano", value=row["Ano"])

                transicoes = buscar_transicoes(key)
                status_atual = fields.get("status", {}).get("name", "")
                opcoes_status = {t["name"]: t["id"] for t in transicoes}
                status_escolhido = st.selectbox("Status", [status_atual] + list(opcoes_status.keys()))

                salvar = st.form_submit_button("💾 Salvar alterações")

                if salvar:
                    campos = {
                        "summary": resumo,
                        "description": descricao,
                        "customfield_10134": placa,
                        "customfield_10041": telefone,
                        "customfield_10140": {"value": marca} if marca else None,
                        "customfield_10136": modelo,
                        "customfield_10138": ano
                    }
                    campos = {k: v for k, v in campos.items() if v is not None}
                    sucesso_edicao = aplicar_edicao(key, campos)

                    sucesso_status = True
                    if status_escolhido != status_atual and status_escolhido in opcoes_status:
                        sucesso_status = aplicar_transicao(key, opcoes_status[status_escolhido])

                    if sucesso_edicao and sucesso_status:
                        st.success("✅ OS atualizada com sucesso!")
                    else:
                        st.error("❌ Erro ao atualizar a OS.")
