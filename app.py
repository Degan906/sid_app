import streamlit as st
from datetime import datetime

st.set_page_config(page_title="SID - Oficina", layout="wide")

# === INICIALIZA CONTROLE DE PÁGINAS ===
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = None

# === FUNÇÃO DE BOTÃO COM SUBMENU PADRONIZADO ===
def menu_botao(titulo, icone, chave, mod_cadastro, mod_consulta=None):
    with st.container():
        st.markdown(f"<div style='text-align:center'><span style='font-size:30px;'>{icone}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; font-weight:bold'>{titulo}</div>", unsafe_allow_html=True)
        if st.button("📄 Cadastro", key=f"{chave}_cad"):
            st.session_state['pagina'] = mod_cadastro
        if st.button("🔎 Consulta", key=f"{chave}_cons"):
            st.session_state['pagina'] = mod_consulta or mod_cadastro

# === BARRA DE MENU SUPERIOR COM BOTÕES PADRÃO ===
col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1.2, 1.2, 6])
with col1:
    menu_botao("Usuário", "👤", "usuario", "cad_usuario", "cons_usuario")
with col2:
    menu_botao("Cliente", "👥", "cliente", "cad_cliente", "cons_cliente")
with col3:
    menu_botao("Veículo", "🚗", "veiculo", "cad_veiculo", "cons_veiculo")
with col4:
    menu_botao("OS", "🧾", "os", "cad_os", "cons_os")
with col5:
    st.markdown("<h3 style='text-align:right;'>🔧 HCD-DEV&CONSULT</h3>", unsafe_allow_html=True)

st.markdown("---")

# === LOGO CENTRAL (pode substituir pela sua imagem local) ===
st.image("https://i.imgur.com/UvWZJ4z.png", width=300)

# === CONTROLE VISUAL (PAINEL SIMBÓLICO) ===
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

# === NAVEGAÇÃO ENTRE MÓDULOS ===
if st.session_state['pagina'] == 'cad_usuario':
    st.warning("⚠️ Módulo de cadastro de usuário ainda em desenvolvimento.")

elif st.session_state['pagina'] == 'cons_usuario':
    st.warning("⚠️ Módulo de consulta de usuário ainda em desenvolvimento.")

elif st.session_state['pagina'] == 'cad_cliente':
    from modules import clientes
    clientes.tela_clientes()

elif st.session_state['pagina'] == 'cons_cliente':
    from modules import consultar_clientes
    consultar_clientes.tela_busca_edicao_clientes()

elif st.session_state['pagina'] == 'cad_veiculo':
    from modules import veiculos
    veiculos.tela_veiculos()

elif st.session_state['pagina'] == 'cons_veiculo':
    from modules import veiculos
    veiculos.tela_busca_edicao_veiculos()

elif st.session_state['pagina'] == 'cad_os':
    from modules import manutencoes
    manutencoes.tela_manutencao()

elif st.session_state['pagina'] == 'cons_os':
    from modules import consultar_os
    consultar_os.tela_consulta_os()
