# pages/login.py
# Score de Vendas Urba
# Página de login — visual inspirado na SpellUI (fundo com raios de luz e
# gradiente animado, título com blur reveal + shimmer, prévia do score em
# vidro, botão "rich" e campos com anel de foco). Tudo em CSS, sem JS.
#
# CORREÇÃO (V2.0) — "precisava clicar duas vezes para entrar":
# os campos ficam dentro de st.form; os valores vão junto com o clique e
# o Enter também entra.

import streamlit as st

from db import autenticar_usuario
from styles import aplicar_estilos_login, login_cabecalho, login_fundo, login_hero, login_rodape


def pagina_login() -> None:
    aplicar_estilos_login()
    login_fundo()

    st.markdown("<div style='height:7vh'></div>", unsafe_allow_html=True)
    col_hero, col_form = st.columns([1.2, 0.85], gap="large", vertical_alignment="center")

    with col_hero:
        login_hero()

    with col_form, st.container(key="login_box"):
        st.markdown(login_cabecalho(), unsafe_allow_html=True)

        with st.form("form_login", clear_on_submit=False, border=False):
            email = st.text_input("E-mail", placeholder="nome@urba.com.br", key="login_email")
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="login_senha")
            entrar = st.form_submit_button("Entrar", type="primary", icon=":material/arrow_forward:",
                                           use_container_width=True)

        if entrar:
            if not email.strip() or not senha:
                st.error("Preencha e-mail e senha.")
            else:
                try:
                    usuario = autenticar_usuario(email.strip().lower(), senha)
                except Exception:
                    usuario = False
                    st.error("Não foi possível validar o acesso agora. Tente novamente.")
                if usuario:
                    st.session_state.usuario      = usuario
                    st.session_state.pagina_atual = "Simulador"
                    st.session_state.resultado    = None
                    st.session_state.pop("login_senha", None)
                    st.rerun()
                elif usuario is None:
                    st.error("E-mail ou senha incorretos.")

        st.markdown(login_rodape(), unsafe_allow_html=True)
