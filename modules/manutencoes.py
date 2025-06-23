import streamlit as st
import requests
import base64
import unicodedata
import re
import datetime

# === CONFIG JIRA ===
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

def buscar_clientes():
    jql = 'project = MC AND issuetype = "Clientes" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 100, "fields": "summary,customfield_10040,customfield_10041,customfield_10042"}
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    if r.status_code == 200:
        return r.json().get("issues", [])
    return []

def buscar_veiculos_do_cliente(cpf):
    jql = f'project = MC AND issuetype = "Veículos" AND "CPF/CNPJ" ~ "{cpf}" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 50, "fields": "summary,customfield_10134"}
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    if r.status_code == 200:
        return r.json().get("issues", [])
    return []

def criar_os(cliente_nome, cliente_cpf, veiculo_key, km, data_entrada, data_saida, descricao):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10032"},
            "summary": f"OS - {cliente_nome} ({cliente_cpf}) - {veiculo_key}",
            "description": f"CPF: {cliente_cpf}\nPlaca: {veiculo_key}\nKM: {km}\n\nDescrição:\n{descricao}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code == 201:
        return r.json().get("key")
    st.error(f"Erro ao criar OS: {r.status_code} - {r.text}")
    return None

def criar_subtarefa(os_key, descricao, tipo, quantidade, valor):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10030"},
            "parent": {"key": os_key},
            "summary": descricao,
            "description": f"Tipo: {tipo}\nDescrição: {descricao}\nQuantidade: {quantidade}\nValor: R${valor:.2f}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code != 201:
        st.error(f"Erro ao adicionar subtarefa: {r.status_code} - {r.text}")
    return r.status_code == 201

def atualizar_total_os(issue_key, total):
    payload = {"fields": {"customfield_10119": total}}
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    r = requests.put(url, headers=JIRA_HEADERS, json=payload)
    return r.status_code == 204

def tela_manutencoes():
    st.title("\U0001F698 SID - Sistema de Manutenção de Veículos")
    st.header("\U0001F6E0️ Abertura de Ordem de Serviço (OS)")

    if "os_key" not in st.session_state:
        st.subheader("\U0001F464 Selecionar Cliente")
        clientes = buscar_clientes()
        nomes = [f"{c['fields'].get('summary')} - {c['fields'].get('customfield_10041')}" for c in clientes]
        cliente_index = st.selectbox("Buscar por CPF ou Tel", nomes)
        cliente_escolhido = clientes[nomes.index(cliente_index)]
        cpf = cliente_escolhido['fields'].get('customfield_10040')
        nome_cliente = cliente_escolhido['fields'].get('summary')

        st.info(f"**Cliente:** {nome_cliente} | **CPF:** {cpf}")

        st.subheader("\U0001F697 Selecionar Veículo")
        veiculos = buscar_veiculos_do_cliente(cpf)
        if not veiculos:
            st.warning("Este cliente não possui veículos cadastrados.")
            return

        veiculo_opcoes = [f"{v['fields'].get('summary')} ({v['fields'].get('customfield_10134')})" for v in veiculos]
        veiculo_escolhido = st.selectbox("Selecione o Veículo:", veiculo_opcoes)
        veiculo_info = veiculos[veiculo_opcoes.index(veiculo_escolhido)]
        veiculo_key = veiculo_info["key"]

        km = st.text_input("KM Atual")
        data_entrada = st.date_input("Data Entrada", value=datetime.date.today())
        data_saida = st.date_input("Data Prevista Saída", value=datetime.date.today())
        descricao = st.text_area("Descrição geral do problema")

        if st.button("✅ Criar OS"):
            os_key = criar_os(nome_cliente, cpf, veiculo_key, km, str(data_entrada), str(data_saida), descricao)
            if os_key:
                st.session_state.os_key = os_key
                st.session_state.itens = []
                st.rerun()
    else:
        os_key = st.session_state.os_key
        st.subheader(f"\U0001F4CC OS em andamento: {os_key}")

        st.markdown("### Itens da OS")
        with st.form("form_item"):
            cols = st.columns(4)
            tipo = cols[0].selectbox("Tipo", ["Serviço", "Peça"])
            descricao = cols[1].text_input("Descrição")
            quantidade = cols[2].number_input("Qtd", step=1, min_value=1, value=1)
            valor = cols[3].number_input("Valor R$", step=0.01, min_value=0.0)
            submitted = st.form_submit_button("Adicionar")
            if submitted:
                st.session_state.itens.append({"tipo": tipo, "descricao": descricao, "quantidade": quantidade, "valor": valor})
                criar_subtarefa(os_key, descricao, tipo, quantidade, valor)

        if "itens" in st.session_state and st.session_state.itens:
            total_servico = sum(i['quantidade'] * i['valor'] for i in st.session_state.itens if i['tipo'] == 'Serviço')
            total_peca = sum(i['quantidade'] * i['valor'] for i in st.session_state.itens if i['tipo'] == 'Peça')
            total_geral = total_servico + total_peca

            st.dataframe([
                {
                    "Tipo": i['tipo'],
                    "Descrição": i['descricao'],
                    "Qtd": i['quantidade'],
                    "Valor Unitário": f"R$ {i['valor']:.2f}",
                    "Total": f"R$ {i['quantidade'] * i['valor']:.2f}"
                } for i in st.session_state.itens
            ])

            with st.container():
                col1, col2, col3 = st.columns(3)
                col1.metric("🧰 Total de Peças", f"R$ {total_peca:.2f}")
                col2.metric("🛠️ Total M.O. (Serviços)", f"R$ {total_servico:.2f}")
                col3.metric("💰 Total do Orçamento", f"R$ {total_geral:.2f}")

            atualizar_total_os(os_key, total_geral)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Finalizar OS"):
                del st.session_state.os_key
                st.success("OS finalizada.")
                st.rerun()
        with col2:
            if st.button("➕ Nova OS"):
                del st.session_state.os_key
                if "itens" in st.session_state:
                    del st.session_state.itens
                st.rerun()
