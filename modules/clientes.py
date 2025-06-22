import streamlit as st
import pandas as pd
import requests
import unicodedata
import re
import base64
from io import BytesIO

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

def buscar_clientes_jira(jql_extra=""):
    jql = f'project = MC AND issuetype = Clientes {jql_extra} ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 100}
    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        st.error(f"Erro ao buscar clientes: {response.text}")
        return []

def exportar_para_excel(dados_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dados_df.to_excel(writer, index=False, sheet_name="Clientes")
    return output.getvalue()

# === TELA DE BUSCA E EDIÇÃO ===
def tela_busca_edicao_clientes():
    st.header("🔍 Buscar e Editar Clientes")

    if "cliente_edicao" not in st.session_state:
        st.session_state.cliente_edicao = None

    # Busca e filtros
    with st.expander("🔎 Filtros de Busca", expanded=True):
        termo_busca = st.text_input("Digite parte do nome, CPF, telefone ou e-mail:")
        col1, col2 = st.columns([1, 1])
        with col1:
            buscar = st.button("🔍 Aplicar Filtro")
        with col2:
            limpar = st.button("🧹 Limpar Filtros")

    # Aplicar filtro
    jql_filtro = ""
    if buscar and termo_busca:
        termo = termo_busca.strip()
        jql_filtro = f"""AND (
            summary ~ "{termo}" OR
            customfield_10040 ~ "{termo}" OR
            customfield_10041 ~ "{termo}" OR
            customfield_10042 ~ "{termo}"
        )"""
    elif limpar:
        termo_busca = ""
        jql_filtro = ""

    # Buscar clientes
    with st.spinner("🔄 Carregando clientes..."):
        issues = buscar_clientes_jira(jql_filtro)

    if not issues:
        st.warning("Nenhum cliente encontrado.")
        return

    # Transformar em DataFrame
    dados = []
    for issue in issues:
        fields = issue["fields"]
        dados.append({
            "Key": issue["key"],
            "Nome": fields.get("customfield_10038", ""),
            "CPF/CNPJ": fields.get("customfield_10040", ""),
            "Empresa": fields.get("customfield_10051", ""),
            "Telefone": fields.get("customfield_10041", ""),
            "E-mail": fields.get("customfield_10042", ""),
            "CEP": fields.get("customfield_10133", ""),
            "Nº": fields.get("customfield_10139", ""),
            "Complemento": fields.get("customfield_10044", "")
        })

    df = pd.DataFrame(dados)

    # Exportar Excel
    excel = exportar_para_excel(df)
    st.download_button("📥 Exportar resultados para Excel", data=excel, file_name="clientes.xlsx")

    # Tabela de resultados
    st.dataframe(df, use_container_width=True, height=400)

    # Seleção para edição
    selected_key = st.selectbox("Selecione um cliente para editar:", options=df["Key"].tolist())

    if selected_key:
        cliente = df[df["Key"] == selected_key].iloc[0]
        st.subheader(f"✏️ Editar Cliente: {cliente['Nome']} ({selected_key})")
        with st.form("form_edicao"):
            nome = st.text_input("Nome:", value=cliente["Nome"])
            cpf = st.text_input("CPF/CNPJ:", value=cliente["CPF/CNPJ"])
            empresa = st.text_input("Empresa:", value=cliente["Empresa"])
            telefone = st.text_input("Telefone:", value=cliente["Telefone"])
            email = st.text_input("E-mail:", value=cliente["E-mail"])
            cep = st.text_input("CEP:", value=cliente["CEP"])
            numero = st.text_input("Nº:", value=cliente["Nº"])
            complemento = st.text_input("Complemento:", value=cliente["Complemento"])
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
                    "customfield_10044": complemento
                }
            }
            url = f"{JIRA_URL}/rest/api/2/issue/{selected_key}"
            resp = requests.put(url, headers=JIRA_HEADERS, json=payload)
            if resp.status_code == 204:
                st.success("✅ Cliente atualizado com sucesso!")
            else:
                st.error(f"Erro ao atualizar cliente: {resp.text}")
