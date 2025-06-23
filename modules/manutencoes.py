import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import uuid # Para gerar IDs únicos para os itens

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Sistema de Ordem de Serviço")

# --- Inicialização do Firebase ---
# ATENÇÃO: Substitua o caminho para o seu arquivo de credenciais do Firebase.
# O arquivo "serviceAccount.json" deve estar no mesmo diretório ou o caminho deve ser ajustado.
def initialize_firebase():
    try:
        # Usando st.secrets para gerenciar as credenciais de forma segura no Streamlit Cloud
        if "firebase_credentials" in st.secrets:
            creds_dict = st.secrets["firebase_credentials"]
        else:
            # Para desenvolvimento local, use o arquivo JSON
            # Certifique-se de que o arquivo está no formato de dicionário Python correto
            # ou carregue-o de um arquivo .json
            st.error("Credenciais do Firebase não encontradas nos segredos do Streamlit. Carregue seu arquivo serviceAccount.json.")
            st.stop()

        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
        st.session_state.firebase_initialized = True
        return firestore.client()

    except ValueError as e:
        # Evita o erro "app already exists" em reruns do Streamlit
        if "The default Firebase app already exists" not in str(e):
            st.error(f"Erro ao inicializar o Firebase: {e}")
            st.stop()
        return firestore.client()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado na inicialização do Firebase: {e}")
        st.stop()

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

        # Usamos st.dataframe para exibir e capturar a seleção
        # O evento de seleção fará o rerun da página, atualizando o estado
        selecao = st.dataframe(
            df,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="grid_os"
        )

        # Verifica se uma linha foi selecionada
        if selecao.selection.rows:
            indice_selecionado = selecao.selection.rows[0]
            os_id_selecionada = df.iloc[indice_selecionado]["ID"]
            
            st.session_state.os_id_selecionada = os_id_selecionada

            if st.button("⚙️ Abrir OS Selecionada", type="primary"):
                st.session_state.pagina_atual = "manutencao"
                st.rerun()
        else:
            # Limpa a seleção se não houver nenhuma linha marcada
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

        # Carrega os dados da OS apenas uma vez
        if st.session_state.get('loaded_os_id') != os_id:
            doc_ref = db.collection('manutencoes').document(os_id)
            os_doc = doc_ref.get()
            if not os_doc.exists:
                st.error("OS não encontrada.")
                del st.session_state.os_id_selecionada
                st.stop()
            
            st.session_state.os_data = os_doc.to_dict()

            # Carrega os itens da subcoleção
            items_ref = doc_ref.collection('items').stream()
            items_list = []
            for item in items_ref:
                item_data = item.to_dict()
                item_data['id'] = item.id # Guarda o ID do documento do item
                items_list.append(item_data)
            st.session_state.os_items = pd.DataFrame(items_list)
            st.session_state.loaded_os_id = os_id

        # Formulário com os dados da OS
        with st.form("form_edit_os"):
            veiculo = st.text_input("Veículo", value=st.session_state.os_data.get("veiculo"))
            km_veiculo = st.number_input("KM do Veículo", value=st.session_state.os_data.get("km_veiculo"), step=1)
            data_abertura = st.date_input("Data de Abertura", value=pd.to_datetime(st.session_state.os_data.get("data_abertura")).date())
            descricao_servico = st.text_area("Descrição Geral do Serviço", value=st.session_state.os_data.get("descricao_servico"))
            status = st.selectbox("Status da OS", ["Aberta", "Em Andamento", "Concluída", "Cancelada"], index=["Aberta", "Em Andamento", "Concluída", "Cancelada"].index(st.session_state.os_data.get("status", "Aberta")))

            st.subheader("Itens da OS")
            # Editor de dados para os itens
            edited_items_df = st.data_editor(
                st.session_state.os_items,
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "id": None, # Oculta a coluna de ID do Firestore
                    "descricao": st.column_config.TextColumn("Descrição do Item", required=True),
                    "quantidade": st.column_config.NumberColumn("Qtde", min_value=1, step=1, required=True),
                    "valor_unitario": st.column_config.NumberColumn("Valor Unit. (R$)", format="%.2f", required=True)
                },
                key="editor_items"
            )

            submitted = st.form_submit_button("Salvar Alterações", type="primary")
            if submitted:
                with st.spinner("Salvando alterações..."):
                    # 1. Atualiza o documento principal da OS
                    doc_ref = db.collection('manutencoes').document(os_id)
                    doc_ref.update({
                        "veiculo": veiculo,
                        "km_veiculo": km_veiculo,
                        "data_abertura": data_abertura.strftime("%Y-%m-%d"),
                        "descricao_servico": descricao_servico,
                        "status": status
                    })

                    # 2. Atualiza os itens (estratégia: apaga os antigos e insere os novos)
                    # Isso simplifica a lógica de sincronização
                    items_ref = doc_ref.collection('items')
                    # Primeiro, apaga todos os itens existentes para a OS
                    existing_items_snapshot = items_ref.stream()
                    for item_doc in existing_items_snapshot:
                        items_ref.document(item_doc.id).delete()
                    
                    # Em seguida, adiciona os itens do DataFrame editado
                    for index, row in edited_items_df.iterrows():
                        new_item_data = {
                            "descricao": row["descricao"],
                            "quantidade": row["quantidade"],
                            "valor_unitario": row["valor_unitario"]
                        }
                        items_ref.add(new_item_data)

                st.success("Ordem de Serviço atualizada com sucesso!")
                # Limpa o estado para forçar o recarregamento na próxima edição
                del st.session_state.loaded_os_id
                del st.session_state.os_id_selecionada
                st.session_state.pagina_atual = "consulta"
                st.rerun()

    # --- MODO DE CRIAÇÃO ---
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
            # Editor para adicionar novos itens
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
                        # 1. Cria o documento principal da OS
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

                        # 2. Adiciona os itens na subcoleção
                        items_data = st.session_state.new_os_items.to_dict('records')
                        for item in items_data:
                            doc_ref.collection('items').add(item)

                    st.success(f"Ordem de Serviço {doc_ref.id} criada com sucesso!")
                    # Limpa o formulário
                    del st.session_state.new_os_items
                    st.rerun()

# --- Lógica Principal do App ---
def main():
    st.title("🛠️ Sistema de Gestão de OS")

    # Inicializa o Firebase e o armazena no estado da sessão
    if 'firebase_initialized' not in st.session_state:
        st.session_state.db = initialize_firebase()

    # Inicializa o controle de página
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "consulta"

    # Barra de Navegação Lateral
    with st.sidebar:
        st.header("Navegação")
        if st.button("Consultar OS", use_container_width=True):
            st.session_state.pagina_atual = "consulta"
            # Limpa qualquer seleção anterior ao voltar para a consulta
            if 'os_id_selecionada' in st.session_state:
                del st.session_state.os_id_selecionada
            if 'loaded_os_id' in st.session_state:
                del st.session_state.loaded_os_id
            st.rerun()
        
        if st.button("➕ Criar Nova OS", use_container_width=True):
            st.session_state.pagina_atual = "manutencao"
            # Garante que estamos no modo de criação, limpando qualquer ID selecionado
            if 'os_id_selecionada' in st.session_state:
                del st.session_state.os_id_selecionada
            if 'loaded_os_id' in st.session_state:
                del st.session_state.loaded_os_id
            st.rerun()

    # Roteamento de Página
    if st.session_state.pagina_atual == "consulta":
        tela_consulta_os()
    elif st.session_state.pagina_atual == "manutencao":
        tela_manutencoes()

if __name__ == "__main__":
    main()


