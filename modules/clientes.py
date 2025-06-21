# sid_app/modules/clientes.py
import streamlit as st
import pandas as pd
import os

CAMINHO_CSV = "data/clientes.csv"

# Cria o arquivo se não existir
def inicializar_csv():
    if not os.path.exists(CAMINHO_CSV):
        df = pd.DataFrame(columns=["id_cliente", "nome", "cpf_cnpj", "telefone", "email", "endereco"])
        df.to_csv(CAMINHO_CSV, index=False)

def gerar_id():
    df = pd.read_csv(CAMINHO_CSV)
    if df.empty:
        return 1
    return int(df["id_cliente"].max()) + 1

def salvar_cliente(cliente):
    df = pd.read_csv(CAMINHO_CSV)
    df = pd.concat([df, pd.DataFrame([cliente])], ignore_index=True)
    df.to_csv(CAMINHO_CSV, index=False)

def listar_clientes():
    return pd.read_csv(CAMINHO_CSV)

def tela_clientes():
    st.header("👤 Cadastro de Clientes")
    inicializar_csv()

    with st.form("form_cliente"):
        nome = st.text_input("Nome completo")
        cpf_cnpj = st.text_input("CPF ou CNPJ")
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")
        endereco = st.text_area("Endereço completo")
        submitted = st.form_submit_button("Salvar cliente")

        if submitted:
            if not nome or not cpf_cnpj:
                st.warning("Nome e CPF/CNPJ são obrigatórios.")
            else:
                cliente = {
                    "id_cliente": gerar_id(),
                    "nome": nome,
                    "cpf_cnpj": cpf_cnpj,
                    "telefone": telefone,
                    "email": email,
                    "endereco": endereco,
                }
                salvar_cliente(cliente)
                st.success("Cliente salvo com sucesso!")

    st.subheader("📋 Clientes cadastrados")
    df_clientes = listar_clientes()
    st.dataframe(df_clientes, use_container_width=True)
