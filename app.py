import streamlit as st
from datetime import datetime

st.set_page_config(page_title="SID - Oficina", layout="wide")

# === BARRA DE MENUS SUPERIOR COM ÍCONES ===
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,6])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/847/847969.png", width=40)
    st.caption("Usuário")
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/471/471664.png", width=40)
    st.caption("Cliente")
with col3:
    st.image("https://cdn-icons-png.flaticon.com/512/679/679720.png", width=40)
    st.caption("Veículo")
with col4:
    st.image("https://cdn-icons-png.flaticon.com/512/1828/1828919.png", width=40)
    st.caption("OS")
with col5:
    st.markdown("<h3 style='text-align:right;'>🔧 HCD-DEV&CONSULT</h3>", unsafe_allow_html=True)

st.markdown("---")

# === LOGO CENTRAL (usei uma imagem de exemplo, trocamos depois pela sua) ===
st.image("https://i.imgur.com/UvWZJ4z.png", width=300)

# === PAINEL DE CONTROLE ===
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

# === RODAPÉ ===
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; font-size:14px;'>"
    f"Usuário logado: <strong>ADMINISTRADOR TESTE</strong> - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>"
    f"SID - Sistema Integrado de Dados: Versão 8.0"
    f"</div>", unsafe_allow_html=True)
