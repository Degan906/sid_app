import streamlit as st
from datetime import datetime

st.set_page_config(page_title="SID - Oficina", layout="wide")

# === INICIALIZA CONTROLE DE PÁGINAS ===
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = None

# === BARRA SUPERIOR COM ÍCONES ===
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 6])
with col1:
    if st.button("👤 Usuário"):
        st.session_state['pagina'] = 'usuario'
with col2:
    if st.button("👥 Cliente"):
        st.session_state['pagina'] = 'clientes'
with col3:
    if st.button("🚗 Veículo"):
        st.session_state['pagina'] = 'veiculos'
with col4:
    if st.button("🧾 OS"):
        st.session_state['pagina'] = 'manutencoes'
with col5:
    st.markdown("<h3 style='text-align:right;'>🔧 HCD-DEV&CONSULT</h3>", unsafe_allow_html=True)

st.markdown("---")

# === EXIBE LOGO CENTRAL ===
st.image("https://i.imgur.com/UvWZJ4z.png", width=300)

# === CONTROLES RÁPIDOS ===
colA, colB, colC = st.columns(3)
with colA:
    st.markdown("### Controle Diário")
    st.button("📆 Orçamentos do dia (0)")
with colB:
    st.markdown("### Controle Abertos")
    st.button("🛠️ Orçamentos abertos (1)")
    st.button("🚚 Entregas pra hoje (0)")
with colC:
    st.markdown("### Controle Pagamentos")
    st.button("💰 PGTO Agendados hoje (0)")

st.markdown("---")

# === RODAPÉ ===
st.markdown(
    f"<div style='text-align:center; font-size:14px;'>"
    f"Usuário logado: <strong>ADMINISTRADOR TESTE</strong> - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>"
    f"SID - Sistema Integrado de Dados: Versão 8.0"
    f"</div>", unsafe_allow_html=True
)

# === CHAMA OS MÓDULOS CONFORME A OPÇÃO ESCOLHIDA ===
if st.session_state['pagina'] == 'clientes':
    from modules import clientes
    clientes.tela_clientes()

elif st.session_state['pagina'] == 'veiculos':
    from modules import veiculos
    veiculos.tela_veiculos()

elif st.session_state['pagina'] == 'manutencoes':
    from modules import manutencoes
    manutencoes.tela_manutencao()

elif st.session_state['pagina'] == 'usuario':
    st.warning("⚠️ Módulo de Usuários ainda em desenvolvimento.")
