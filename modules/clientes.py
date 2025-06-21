# sid_app/modules/clientes.py
import streamlit as st
import pandas as pd
import os
import re
import requests

CAMINHO_CSV = "data/clientes.csv"
CAMINHO_FOTOS = "data/fotos/clientes/"
os.makedirs(CAMINHO_FOTOS, exist_ok=True)

# Cria o arquivo se não existir
def inicializar_csv():
    if not os.path.exists(CAMINHO_CSV):
        df = pd.DataFrame(columns=[
            "id_cliente", "nome", "cpf_cnpj", "telefone", "email",
            "cep", "endereco", "numero", "complemento", "ativo", "foto"
        ])
        df.to_csv(CAMINHO_CSV, index=False)

# Corrige nome para padrão ABNT
def corrigir_nome_abnt(nome):
    nome = nome.strip().lower()
    return re.sub(r"\b(\w)", lambda m: m.group(1).upper(), nome)

def gerar_id():
    df = pd.read_csv(CAMINHO_CSV)
    if df.empty:
        return 1
    return int(df["id_cliente"].max()) + 1

def salvar_cliente(cliente):
    df = pd.read_csv(CAMINHO_CSV)
    df = pd.concat([df, pd.DataFrame([cliente])], ignore_index=True)
    df.to_csv(CAMINHO_CSV, index=False)

def atualizar_cliente(linha, novos_dados):
    df = pd.read_csv(CAMINHO_CSV)
    for key in novos_dados:
        df.at[linha, key] = novos_dados[key]
    df.to_csv(CAMINHO_CSV, index=False)

def listar_clientes():
    return pd.read_csv(CAMINHO_CSV)

def buscar_cep(cep):
    try:
        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        if response.status_code == 200:
            data = response.json()
            if "erro" in data:
                return None
            return f"{data['logradouro']} - {data['bairro']} - {data['localidade']}/{data['uf']}"
    except:
        return None
    return None

def tela_clientes():
    st.header("👤 Cadastro de Clientes V1")
    inicializar_csv()
    df_clientes = listar_clientes()

    with st.expander("➕ Novo Cliente"):
        with st.form("form_cliente"):
            nome = st.text_input("Nome completo")
            cpf_cnpj = st.text_input("CPF ou CNPJ")
            telefone = st.text_input("Telefone")
            email = st.text_input("E-mail")
            cep = st.text_input("CEP")
            endereco = ""
            if st.button("🔍 Buscar Endereço"):
                endereco = buscar_cep(cep) or "CEP inválido ou não encontrado"
                st.session_state.endereco_busca = endereco
            endereco_final = st.text_input("Endereço", value=st.session_state.get("endereco_busca", ""))
            numero = st.text_input("Número")
            complemento = st.text_input("Complemento")
            ativo = st.selectbox("Status", ["Ativo", "Inativo"])
            foto = st.file_uploader("Foto do cliente", type=["jpg", "jpeg", "png"])
            submitted = st.form_submit_button("Salvar cliente")

            if submitted:
                if not nome or not cpf_cnpj:
                    st.warning("Nome e CPF/CNPJ são obrigatórios.")
                else:
                    nome_corrigido = corrigir_nome_abnt(nome)
                    novo_id = gerar_id()
                    caminho_foto = ""
                    if foto:
                        ext = os.path.splitext(foto.name)[-1]
                        caminho_foto = f"{CAMINHO_FOTOS}cliente_{novo_id}{ext}"
                        with open(caminho_foto, "wb") as f:
                            f.write(foto.read())
                    cliente = {
                        "id_cliente": novo_id,
                        "nome": nome_corrigido,
                        "cpf_cnpj": cpf_cnpj,
                        "telefone": telefone,
                        "email": email,
                        "cep": cep,
                        "endereco": endereco_final,
                        "numero": numero,
                        "complemento": complemento,
                        "ativo": ativo,
                        "foto": caminho_foto
                    }
                    salvar_cliente(cliente)
                    st.success(f"Cliente '{nome_corrigido}' salvo com sucesso!")

    st.subheader("📋 Clientes cadastrados")
    if not df_clientes.empty:
        for i, row in df_clientes.iterrows():
            with st.expander(f"{row['nome']} ({'✅' if row['ativo']=='Ativo' else '❌'})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    with st.form(f"edit_{row['id_cliente']}"):
                        nome_edit = st.text_input("Nome", value=row["nome"])
                        telefone_edit = st.text_input("Telefone", value=row["telefone"])
                        email_edit = st.text_input("Email", value=row["email"])
                        endereco_edit = st.text_input("Endereço", value=row["endereco"])
                        numero_edit = st.text_input("Número", value=row["numero"])
                        complemento_edit = st.text_input("Complemento", value=row["complemento"])
                        ativo_edit = st.selectbox("Status", ["Ativo", "Inativo"], index=0 if row["ativo"]=="Ativo" else 1)
                        if st.form_submit_button("Salvar alterações"):
                            novos_dados = {
                                "nome": corrigir_nome_abnt(nome_edit),
                                "telefone": telefone_edit,
                                "email": email_edit,
                                "endereco": endereco_edit,
                                "numero": numero_edit,
                                "complemento": complemento_edit,
                                "ativo": ativo_edit
                            }
                            atualizar_cliente(i, novos_dados)
                            st.success("Dados atualizados! Recarregue a página para ver as mudanças.")
                with col2:
                    if row["foto"] and os.path.exists(row["foto"]):
                        st.image(row["foto"], caption="Foto", width=100)
                    else:
                        st.info("Sem foto")
    else:
        st.info("Nenhum cliente cadastrado.")
