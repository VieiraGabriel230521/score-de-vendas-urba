from __future__ import annotations
# pages/empreendimentos.py
# Score de Vendas Urba
# Página de gestão de empreendimentos (somente ADMINISTRADOR)
# CORREÇÃO: bug do upload Excel — buffer lido duas vezes corrigido com io.BytesIO

import io

import pandas as pd
import streamlit as st

from db import (
    carregar_empreendimentos,
    importar_empreendimentos_xlsx,
    inserir_empreendimento,
    remover_empreendimento,
    toggle_empreendimento,
)
from utils import mapear_colunas_xlsx


def pagina_empreendimentos() -> None:

    st.markdown("""
    <h2 style='color:#056B3A; font-size:1.3rem;
               font-weight:800; margin-bottom:8px;'>
        Gestão de Empreendimentos
    </h2>
    """, unsafe_allow_html=True)
    st.caption("Cadastre os empreendimentos e unidades disponíveis para simulação.")

    # ============================================================
    # IMPORTAR VIA EXCEL
    # ============================================================
    with st.expander("📥 Importar via planilha Excel (.xlsx)", expanded=False):
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

                    st.success(f"✅ **{len(df_xl)}** linhas válidas encontradas na aba **{aba}**.")
                    st.dataframe(
                        df_xl[["Empreendimento", "Unidade"]].head(10),
                        use_container_width=True,
                        hide_index=True,
                    )

                    if st.button("📥 IMPORTAR PARA O BANCO", type="primary", key="emp_btn_importar"):
                        with st.spinner("Importando..."):
                            inseridos, ignorados = importar_empreendimentos_xlsx(
                                df_xl[["Empreendimento", "Unidade"]]
                            )
                        st.success(
                            f"✅ Importação concluída: "
                            f"**{inseridos}** inseridos, **{ignorados}** ignorados (duplicatas)."
                        )
                        st.rerun()
                else:
                    cols_encontradas = ", ".join(df_xl.columns.tolist())
                    st.error(
                        f"Colunas **Empreendimento** e **Unidade** não encontradas. "
                        f"Colunas detectadas: `{cols_encontradas}`. "
                        f"Renomeie as colunas na planilha e tente novamente."
                    )

            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")

    # ============================================================
    # ADICIONAR MANUALMENTE
    # ============================================================
    with st.expander("➕ Adicionar empreendimento manualmente", expanded=False):
        a1, a2 = st.columns(2)
        with a1:
            novo_emp = st.text_input("Empreendimento *", key="emp_novo_emp")
        with a2:
            nova_uni = st.text_input("Unidade *", key="emp_nova_uni")

        if st.button("ADICIONAR", type="primary", key="emp_btn_adicionar"):
            if not novo_emp or not nova_uni:
                st.error("Preencha empreendimento e unidade.")
            else:
                try:
                    inserir_empreendimento(novo_emp, nova_uni)
                    st.success(f"✅ **{novo_emp} — {nova_uni}** adicionado com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar: {e}")

    st.divider()

    # ============================================================
    # LISTA DE EMPREENDIMENTOS
    # ============================================================
    try:
        df = carregar_empreendimentos()
    except Exception as e:
        st.error(f"Erro ao carregar empreendimentos: {e}")
        return

    if df.empty:
        st.info("Nenhum empreendimento cadastrado ainda.")
        return

    # ── Filtro ──
    emps = sorted(df["empreendimento"].dropna().astype(str).unique().tolist())
    filtro = st.selectbox(
        "Filtrar por empreendimento",
        ["TODOS"] + emps,
        key="emp_filtro",
    )

    exib = df.copy()
    if filtro != "TODOS":
        exib = exib[exib["empreendimento"].astype(str) == filtro]

    st.markdown(f"""
    <div style='font-size:.85rem; color:#6B7280; margin-bottom:12px;'>
        {len(exib)} unidade(s) encontrada(s)
    </div>
    """, unsafe_allow_html=True)

    # ── Tabela com ações ──
    for _, row in exib.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])

            with c1:
                st.markdown(f"**{row['empreendimento']}**")
            with c2:
                st.caption(f"Unidade: {row['unidade']}")
            with c3:
                status = "🟢 Ativo" if row["ativo"] else "🔴 Inativo"
                st.markdown(status)
            with c4:
                col_tog, col_del = st.columns(2)
                with col_tog:
                    label = "Desativar" if row["ativo"] else "Ativar"
                    if st.button(label, key=f"emp_toggle_{row['id']}"):
                        toggle_empreendimento(row["id"], not row["ativo"])
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"emp_del_{row['id']}", help="Remover permanentemente"):
                        remover_empreendimento(row["id"])
                        st.rerun()
