from __future__ import annotations
# pages/parametros.py
# Score de Vendas Urba
# Aba "Parâmetros" (somente ADMINISTRADOR) — V2.0
#
# Permite editar, sem mexer no código:
#   - o PESO de cada variável;
#   - a NOTA de cada faixa (ex.: Score A-B = 5);
#   - os LIMITES de classificação (Baixo / Moderado / Alto).
# Cada "Salvar" cria uma nova versão (nada é sobrescrito). A versão usada
# fica gravada em cada simulação, para auditoria da premiação.
# Antes de salvar, mostra o impacto dos novos valores no histórico.

import logging

import numpy as np
import pandas as pd
import streamlit as st

from db import carregar_historico, carregar_parametros, listar_versoes_parametros, salvar_parametros
from styles import (
    CINZA_60, LARANJA, LIMAO, PINK, VERDE, kpi, limpar_html, secao,
)
from utils import (
    NOTA_MAX_PERMITIDA,
    PARAMETROS_PADRAO,
    PESO_MAX_PERMITIDO,
    VARIAVEIS,
    normalizar_parametros,
    rotulo_faixa,
    score_maximo,
    validar_parametros,
)

logger = logging.getLogger(__name__)

_CHAVE_PESO = "par_peso_{var}"
_CHAVE_NOTA = "par_nota_{var}_{i}"


def _escrever_nos_campos(params: dict) -> None:
    """Coloca um conjunto de parâmetros nos campos da tela."""
    p = normalizar_parametros(params)
    for var, peso in p["pesos"].items():
        st.session_state[_CHAVE_PESO.format(var=var)] = peso
    for var, faixas in p["notas"].items():
        for i, nota in enumerate(faixas.values()):
            st.session_state[_CHAVE_NOTA.format(var=var, i=i)] = nota
    st.session_state["par_lim_baixo"] = p["limites"]["baixo"]
    st.session_state["par_lim_mod"]   = p["limites"]["moderado"]


def _ler_dos_campos() -> dict:
    return normalizar_parametros({
        "pesos": {var: st.session_state.get(_CHAVE_PESO.format(var=var)) for var in VARIAVEIS},
        "notas": {
            var: {f: st.session_state.get(_CHAVE_NOTA.format(var=var, i=i))
                  for i, f in enumerate(faixas)}
            for var, faixas in PARAMETROS_PADRAO["notas"].items()
        },
        "limites": {
            "baixo":    st.session_state.get("par_lim_baixo"),
            "moderado": st.session_state.get("par_lim_mod"),
        },
    })


@st.cache_data(ttl=60, show_spinner=False)
def _historico_resumido() -> pd.DataFrame:
    df = carregar_historico()
    cols = ["score_proponente", "faixa_ato", "faixa_comprometimento",
            "faixa_etaria", "estado_civil", "classificacao"]
    return df[cols] if not df.empty else pd.DataFrame(columns=cols)


def _reclassificar(df: pd.DataFrame, params: dict) -> pd.Series:
    """Reclassifica o histórico inteiro de uma vez (vetorizado: rápido mesmo com milhares de linhas)."""
    n, pesos, lim = params["notas"], params["pesos"], params["limites"]
    colunas = {
        "score_credito":         "score_proponente",
        "ato":                   "faixa_ato",
        "comprometimento_renda": "faixa_comprometimento",
        "idade":                 "faixa_etaria",
        "estado_civil":          "estado_civil",
    }
    score = sum(df[col].map(n[var]).fillna(0) * pesos[var] for var, col in colunas.items())
    return pd.Series(
        np.select([score >= lim["baixo"], score >= lim["moderado"]],
                  ["BAIXO RISCO", "RISCO MODERADO"], "ALTO RISCO"),
        index=df.index,
    )


def _faixa_limites_html(maximo: int, moderado: int, baixo: int) -> str:
    mx = max(maximo, 1)
    a = min(max(moderado / mx * 100, 0), 100)
    b = min(max(baixo / mx * 100, a), 100)
    return limpar_html(f"""
    <div style="margin:4px 0 2px;">
      <div style="display:flex;height:16px;border-radius:999px;overflow:hidden;">
        <div style="width:{a:.1f}%;background:{PINK}"></div>
        <div style="width:{b-a:.1f}%;background:{LARANJA}"></div>
        <div style="flex:1;background:{VERDE}"></div>
      </div>
      <div style="position:relative;height:16px;font-size:.66rem;color:{CINZA_60};margin-top:3px;">
        <span style="position:absolute;left:0">0</span>
        <span style="position:absolute;left:{a:.1f}%;transform:translateX(-50%)">{moderado}</span>
        <span style="position:absolute;left:{b:.1f}%;transform:translateX(-50%)">{baixo}</span>
        <span style="position:absolute;right:0">{maximo}</span>
      </div>
      <div style="display:flex;gap:14px;font-size:.68rem;color:{CINZA_60};margin-top:2px;flex-wrap:wrap">
        <span><b style="color:{PINK}">●</b> <b style="color:#B0124F">Alto</b> abaixo de {moderado}</span>
        <span><b style="color:{LARANJA}">●</b> <b style="color:#B35A0A">Moderado</b> de {moderado} a {baixo-1}</span>
        <span><b style="color:{VERDE}">●</b> <b style="color:#006B3F">Baixo</b> a partir de {baixo}</span>
      </div>
    </div>""")


