# pages/login.py
# Score de Vendas Urba
# Página de login

import streamlit as st

from db import autenticar_usuario
from styles import login_card


def pagina_login() -> None:

    # CSS extra — fundo cinza claro na tela de login
    st.markdown("""
    <style>
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main, .block-container {
        background-color: #F4F6F8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Centraliza o card
    _, col, _ = st.columns([1, 1.4, 1])

    with col:

        # ── Cabeçalho do card ──
        login_card()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Campos fora do form para reatividade imediata ──
        email = st.text_input(
            "E-MAIL",
            placeholder="nome@urba.com.br",
            key="login_email",
        )
        senha = st.text_input(
            "SENHA",
            type="password",
            placeholder="••••••••",
            key="login_senha",
        )

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── Guarda erro no session_state para não perder entre reruns ──
        if "login_erro" not in st.session_state:
            st.session_state.login_erro = ""

        if st.button(
            "ENTRAR",
            type="primary",
            use_container_width=True,
            key="btn_entrar",
        ):
            st.session_state.login_erro = ""

            if not email or not senha:
                st.session_state.login_erro = "Preencha e-mail e senha."
            else:
                usuario = autenticar_usuario(email.strip().lower(), senha)
                if usuario:
                    # Limpa erro e seta usuário ANTES do rerun
                    st.session_state.login_erro = ""
                    st.session_state.usuario      = usuario
                    st.session_state.pagina_atual = "Simulador"
                    st.session_state.resultado    = None
                    st.rerun()
                else:
                    st.session_state.login_erro = "E-mail ou senha incorretos, ou usuário inativo."

        # Exibe erro persistido no session_state
        if st.session_state.login_erro:
            st.error(st.session_state.login_erro)

        # ── Rodapé do card ──
        st.markdown("""
        <div style="text-align:center; margin-top:20px;">
            <span style="font-size:.75rem; color:#9CA3AF;">
                Problemas de acesso? Fale com o administrador do sistema.
            </span>
        </div>
        """, unsafe_allow_html=True)
