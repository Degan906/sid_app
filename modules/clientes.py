import streamlit as st
import requests
from datetime import datetime
import base64
from modules.utils import corrigir_abnt, buscar_endereco_por_cep

# === Configurações do Jira ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
API_URL = f"{JIRA_URL}/rest/api/2"
EMAIL = "degan906@gmail.com"
TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
PROJECT_KEY = "MC"
ISSUE_TYPE = "Clientes"
HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{EMAIL}:{TOKEN}'.encode()).decode()}",
    "Content-Type": "application/json"
}

# === Função para criar cliente ===
def criar_cliente(payload, foto):
    resposta = requests.post(f"{API_URL}/issue", headers=HEADERS, json=payload)
    if resposta.status_code == 201:
        issue_key = resposta.json()["key"]
        if foto:
            upload_url = f"{API_URL}/issue/{issue_key}/attachments"
            files = {"file": (foto.name, foto.getvalue())}
            headers_upload = HEADERS.copy()
            headers_upload.pop("Content-Type")
            headers_upload["X-Atlassian-Token"] = "no-check"
            requests.post(upload_url, headers=headers_upload, files=files)
        return True, issue_key
    else:
        return False, resposta.text

# === Tela principal ===
def tela_clientes():
    st.subheader("👤 Cadastro de Clientes")

    with st.form("form_cliente"):
        nome = st.text_input("Nome completo:")
        cpf_cnpj = st.text_input("CPF/CNPJ:")
        empresa = st.text_input("Empresa:")
        telefone = st.text_input("Telefone:")
        email = st.text_input("E-mail:")

        col1, col2 = st.columns([2, 1])
        with col1:
            cep = st.text_input("CEP:")
            numero = st.text_input("Número:")
            complemento = st.text_input("Complemento:")
            buscar = st.form_submit_button("🔍 Buscar Endereço")
        with col2:
            foto = st.file_uploader("Foto do Cliente:", type=["png", "jpg", "jpeg"])

        endereco = ""
        if buscar and cep:
            endereco = buscar_endereco_por_cep(cep)
            if endereco:
                st.success(f"Endereço localizado: {endereco}")
            else:
                st.warning("CEP não encontrado.")

        confirmar = st.form_submit_button("✅ Confirmar cadastro")

    if confirmar:
        nome_abnt = corrigir_abnt(nome)
        endereco_formatado = f"{endereco} - nº {numero}, {complemento}" if endereco else "Não informado"

        with st.expander("📋 Resumo do cadastro gerado", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"""
                **Nome:** {nome_abnt}  
                **CPF/CNPJ:** {cpf_cnpj}  
                **Empresa:** {empresa}  
                **Telefone:** {telefone}  
                **E-mail:** {email}  
                **Endereço:** {endereco_formatado}
                """)
            with col2:
                if foto:
                    st.image(foto, width=150, caption="Foto selecionada")

        # Monta o payload da issue
        payload = {
            "fields": {
                "project": {"key": PROJECT_KEY},
                "issuetype": {"name": ISSUE_TYPE},
                "summary": nome_abnt,
                "customfield_10038": nome_abnt,
                "customfield_10040": cpf_cnpj,
                "customfield_10051": empresa,
                "customfield_10041": telefone,
                "customfield_10042": email,
                "customfield_10133": cep,
                "customfield_10044": complemento,
                "customfield_10139": numero,
                "description": f"Cliente cadastrado via SID em {datetime.now().strftime('%d/%m/%Y')}"
            }
        }

        sucesso, retorno = criar_cliente(payload, foto)
        if sucesso:
            st.success(f"✅ Cliente criado com sucesso no Jira! Issue: {retorno}")
        else:
            st.error(f"Erro ao criar cliente: {retorno}")
