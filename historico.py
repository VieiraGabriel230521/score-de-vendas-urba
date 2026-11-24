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
#
# ALTERAÇÕES (V2.0):
# - Visual padrão Urba: cards de indicador e barra de distribuição.
# - Nova coluna "Parâm." com a versão dos parâmetros usada no cálculo.
# - Classificação com destaque de cor na tabela.

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from db import carregar_historico, excluir_simulacao
from styles import LARANJA, LIMAO, PINK, VERDE, html_md, kpi, secao

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")
logger = logging.getLogger(__name__)


def pagina_historico(usuario: dict | None = None) -> None:

    secao("historico", "Histórico de simulações",
          "Todas as simulações salvas pelos vendedores.")

    # Mensagem pendente (sobrevive ao st.rerun)
    msg = st.session_state.pop("hist_msg", None)
    if msg:
        st.success(msg, icon=":material/check_circle:")

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
    classif = exib["classificacao"].astype(str)
    total   = len(exib)
    n_baixo = int(classif.str.contains("BAIXO",    na=False).sum())
    n_mod   = int(classif.str.contains("MODERADO", na=False).sum())
    n_alto  = int(classif.str.contains("ALTO",     na=False).sum())

    def _pct(n: int) -> str:
        return f"{n / total:.0%} do total" if total else "—"

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    media = exib["score_final"].dropna()
    k1.markdown(kpi("Simulações", f"{total:,}".replace(",", "."),
                    f"score médio {media.mean():.0f}" if not media.empty else "", LIMAO), unsafe_allow_html=True)
    k2.markdown(kpi("Baixo risco",    str(n_baixo), _pct(n_baixo), VERDE,   "#006B3F"), unsafe_allow_html=True)
    k3.markdown(kpi("Risco moderado", str(n_mod),   _pct(n_mod),   LARANJA, "#B35A0A"), unsafe_allow_html=True)
    k4.markdown(kpi("Alto risco",     str(n_alto),  _pct(n_alto),  PINK,    "#B0124F"), unsafe_allow_html=True)

    if total:
        html_md(f"""
        <div style="display:flex;height:12px;border-radius:999px;overflow:hidden;margin:6px 0 16px;">
          <div style="width:{n_baixo/total*100:.2f}%;background:{VERDE}"></div>
          <div style="width:{n_mod/total*100:.2f}%;background:{LARANJA}"></div>
          <div style="width:{n_alto/total*100:.2f}%;background:{PINK}"></div>
        </div>""")

    # ============================================================
    # TABELA
    # ============================================================
    colunas_exib = [
        "id", "data_hora", "vendedor_nome", "empreendimento", "unidade",
        "nome_proponente",
        "score_proponente", "renda_total",
        "percentual_ato", "percentual_comprometimento",
        "score_final", "classificacao", "preenchimento_manual", "parametros_id",
    ]
    colunas_exib = [c for c in colunas_exib if c in exib.columns]

    tabela = exib[colunas_exib]  # sem Styler: renderiza bem mais rápido

    st.dataframe(
        tabela,
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
            "parametros_id":              st.column_config.NumberColumn("Parâm.",         width="small",
                                                                        help="Versão dos parâmetros usada no cálculo (vazio = padrão)"),
        },
    )

    # ============================================================
    # EXPORTAR CSV
    # ============================================================
    st.download_button(
        label="Baixar histórico filtrado (CSV)",
        icon=":material/download:",
        data=exib.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),  # abre certo no Excel pt-BR
        file_name=f"score_vendas_urba_{datetime.now(TIMEZONE_BRASILIA).strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        key="hist_download",
    )

    st.divider()

    # ============================================================
    # EXCLUIR SIMULAÇÃO INDIVIDUAL (exclusão lógica, com motivo)
    # ============================================================
    with st.expander("Excluir simulação", expanded=False, icon=":material/delete:"):
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
            "Excluir esta simulação",
            icon=":material/delete:",
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