def pagina_parametros(usuario: dict) -> None:
    msg = st.session_state.pop("par_msg", None)
    if msg:
        st.success(msg, icon=":material/check_circle:")

    vigente_id, vigente = carregar_parametros()

    # Campos começam com a versão vigente (e voltam a ela se outra versão for salva)
    # (os campos também somem do session_state quando o admin troca de aba)
    if (st.session_state.get("par_base_id", "x") != vigente_id
            or "par_lim_baixo" not in st.session_state):
        _escrever_nos_campos(vigente)
        st.session_state["par_base_id"] = vigente_id

    origem = f"versão #{vigente_id}" if vigente_id else "valores padrão (nenhuma versão salva ainda)"
    secao("ajustes", "Parâmetros do score",
          f"Edite notas, pesos e limites. Em uso agora: {origem}. Cada alteração salva vira uma nova versão.")

    # ============================================================
    # 1. PESOS
    # ============================================================
    with st.container(key="card_pesos"):
        st.markdown("<div class='u-colhead'><span class='u-colhead-num'>1</span>"
                    "<span>Peso de cada variável</span></div>", unsafe_allow_html=True)
        st.caption("Quanto cada variável vale no total. Pontos da variável = nota da faixa × peso.")
        cols = st.columns(len(VARIAVEIS), gap="small")
        for col, (var, nome) in zip(cols, VARIAVEIS.items()):
            with col:
                st.number_input(nome, min_value=0, max_value=PESO_MAX_PERMITIDO, step=1,
                                key=_CHAVE_PESO.format(var=var))

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ============================================================
    # 2. NOTAS POR FAIXA
    # ============================================================
    with st.container(key="card_notas"):
        st.markdown("<div class='u-colhead'><span class='u-colhead-num'>2</span>"
                    "<span>Nota de cada faixa</span></div>", unsafe_allow_html=True)
        st.caption(f"De 0 a {NOTA_MAX_PERMITIDA}. A maior nota de cada variável define o máximo dela.")
        cols = st.columns(len(VARIAVEIS), gap="medium")
        for col, (var, nome) in zip(cols, VARIAVEIS.items()):
            with col:
                st.markdown(f"<div style='font-weight:700;font-size:.78rem;color:#006B3F;"
                            f"margin:2px 0 6px'>{nome}</div>", unsafe_allow_html=True)
                for i, faixa in enumerate(PARAMETROS_PADRAO["notas"][var]):
                    st.number_input(rotulo_faixa(faixa), min_value=0, max_value=NOTA_MAX_PERMITIDA,
                                    step=1, key=_CHAVE_NOTA.format(var=var, i=i))

    novo   = _ler_dos_campos()
    maximo = score_maximo(novo)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ============================================================
    # 3. LIMITES
    # ============================================================
    with st.container(key="card_limites"):
        st.markdown("<div class='u-colhead'><span class='u-colhead-num'>3</span>"
                    "<span>Limites de classificação</span></div>", unsafe_allow_html=True)
        st.caption(f"Pontuação máxima com estes pesos e notas: {maximo} pontos.")
        l1, l2, l3 = st.columns([1, 1, 2.4], gap="medium", vertical_alignment="center")
        with l1:
            st.number_input("Baixo risco a partir de", min_value=1, max_value=999, step=1, key="par_lim_baixo")
        with l2:
            st.number_input("Risco moderado a partir de", min_value=1, max_value=999, step=1, key="par_lim_mod")
        novo = _ler_dos_campos()
        with l3:
            st.markdown(_faixa_limites_html(maximo, novo["limites"]["moderado"], novo["limites"]["baixo"]),
                        unsafe_allow_html=True)

    erros    = validar_parametros(novo)
    alterado = novo != vigente

    # ============================================================
    # 4. IMPACTO + SALVAR
    # ============================================================
    st.divider()
    secao("grafico", "Impacto antes de salvar",
          "Como as simulações já registradas ficariam com os valores da tela.")

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    max_atual = score_maximo(vigente)
    k1.markdown(kpi("Pontuação máxima", str(maximo),
                    f"hoje: {max_atual}" if maximo != max_atual else "sem mudança", VERDE), unsafe_allow_html=True)
    k2.markdown(kpi("Baixo risco a partir de", str(novo["limites"]["baixo"]),
                    f"{novo['limites']['baixo'] / max(maximo, 1):.0%} do máximo".replace(".", ","), LIMAO),
                unsafe_allow_html=True)
    k3.markdown(kpi("Moderado a partir de", str(novo["limites"]["moderado"]),
                    f"{novo['limites']['moderado'] / max(maximo, 1):.0%} do máximo".replace(".", ","), LARANJA),
                unsafe_allow_html=True)

    mudariam_txt, det = "—", "sem simulações no histórico"
    try:
        hist = _historico_resumido()
    except Exception:
        logger.exception("Erro ao carregar histórico para impacto")
        hist = pd.DataFrame()
    tabela_impacto = None
    if not hist.empty and not erros:
        antes  = _reclassificar(hist, vigente)
        depois = _reclassificar(hist, novo)
        n_mud  = int((antes != depois).sum())
        mudariam_txt = f"{n_mud} de {len(hist)}"
        det = "mudariam de classificação" if n_mud else "nenhuma muda de classificação"
        ordem = ["BAIXO RISCO", "RISCO MODERADO", "ALTO RISCO"]
        tabela_impacto = pd.DataFrame({
            "Classificação": [rotulo_faixa(c) for c in ordem],
            "Hoje":          [int((antes == c).sum()) for c in ordem],
            "Com a tela":    [int((depois == c).sum()) for c in ordem],
        })
        tabela_impacto["Diferença"] = tabela_impacto["Com a tela"] - tabela_impacto["Hoje"]
    k4.markdown(kpi("Simulações afetadas", mudariam_txt, det, PINK), unsafe_allow_html=True)

    if tabela_impacto is not None and alterado:
        st.dataframe(tabela_impacto, hide_index=True, use_container_width=True)

    if erros:
        st.error("Corrija antes de salvar:\n\n" + "\n".join(f"- {e}" for e in erros))

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    obs = st.text_input("Motivo da alteração (fica no registro da versão)",
                        placeholder="Ex.: ajuste aprovado na reunião comercial de 13/11",
                        key="par_obs")

    b1, b2, b3 = st.columns([1.2, 1, 1], gap="small")
    with b1:
        if st.button("Salvar nova versão", icon=":material/save:", type="primary",
                     use_container_width=True, disabled=bool(erros) or not alterado, key="par_salvar"):
            try:
                novo_id = salvar_parametros(novo, usuario["email"], obs)
                st.session_state["par_base_id"] = novo_id
                st.session_state["par_msg"] = (f"Versão #{novo_id} salva. As próximas simulações "
                                               "já usam os novos valores.")
                st.session_state.pop("par_obs", None)
                st.rerun()
            except Exception:
                logger.exception("Erro ao salvar parâmetros")
                st.error("Não foi possível salvar agora. Tente novamente em instantes.")
    with b2:
        st.button("Descartar alterações", icon=":material/undo:", use_container_width=True,
                  disabled=not alterado, key="par_descartar",
                  on_click=_escrever_nos_campos, args=(vigente,))
    with b3:
        st.button("Carregar valores padrão", icon=":material/restart_alt:", use_container_width=True,
                  key="par_padrao", on_click=_escrever_nos_campos, args=(PARAMETROS_PADRAO,),
                  help="Só preenche a tela com os valores originais. Nada muda até você salvar.")
    if not alterado:
        st.caption("Nenhuma alteração em relação à versão em uso.")

    # ============================================================
    # 5. VERSÕES ANTERIORES
    # ============================================================
    st.divider()
    with st.expander("Versões salvas", icon=":material/history:"):
        try:
            versoes = listar_versoes_parametros()
        except Exception:
            logger.exception("Erro ao listar versões")
            st.error("Não foi possível carregar as versões agora.")
            return
        if versoes.empty:
            st.caption("Nenhuma versão salva ainda: o sistema usa os valores padrão.")
            return
        versoes["p"] = versoes["dados"].map(normalizar_parametros)
        tabela = pd.DataFrame({
            "Versão":     versoes["id"].map(lambda x: f"#{x}"),
            "Salva em":   pd.to_datetime(versoes["criado_em"]),
            "Por":        versoes["criado_por"],
            "Máximo":     versoes["p"].map(score_maximo),
            "Baixo ≥":    versoes["p"].map(lambda p: p["limites"]["baixo"]),
            "Moderado ≥": versoes["p"].map(lambda p: p["limites"]["moderado"]),
            "Motivo":     versoes["observacao"].fillna(""),
        })
        st.dataframe(tabela, hide_index=True, use_container_width=True,
                     column_config={"Salva em": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")})
        c1, c2 = st.columns([1.4, 1], vertical_alignment="bottom")
        with c1:
            escolha = st.selectbox("Trazer uma versão para a tela", versoes["id"].tolist(),
                                   format_func=lambda x: f"Versão #{x}", key="par_versao_sel")
        with c2:
            p_sel = versoes.loc[versoes["id"] == escolha, "p"].iloc[0]
            st.button("Carregar na tela", icon=":material/download:", use_container_width=True,
                      key="par_carregar_versao", on_click=_escrever_nos_campos, args=(p_sel,))
        st.caption("Carregar não altera nada: revise e clique em “Salvar nova versão” para voltar a usá-la.")
