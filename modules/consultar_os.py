import streamlit as st
import requests
import base64
import re

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

    # === FUNÇÕES AUXILIARES ===
    def buscar_os_por_id(os_key):
        url = f"{JIRA_URL}/rest/api/2/issue/{os_key}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.json()
        return None

    def buscar_os_por_placa(placa):
        jql = f'project = MC AND issuetype = "OS" AND description ~ "{placa}" ORDER BY created DESC'
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 5, "fields": "summary,description,status"}
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

    def atualizar_descricao_os(issue_key, nova_descricao):
        payload = {"fields": {"description": nova_descricao}}
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
        r = requests.put(url, headers=HEADERS, json=payload)
        return r.status_code == 204

    # === INTERFACE ===
    modo_busca = st.radio("Buscar OS por:", ["ID da OS", "Placa do veículo"])

    if modo_busca == "ID da OS":
        os_id = st.text_input("Digite a ID da OS (ex: MC-123)")
        if os_id and st.button("🔍 Buscar OS"):
            os_data = buscar_os_por_id(os_id)
            if os_data:
                st.success(f"OS {os_id} encontrada.")
                st.subheader("📋 Dados da OS")
                summary = os_data["fields"]["summary"]
                descricao = os_data["fields"].get("description", "")
                status = os_data["fields"]["status"]["name"]

                nova_desc = st.text_area("Descrição", value=descricao, height=200)

                if st.button("💾 Salvar Descrição"):
                    sucesso = atualizar_descricao_os(os_id, nova_desc)
                    if sucesso:
                        st.success("Descrição atualizada com sucesso.")
                    else:
                        st.error("Erro ao atualizar descrição.")

                st.markdown("---")
                st.subheader("🧾 Itens/Subtarefas")
                subtarefas = buscar_subtarefas(os_id)
                if not subtarefas:
                    st.warning("Nenhuma subtarefa encontrada.")
                else:
                    for item in subtarefas:
                        st.markdown(f"**{item['key']} - {item['fields']['summary']}**")
                        desc = item["fields"].get("description", "")
                        st.markdown(f"> {desc}")
                        st.markdown("---")

            else:
                st.error("OS não encontrada.")
    else:
        placa = st.text_input("Digite a placa (ex: ABC1234)")
        if placa and st.button("🔍 Buscar por Placa"):
            resultados = buscar_os_por_placa(placa)
            if not resultados:
                st.warning("Nenhuma OS encontrada com essa placa.")
            else:
                st.success(f"{len(resultados)} OS encontradas.")
                for os_item in resultados:
                    key = os_item["key"]
                    summary = os_item["fields"]["summary"]
                    status = os_item["fields"]["status"]["name"]
                    desc = os_item["fields"].get("description", "")
                    st.markdown(f"### 🔧 {key} - {summary}")
                    st.markdown(f"**Status:** {status}")
                    st.markdown(f"**Descrição:**\n{desc}")
                    st.markdown("---")
