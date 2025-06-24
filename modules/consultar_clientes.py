import streamlit as st
import requests
import base64
import pandas as pd
from io import BytesIO

# === CONFIG JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def tela_busca_edicao_clientes():
    st.header("🔍 Buscar e Editar Clientes")

    termo = st.text_input("🔎 Buscar por nome (campo summary):")

    if termo:
        jql = f'project = MC AND issuetype = Clientes AND summary ~ "{termo}" ORDER BY created DESC'
    else:
        jql = 'project = MC AND issuetype = Clientes ORDER BY created DESC'

    with st.spinner("🔍 Buscando clientes..."):
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 100}
        response = requests.get(url, headers=JIRA_HEADERS, params=params)

    if response.status_code == 200:
        issues = response.json().get("issues", [])
        if issues:
            st.success(f"✅ {len(issues)} cliente(s) encontrado(s)")

            data = []
            for issue in issues:
                fields = issue["fields"]
                data.append({
                    "Key": issue["key"],
                    "Nome": fields.get("customfield_10038", "—"),
                    "Empresa": fields.get("customfield_10051", "—"),
                    "Telefone": fields.get("customfield_10041", "—"),
                    "E-mail": fields.get("customfield_10042", "—")
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

            for issue in issues:
                key = issue["key"]
                fields = issue["fields"]
                nome = fields.get("customfield_10038", "—")

                if f"editar_{key}" not in st.session_state:
                    st.session_state[f"editar_{key}"] = False

                with st.expander(f"👤 {nome} ({key})"):
                    st.markdown(f"**Empresa:** {fields.get('customfield_10051', '—')}")
                    st.markdown(f"**Telefone:** {fields.get('customfield_10041', '—')}")
                    st.markdown(f"**E-mail:** {fields.get('customfield_10042', '—')}")
                    st.markdown(f"**CPF/CNPJ:** {fields.get('customfield_10040', '—')}")
                    st.markdown(f"**CEP:** {fields.get('customfield_10133', '—')}")
                    st.markdown(f"**Número:** {fields.get('customfield_10139', '—')}")
                    st.markdown(f"**Complemento:** {fields.get('customfield_10044', '—')}")

                    if st.button(f"✏️ Editar {key}", key=f"editar_btn_{key}"):
                        st.session_state[f"editar_{key}"] = True

                    if st.session_state.get(f"editar_{key}", False):
                        cliente = {
                            "key": key,
                            "nome": nome,
                            "cpf": fields.get("customfield_10040", ""),
                            "empresa": fields.get("customfield_10051", ""),
                            "telefone": fields.get("customfield_10041", ""),
                            "email": fields.get("customfield_10042", ""),
                            "cep": fields.get("customfield_10133", ""),
                            "numero": fields.get("customfield_10139", ""),
                            "complemento": fields.get("customfield_10044", "")
                        }

                        # Carrega imagem se houver
                        url_anexo = f"{JIRA_URL}/rest/api/2/issue/{cliente['key']}?fields=attachment"
                        resp_anexo = requests.get(url_anexo, headers=JIRA_HEADERS)
                        foto_url = None
                        if resp_anexo.status_code == 200:
                            anexos = resp_anexo.json()["fields"].get("attachment", [])
                            if anexos:
                                foto_url = anexos[0]["content"]

                        if foto_url:
                            resp_img = requests.get(foto_url, headers=JIRA_HEADERS)
                            if resp_img.status_code == 200:
                                st.image(BytesIO(resp_img.content), width=200, caption="📸 Foto atual do cliente")

                        st.subheader(f"✏️ Editar Cliente: {cliente['nome']} ({cliente['key']})")
                        with st.form(f"form_edicao_{key}"):
                            nome = st.text_input("Nome:", value=cliente["nome"])
                            cpf = st.text_input("CPF/CNPJ:", value=cliente["cpf"])
                            empresa = st.text_input("Empresa:", value=cliente["empresa"])
                            telefone = st.text_input("Telefone:", value=cliente["telefone"])
                            email = st.text_input("E-mail:", value=cliente["email"])
                            cep = st.text_input("CEP:", value=cliente["cep"])
                            numero = st.text_input("Nº:", value=cliente["numero"])
                            complemento = st.text_input("Complemento:", value=cliente["complemento"])
                            salvar = st.form_submit_button("💾 Salvar alterações")

                        if salvar:
                            payload = {
                                "fields": {
                                    "summary": nome,
                                    "customfield_10038": nome,
                                    "customfield_10040": cpf,
                                    "customfield_10051": empresa,
                                    "customfield_10041": telefone,
                                    "customfield_10042": email,
                                    "customfield_10133": cep,
                                    "customfield_10139": numero,
                                    "customfield_10044": complemento,
                                }
                            }
                            url_update = f"{JIRA_URL}/rest/api/2/issue/{cliente['key']}"
                            resp = requests.put(url_update, headers=JIRA_HEADERS, json=payload)
                            if resp.status_code == 204:
                                st.success("✅ Cliente atualizado com sucesso!")
                                st.session_state[f"editar_{key}"] = False
                            else:
                                st.error(f"Erro ao atualizar cliente: {resp.text}")
        else:
            st.warning("Nenhum cliente encontrado.")
    else:
        st.error(f"Erro ao buscar clientes: {response.text}")
