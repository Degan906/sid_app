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

# === FUNÇÕES AUXILIARES ===
def corrige_abnt(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    texto = ' '.join(word.capitalize() for word in texto.split())
    return texto

def buscar_endereco(cep):
    try:
        resposta = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        if resposta.status_code == 200:
            return resposta.json()
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

def buscar_clientes_jira(termo_busca):
    jql = f"""
    project = MC AND issuetype = Clientes AND (
        summary ~ "{termo_busca}" OR
        customfield_10040 ~ "{termo_busca}" OR
        customfield_10041 ~ "{termo_busca}" OR
        customfield_10042 ~ "{termo_busca}"
    ) ORDER BY created DESC
    """
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 50}
    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        st.error(f"Erro ao buscar clientes: {response.text}")
        return []

# === TELA 1: CADASTRO DE CLIENTES ===
def tela_clientes():
    st.header("👤 Cadastro de Clientes")

    if "resumo_confirmado" not in st.session_state:
        st.session_state.resumo_confirmado = False
    if "dados_confirmados" not in st.session_state:
        st.session_state.dados_confirmados = {}

    with st.form("form_cliente"):
        nome = st.text_input("Nome do Cliente:")
        cpf = st.text_input("CPF/CNPJ:")
        empresa = st.text_input("Empresa:")
        telefone = st.text_input("Telefone:")
        email = st.text_input("E-mail:")
        cep = st.text_input("CEP:")
        numero = st.text_input("Nº")
        complemento = st.text_input("Complemento")
        imagem = st.file_uploader("Foto do cliente:", type=["png", "jpg", "jpeg"])
        confirmar = st.form_submit_button("✅ Confirmar Dados")

    if confirmar:
        nome_abnt = corrige_abnt(nome)
        empresa_abnt = corrige_abnt(empresa)
        endereco_obj = buscar_endereco(cep)

        if endereco_obj and not endereco_obj.get("erro"):
            endereco_formatado = f"{endereco_obj['logradouro']} - {endereco_obj['bairro']} - {endereco_obj['localidade']}/{endereco_obj['uf']}, nº {numero}"
        else:
            endereco_formatado = f"CEP: {cep}, Nº: {numero}, Compl: {complemento}"

        st.session_state.resumo_confirmado = True
        st.session_state.dados_confirmados = {
            "nome": nome_abnt,
            "cpf": cpf,
            "empresa": empresa_abnt,
            "telefone": telefone,
            "email": email,
            "cep": cep,
            "numero": numero,
            "complemento": complemento,
            "endereco_formatado": endereco_formatado,
            "imagem": imagem
        }

        st.success("✅ Dados confirmados! Verifique abaixo antes de enviar.")

    if st.session_state.resumo_confirmado:
        dados = st.session_state.dados_confirmados
        st.markdown("### 📄 Resumo do cadastro")
        st.markdown(f"**Nome:** {dados['nome']}")
        st.markdown(f"**CPF/CNPJ:** {dados['cpf']}")
        st.markdown(f"**Empresa:** {dados['empresa']}")
        st.markdown(f"**Telefone:** {dados['telefone']}")
        st.markdown(f"**E-mail:** {dados['email']}")
        st.markdown(f"**Endereço:** {dados['endereco_formatado']}")
        if dados["imagem"]:
            st.image(dados["imagem"], width=160, caption="📸 Foto selecionada")

        if st.button("🚀 Enviar para o Jira"):
            with st.spinner("Enviando para o Jira..."):
                issue_key = criar_issue_jira(
                    dados["nome"], dados["cpf"], dados["empresa"],
                    dados["telefone"], dados["email"], dados["cep"],
                    dados["numero"], dados["complemento"], dados["endereco_formatado"]
                )
                if issue_key:
                    if dados["imagem"]:
                        sucesso_foto = anexar_foto(issue_key, dados["imagem"])
                        if not sucesso_foto:
                            st.warning("⚠️ Cliente criado, mas não foi possível anexar a foto.")
                    st.success(f"🎉 Cliente criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
                    st.session_state.resumo_confirmado = False
                    st.session_state.dados_confirmados = {}

# === TELA 2: BUSCA E EDIÇÃO DE CLIENTES ===
def tela_busca_edicao_clientes():
    st.header("🔍 Buscar e Editar Clientes")

    termo = st.text_input("🔎 Buscar por nome (campo summary):")

    # Define a JQL padrão (todos os clientes)
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

            # Monta tabela
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

            # Expansores individuais para edição
            for issue in issues:
                key = issue["key"]
                fields = issue["fields"]
                nome = fields.get("customfield_10038", "—")
                with st.expander(f"👤 {nome} ({key})"):
                    st.markdown(f"**Empresa:** {fields.get('customfield_10051', '—')}")
                    st.markdown(f"**Telefone:** {fields.get('customfield_10041', '—')}")
                    st.markdown(f"**E-mail:** {fields.get('customfield_10042', '—')}")
                    if st.button(f"✏️ Editar {key}", key=f"editar_{key}"):
                        st.session_state.cliente_edicao = {
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
                        st.experimental_rerun()
        else:
            st.warning("Nenhum cliente encontrado.")
    else:
        st.error(f"Erro ao buscar clientes: {response.text}")

    # Tela de edição
    if "cliente_edicao" in st.session_state:
        cliente = st.session_state.cliente_edicao
        st.subheader(f"✏️ Editar Cliente: {cliente['nome']} ({cliente['key']})")
        with st.form("form_edicao"):
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
            url = f"{JIRA_URL}/rest/api/2/issue/{cliente['key']}"
            resp = requests.put(url, headers=JIRA_HEADERS, json=payload)
            if resp.status_code == 204:
                st.success("✅ Cliente atualizado com sucesso!")
                del st.session_state.cliente_edicao
            else:
                st.error(f"Erro ao atualizar cliente: {resp.text}")

