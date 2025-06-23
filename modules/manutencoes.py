import streamlit as st
import firebase_admin
from firebase_admin import firestore
import pandas as pd
from datetime import datetime

# --- Tela de Consulta de OS ---
def tela_consulta_os():
    st.header("Consultar Ordens de Serviço")
    db = st.session_state.db

    try:
        os_ref = db.collection("manutencoes").stream()
        os_list = []
        for os in os_ref:
            os_data = os.to_dict()
            os_list.append({
                "ID": os.id,
                "Veículo": os_data.get("veiculo", "N/A"),
                "KM": os_data.get("km_veiculo", "N/A"),
                "Data Abertura": os_data.get("data_abertura", "N/A"),
                "Descrição": os_data.get("descricao_servico", "N/A"),
                "Status": os_data.get("status", "Aberta")
            })

        if not os_list:
            st.warning("Nenhuma Ordem de Serviço encontrada.")
            return

        df = pd.DataFrame(os_list)
        
        st.info("Selecione uma OS na tabela abaixo e clique no botão para abrir os detalhes.")

        selecao = st.dataframe(
            df,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="grid_os"
        )

        if selecao.selection.rows:
            indice_selecionado = selecao.selection.rows[0]
            os_id_selecionada = df.iloc[indice_selecionado]["ID"]
            
            st.session_state.os_id_selecionada = os_id_selecionada

            if st.button("⚙️ Abrir OS Selecionada", type="primary"):
                st.session_state.pagina_atual = "manutencao"
                st.rerun()
        else:
            if 'os_id_selecionada' in st.session_state:
                del st.session_state.os_id_selecionada

    except Exception as e:
        st.error(f"Erro ao consultar as Ordens de Serviço: {e}")

# --- Tela de Manutenção (Criar/Editar OS) ---
def tela_manutencoes():
    db = st.session_state.db
    os_id = st.session_state.get('os_id_selecionada')

    # --- MODO DE EDIÇÃO ---
    if os_id:
        st.header(f"Editando Ordem de Serviço: {os_id}")

        if st.session_state.get('loaded_os_id') != os_id:
            doc_ref = db.collection('manutencoes').document(os_id)
            os_doc = doc_ref.get()
            if not os_doc.exists:
                st.error("OS não encontrada.")
                del st.session_state.os_id_selecionada
                st.stop()
            
            st.session_state.os_data = os_doc.to_dict()

            items_ref = doc_ref.collection('items').stream()
            items_list = []
            for item in items_ref:
                item_data = item.to_dict()
                item_data['id'] = item.id
                items_list.append(item_data)
            st.session_state.os_items = pd.DataFrame(items_list)
            st.session_state.loaded_os_id = os_id

        with st.form("form_edit_os"):
            veiculo = st.text_input("Veículo", value=st.session_state.os_data.get("veiculo"))
            km_veiculo = st.number_input("KM do Veículo", value=st.session_state.os_data.get("km_veiculo"), step=1)
            data_abertura = st.date_input("Data de Abertura", value=pd.to_datetime(st.session_state.os_data.get("data_abertura")).date())
            descricao_servico = st.text_area("Descrição Geral do Serviço", value=st.session_state.os_data.get("descricao_servico"))
            status = st.selectbox("Status da OS", ["Aberta", "Em Andamento", "Concluída", "Cancelada"], index=["Aberta", "Em Andamento", "Concluída", "Cancelada"].index(st.session_state.os_data.get("status", "Aberta")))

            st.subheader("Itens da OS")
            edited_items_df = st.data_editor(
                st.session_state.os_items,
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "id": None,
                    "descricao": st.column_config.TextColumn("Descrição do Item", required=True),
                    "quantidade": st.column_config.NumberColumn("Qtde", min_value=1, step=1, required=True),
                    "valor_unitario": st.column_config.NumberColumn("Valor Unit. (R$)", format="%.2f", required=True)
                },
                key="editor_items"
            )

            submitted = st.form_submit_button("Salvar Alterações", type="primary")
            if submitted:
                with st.spinner("Salvando alterações..."):
                    doc_ref = db.collection('manutencoes').document(os_id)
                    doc_ref.update({
                        "veiculo": veiculo,
                        "km_veiculo": km_veiculo,
                        "data_abertura": data_abertura.strftime("%Y-%m-%d"),
                        "descricao_servico": descricao_servico,
                        "status": status
                    })

                    items_ref = doc_ref.collection('items')
                    existing_items_snapshot = items_ref.stream()
                    for item_doc in existing_items_snapshot:
                        items_ref.document(item_doc.id).delete()
                    
                    for index, row in edited_items_df.iterrows():
                        new_item_data = {
                            "descricao": row["descricao"],
                            "quantidade": row["quantidade"],
                            "valor_unitario": row["valor_unitario"]
                        }
                        items_ref.add(new_item_data)

                st.success("Ordem de Serviço atualizada com sucesso!")
                del st.session_state.loaded_os_id
                del st.session_state.os_id_selecionada
                st.session_state.pagina_atual = "consulta"
                st.rerun()

    else:
        st.header("Criar Nova Ordem de Serviço")

        if 'new_os_items' not in st.session_state:
            st.session_state.new_os_items = pd.DataFrame(columns=["descricao", "quantidade", "valor_unitario"])

        with st.form("form_new_os"):
            veiculo = st.text_input("Veículo")
            km_veiculo = st.number_input("KM do Veículo", step=1, min_value=0)
            data_abertura = st.date_input("Data de Abertura", value=datetime.now())
            descricao_servico = st.text_area("Descrição Geral do Serviço")

            st.subheader("Adicionar Itens à OS")
            st.session_state.new_os_items = st.data_editor(
                st.session_state.new_os_items,
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "descricao": st.column_config.TextColumn("Descrição do Item", required=True),
                    "quantidade": st.column_config.NumberColumn("Qtde", min_value=1, step=1, required=True),
                    "valor_unitario": st.column_config.NumberColumn("Valor Unit. (R$)", format="%.2f", required=True)
                },
                key="editor_new_items"
            )

            submitted = st.form_submit_button("Salvar Nova OS", type="primary")
            if submitted:
                if not veiculo or not descricao_servico:
                    st.warning("Os campos Veículo e Descrição Geral são obrigatórios.")
                else:
                    with st.spinner("Criando nova OS..."):
                        os_data = {
                            "veiculo": veiculo,
                            "km_veiculo": km_veiculo,
                            "data_abertura": data_abertura.strftime("%Y-%m-%d"),
                            "descricao_servico": descricao_servico,
                            "status": "Aberta",
                            "data_criacao": firestore.SERVER_TIMESTAMP
                        }
                        doc_ref = db.collection('manutencoes').document()
                        doc_ref.set(os_data)

                        items_data = st.session_state.new_os_items.to_dict('records')
                        for item in items_data:
                            doc_ref.collection('items').add(item)

                    st.success(f"Ordem de Serviço {doc_ref.id} criada com sucesso!")
                    del st.session_state.new_os_items
                    st.rerun()
