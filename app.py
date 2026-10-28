# app.py
# Score de Vendas Urba
# Arquivo principal — ponto de entrada do Streamlit

import streamlit as st

from db import init_db
from styles import aplicar_estilos, hero_banner, rodape

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Score de Vendas | Urba",
    page_icon="assets/logo_urba.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# INICIALIZAÇÃO
# ============================================================
aplicar_estilos()

try:
    init_db()
except Exception as e:
    st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
    st.stop()

# ============================================================
# SESSION STATE — DEFAULTS
# ============================================================
DEFAULTS = {
    "usuario":      None,
    "pagina_atual": "Simulador",
    "resultado":    None,
}
for chave, valor in DEFAULTS.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

# ============================================================
# IMPORTAÇÃO DAS PÁGINAS
# (feita aqui para evitar importação circular)
# ============================================================
from pages.login    import pagina_login
from pages.simulador import pagina_simulador
from pages.historico import pagina_historico
from pages.usuarios  import pagina_usuarios

# ============================================================
# ROTEAMENTO — SEM USUÁRIO → LOGIN
# ============================================================
if st.session_state.usuario is None:
    pagina_login()
    st.stop()

# ============================================================
# USUÁRIO LOGADO
# ============================================================
u        = st.session_state.usuario
eh_admin = u["perfil"] == "ADMINISTRADOR"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 8px 0 16px;">
        <div style="font-size:1.7rem; font-weight:900; color:#FFFFFF;
                    letter-spacing:-0.03em; margin-bottom:2px;">
            Urba
        </div>
        <div style="font-size:.68rem; font-weight:700; letter-spacing:.12em;
                    text-transform:uppercase; color:rgba(255,255,255,.75);
                    margin-bottom:18px;">
            Score de Vendas
        </div>
        <hr style="border-color:rgba(255,255,255,.25); margin-bottom:16px;">
        <div style="font-size:.95rem; font-weight:700; color:#FFFFFF;">
            {u['nome']}
        </div>
        <div style="font-size:.78rem; color:rgba(255,255,255,.80); margin-bottom:6px;">
            {u['email']}
        </div>
        <div class="badge-perfil">{u['perfil']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("Sair", use_container_width=True, key="btn_sair"):
        for chave, valor in DEFAULTS.items():
            st.session_state[chave] = valor
        st.rerun()

# ============================================================
# HERO BANNER
# ============================================================
hero_banner()

# ============================================================
# NAVEGAÇÃO
# ============================================================
paginas_disponiveis = ["Simulador"]
if eh_admin:
    paginas_disponiveis += ["Histórico", "Usuários", "Empreendimentos"]

# Garante que a página atual é válida para o perfil
if st.session_state.pagina_atual not in paginas_disponiveis:
    st.session_state.pagina_atual = "Simulador"

icones = {
    "Simulador":       "🧮",
    "Histórico":       "📋",
    "Usuários":        "👥",
    "Empreendimentos": "🏘️",
}

nav_cols = st.columns(len(paginas_disponiveis) + 1)
for i, pag in enumerate(paginas_disponiveis):
    with nav_cols[i]:
        st.button(
            f"{icones[pag]} {pag}",
            type="primary" if st.session_state.pagina_atual == pag else "secondary",
            use_container_width=True,
            key=f"nav_{pag}",
            on_click=lambda p=pag: st.session_state.update({"pagina_atual": p}),
        )

st.divider()

# ============================================================
# ROTEAMENTO DE PÁGINAS
# ============================================================
pagina = st.session_state.pagina_atual

if pagina == "Simulador":
    pagina_simulador(u)

elif pagina == "Histórico":
    if eh_admin:
        pagina_historico()
    else:
        st.warning("⛔ Acesso restrito a administradores.")

elif pagina == "Usuários":
    if eh_admin:
        pagina_usuarios(u)
    else:
        st.warning("⛔ Acesso restrito a administradores.")

elif pagina == "Empreendimentos":
    if eh_admin:
        from pages.empreendimentos import pagina_empreendimentos
        pagina_empreendimentos()
    else:
        st.warning("⛔ Acesso restrito a administradores.")

# ============================================================
# RODAPÉ
# ============================================================
rodape(versao="V1.0")
