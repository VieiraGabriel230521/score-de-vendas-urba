# pages/usuarios.py
# Score de Vendas Urba
# Página de gestão de usuários (somente ADMINISTRADOR)

import streamlit as st

from db import (
    criar_usuario,
    listar_usuarios,
    redefinir_senha,
    remover_usuario,
    toggle_usuario,
)


def pagina_usuarios(usuario_logado: dict) -> None:

    st.markdown("""
    <h2 style='color:#056B3A; font-size:1.3rem;
               font-weight:800; margin-bottom:8px;'>
        Gestão de Usuários
    </h2>
    """, unsafe_allow_html=True)

    # ============================================================
    # CRIAR NOVO USUÁRIO
    # ============================================================
    with st.expander("➕ Adicionar novo usuário", expanded=False):
        n1, n2 = st.columns(2)
        with n1:
            novo_nome  = st.text_input("Nome completo *", key="usr_novo_nome")
            novo_email = st.text_input("E-mail *",        key="usr_novo_email")
        with n2:
            novo_perfil = st.selectbox(
                "Perfil *",
                ["VENDEDOR", "ADMINISTRADOR"],
                key="usr_novo_perfil",
            )
            nova_senha = st.text_input(
                "Senha *",
                type="password",
                key="usr_nova_senha",
            )

        if st.button("CRIAR USUÁRIO", type="primary", key="usr_btn_criar"):
            if not all([novo_nome, novo_email, nova_senha]):
                st.error("Preencha todos os campos obrigatórios.")
            elif len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    criar_usuario(novo_nome, novo_email, nova_senha, novo_perfil)
                    st.success(f"✅ Usuário **{novo_email}** criado com sucesso.")
                    st.rerun()
                except Exception as e:
                    if "unique" in str(e).lower():
                        st.error("Este e-mail já está cadastrado.")
                    else:
                        st.error(f"Erro ao criar usuário: {e}")

    st.divider()

    # ============================================================
    # LISTA DE USUÁRIOS
    # ============================================================
    try:
        df_usuarios = listar_usuarios()
    except Exception as e:
        st.error(f"Erro ao listar usuários: {e}")
        return

    if df_usuarios.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    st.markdown(f"""
    <div style='font-size:.85rem; color:#6B7280; margin-bottom:12px;'>
        {len(df_usuarios)} usuário(s) cadastrado(s)
    </div>
    """, unsafe_allow_html=True)

    for _, row in df_usuarios.iterrows():
        eh_proprio = str(row["email"]) == str(usuario_logado["email"])

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([2, 2.5, 1.2, 1, 1])

            with c1:
                st.markdown(f"**{row['nome']}**")
                if eh_proprio:
                    st.caption("(você)")

            with c2:
                st.caption(row["email"])

            with c3:
                badge_cor = "#079D56" if row["perfil"] == "ADMINISTRADOR" else "#6B7280"
                st.markdown(
                    f"<span style='background:{badge_cor}; color:#fff; "
                    f"border-radius:12px; padding:2px 10px; font-size:.75rem; "
                    f"font-weight:700;'>{row['perfil']}</span>",
                    unsafe_allow_html=True,
                )

            with c4:
                status_txt = "🟢 Ativo" if row["ativo"] else "🔴 Inativo"
                st.markdown(status_txt)

            with c5:
                if not eh_proprio:
                    if row["ativo"]:
                        if st.button(
                            "Desativar",
                            key=f"usr_desativar_{row['id']}",
                            use_container_width=True,
                        ):
                            toggle_usuario(row["id"], False)
                            st.rerun()
                    else:
                        if st.button(
                            "Ativar",
                            key=f"usr_ativar_{row['id']}",
                            use_container_width=True,
                        ):
                            toggle_usuario(row["id"], True)
                            st.rerun()

        # ── Redefinir senha ──
        with st.expander(f"🔑 Redefinir senha — {row['email']}", expanded=False):
            nova = st.text_input(
                "Nova senha",
                type="password",
                key=f"usr_nova_senha_{row['id']}",
            )
            col_salvar, col_remover = st.columns(2)

            with col_salvar:
                if st.button(
                    "SALVAR NOVA SENHA",
                    key=f"usr_salvar_senha_{row['id']}",
                    type="primary",
                ):
                    if not nova:
                        st.error("Digite a nova senha.")
                    elif len(nova) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres.")
                    else:
                        redefinir_senha(row["id"], nova)
                        st.success("✅ Senha redefinida com sucesso.")

            with col_remover:
                if not eh_proprio:
                    if st.button(
                        "REMOVER USUÁRIO",
                        key=f"usr_remover_{row['id']}",
                    ):
                        remover_usuario(row["id"])
                        st.success(f"Usuário {row['email']} removido.")
                        st.rerun()
