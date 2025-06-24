import streamlit as st
import requests
import base64
import unicodedata
import re

# === CONFIG JIRA ===
JIRA_URL = "https://hcdconsultoria.atlassian.net"
JIRA_EMAIL = "degan906@gmail.com"
JIRA_API_TOKEN = "glUQTNZG0V1uYnrRjp9yBB17"
JIRA_HEADERS = {
    "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === Funções auxiliares ===
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

# === Tela de cadastro de clientes ===
def tela_clientes():
    st.header("👤 Cadastro de Clientes")

    if "form_confirmado" not in st.session_state:
        st.session_state.form_confirmado = False
    if "dados_cliente" not in st.session_state:
        st.session_state.dados_cliente = {}

    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Cliente:")
            cpf_cnpj = st.text_input("CPF/CNPJ:")
            empresa = st.text_input("Empresa:")
            telefone = st.text_input("Telefone:")
            email = st.text_input("E-mail:")
        with col2:
            cep = st.text_input("CEP:")
            numero = st.text_input("Número:")
            complemento = st.text_input("Complemento:")
            imagem = st.file_uploader("Foto do Cliente:", type=["png", "jpg", "jpeg"])

        confirmar = st.form_submit_button("✅ Confirmar Dados")

    if confirmar:
        if not all([nome, cpf_cnpj, empresa, telefone, email, cep, numero]):
            st.warning("⚠️ Preencha todos os campos obrigatórios!")
            return

        endereco = buscar_cep(re.sub(r'\D', '', cep))
        if endereco and not endereco.get("erro"):
            endereco_formatado = f"{endereco['logradouro']} - {endereco['bairro']} - {endereco['localidade']}/{endereco['uf']}, nº {numero}"
        else:
            endereco_formatado = f"CEP: {cep}, Nº: {numero}, Compl: {complemento}"

        st.session_state.form_confirmado = True
        st.session_state.dados_cliente = {
            "nome": corrige_abnt(nome),
            "cpf": cpf_cnpj,
            "empresa": corrige_abnt(empresa),
            "telefone": telefone,
            "email": email,
            "cep": cep,
            "numero": numero,
            "complemento": complemento,
            "endereco_formatado": endereco_formatado,
            "imagem": imagem
        }

    if st.session_state.form_confirmado:
        dados = st.session_state.dados_cliente
        st.markdown("### 📋 Confirme os dados abaixo")
        st.markdown(f"**Nome:** {dados['nome']}")
        st.markdown(f"**CPF/CNPJ:** {dados['cpf']}")
        st.markdown(f"**Empresa:** {dados['empresa']}")
        st.markdown(f"**Telefone:** {dados['telefone']}")
        st.markdown(f"**E-mail:** {dados['email']}")
        st.markdown(f"**Endereço:** {dados['endereco_formatado']}")

        if dados['imagem']:
            st.image(dados['imagem'], width=150)

        if st.button("🚀 Deseja realmente cadastrar este cliente?"):
            with st.spinner("Enviando para o Jira..."):
                key = criar_issue_jira(
                    dados['nome'], dados['cpf'], dados['empresa'], dados['telefone'],
                    dados['email'], dados['cep'], dados['numero'], dados['complemento'],
                    dados['endereco_formatado']
                )
                if key:
                    if dados['imagem']:
                        anexar_foto(key, dados['imagem'])
                    st.success(f"✅ Cliente criado com sucesso: [{key}]({JIRA_URL}/browse/{key})")
                    st.session_state.form_confirmado = False
                    st.session_state.dados_cliente = {}
                    st.experimental_rerun()
                else:
                    st.error("❌ Erro ao cadastrar cliente. Verifique os dados e tente novamente.")
