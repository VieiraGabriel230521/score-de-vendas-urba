# pages/usuarios.py
# Score de Vendas Urba
# Página de gestão de usuários (somente ADMINISTRADOR)
#
# ALTERAÇÕES (V2.0):
# - Visual padrão Urba.
# - Mais leve: em vez de um bloco + expander por usuário, uma tabela e um
#   painel "Gerenciar" para o usuário escolhido.
# - Mensagens de sucesso não somem mais no rerun.
# - Remover usuário pede confirmação; agora também dá para mudar o nome
#   e o perfil (função já existia no banco, mas não tinha tela).
# - Cadastro dentro de formulário: digitar não recarrega a página.
# - Erros técnicos vão para o log; a tela mostra mensagem orientativa.

import logging
import re

import streamlit as st

from db import (
    atualizar_usuario,
    criar_usuario,
    listar_usuarios,
    redefinir_senha,
    remover_usuario,
)
from styles import secao

logger = logging.getLogger(__name__)
_EMAIL_OK = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _flash(texto: str) -> None:
    st.session_state["usr_msg"] = texto


def pagina_usuarios(usuario_logado: dict) -> None:
    secao("usuarios", "Usuários", "Quem acessa o simulador e com qual perfil.")

    msg = st.session_state.pop("usr_msg", None)
    if msg:
        st.success(msg, icon=":material/check_circle:")

    # ============================================================
    # CRIAR NOVO USUÁRIO
    # ============================================================
    with st.expander("Adicionar usuário", icon=":material/person_add:"):
        with st.form("form_novo_usuario", clear_on_submit=False, border=False):
            n1, n2 = st.columns(2)
            with n1:
                novo_nome  = st.text_input("Nome completo *")
                novo_email = st.text_input("E-mail *", placeholder="nome@urba.com.br")
            with n2:
                novo_perfil = st.selectbox("Perfil *", ["VENDEDOR", "ADMINISTRADOR"],
                                           format_func=str.title)
                nova_senha  = st.text_input("Senha inicial * (mín. 6 caracteres)", type="password")
            criar = st.form_submit_button("Criar usuário", type="primary", icon=":material/add:")

        if criar:
            email = (novo_email or "").strip().lower()
            if not all([novo_nome.strip(), email, nova_senha]):
                st.error("Preencha todos os campos obrigatórios.")
            elif not _EMAIL_OK.match(email):
                st.error("E-mail inválido.")
            elif len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    criar_usuario(novo_nome, email, nova_senha, novo_perfil)
                    _flash(f"Usuário {email} criado.")
                    st.rerun()
                except Exception as e:
                    if "unique" in str(e).lower():
                        st.error("Este e-mail já está cadastrado.")
                    else:
                        logger.exception("Erro ao criar usuário")
                        st.error("Não foi possível criar o usuário agora.")

    # ============================================================
    # LISTA
    # ============================================================
    try:
        df = listar_usuarios()
    except Exception:
        logger.exception("Erro ao listar usuários")
        st.error("Não foi possível carregar os usuários agora.")
        return

    if df.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    ativos = int(df["ativo"].sum())
    st.caption(f"{len(df)} usuário(s) · {ativos} ativo(s) · "
               f"{int((df['perfil'] == 'ADMINISTRADOR').sum())} administrador(es)")

    exib = df.assign(
        perfil=df["perfil"].str.title(),
        status=df["ativo"].map({True: "Ativo", False: "Inativo"}),
    )[["nome", "email", "perfil", "status", "criado_em"]]
    st.dataframe(
        exib, hide_index=True, use_container_width=True,
        column_config={
            "nome":      st.column_config.TextColumn("Nome", width="medium"),
            "email":     st.column_config.TextColumn("E-mail", width="medium"),
            "perfil":    st.column_config.TextColumn("Perfil", width="small"),
            "status":    st.column_config.TextColumn("Status", width="small"),
            "criado_em": st.column_config.DatetimeColumn("Criado em", format="DD/MM/YYYY", width="small"),
        },
    )

    # ============================================================
    # GERENCIAR UM USUÁRIO
    # ============================================================
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.container(key="card_gerenciar"):
        st.markdown("<div class='u-colhead'><span class='u-colhead-num'>✓</span>"
                    "<span>Gerenciar usuário</span></div>", unsafe_allow_html=True)

        ids = df["id"].tolist()
        uid = st.selectbox(
            "Usuário", ids, key="usr_sel",
            format_func=lambda i: f"{df.loc[df.id == i, 'nome'].iloc[0]} — {df.loc[df.id == i, 'email'].iloc[0]}",
        )
        row = df.loc[df["id"] == uid].iloc[0]
        eh_proprio = str(row["email"]) == str(usuario_logado["email"])
        if eh_proprio:
            st.caption("Este é você: perfil, status e remoção ficam bloqueados para não perder o acesso.")

        c1, c2, c3 = st.columns([1.6, 1, 1], gap="medium")
        with c1:
            nome = st.text_input("Nome", value=row["nome"], key=f"usr_nome_{uid}")
        with c2:
            perfil = st.selectbox("Perfil", ["VENDEDOR", "ADMINISTRADOR"],
                                  index=0 if row["perfil"] == "VENDEDOR" else 1,
                                  format_func=str.title, disabled=eh_proprio, key=f"usr_perfil_{uid}")
        with c3:
            ativo = st.toggle("Ativo", value=bool(row["ativo"]), disabled=eh_proprio, key=f"usr_ativo_{uid}")

        mudou = (nome.strip() != row["nome"] or perfil != row["perfil"] or ativo != bool(row["ativo"]))
        if st.button("Salvar dados", icon=":material/save:", type="primary",
                     disabled=not mudou or not nome.strip(), key=f"usr_salvar_{uid}"):
            try:
                atualizar_usuario(int(uid), nome, perfil, ativo)
                _flash(f"Dados de {row['email']} atualizados.")
                st.rerun()
            except Exception:
                logger.exception("Erro ao atualizar usuário")
                st.error("Não foi possível salvar agora.")

        st.divider()
        s1, s2 = st.columns(2, gap="large")
        with s1:
            with st.form(f"form_senha_{uid}", border=False, clear_on_submit=True):
                nova = st.text_input("Nova senha (mín. 6 caracteres)", type="password")
                trocar = st.form_submit_button("Redefinir senha", icon=":material/key:")
            if trocar:
                if len(nova or "") < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    try:
                        redefinir_senha(int(uid), nova)
                        st.success("Senha redefinida.")
                    except Exception:
                        logger.exception("Erro ao redefinir senha")
                        st.error("Não foi possível redefinir agora.")
        with s2:
            if not eh_proprio:
                st.caption("Remover apaga o acesso de vez. Para só bloquear, desative.")
                conf = st.checkbox("Confirmo remover este usuário", key=f"usr_conf_{uid}")
                if st.button("Remover usuário", icon=":material/delete:", disabled=not conf,
                             key=f"usr_remover_{uid}"):
                    try:
                        remover_usuario(int(uid))
                        _flash(f"Usuário {row['email']} removido.")
                        st.session_state.pop("usr_sel", None)
                        st.rerun()
                    except Exception:
                        logger.exception("Erro ao remover usuário")
                        st.error("Não foi possível remover agora.")
