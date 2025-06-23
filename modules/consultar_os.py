import streamlit as st
import requests
import base64

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

    def buscar_oss():
        """
        Busca todas as ordens de serviço (OS) no Jira.
        """
        jql = 'project = MC AND issuetype = "OS" ORDER BY created DESC'
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 50, "fields": "summary,description,status,customfield_10134,customfield_10041,customfield_10140,customfield_10136,customfield_10138"}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json().get("issues", [])
        else:
            st.error(f"Erro ao buscar OS: {r.status_code} - {r.text}")
            return []

    def buscar_subtarefas(os_key):
        """
        Busca as subtarefas associadas a uma ordem de serviço (OS).
        """
        url = f"{JIRA_URL}/rest/api/2/search"
        jql = f'parent = {os_key}'
        params = {"jql": jql, "fields": "summary,description"}
        r = requests.get(url, headers=HEADERS, params=params)
        
        if r.status_code == 200:
            data = r.json()
            issues = data.get("issues", [])
            return issues
        else:
            st.error(f"Erro ao buscar subtarefas: {r.status_code} - {r.text}")
            return []

    def buscar_transicoes(issue_key):
        """
        Busca as transições disponíveis para uma issue específica.
        """
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.json().get("transitions", [])
        else:
            st.error(f"Erro ao buscar transições: {r.status_code} - {r.text}")
            return []

    def aplicar_edicao(issue_key, campos, status_id=None):
        """
        Aplica as alterações em uma issue e, opcionalmente, altera seu status.
        """
        payload = {"fields": campos}
        url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
        r1 = requests.put(url, headers=HEADERS, json=payload)

        if status_id:
            url_transition = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/transitions"
            payload_transition = {"transition": {"id": status_id}}
            requests.post(url_transition, headers=HEADERS, json=payload_transition)

        return r1.status_code == 204

    # Busca todas as OS
    oss = buscar_oss()
    termo_busca = st.text_input("🔍 Buscar OS", placeholder="Resumo, descrição, placa, telefone, marca, modelo, ano")

    for os_item in oss:
        campos = os_item["fields"]
        key = os_item["key"]
        resumo = campos.get("summary", "")
        desc = campos.get("description", "")
        status = campos.get("status", {}).get("name", "")
        placa = campos.get("customfield_10134", "")
        telefone = campos.get("customfield_10041", "")
        marca = campos.get("customfield_10140", {}).get("value", "")
        modelo = campos.get("customfield_10136", "")
        ano = campos.get("customfield_10138", "")

        texto_completo = f"{resumo} {desc} {placa} {telefone} {marca} {modelo} {ano}".lower()
        if termo_busca.lower() not in texto_completo:
            continue

        with st.expander(f"🔧 {key} - {resumo} [{status}]"):
            st.markdown(f"**Descrição:** {desc}")
            st.markdown(f"**Placa:** {placa}  ")
            st.markdown(f"**Telefone:** {telefone}  ")
            st.markdown(f"**Marca:** {marca}  ")
            st.markdown(f"**Modelo:** {modelo}  ")
            st.markdown(f"**Ano:** {ano}  ")

            # Busca e exibe subtarefas
            subtarefas = buscar_subtarefas(key)
            st.write("Subtarefas retornadas pela API:", subtarefas)  # Log temporário para depuração
            if subtarefas:
                st.markdown("---")
                st.subheader("🧾 Subtarefas")
                for sub in subtarefas:
                    sub_key = sub["key"]
                    sub_summary = sub["fields"].get("summary", "Sem resumo")
                    sub_description = sub["fields"].get("description", "Sem descrição")
                    st.markdown(f"**{sub_key} - {sub_summary}**")
                    st.markdown(f"> {sub_description}")
            else:
                st.markdown("_Nenhuma subtarefa encontrada._")

            if st.button(f"✏️ Editar {key}", key=f"editar_{key}"):
                st.session_state["editar_os"] = {
                    "key": key,
                    "resumo": resumo,
                    "desc": desc,
                    "placa": placa,
                    "telefone": telefone,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano,
                    "status": status
                }

    if "editar_os" in st.session_state:
        os = st.session_state["editar_os"]
        st.markdown("---")
        st.subheader(f"📝 Editar OS {os['key']}")
        with st.form("form_edicao"):
            novo_resumo = st.text_input("Resumo", os["resumo"])
            nova_desc = st.text_area("Descrição", os["desc"])
            nova_placa = st.text_input("Placa", os["placa"])
            novo_tel = st.text_input("Telefone", os["telefone"])
            nova_marca = st.text_input("Marca", os["marca"])
            novo_modelo = st.text_input("Modelo", os["modelo"])
            novo_ano = st.text_input("Ano", os["ano"])

            transicoes = buscar_transicoes(os["key"])
            opcoes_status = {t["name"]: t["id"] for t in transicoes}
            novo_status_nome = st.selectbox("Status", list(opcoes_status.keys()), index=list(opcoes_status.keys()).index(os["status"]) if os["status"] in opcoes_status else 0)
            novo_status_id = opcoes_status.get(novo_status_nome)

            col1, col2 = st.columns(2)
            with col1:
                salvar = st.form_submit_button("💾 Salvar alterações")
            with col2:
                cancelar = st.form_submit_button("❌ Cancelar")

        if salvar:
            campos_atualizados = {
                "summary": novo_resumo,
                "description": nova_desc,
                "customfield_10134": nova_placa,
                "customfield_10041": novo_tel,
                "customfield_10140": {"value": nova_marca},
                "customfield_10136": novo_modelo,
                "customfield_10138": novo_ano
            }
            sucesso = aplicar_edicao(os["key"], campos_atualizados, status_id=novo_status_id)
            if sucesso:
                st.success("OS atualizada com sucesso!")
                del st.session_state["editar_os"]
                st.rerun()
            else:
                st.error("Erro ao atualizar OS.")

        if cancelar:
            del st.session_state["editar_os"]
            st.rerun()

# Executa a interface
if __name__ == "__main__":
    tela_consulta_os()
