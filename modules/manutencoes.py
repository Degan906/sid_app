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

def criar_subtarefa(os_key, item):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10030"},
            "parent": {"key": os_key},
            "summary": item['descricao'],
            "description": f"Tipo: {item['tipo']}\nDescrição: {item['descricao']}\nQuantidade: {item['quantidade']}\nValor: R${item['valor']:.2f}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    if r.status_code != 201:
        st.error(f"Erro ao adicionar subtarefa: {r.status_code} - {r.text}")

def atualizar_total_os(issue_key, total):
    payload = {"fields": {"customfield_10119": total}}
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
    r = requests.put(url, headers=JIRA_HEADERS, json=payload)
    return r.status_code == 204

# === TELAS ===
def tela_manutencoes():
    st.title("\U0001F698 SID - Sistema de Manutenção de Veículos")
    st.header("\U0001F6E0️ Abertura de Ordem de Serviço (OS)")

    if "os_key" not in st.session_state or not st.session_state.os_key:
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
                st.session_state.confirmado = False
                st.rerun()

    else:
        os_key = st.session_state.os_key
        st.subheader(f"\U0001F4CC OS em andamento: {os_key}")

        st.markdown("### Itens da OS")
        cols = st.columns(5)
        with cols[0]: tipo = st.selectbox("Tipo", ["Serviço", "Peça"])
        with cols[1]: descricao = st.text_input("Descrição")
        with cols[2]: quantidade = st.number_input("Qtd", step=1, min_value=1, key="qtd")
        with cols[3]: valor = st.number_input("Valor R$", step=0.01, min_value=0.0, key="valor")
        with cols[4]:
            total_temp = quantidade * valor
            st.write(f"**Total:** R$ {total_temp:.2f}")

        if st.button("Adicionar Item"):
            st.session_state.itens.append({"tipo": tipo, "descricao": descricao, "quantidade": quantidade, "valor": valor})
            st.rerun()

        if st.session_state.itens:
            st.markdown("#### Itens pendentes")
            for idx, item in enumerate(st.session_state.itens):
                col1, col2, col3, col4, col5, col6 = st.columns([1.5, 3, 1, 2, 2, 1])
                col1.write(item['tipo'])
                col2.write(item['descricao'])
                col3.write(item['quantidade'])
                col4.write(f"R$ {item['valor']:.2f}")
                col5.write(f"R$ {item['quantidade'] * item['valor']:.2f}")
                if col6.button("🗑️", key=f"del_{idx}"):
                    st.session_state.itens.pop(idx)
                    st.rerun()

            if st.button("✅ Confirmar Itens e Criar Subtarefas"):
                for item in st.session_state.itens:
                    criar_subtarefa(os_key, item)
                total = sum(i['quantidade'] * i['valor'] for i in st.session_state.itens)
                atualizar_total_os(os_key, total)
                st.success(f"Subtarefas criadas com sucesso. Total da OS: R$ {total:.2f}")
                st.session_state.confirmado = True

        if st.session_state.get("confirmado"):
            st.info("Todos os itens foram confirmados e salvos no Jira.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔚 Finalizar OS"):
                for key in ["os_key", "itens", "confirmado"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        with col2:
            if st.button("➕ Nova OS"):
                for key in ["os_key", "itens", "confirmado"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

def tela_consulta_os():
    st.title("🔍 Consultar Ordens de Serviço")

    jql = 'project = MC AND issuetype = "OS" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": 100,
        "fields": "summary,status"
    }
    r = requests.get(url, headers=JIRA_HEADERS, params=params)

    if r.status_code != 200:
        st.error("Erro ao buscar OS")
        return

    issues = r.json().get("issues", [])
    if not issues:
        st.info("Nenhuma OS encontrada.")
        return

    st.markdown("### 🗂 Lista de OS")
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"].get("summary", "-")
        status = issue["fields"].get("status", {}).get("name", "-")

        # Extrai cliente e placa do summary
        cliente_match = re.search(r"OS - (.*?) \(", summary)
        cliente = cliente_match.group(1) if cliente_match else "-"
        placa_match = re.search(r"\((.*?)\)", summary)
        placa = placa_match.group(1) if placa_match else "-"

        # Exibe os dados principais em linha
        cols = st.columns([2, 4, 2, 2])
        cols[0].markdown(f"**{key}**")
        cols[1].markdown(f"{cliente}")
        cols[2].markdown(f"{placa}")
        cols[3].markdown(f"📋 *{status}*")

        # Botão separado para evitar conflito de estado
        if st.button(f"📂 Abrir OS {key}", key=f"abrir_os_{key}"):
            st.session_state.tela_atual = "manutencoes"
            st.session_state.os_key = key
            st.session_state.itens = []
            st.session_state.confirmado = False
            st.rerun()



# === LÓGICA DE NAVEGAÇÃO ===
if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "consulta_os"

if st.session_state.tela_atual == "consulta_os":
    tela_consulta_os()
elif st.session_state.tela_atual == "manutencoes":
    tela_manutencoes()
