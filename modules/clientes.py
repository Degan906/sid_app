import streamlit as st
import requests
import unicodedata
import re
import base64

# === CONFIGURAÇÕES DO JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === Funções auxiliares ===
def criar_issue_jira(nome, cpf, empresa, telefone, email, cep, numero, complemento, endereco_formatado):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "summary": nome,
            "issuetype": {"name": "Clientes"},
            "customfield_10038": nome,
            "customfield_10040": cpf,
            "customfield_10051": empresa,
            "customfield_10041": telefone,
            "customfield_10042": email,
            "customfield_10133": cep,
            "customfield_10039": "",
            "customfield_10044": complemento,
            "customfield_10139": numero,
            "description": endereco_formatado
        }
    }
    response = requests.post(f"{JIRA_URL}/rest/api/2/issue", json=payload, headers=JIRA_HEADERS)
    if response.status_code == 201:
        return response.json().get("key")
    else:
        st.error(f"Erro ao criar cliente: {response.status_code} - {response.text}")
        return None

def anexar_foto(issue_key, imagem):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    headers = {
        "Authorization": JIRA_HEADERS["Authorization"],
        "X-Atlassian-Token": "no-check"
    }
    files = {"file": (imagem.name, imagem.getvalue())}
    response = requests.post(url, headers=headers, files=files)
    return response.status_code == 200

def tela_clientes():
    st.header("👤 Cadastro de Clientes")

    def validar_email(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    def mascarar_documento(valor):
        valor = re.sub(r'\D', '', valor)
        if len(valor) <= 11:
            return f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"
        else:
            return f"{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}"

    def buscar_cep(cep):
        cep = re.sub(r'\D', '', cep)
        if len(cep) == 8:
            resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
            if resp.status_code == 200 and "erro" not in resp.text:
                return resp.json()
        return None

    def cliente_duplicado(cpf, email):
        jql = f'project = MC AND issuetype = Clientes AND (customfield_10040 ~ "{cpf}" OR customfield_10042 ~ "{email}")'
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {"jql": jql, "maxResults": 1}
        resp = requests.get(url, headers=JIRA_HEADERS, params=params)
        return resp.status_code == 200 and resp.json().get("issues")

    with st.form("form_cliente"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome do Cliente *").strip()
            documento = st.text_input("CPF ou CNPJ *")
            telefone = st.text_input("Telefone *", placeholder="(00) 00000-0000")
            email = st.text_input("E-mail *")
            empresa = st.text_input("Empresa")

        with col2:
            cep = st.text_input("CEP *")
            numero = st.text_input("Número")
            complemento = st.text_input("Complemento")
            imagem = st.file_uploader("Foto do cliente", type=["jpg", "png", "jpeg"])

            cep_limpo = re.sub(r'\D', '', cep)
            endereco = buscar_cep(cep_limpo) if len(cep_limpo) == 8 else None

            if endereco:
                st.text_input("Logradouro", value=endereco.get("logradouro", ""), disabled=True)
                st.text_input("Bairro", value=endereco.get("bairro", ""), disabled=True)
                st.text_input("Cidade", value=endereco.get("localidade", ""), disabled=True)
                st.text_input("UF", value=endereco.get("uf", ""), disabled=True)
            elif cep_limpo:
                st.warning("⚠️ CEP inválido ou não encontrado.")

        confirmar = st.form_submit_button("✅ Confirmar dados")

    if confirmar:
        erros = []
        if not nome:
            erros.append("Nome é obrigatório.")
        if not documento:
            erros.append("CPF ou CNPJ é obrigatório.")
        if not telefone:
            erros.append("Telefone é obrigatório.")
        if not email or not validar_email(email):
            erros.append("E-mail inválido.")
        if not cep or not buscar_cep(cep):
            erros.append("CEP inválido ou não encontrado.")

        if erros:
            for erro in erros:
                st.error(f"❌ {erro}")
            return

        doc_formatado = mascarar_documento(documento)
        endereco_formatado = (
            f"{endereco['logradouro']} - {endereco['bairro']} - "
            f"{endereco['localidade']}/{endereco['uf']}, nº {numero}"
            if endereco else f"CEP: {cep}, Nº: {numero}, Compl: {complemento}"
        )

        st.markdown("### 📄 Resumo do cadastro")
        st.markdown(f"**Nome:** {nome}")
        st.markdown(f"**Documento:** {doc_formatado}")
        st.markdown(f"**Telefone:** {telefone}")
        st.markdown(f"**E-mail:** {email}")
        st.markdown(f"**Empresa:** {empresa}")
        st.markdown(f"**Endereço:** {endereco_formatado}")
        if imagem:
            st.image(imagem, width=160)

        if cliente_duplicado(documento, email):
            st.warning("⚠️ Já existe um cliente com esse CPF ou E-mail no sistema!")

        if st.button("🚀 Deseja realmente cadastrar este cliente?"):
            with st.spinner("Enviando para o Jira..."):
                issue_key = criar_issue_jira(
                    nome, doc_formatado, empresa, telefone, email,
                    cep, numero, complemento, endereco_formatado
                )
                if issue_key:
                    if imagem:
                        if not anexar_foto(issue_key, imagem):
                            st.warning("⚠️ Cliente criado, mas não foi possível anexar a foto.")
                    st.success(f"🎉 Cliente criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
