# sid_app/modules/manutencoes.py
import streamlit as st
import pandas as pd
import os
from datetime import date

CAMINHO_MANUTENCOES = "data/manutencoes.csv"
CAMINHO_VEICULOS = "data/veiculos.csv"

# Cria o arquivo de manutencoes se não existir
def inicializar_csv():
    if not os.path.exists(CAMINHO_MANUTENCOES):
        df = pd.DataFrame(columns=[
            "id_manutencao", "id_veiculo", "data", "tipo_manutencao",
            "descricao", "custo", "oficina", "km"
        ])
        df.to_csv(CAMINHO_MANUTENCOES, index=False)

def gerar_id():
    df = pd.read_csv(CAMINHO_MANUTENCOES)
    if df.empty:
        return 1
    return int(df["id_manutencao"].max()) + 1

def salvar_manutencao(m):
    df = pd.read_csv(CAMINHO_MANUTENCOES)
    df = pd.concat([df, pd.DataFrame([m])], ignore_index=True)
    df.to_csv(CAMINHO_MANUTENCOES, index=False)

def listar_manutencoes():
    return pd.read_csv(CAMINHO_MANUTENCOES)

def obter_veiculos():
    if not os.path.exists(CAMINHO_VEICULOS):
        return pd.DataFrame()
    return pd.read_csv(CAMINHO_VEICULOS)

def tela_manutencoes():
    st.header("🔧 Cadastro de Manutenções")
    inicializar_csv()
    veiculos_df = obter_veiculos()

    if veiculos_df.empty:
        st.warning("Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
        return

    placa_para_id = {
        f"{row['placa']} - {row['modelo']}": row["id_veiculo"]
        for _, row in veiculos_df.iterrows()
    }
    opcoes_veiculos = list(placa_para_id.keys())

    with st.form("form_manutencao"):
        veiculo = st.selectbox("Veículo", opcoes_veiculos)
        data_manutencao = st.date_input("Data da manutenção", value=date.today())
        tipo = st.text_input("Tipo de manutenção")
        descricao = st.text_area("Descrição")
        custo = st.number_input("Custo (R$)", min_value=0.0, step=10.0, format="%.2f")
        oficina = st.text_input("Oficina")
        km = st.number_input("Km atual", min_value=0, step=100)
        submitted = st.form_submit_button("Salvar manutenção")

        if submitted:
            manutencao = {
                "id_manutencao": gerar_id(),
                "id_veiculo": placa_para_id[veiculo],
                "data": data_manutencao.strftime("%Y-%m-%d"),
                "tipo_manutencao": tipo,
                "descricao": descricao,
                "custo": custo,
                "oficina": oficina,
                "km": km
            }
            salvar_manutencao(manutencao)
            st.success("Manutenção salva com sucesso!")

    st.subheader("📋 Manutenções cadastradas")
    df_manutencoes = listar_manutencoes()
    if not df_manutencoes.empty:
        df = df_manutencoes.merge(veiculos_df, on="id_veiculo", how="left")
        df = df[["data", "placa", "modelo", "tipo_manutencao", "descricao", "custo", "oficina", "km"]]
        df.sort_values("data", ascending=False, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma manutenção cadastrada.")
