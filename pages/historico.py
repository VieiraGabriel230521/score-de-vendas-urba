from __future__ import annotations
# pages/historico.py
# Score de Vendas Urba
# Página de histórico de simulações (somente ADMINISTRADOR)
# SEGURANÇA: CPF removido — exibe nome_proponente
#
# ALTERAÇÕES (V1.1):
# - Removido "Excluir todo o histórico".
# - Exclusão individual exige motivo + confirmação e é lógica (soft delete).
# - Mostra a simulação antes de excluir, para evitar excluir o ID errado.
# - Nova coluna "Manual" indica dados digitados pelo vendedor.
# - Erros técnicos vão para o log, não para a tela.

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from db import carregar_historico, excluir_simulacao

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")
logger = logging.getLogger(__name__)


def pagina_historico(usuario: dict | None = None) -> None:

    st.markdown("""
    <h2 style='color:#056B3A; font-size:1.3rem;
               font-weight:800; margin-bottom:8px;'>
        Histórico de Simulações
    </h2>
    """, unsafe_allow_html=True)

    # Mensagem pendente (sobrevive ao st.rerun)
    msg = st.session_state.pop("hist_msg", None)
    if msg:
        st.success(msg)

    # ── Carrega dados ──
    try:
        hist = carregar_historico()
    except Exception:
        logger.exception("Erro ao carregar histórico")
        st.error("Não foi possível carregar o histórico agora. Tente novamente em instantes.")
        return

    if hist.empty:
        st.info("Nenhuma simulação registrada ainda.")
        return

    # ============================================================
    # FILTROS
    # ============================================================
    f1, f2, f3 = st.columns(3)

    with f1:
        vendedores = sorted(x for x in hist["vendedor_nome"].fillna("").astype(str).unique() if x)
        filtro_v = st.selectbox("Vendedor", ["TODOS"] + vendedores, key="hist_filtro_v")

    with f2:
        emps = sorted(x for x in hist["empreendimento"].fillna("").astype(str).unique() if x)
        filtro_e = st.selectbox("Empreendimento", ["TODOS"] + emps, key="hist_filtro_e")

    with f3:
        classes = sorted(x for x in hist["classificacao"].fillna("").astype(str).unique() if x)
        filtro_c = st.selectbox("Classificação", ["TODAS"] + classes, key="hist_filtro_c")

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
    classif = exib["classificacao"].astype(str)
    k1.metric("Total de Simulações", len(exib))
    k2.metric("🟢 Baixo Risco",    int(classif.str.contains("BAIXO",    na=False).sum()))
    k3.metric("🟡 Risco Moderado", int(classif.str.contains("MODERADO", na=False).sum()))
    k4.metric("🔴 Alto Risco",     int(classif.str.contains("ALTO",     na=False).sum()))

    st.divider()

    # ============================================================
    # TABELA
    # ============================================================
    colunas_exib = [
        "id", "data_hora", "vendedor_nome", "empreendimento", "unidade",
        "nome_proponente",
        "score_proponente", "renda_total",
        "percentual_ato", "percentual_comprometimento",
        "score_final", "classificacao", "preenchimento_manual",
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
            "preenchimento_manual":       st.column_config.TextColumn("Manual",           width="medium",
                                                                      help="Dados digitados pelo vendedor (não lidos do SPC)"),
        },
    )

    # ============================================================
    # EXPORTAR CSV
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
    # EXCLUIR SIMULAÇÃO INDIVIDUAL (exclusão lógica, com motivo)
    # ============================================================
    with st.expander("🗑️ Excluir simulação", expanded=False):
        st.caption(
            "A simulação deixa de aparecer no histórico e nos indicadores, "
            "mas fica registrada no banco com quem excluiu, quando e o motivo."
        )

        sid = st.number_input("ID da simulação", min_value=1, step=1, key="hist_excluir_id")

        alvo = hist[hist["id"] == int(sid)]
        if alvo.empty:
            st.info("Nenhuma simulação ativa com esse ID.")
            return

        r = alvo.iloc[0]
        st.markdown(
            f"**#{int(r['id'])}** · {r['vendedor_nome']} · {r['empreendimento']} / {r['unidade']} · "
            f"{r['nome_proponente'] or '—'} · **{r['classificacao']}**"
        )

        motivo = st.text_input(
            "Motivo da exclusão *",
            placeholder="Ex.: simulação duplicada, valores digitados errados",
            key="hist_excluir_motivo",
        )
        confirmar = st.checkbox("Confirmo a exclusão desta simulação", key="hist_excluir_confirma")

        if st.button(
            "EXCLUIR ESTA SIMULAÇÃO",
            disabled=not (confirmar and motivo.strip()),
            key="hist_btn_excluir_individual",
        ):
            admin_email = (usuario or st.session_state.get("usuario") or {}).get("email", "desconhecido")
            try:
                if excluir_simulacao(int(sid), admin_email, motivo):
                    st.session_state["hist_msg"] = f"Simulação #{int(sid)} excluída."
                st.rerun()
            except Exception:
                logger.exception("Erro ao excluir simulação %s", sid)
                st.error("Não foi possível excluir agora. Tente novamente em instantes.")
