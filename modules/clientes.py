def tela_clientes():
    import streamlit as st
    import re
    import requests
    import base64

    # === Funções auxiliares internas ===
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

    # === Formulário dividido em colunas ===
    st.header("👤 Cadastro de Clientes")

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

            endereco = buscar_cep(cep)
            if endereco:
                st.success(f"{endereco['logradouro']} - {endereco['bairro']} - {endereco['localidade']}/{endereco['uf']}")
            else:
                if len(re.sub(r'\D', '', cep)) == 8:
                    st.warning("CEP inválido ou não encontrado.")

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

        # Verifica duplicidade
        if cliente_duplicado(documento, email):
            st.warning("⚠️ Já existe um cliente com esse CPF ou E-mail no sistema!")

        # Confirmação final
        if st.button("🚀 Deseja realmente cadastrar este cliente?"):
            with st.spinner("Enviando para o Jira..."):
                issue_key = criar_issue_jira(
                    nome, doc_formatado, empresa, telefone, email, cep, numero, complemento, endereco_formatado
                )
                if issue_key:
                    if imagem:
                        if not anexar_foto(issue_key, imagem):
                            st.warning("⚠️ Cliente criado, mas não foi possível anexar a foto.")
                    st.success(f"🎉 Cliente criado com sucesso: [{issue_key}]({JIRA_URL}/browse/{issue_key})")
