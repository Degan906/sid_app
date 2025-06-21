# sid_app/modules/veiculos.py
import streamlit as st
import pandas as pd
import os

CAMINHO_VEICULOS = "data/veiculos.csv"
CAMINHO_CLIENTES = "data/clientes.csv"

# Cria o arquivo de veículos se não existir
def inicializar_csv():
    if not os.path.exists(CAMINHO_VEICULOS):
        df = pd.DataFrame(columns=[
            "id_veiculo", "id_cliente", "placa", "marca", "modelo", "ano",
            "cor", "renavam", "tipo", "status"
        ])
        df.to_csv(CAMINHO_VEICULOS, index=False)

def gerar_id():
    df = pd.read_csv(CAMINHO_VEICULOS)
    if df.empty:
        return 1
    return int(df["id_veiculo"].max()) + 1

def salvar_veiculo(veiculo):
    df = pd.read_csv(CAMINHO_VEICULOS)
    df = pd.concat([df, pd.DataFrame([veiculo])], ignore_index=True)
    df.to_csv(CAMINHO_VEICULOS, index=False)

def listar_veiculos():
    return pd.read_csv(CAMINHO_VEICULOS)

def obter_clientes():
    if not os.path.exists(CAMINHO_CLIENTES):
        return pd.DataFrame()
    return pd.read_csv(CAMINHO_CLIENTES)

def tela_veiculos():
    st.header("🚗 Cadastro de Veículos")
    inicializar_csv()
    clientes_df = obter_clientes()

    if clientes_df.empty:
        st.warning("Nenhum cliente cadastrado. Cadastre um cliente primeiro.")
        return

    nome_para_id = dict(zip(clientes_df["nome"], clientes_df["id_cliente"]))
    nomes_clientes = list(nome_para_id.keys())

    with st.form("form_veiculo"):
        cliente_nome = st.selectbox("Cliente proprietário", nomes_clientes)
        placa = st.text_input("Placa")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        ano = st.number_input("Ano", min_value=1900, max_value=2100, step=1)
        cor = st.text_input("Cor")
        renavam = st.text_input("RENAVAM")
        tipo = st.selectbox("Tipo", ["Carro", "Moto", "Caminhão", "Outro"])
        status = st.selectbox("Status", ["Ativo", "Inativo"])
        submitted = st.form_submit_button("Salvar veículo")

        if submitted:
            if not placa or not modelo:
                st.warning("Placa e modelo são obrigatórios.")
            else:
                veiculo = {
                    "id_veiculo": gerar_id(),
                    "id_cliente": nome_para_id[cliente_nome],
                    "placa": placa,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano,
                    "cor": cor,
                    "renavam": renavam,
                    "tipo": tipo,
                    "status": status
                }
                salvar_veiculo(veiculo)
                st.success("Veículo salvo com sucesso!")

    st.subheader("📋 Veículos cadastrados")
    df_veiculos = listar_veiculos()
    if not df_veiculos.empty:
        df_exibicao = df_veiculos.merge(clientes_df, on="id_cliente", how="left")
        df_exibicao = df_exibicao[["placa", "marca", "modelo", "ano", "cor", "tipo", "status", "nome"]]
        df_exibicao.rename(columns={"nome": "Cliente"}, inplace=True)
        st.dataframe(df_exibicao, use_container_width=True)
    else:
        st.info("Nenhum veículo cadastrado.")
