from __future__ import annotations
# pages/empreendimentos.py
# Score de Vendas Urba
# Página de gestão de empreendimentos (somente ADMINISTRADOR)
# CORREÇÃO: bug do upload Excel — buffer lido duas vezes corrigido com io.BytesIO
#
# ALTERAÇÕES (V2.0):
# - Visual padrão Urba.
# - A lista agora mostra também os INATIVOS (antes, ao desativar, a unidade
#   sumia da tela e não havia como reativar).
# - Lista em tabela editável (marcar ativo / remover em lote) em vez de um
#   bloco com 2 botões por unidade — muito mais leve com centenas de lotes.
# - Remoção pede confirmação. Mensagens não somem mais no rerun.

import io

import pandas as pd
import streamlit as st

import logging

from db import (
    atualizar_status_empreendimentos,
    importar_empreendimentos_xlsx,
    inserir_empreendimento,
    listar_empreendimentos_admin,
    remover_empreendimentos,
)
from styles import secao
from utils import mapear_colunas_xlsx

logger = logging.getLogger(__name__)


def pagina_empreendimentos() -> None:

    secao("predio", "Empreendimentos",
          "Empreendimentos e unidades que aparecem para o vendedor no simulador.")

    msg = st.session_state.pop("emp_msg", None)
    if msg:
        st.success(msg, icon=":material/check_circle:")

    # ============================================================
    # IMPORTAR VIA EXCEL
    # ============================================================
    with st.expander("Importar planilha Excel (.xlsx)", expanded=False, icon=":material/upload_file:"):
        st.caption(
            "A planilha deve ter colunas **Empreendimento** e **Unidade** "
            "(ou variações como 'empreendimentos', 'quadra/lote')."
        )
        arquivo = st.file_uploader(
            "Selecione o arquivo .xlsx",
            type=["xlsx"],
            key="emp_upload_xlsx",
        )

        if arquivo:
            try:
                # ── CORREÇÃO: lê os bytes uma vez e reutiliza com BytesIO ──
                # O problema anterior: pd.ExcelFile consumia o buffer do arquivo,
                # e pd.read_excel não conseguia mais ler (buffer já no final).
                conteudo = arquivo.read()

                xl   = pd.ExcelFile(io.BytesIO(conteudo), engine="openpyxl")
                abas = xl.sheet_names

                aba = st.selectbox("Selecione a aba", abas, key="emp_aba")

                # Usa um novo BytesIO para o read_excel (buffer independente)
                df_xl = pd.read_excel(io.BytesIO(conteudo), sheet_name=aba, engine="openpyxl")
                df_xl = mapear_colunas_xlsx(df_xl)

                if {"Empreendimento", "Unidade"}.issubset(df_xl.columns):
                    # Remove linhas completamente vazias
                    df_xl = df_xl.dropna(subset=["Empreendimento", "Unidade"], how="all")
                    df_xl["Empreendimento"] = df_xl["Empreendimento"].astype(str).str.strip()
                    df_xl["Unidade"]        = df_xl["Unidade"].astype(str).str.strip()
                    df_xl = df_xl[
                        df_xl["Empreendimento"].ne("") & df_xl["Empreendimento"].ne("nan") &
                        df_xl["Unidade"].ne("")        & df_xl["Unidade"].ne("nan")
                    ]

                    st.success(f"**{len(df_xl)}** linhas válidas na aba **{aba}**.")
                    st.dataframe(
                        df_xl[["Empreendimento", "Unidade"]].head(10),
                        use_container_width=True,
                        hide_index=True,
                    )

                    if st.button("Importar para o banco", icon=":material/upload:",
                                 type="primary", key="emp_btn_importar"):
                        with st.spinner("Importando..."):
                            inseridos, ignorados = importar_empreendimentos_xlsx(
                                df_xl[["Empreendimento", "Unidade"]]
                            )
                        st.session_state["emp_msg"] = (
                            f"Importação concluída: {inseridos} inseridos, "
                            f"{ignorados} ignorados (já existiam)."
                        )
                        st.session_state.pop("emp_upload_xlsx", None)
                        st.rerun()
                else:
                    cols_encontradas = ", ".join(df_xl.columns.tolist())
                    st.error(
                        f"Colunas **Empreendimento** e **Unidade** não encontradas. "
                        f"Colunas detectadas: `{cols_encontradas}`. "
                        f"Renomeie as colunas na planilha e tente novamente."
                    )

            except Exception:
                logger.exception("Erro ao ler planilha de empreendimentos")
                st.error("Não foi possível ler este arquivo. Confira se é um .xlsx válido.")

    # ============================================================
    # ADICIONAR MANUALMENTE
    # ============================================================
    with st.expander("Adicionar unidade manualmente", expanded=False, icon=":material/add_home:"):
        with st.form("form_nova_unidade", border=False, clear_on_submit=True):
            a1, a2 = st.columns(2)
            with a1:
                novo_emp = st.text_input("Empreendimento *")
            with a2:
                nova_uni = st.text_input("Unidade *", placeholder="Ex.: Q01 L05")
            adicionar = st.form_submit_button("Adicionar", type="primary", icon=":material/add:")
        if adicionar:
            if not novo_emp.strip() or not nova_uni.strip():
                st.error("Preencha empreendimento e unidade.")
            else:
                try:
                    if inserir_empreendimento(novo_emp, nova_uni):
                        st.session_state["emp_msg"] = f"{novo_emp.strip()} — {nova_uni.strip()} adicionado."
                        st.rerun()
                    else:
                        st.warning("Essa unidade já está cadastrada.")
                except Exception:
                    logger.exception("Erro ao adicionar empreendimento")
                    st.error("Não foi possível adicionar agora.")

    # ============================================================
    # LISTA (ativos e inativos) — tabela editável
    # ============================================================
    try:
        df = listar_empreendimentos_admin()
    except Exception:
        logger.exception("Erro ao carregar empreendimentos")
        st.error("Não foi possível carregar os empreendimentos agora.")
        return

    if df.empty:
        st.info("Nenhum empreendimento cadastrado ainda.")
        return

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1.4, 1.4, 1], gap="medium")
    with f1:
        emps = sorted(df["empreendimento"].dropna().astype(str).unique().tolist())
        filtro = st.selectbox("Empreendimento", ["TODOS"] + emps, key="emp_filtro",
                              format_func=lambda x: "Todos" if x == "TODOS" else x)
    with f2:
        busca = st.text_input("Buscar unidade", placeholder="Ex.: Q01", key="emp_busca")
    with f3:
        status = st.selectbox("Status", ["Todos", "Ativos", "Inativos"], key="emp_status")

    exib = df.copy()
    if filtro != "TODOS":
        exib = exib[exib["empreendimento"].astype(str) == filtro]
    if busca.strip():
        exib = exib[exib["unidade"].astype(str).str.contains(busca.strip(), case=False, regex=False)]
    if status == "Ativos":
        exib = exib[exib["ativo"]]
    elif status == "Inativos":
        exib = exib[~exib["ativo"]]

    st.caption(f"{len(exib)} unidade(s) na lista · {int(df['ativo'].sum())} ativa(s) de {len(df)} no total. "
               "Marque/desmarque “Ativa” ou “Remover” e clique em Salvar.")

    exib = exib.assign(remover=False).set_index("id")
    editado = st.data_editor(
        exib[["empreendimento", "unidade", "ativo", "remover"]],
        hide_index=True, use_container_width=True, height=min(420, 38 + 35 * max(len(exib), 1)),
        disabled=["empreendimento", "unidade"],
        column_config={
            "empreendimento": st.column_config.TextColumn("Empreendimento", width="medium"),
            "unidade":        st.column_config.TextColumn("Unidade", width="medium"),
            "ativo":          st.column_config.CheckboxColumn("Ativa", width="small"),
            "remover":        st.column_config.CheckboxColumn("Remover", width="small"),
        },
        key=f"emp_editor_{st.session_state.get('emp_ed_v', 0)}_{filtro}_{busca}_{status}",
    )

    mudou_status = editado["ativo"] != exib["ativo"]
    ativar    = [int(i) for i in editado.index[mudou_status & editado["ativo"]]]
    desativar = [int(i) for i in editado.index[mudou_status & ~editado["ativo"]]]
    remover   = [int(i) for i in editado.index[editado["remover"]]]

    if ativar or desativar or remover:
        partes = []
        if ativar:    partes.append(f"{len(ativar)} para ativar")
        if desativar: partes.append(f"{len(desativar)} para desativar")
        if remover:   partes.append(f"{len(remover)} para remover de vez")
        st.info("Alterações pendentes: " + ", ".join(partes) + ".")
        conf_ok = True
        if remover:
            conf_ok = st.checkbox("Confirmo a remoção permanente das unidades marcadas", key="emp_conf_remover")
        if st.button("Salvar alterações", icon=":material/save:", type="primary",
                     disabled=not conf_ok, key="emp_salvar"):
            try:
                atualizar_status_empreendimentos(
                    [i for i in ativar if i not in remover],
                    [i for i in desativar if i not in remover],
                )
                n = remover_empreendimentos(remover)
                st.session_state["emp_ed_v"] = st.session_state.get("emp_ed_v", 0) + 1
                st.session_state["emp_msg"] = "Alterações salvas." + (f" {n} unidade(s) removida(s)." if n else "")
                st.rerun()
            except Exception:
                logger.exception("Erro ao salvar empreendimentos")
                st.error("Não foi possível salvar agora.")
