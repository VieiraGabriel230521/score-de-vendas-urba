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

        # ── Formulário com st.form para evitar duplo clique ──
        with st.form(key="form_login", clear_on_submit=False):
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

            submitted = st.form_submit_button(
                "ENTRAR",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            # ── Validação básica ──
            if not email or not senha:
                st.error("Preencha e-mail e senha.")
                return

            # ── Autenticação ──
            with st.spinner("Verificando credenciais..."):
                usuario = autenticar_usuario(email.strip().lower(), senha)

            if usuario:
                st.session_state.usuario      = usuario
                st.session_state.pagina_atual = "Simulador"
                st.session_state.resultado    = None
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos, ou usuário inativo.")

        # ── Rodapé do card ──
        st.markdown("""
        <div style="text-align:center; margin-top:20px;">
            <span style="font-size:.75rem; color:#9CA3AF;">
                Problemas de acesso? Fale com o administrador do sistema.
            </span>
        </div>
        """, unsafe_allow_html=True)
