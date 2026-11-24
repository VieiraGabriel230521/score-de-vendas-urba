# app.py
# Score de Vendas Urba
# Arquivo principal — ponto de entrada do Streamlit
#
# ALTERAÇÕES (V2.0):
# - Redesign no padrão visual Urba (topo em gradiente, abas em pílula,
#   sem sidebar). Nome e e-mail continuam escapados antes do HTML.
# - init_db roda uma vez por servidor (cache), não a cada sessão.
# - Nova aba "Parâmetros" (admin): notas, pesos e limites do score.
# - Botão "Sair" limpa toda a sessão (antes ficavam dados do formulário).

import logging

import streamlit as st

from db import init_db
from styles import aplicar_estilos, hero_banner, rodape

VERSAO = "V2.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Score de Vendas | Urba",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)
aplicar_estilos()

# ============================================================
# BANCO (uma vez por servidor)
# ============================================================
try:
    init_db()
except Exception:
    logger.exception("Erro ao conectar ao banco de dados")
    st.error("Não foi possível conectar ao banco de dados. Tente novamente em instantes.")
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
    st.session_state.setdefault(chave, valor)

from pages.login import pagina_login  # noqa: E402

# ============================================================
# SEM USUÁRIO → LOGIN
# ============================================================
if st.session_state.usuario is None:
    pagina_login()
    st.stop()

# ============================================================
# USUÁRIO LOGADO
# ============================================================
u        = st.session_state.usuario
eh_admin = u["perfil"] == "ADMINISTRADOR"

hero_banner(u)

PAGINAS = {
    "Simulador":       ":material/calculate:",
    "Histórico":       ":material/history:",
    "Parâmetros":      ":material/tune:",
    "Usuários":        ":material/group:",
    "Empreendimentos": ":material/apartment:",
}
disponiveis = ["Simulador"] + (["Histórico", "Parâmetros", "Usuários", "Empreendimentos"] if eh_admin else [])
if st.session_state.pagina_atual not in disponiveis:
    st.session_state.pagina_atual = "Simulador"


def _ir_para(pagina: str) -> None:
    st.session_state.pagina_atual = pagina


def _sair() -> None:
    st.session_state.clear()


with st.container(key="navbar", horizontal=True, horizontal_alignment="distribute",
                  vertical_alignment="center"):
    with st.container(key="nav_tabs", horizontal=True, gap="small"):
        for pag in disponiveis:
            st.button(
                pag,
                icon=PAGINAS[pag],
                type="primary" if st.session_state.pagina_atual == pag else "secondary",
                key=f"nav_{pag}",
                on_click=_ir_para,
                args=(pag,),
            )
    st.button("Sair", icon=":material/logout:", key="nav_sair", on_click=_sair)


# ============================================================
# ROTEAMENTO (imports sob demanda: só carrega a página aberta)
# ============================================================
pagina = st.session_state.pagina_atual

if pagina == "Simulador":
    from pages.simulador import pagina_simulador
    pagina_simulador(u)
elif not eh_admin:
    st.warning("Acesso restrito a administradores.")
elif pagina == "Histórico":
    from pages.historico import pagina_historico
    pagina_historico(u)
elif pagina == "Parâmetros":
    from pages.parametros import pagina_parametros
    pagina_parametros(u)
elif pagina == "Usuários":
    from pages.usuarios import pagina_usuarios
    pagina_usuarios(u)
elif pagina == "Empreendimentos":
    from pages.empreendimentos import pagina_empreendimentos
    pagina_empreendimentos()

rodape(versao=VERSAO)
