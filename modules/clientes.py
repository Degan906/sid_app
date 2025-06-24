import streamlit as st
import requests
import base64
import unicodedata
import re

# === CONFIGURAÇÕES DO JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === FUNÇÕES AUXILIARES ===
def corrige_abnt(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    texto = ' '.join(word.capitalize() for word in texto.split())
    return texto

def buscar_cep(cep):
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        if resp.status_code == 200:
            return resp.json()
    except:
        return None
    return None

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
            "customfield_10044": complemento,
            "customfield_10139": numero,
            "description": endereco_formatado
        }
    }
    response = requests.post(f"{JIRA_URL}/rest/api/2/issue", json=payload, headers=JIRA_HEADERS)
    if response.status_code == 201:
        return response.json().get("key")
    else:
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

# === TELA DE CADASTRO DE CLIENTE ===
def tela_clientes():
    st.header("👤 Cadastro de Cliente")

    with st.form("form_cliente"):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome *")
            doc = st.text_input("CPF/CNPJ *")
            empresa = st.text_input("Empresa")
            telefone = st.text_input("Telefone *")
            email = st.text_input("E-mail *")

        with col2:
            cep = st.text_input("CEP *", key="cep_input")
            cep_limpo = re.sub(r'\D', '', cep)
            endereco = buscar_cep(cep_limpo) if len(cep_limpo) == 8 else None
            numero = st.text_input("Número *")
            complemento = st.text_input("Complemento")
            imagem = st.file_uploader("Foto do cliente (opcional)", type=["png", "jpg", "jpeg"])

        if endereco:
            st.markdown("#### 📍 Endereço detectado:")
            st.markdown(f"""
            <ul style='line-height: 1.6'>
                <li><strong>Logradouro:</strong> {endereco.get('logradouro')}</li>
                <li><strong>Bairro:</strong> {endereco.get('bairro')}</li>
                <li><strong>Cidade:</strong> {endereco.get('localidade')} - {endereco.get('uf')}</li>
            </ul>
            """, unsafe_allow_html=True)
        elif len(cep_limpo) == 8:
            st.error("❌ CEP inválido ou não encontrado.")

        submitted = st.form_submit_button("🚀 Deseja realmente cadastrar este cliente?")

    if submitted:
        if not all([nome, doc, telefone, email, cep, numero]):
            st.error("⚠️ Por favor, preencha todos os campos obrigatórios.")
            return

        nome = corrige_abnt(nome)
        empresa = corrige_abnt(empresa)

        endereco_formatado = ""
        if endereco:
            endereco_formatado = f"{endereco.get('logradouro')} - {endereco.get('bairro')} - {endereco.get('localidade')}/{endereco.get('uf')}, nº {numero}"
        else:
            endereco_formatado = f"CEP: {cep}, Nº: {numero}, Compl: {complemento}"

        with st.spinner("Enviando para o Jira..."):
            issue_key = criar_issue_jira(
                nome, doc, empresa, telefone, email,
                cep, numero, complemento, endereco_formatado
            )

        if issue_key:
            if imagem:
                if not anexar_foto(issue_key, imagem):
                    st.warning("⚠️ Cliente criado, mas não foi possível anexar a foto.")

            st.success(f"🎉 Cliente criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
            st.balloons()
            st.experimental_rerun()
        else:
            st.error("❌ Erro ao cadastrar cliente. Verifique os dados ou tente novamente.")
