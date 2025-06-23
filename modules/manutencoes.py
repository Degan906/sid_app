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
    return r.json().get("issues", []) if r.status_code == 200 else []

def buscar_veiculos_do_cliente(cpf):
    jql = f'project = MC AND issuetype = "Veículos" AND "CPF/CNPJ" ~ "{cpf}" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": 50, "fields": "summary,customfield_10134"}
    r = requests.get(url, headers=JIRA_HEADERS, params=params)
    return r.json().get("issues", []) if r.status_code == 200 else []

def criar_os(cliente_nome, cliente_cpf, veiculo_key, km, data_entrada, data_saida, descricao, total_orcamento):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10032"},
            "summary": f"OS - {cliente_nome} ({cliente_cpf}) - {veiculo_key}",
            "description": f"CPF: {cliente_cpf}\nPlaca: {veiculo_key}\nKM: {km}\n\nDescrição:\n{descricao}",
            "customfield_10119": total_orcamento
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    return r.json().get("key") if r.status_code == 201 else None

def criar_subtarefa(os_key, item):
    payload = {
        "fields": {
            "project": {"key": "MC"},
            "issuetype": {"id": "10030"},
            "parent": {"key": os_key},
            "summary": item['descricao'],
            "description": f"Tipo: {item['tipo']}\nQuantidade: {item['quantidade']}\nValor: R${item['valor']:.2f}\nTotal: R${item['total']:.2f}"
        }
    }
    r = requests.post(f"{JIRA_URL}/rest/api/2/issue", headers=JIRA_HEADERS, json=payload)
    return r.status_code == 201

# === TELA DE MANUTENÇÃO ===
def tela_manutencoes():
    st.title("\U0001F698 SID - Sistema de Manutenção de Veículos")

    if "orcamento" not in st.session_state:
        st.session_state.orcamento = []

    if "os_key" not in st.session_state:
        st.header("\U0001F464 Cliente")
        clientes = buscar_clientes()
        nomes = [f"{c['fields'].get('summary')} - {c['fields'].get('customfield_10041')}" for c in clientes]
        cliente_index = st.selectbox("Buscar por CPF ou Tel", nomes)
        cliente_escolhido = clientes[nomes.index(cliente_index)]
        cpf = cliente_escolhido['fields'].get('customfield_10040')
        nome_cliente = cliente_escolhido['fields'].get('summary')
        email_cliente = cliente_escolhido['fields'].get('customfield_10042')

        st.info(f"**Cliente:** {nome_cliente} | **CPF:** {cpf} | **Email:** {email_cliente}")

        veiculos = buscar_veiculos_do_cliente(cpf)
        if not veiculos:
            st.warning("Este cliente não possui veículos cadastrados.")
            return

        st.header("\U0001F697 Veículo")
        veiculo_opcoes = [f"{v['fields'].get('summary')} ({v['fields'].get('customfield_10134')})" for v in veiculos]
        veiculo_escolhido = st.selectbox("Selecione o Veículo:", veiculo_opcoes)
        veiculo_info = veiculos[veiculo_opcoes.index(veiculo_escolhido)]
        veiculo_key = veiculo_info["key"]

        st.markdown(f"**Placa:** {veiculo_info['fields'].get('customfield_10134')}")

        st.header("\U0001F4CB Detalhes da OS")
        km = st.text_input("KM atual:")
        data_entrada = st.date_input("Data Entrada", value=datetime.date.today())
        data_saida = st.date_input("Previsão Saída", value=datetime.date.today())
        descricao = st.text_area("Descrição geral")

        if st.button("✅ Criar Ordem de Serviço"):
            total_orcamento = sum(i['total'] for i in st.session_state.orcamento)
            os_key = criar_os(nome_cliente, cpf, veiculo_key, km, str(data_entrada), str(data_saida), descricao, total_orcamento)
            if os_key:
                st.session_state.os_key = os_key
                st.rerun()
    else:
        os_key = st.session_state.os_key
        st.subheader(f"\U0001F4CC OS em andamento: {os_key}")

        with st.form(key="form_item"):
            cols = st.columns(4)
            tipo = cols[0].selectbox("Tipo", ["Serviço", "Peça"])
            descricao = cols[1].text_input("Descrição")
            quantidade = cols[2].number_input("Quantidade", min_value=1, step=1)
            valor = cols[3].number_input("Valor unitário (R$)", min_value=0.0, step=0.01)
            submitted = st.form_submit_button("➕ Adicionar ao Orçamento")
            if submitted and descricao:
                total = quantidade * valor
                st.session_state.orcamento.append({"tipo": tipo, "descricao": descricao, "quantidade": quantidade, "valor": valor, "total": total})
                st.experimental_rerun()

        # Exibir itens
        if st.session_state.orcamento:
            st.markdown("### 🧾 Itens do Orçamento")
            total_pecas = total_servicos = 0
            for i, item in enumerate(st.session_state.orcamento):
                col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 1, 1, 1, 1])
                col1.write(f"{i+1}")
                col2.write(item['descricao'])
                col3.write(item['tipo'])
                col4.write(f"{item['quantidade']}")
                col5.write(f"R${item['valor']:.2f}")
                col6.write(f"R${item['total']:.2f}")
                if item['tipo'] == 'Peça':
                    total_pecas += item['total']
                else:
                    total_servicos += item['total']

            st.success(f"**Total de Peças:** R${total_pecas:.2f} | **Total de Serviços:** R${total_servicos:.2f} | **Total Geral:** R${total_pecas + total_servicos:.2f}")

            if st.button("📤 Validar e Criar Itens no Jira"):
                for item in st.session_state.orcamento:
                    criar_subtarefa(os_key, item)
                st.success("Itens criados no Jira com sucesso!")

        st.markdown("---")
        if st.button("🆕 Nova OS"):
            del st.session_state.os_key
            st.session_state.orcamento = []
            st.rerun()
