import streamlit as st
import requests
import base64
import unicodedata
import re

# === CONFIGURAÇÃO DO JIRA ===
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
    cep_limpo = re.sub(r'\D', '', cep)
    if len(cep_limpo) != 8:
        return None

    try:
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"   
        headers = {"User-Agent": "Mozilla/5.0"}  # Evita bloqueio por falta de User-Agent
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("erro"):
                st.warning("⚠️ CEP não encontrado.")
                return None
            return {
                'logradouro': data.get('logradouro', '').strip() or '(Sem logradouro)',
                'bairro': data.get('bairro', '').strip() or '(Sem bairro)',
                'localidade': data.get('localidade', '').strip() or '(Sem cidade)',
                'uf': data.get('uf', '').strip() or '(Sem UF)'
            }
        else:
            st.error(f"❌ Erro ao acessar ViaCEP: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"🚨 Erro na conexão com o ViaCEP: {e}")
        return None

def cpf_cnpj_existe(cpf_cnpj):
    jql = f'project=MC AND customfield_10040="{cpf_cnpj}"'
    url = f"{JIRA_URL}/rest/api/2/search"
    payload = {"jql": jql, "maxResults": 1}
    try:
        response = requests.post(url, json=payload, headers=JIRA_HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("total", 0) > 0
        else:
            st.warning("⚠️ Erro na conexão com o Jira.")
            return False
    except Exception as e:
        st.error(f"🚨 Erro ao verificar CPF/CNPJ: {e}")
        return False

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
    try:
        response = requests.post(
            f"{JIRA_URL}/rest/api/2/issue",
            json=payload,
            headers=JIRA_HEADERS,
            timeout=10
        )
        if response.status_code == 201:
            return True, response.json().get("key")
        else:
            st.error(f"❌ Erro ao criar issue: {response.text}")
            return False, None
    except Exception as e:
        st.error(f"🚨 Erro ao conectar ao Jira: {e}")
        return False, None

def anexar_foto(issue_key, imagem):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    headers = {
        "Authorization": JIRA_HEADERS["Authorization"],
        "X-Atlassian-Token": "no-check"
    }
    files = {"file": (imagem.name, imagem.getvalue())}
    try:
        response = requests.post(url, headers=headers, files=files, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"🚨 Erro ao anexar foto: {e}")
        return False

# === TELA DE CLIENTES ===
def tela_clientes():
    st.header("👤 Cadastro e Consulta de Clientes")

    if "form_confirmado" not in st.session_state:
        st.session_state.form_confirmado = False
    if "dados_cliente" not in st.session_state:
        st.session_state.dados_cliente = {}

    with st.expander("🔍 Consultar Cliente por CPF/CNPJ"):
        cpf_busca = st.text_input("Digite o CPF ou CNPJ:")
        if st.button("Buscar no Jira"):
            if cpf_busca:
                with st.spinner("Procurando no Jira..."):
                    if cpf_cnpj_existe(cpf_busca):
                        st.success(f"✅ CPF/CNPJ {cpf_busca} já está cadastrado no Jira.")
                    else:
                        st.info(f"❌ CPF/CNPJ {cpf_busca} ainda não foi cadastrado.")
            else:
                st.warning("⚠️ Digite um CPF/CNPJ válido.")

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

            endereco = buscar_cep(cep) if cep and len(re.sub(r'\D', '', cep)) == 8 else None
            if endereco:
                st.success(f"📍 Endereço: {endereco['logradouro']}, {endereco['bairro']}, {endereco['localidade']}/{endereco['uf']}")
            elif cep:
                st.warning("⚠️ CEP não encontrado ou inválido.")

        confirmar = st.form_submit_button("✅ Confirmar Dados")

    if confirmar:
        if not all([nome, cpf_cnpj, empresa, telefone, email, cep, numero]):
            st.warning("⚠️ Preencha todos os campos obrigatórios!")
            return

        endereco = buscar_cep(cep)
        if not endereco:
            st.error("❌ CEP inválido ou não encontrado. Não é possível continuar.")
            return

        endereco_formatado = f"{endereco['logradouro']} - {endereco['bairro']} - {endereco['localidade']}/{endereco['uf']}, nº {numero}"

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
            with st.spinner("Verificando se o CPF/CNPJ já existe..."):
                if cpf_cnpj_existe(dados['cpf']):
                    st.warning("⚠️ Já existe um cliente cadastrado com este CPF/CNPJ!")
                    return

                with st.spinner("Enviando para o Jira..."):
                    sucesso, key = criar_issue_jira(
                        dados['nome'], dados['cpf'], dados['empresa'], dados['telefone'],
                        dados['email'], dados['cep'], dados['numero'], dados['complemento'],
                        dados['endereco_formatado']
                    )
                    if sucesso:
                        if dados['imagem']:
                            anexar_foto(key, dados['imagem'])
                        st.success(f"✅ Cliente criado com sucesso: [{key}]({JIRA_URL}/browse/{key})")
                        st.session_state.form_confirmado = False
                        st.session_state.dados_cliente = {}
                        st.rerun()
                    else:
                        st.error("❌ Erro ao cadastrar cliente. Verifique os dados e tente novamente.")

# === EXECUÇÃO PRINCIPAL ===
if __name__ == "__main__":
    tela_clientes()
