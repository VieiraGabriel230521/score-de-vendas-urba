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
    page_icon="assets/Logo verde.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# INICIALIZAÇÃO (roda só uma vez por sessão)
# ============================================================
aplicar_estilos()

if "db_iniciado" not in st.session_state:
    try:
        init_db()
        st.session_state.db_iniciado = True
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
# IMPORTS DAS PÁGINAS
# ============================================================
from pages.login      import pagina_login
from pages.simulador  import pagina_simulador
from pages.historico  import pagina_historico
from pages.usuarios   import pagina_usuarios

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

    # Botão Sair — cor forçada via CSS inline para garantir visibilidade
    st.markdown("""
    <style>
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background-color: rgba(255,255,255,0.15) !important;
        color: #FFFFFF !important;
        border: 1.5px solid rgba(255,255,255,0.5) !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background-color: rgba(255,255,255,0.28) !important;
        color: #FFFFFF !important;
        border-color: rgba(255,255,255,0.8) !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button p,
    [data-testid="stSidebar"] [data-testid="stButton"] button span {
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Sair", use_container_width=True, key="btn_sair"):
        for chave, valor in DEFAULTS.items():
            st.session_state[chave] = valor
        st.rerun()

# ============================================================
# HERO BANNER
# ============================================================
hero_banner()

# ============================================================
# NAVEGAÇÃO — CSS para abas ativas com texto preto fundo verde escuro
# ============================================================
st.markdown("""
<style>
/* Aba INATIVA — borda verde, texto verde, fundo branco */
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #079D56 !important;
    border: 1.5px solid #079D56 !important;
    font-weight: 700 !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="secondary"] p,
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="secondary"] span {
    color: #079D56 !important;
}

/* Aba ATIVA — fundo verde escuro, texto PRETO */
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="primary"] {
    background-color: #056B3A !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 800 !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="primary"] p,
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button[kind="primary"] span {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

paginas_disponiveis = ["Simulador"]
if eh_admin:
    paginas_disponiveis += ["Histórico", "Usuários", "Empreendimentos"]

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
