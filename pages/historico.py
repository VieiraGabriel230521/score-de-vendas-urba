from __future__ import annotations
# pages/historico.py
# Score de Vendas Urba
# Página de histórico de simulações (somente ADMINISTRADOR)
# SEGURANÇA: CPF removido — exibe nome_proponente

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from db import carregar_historico, excluir_historico, excluir_simulacao
from utils import brl

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")


def pagina_historico() -> None:

    st.markdown("""
    <h2 style='color:#056B3A; font-size:1.3rem;
               font-weight:800; margin-bottom:8px;'>
        Histórico de Simulações
    </h2>
    """, unsafe_allow_html=True)

    # ── Carrega dados ──
    try:
        hist = carregar_historico()
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return

    if hist.empty:
        st.info("Nenhuma simulação registrada ainda.")
        return

    # ============================================================
    # FILTROS
    # ============================================================
    f1, f2, f3 = st.columns(3)

    with f1:
        vendedores = sorted(
            x for x in hist["vendedor_nome"].fillna("").astype(str).unique() if x
        )
        filtro_v = st.selectbox("Vendedor", ["TODOS"] + vendedores, key="hist_filtro_v")

    with f2:
        emps = sorted(
            x for x in hist["empreendimento"].fillna("").astype(str).unique() if x
        )
        filtro_e = st.selectbox("Empreendimento", ["TODOS"] + emps, key="hist_filtro_e")

    with f3:
        classes = sorted(
            x for x in hist["classificacao"].fillna("").astype(str).unique() if x
        )
        filtro_c = st.selectbox("Classificação", ["TODAS"] + classes, key="hist_filtro_c")

    # ── Aplica filtros ──
    exib = hist.copy()
    if filtro_v != "TODOS":
        exib = exib[exib["vendedor_nome"].astype(str) == filtro_v]
    if filtro_e != "TODOS":
        exib = exib[exib["empreendimento"].astype(str) == filtro_e]
    if filtro_c != "TODAS":
        exib = exib[exib["classificacao"].astype(str) == filtro_c]

    # ============================================================
    # KPIs
    # ============================================================
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de Simulações", len(exib))
    k2.metric(
        "🟢 Baixo Risco",
        int(exib["classificacao"].astype(str).str.contains("BAIXO", na=False).sum()),
    )
    k3.metric(
        "🟡 Risco Moderado",
        int(exib["classificacao"].astype(str).str.contains("MODERADO", na=False).sum()),
    )
    k4.metric(
        "🔴 Alto Risco",
        int(exib["classificacao"].astype(str).str.contains("ALTO", na=False).sum()),
    )

    st.divider()

    # ============================================================
    # TABELA — sem CPF, com nome_proponente
    # ============================================================
    colunas_exib = [
        "id", "data_hora", "vendedor_nome", "empreendimento", "unidade",
        "nome_proponente",
        "score_proponente", "renda_total",
        "percentual_ato", "percentual_comprometimento",
        "score_final", "classificacao",
    ]
    colunas_exib = [c for c in colunas_exib if c in exib.columns]

    st.dataframe(
        exib[colunas_exib],
        use_container_width=True,
        hide_index=True,
        column_config={
            "id":                         st.column_config.NumberColumn("ID",             width="small"),
            "data_hora":                  st.column_config.DatetimeColumn("Data/Hora",    width="medium", format="DD/MM/YYYY HH:mm"),
            "vendedor_nome":              st.column_config.TextColumn("Vendedor",         width="medium"),
            "empreendimento":             st.column_config.TextColumn("Empreendimento",   width="medium"),
            "unidade":                    st.column_config.TextColumn("Unidade",          width="small"),
            "nome_proponente":            st.column_config.TextColumn("Proponente",       width="medium"),
            "score_proponente":           st.column_config.TextColumn("Score SPC",        width="small"),
            "renda_total":                st.column_config.NumberColumn("Renda Total",    width="medium", format="R$ %.2f"),
            "percentual_ato":             st.column_config.NumberColumn("% Ato",          width="small",  format="%.2f%%"),
            "percentual_comprometimento": st.column_config.NumberColumn("% Comp.",        width="small",  format="%.2f%%"),
            "score_final":                st.column_config.NumberColumn("Score",          width="small"),
            "classificacao":              st.column_config.TextColumn("Classificação",    width="medium"),
        },
    )

    # ============================================================
    # EXPORTAR CSV — sem CPF
    # ============================================================
    st.download_button(
        label="⬇️ BAIXAR HISTÓRICO (CSV)",
        data=exib.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"score_vendas_urba_{datetime.now(TIMEZONE_BRASILIA).strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
        key="hist_download",
    )

    st.divider()

    # ============================================================
    # EXCLUIR SIMULAÇÃO INDIVIDUAL
    # ============================================================
    with st.expander("🗑️ Excluir simulação individual", expanded=False):
        sid = st.number_input(
            "ID da simulação a excluir",
            min_value=1, step=1,
            key="hist_excluir_id",
        )
        if st.button("EXCLUIR ESTA SIMULAÇÃO", key="hist_btn_excluir_individual"):
            try:
                excluir_simulacao(int(sid))
                st.success(f"Simulação #{sid} excluída com sucesso.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")

    # ============================================================
    # EXCLUIR TODO O HISTÓRICO
    # ============================================================
    with st.expander("⚠️ Excluir todo o histórico", expanded=False):
        st.warning("Esta ação exclui **TODOS** os registros e não pode ser desfeita.")
        confirmar = st.checkbox(
            "Confirmo que desejo excluir TODO o histórico",
            key="hist_confirmar_exclusao",
        )
        if st.button(
            "EXCLUIR TODO O HISTÓRICO",
            type="primary",
            disabled=not confirmar,
            key="hist_btn_excluir_tudo",
        ):
            try:
                excluir_historico()
                st.success("Histórico excluído com sucesso.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
