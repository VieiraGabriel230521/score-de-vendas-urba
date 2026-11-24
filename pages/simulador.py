from __future__ import annotations
# pages/simulador.py
# Score de Vendas Urba — Página do simulador
# SEGURANÇA: CPF não é extraído, exibido nem armazenado.
# Identificação do cliente feita apenas por Nome Completo.
#
# ALTERAÇÕES (V1.1):
# - Data de nascimento ganhou preenchimento manual.
# - Campos digitados manualmente são registrados em "preenchimento_manual".
# - Textos vindos do SPC/cadastro são escapados antes de entrar em HTML.
# - Mensagem de "salvo com sucesso" aparece mesmo após o rerun.
# - Erros técnicos vão para o log; a tela mostra mensagem orientativa.
#
# ALTERAÇÕES (V2.0):
# - Notas, pesos e limites vêm da aba "Parâmetros" (banco), não mais fixos
#   no código. A versão dos parâmetros usada fica gravada na simulação.
# - Novo visual: etapas numeradas, velocímetro do score, barras por
#   variável e cards de sugestão. Mesma lógica de cálculo.
# - O SPC só é lido uma vez por arquivo (cache): antes era relido a cada
#   clique/digitação na tela, o que deixava tudo lento.
# - Se os parâmetros mudarem entre "Calcular" e "Salvar", o resultado é
#   recalculado e o vendedor é avisado.

import html
import logging
from datetime import date

import streamlit as st

from db import carregar_empreendimentos, carregar_parametros, salvar_simulacao
from styles import (
    CINZA_60, LARANJA, LIMAO, VERDE, VERDE_ESCURO, PINK,
    aviso_faltando, barras_notas, card_score, cenario_item, col_header,
    icone, kpi, resumo_grid, secao,
)
from utils import (
    VARIAVEIS,
    brl,
    calcular_idade,
    calcular_notas,
    calcular_score_total,
    campo_moeda,
    classificar_score,
    extrair_dados_spc,
    faixa_comprometimento,
    faixa_etaria,
    faixa_ato,
    montar_cenarios,
    nota_maxima,
    rotulo_faixa,
    rotulo_unidade,
    score_maximo,
)

logger = logging.getLogger(__name__)


def _esc(valor) -> str:
    """Escapa texto antes de inserir em HTML (unsafe_allow_html)."""
    return html.escape(str(valor), quote=True)


def _ler_spc(arquivo) -> dict:
    """
    Lê o PDF uma única vez por arquivo enviado. O resultado fica só na
    sessão do vendedor (não é compartilhado entre usuários) e é apagado
    ao limpar o formulário.
    """
    cache = st.session_state.setdefault("_spc_cache", {})
    chave = getattr(arquivo, "file_id", None) or f"{arquivo.name}-{arquivo.size}"
    if chave not in cache:
        dados = extrair_dados_spc(arquivo)
        dados.pop("texto_extraido", None)  # não guarda o texto do SPC
        cache[chave] = dados
    return cache[chave]


def _limpar_formulario() -> None:
    """Troca o sufixo das keys: o Streamlit recria todos os campos zerados."""
    st.session_state["sim_versao"] = st.session_state.get("sim_versao", 0) + 1
    st.session_state.pop("resultado", None)
    st.session_state.pop("_spc_cache", None)


def _linha_dado(rotulo: str, valor: str | None) -> str:
    val = f"<b>{_esc(valor)}</b>" if valor else '<b class="falta">Não localizado</b>'
    return f'<div class="u-dado-row"><span>{rotulo}</span>{val}</div>'


def _recalcular(d: dict, params: dict, params_id) -> dict:
    notas = calcular_notas(d["score_proponente"], d["faixa_at"], d["faixa_comp"],
                           d["faixa_idade"], d["estado_civil"], params)
    score = calcular_score_total(notas, params)
    classificacao, cor = classificar_score(score, params)
    return {**d, "notas": notas, "score_final": score, "classificacao": classificacao,
            "cor": cor, "parametros_id": params_id}


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_simulador(usuario: dict) -> None:

    st.session_state.setdefault("sim_versao", 0)
    v = st.session_state["sim_versao"]

    msg = st.session_state.pop("sim_msg", None)
    if msg:
        st.success(msg, icon=":material/check_circle:")

    params_id, params = carregar_parametros()

    secao("calculadora", "Nova simulação",
          "Preencha as quatro etapas. O score é calculado na hora, sem sair da tela.")

    try:
        cadastro = carregar_empreendimentos()
    except Exception:
        logger.exception("Erro ao carregar empreendimentos")
        st.error("Não foi possível carregar os empreendimentos agora. Tente novamente em instantes.")
        return

    col_emp, col_cliente, col_proposta, col_renda = st.columns([1.15, 1.15, 1, 1], gap="small")

    manuais: list[str] = []

    # ────────────────────────────────────────────────────────
    # 1. EMPREENDIMENTO
    # ────────────────────────────────────────────────────────
    with col_emp, st.container(key="card_emp"):
        col_header(1, "Empreendimento")

        if cadastro.empty:
            st.warning("Nenhum empreendimento cadastrado. Solicite ao administrador.")
            empreendimento = ""
            unidade        = ""
        else:
            nomes = cadastro["empreendimento"].dropna().astype(str).str.strip()
            empreendimentos = sorted(nomes[nomes.ne("")].unique().tolist())
            empreendimento = st.selectbox(
                "Empreendimento *", [""] + empreendimentos, index=0,
                key=f"sim_empreendimento_{v}",
                format_func=lambda x: x or "Selecione",
            )
            if empreendimento:
                uni = cadastro.loc[
                    cadastro["empreendimento"].astype(str).str.strip() == str(empreendimento).strip(),
                    "unidade",
                ].dropna().astype(str).str.strip()
                unidades = sorted(uni[uni.ne("")].unique().tolist(), key=lambda x: x.zfill(30))
            else:
                unidades = []

            unidade = st.selectbox(
                "Unidade *", [""] + unidades, index=0,
                disabled=not bool(empreendimento),
                key=f"sim_unidade_{v}",
                format_func=lambda val: rotulo_unidade(val, empreendimento) if val else "Selecione a unidade",
            )

    # ────────────────────────────────────────────────────────
    # 2. PERFIL DO CLIENTE
    # ────────────────────────────────────────────────────────
    with col_cliente, st.container(key="card_cliente"):
        col_header(2, "Perfil do cliente")

        pdf_prop = st.file_uploader(
            "SPC do proponente (PDF) *", type=["pdf"], key=f"sim_pdf_prop_{v}",
        )

        score_proponente = None
        renda_proponente = 0.0
        nascimento       = None
        idade            = None
        faixa_idade      = None
        nome_proponente  = ""

        if pdf_prop:
            try:
                with st.spinner("Lendo o SPC..."):
                    dados = _ler_spc(pdf_prop)

                score_proponente = dados.get("score_faixa")
                renda_proponente = float(dados.get("renda_presumida") or 0)
                nascimento       = dados.get("data_nascimento")
                nome_proponente  = dados.get("nome_completo") or ""

                st.markdown(
                    '<div class="u-dado"><div class="u-dado-tit">'
                    f'{icone("check", VERDE, 14)} Lido do SPC</div>'
                    + _linha_dado("Nome", nome_proponente)
                    + _linha_dado("Nascimento", nascimento.strftime("%d/%m/%Y") if nascimento else None)
                    + _linha_dado("Score", f"{dados.get('score_letra')} → {score_proponente}" if score_proponente else None)
                    + _linha_dado("Renda presumida", brl(renda_proponente) if renda_proponente > 0 else None)
                    + "</div>",
                    unsafe_allow_html=True,
                )
            except Exception:
                logger.exception("Falha na leitura do SPC do proponente")
                st.error("Não foi possível ler este SPC. Confira o arquivo ou preencha os campos abaixo.")

        # ── Preenchimento manual (quando o SPC não traz o dado) ──
        if pdf_prop and not nome_proponente:
            nome_proponente = st.text_input(
                "Nome do proponente (manual)", placeholder="Nome completo",
                key=f"sim_nome_manual_{v}",
            ).strip()
            if nome_proponente:
                manuais.append("Nome")

        if pdf_prop and not nascimento:
            nascimento = st.date_input(
                "Data de nascimento (manual)", value=None,
                min_value=date(1920, 1, 1), max_value=date.today(),
                format="DD/MM/YYYY", key=f"sim_nasc_manual_{v}",
            )
            if nascimento:
                manuais.append("Nascimento")

        if pdf_prop and not score_proponente:
            score_proponente = st.selectbox(
                "Score SPC (manual)", ["", "A - B", "C - D", "E - F"],
                key=f"sim_score_manual_{v}",
                format_func=lambda x: x or "Selecione",
            ) or None
            if score_proponente:
                manuais.append("Score")

        if pdf_prop and renda_proponente <= 0:
            renda_proponente = campo_moeda("Renda presumida (manual, R$)", f"sim_renda_manual_{v}")
            if renda_proponente > 0:
                manuais.append("Renda")

        if nascimento:
            idade       = calcular_idade(nascimento)
            faixa_idade = faixa_etaria(idade)

        estado_civil = st.selectbox(
            "Estado civil *", ["", "SOLTEIRO(A)", "DIVORCIADO(A)", "CASADO(A)"], index=0,
            key=f"sim_estado_civil_{v}",
            format_func=lambda x: rotulo_faixa(x) if x else "Selecione",
        )

    # ────────────────────────────────────────────────────────
    # 3. DADOS DA PROPOSTA
    # ────────────────────────────────────────────────────────
    with col_proposta, st.container(key="card_proposta"):
        col_header(3, "Proposta")
        ato_urba        = campo_moeda("Ato Urba (R$) *",                      f"sim_ato_urba_{v}")
        valor_proposta  = campo_moeda("Valor da proposta / líquido CV (R$) *", f"sim_valor_proposta_{v}")
        primeira_mensal = campo_moeda("Valor da 1ª mensal (R$) *",             f"sim_primeira_mensal_{v}")

    # ────────────────────────────────────────────────────────
    # 4. COMPOSIÇÃO DE RENDA
    # ────────────────────────────────────────────────────────
    with col_renda, st.container(key="card_renda"):
        col_header(4, "Composição de renda")
        st.caption("Só quando houver cliente adicional compondo renda.")

        qtd_adicionais = st.number_input(
            "Clientes adicionais", min_value=0, max_value=4, value=0, step=1,
            key=f"sim_qtd_adicionais_{v}",
        )

        rendas_adicionais = []
        for i in range(int(qtd_adicionais)):
            numero = i + 2
            with st.expander(f"Cliente {numero}", expanded=True, icon=":material/person:"):
                pdf_add = st.file_uploader(
                    f"SPC — cliente {numero}", type=["pdf"], key=f"sim_pdf_add_{numero}_{v}",
                )
                renda_add = 0.0
                if pdf_add:
                    try:
                        d_add     = _ler_spc(pdf_add)
                        renda_add = float(d_add.get("renda_presumida") or 0)
                        if renda_add > 0:
                            st.success(f"Renda identificada: {brl(renda_add)}")
                        else:
                            st.warning("Renda não localizada no SPC.")
                    except Exception:
                        logger.exception("Falha na leitura do SPC do cliente %s", numero)
                        st.error("Não foi possível ler este SPC. Informe a renda manualmente.")
                if pdf_add and renda_add <= 0:
                    renda_add = campo_moeda(f"Renda manual — cliente {numero} (R$)",
                                            f"sim_renda_add_manual_{numero}_{v}")
                    if renda_add > 0:
                        manuais.append(f"Renda Cliente {numero}")
                rendas_adicionais.append(renda_add)

    # ── Cálculos instantâneos ────────────────────────────────
    renda_total = renda_proponente + sum(rendas_adicionais)
    perc_ato    = ato_urba / valor_proposta * 100 if valor_proposta > 0 else 0
    perc_comp   = primeira_mensal / renda_total * 100 if renda_total > 0 else 0
    faixa_at    = faixa_ato(perc_ato)
    faixa_comp  = faixa_comprometimento(perc_comp)

    def _tom(nota: int, var: str) -> str:
        mx = nota_maxima(params, var) or 1
        return VERDE_ESCURO if nota / mx >= .75 else ("#B35A0A" if nota / mx >= .4 else "#B0124F")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    tem_ato  = valor_proposta > 0
    tem_comp = renda_total > 0 and primeira_mensal > 0
    m1.markdown(kpi("% do ato", f"{perc_ato:.2f}%".replace(".", ",") if tem_ato else "—",
                    rotulo_faixa(faixa_at) if tem_ato else "Informe ato e proposta", VERDE,
                    _tom(params["notas"]["ato"][faixa_at], "ato") if tem_ato else CINZA_60),
                unsafe_allow_html=True)
    m2.markdown(kpi("Comprometimento", f"{perc_comp:.2f}%".replace(".", ",") if tem_comp else "—",
                    rotulo_faixa(faixa_comp) if tem_comp else "Informe renda e mensal", LARANJA,
                    _tom(params["notas"]["comprometimento_renda"][faixa_comp], "comprometimento_renda") if tem_comp else CINZA_60),
                unsafe_allow_html=True)
    m3.markdown(kpi("Renda total", brl(renda_total) if renda_total else "—",
                    f"{1 + int(qtd_adicionais)} cliente(s)", LIMAO), unsafe_allow_html=True)
    m4.markdown(kpi("Faixa etária", f"{idade} anos" if idade is not None else "—",
                    rotulo_faixa(faixa_idade) if faixa_idade else "Aguardando nascimento", PINK),
                unsafe_allow_html=True)

    # ── Validação ────────────────────────────────────────────
    faltando = []
    if not empreendimento:   faltando.append("Empreendimento")
    if not unidade:          faltando.append("Unidade")
    if not pdf_prop:         faltando.append("SPC do proponente")
    if pdf_prop and not nascimento:       faltando.append("Data de nascimento")
    if pdf_prop and not score_proponente: faltando.append("Score SPC")
    if not estado_civil:     faltando.append("Estado civil")
    if renda_total <= 0:     faltando.append("Renda presumida")
    if valor_proposta <= 0:  faltando.append("Valor da proposta")
    if primeira_mensal <= 0: faltando.append("1ª mensal")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c_aviso, c_btn = st.columns([3, 1], gap="medium", vertical_alignment="center")
    with c_aviso:
        if faltando:
            st.markdown(aviso_faltando(faltando), unsafe_allow_html=True)
    with c_btn:
        calcular = st.button(
            "Calcular score", icon=":material/speed:", type="primary",
            use_container_width=True, disabled=bool(faltando), key=f"sim_calcular_{v}",
        )

    # ── Cálculo do score ─────────────────────────────────────
    if calcular:
        st.session_state["resultado"] = _recalcular({
            "empreendimento":          empreendimento,
            "unidade":                 unidade,
            "nome_proponente":         nome_proponente,
            "idade":                   idade,
            "faixa_idade":             faixa_idade,
            "estado_civil":            estado_civil,
            "score_proponente":        score_proponente,
            "renda_proponente":        renda_proponente,
            "qtd_clientes_adicionais": int(qtd_adicionais),
            "renda_adicionais":        sum(rendas_adicionais),
            "renda_total":             renda_total,
            "ato_urba":                ato_urba,
            "valor_proposta":          valor_proposta,
            "perc_ato":                perc_ato,
            "faixa_at":                faixa_at,
            "primeira_mensal":         primeira_mensal,
            "perc_comp":               perc_comp,
            "faixa_comp":              faixa_comp,
            "preenchimento_manual":    ", ".join(manuais),
        }, params, params_id)

    # ── Resultado ────────────────────────────────────────────
    d = st.session_state.get("resultado")
    if not d:
        return

    # Parâmetros mudaram depois do cálculo? Recalcula com os vigentes.
    if d.get("parametros_id") != params_id:
        d = _recalcular(d, params, params_id)
        st.session_state["resultado"] = d
        st.info("Os parâmetros do score foram atualizados pelo administrador. O resultado abaixo já usa os novos valores.")

    maximo = score_maximo(params)
    lim    = params["limites"]

    st.divider()
    secao("alvo", "Resultado da simulação",
          f"{_esc(d.get('empreendimento') or '—')} · {_esc(rotulo_unidade(d.get('unidade'), d.get('empreendimento')) or '—')}")

    col_score, col_detalhe = st.columns([1, 1.75], gap="large")

    with col_score:
        st.markdown(card_score(d["score_final"], maximo, d["classificacao"], d["cor"],
                               lim["moderado"], lim["baixo"]), unsafe_allow_html=True)

    with col_detalhe:
        faixas = {
            "score_credito":         d.get("score_proponente") or "—",
            "ato":                   d.get("faixa_at") or "—",
            "comprometimento_renda": d.get("faixa_comp") or "—",
            "idade":                 d.get("faixa_idade") or "—",
            "estado_civil":          d.get("estado_civil") or "—",
        }
        linhas = []
        for var, peso in params["pesos"].items():
            nmax = nota_maxima(params, var)
            linhas.append({
                "nome": VARIAVEIS[var], "faixa": rotulo_faixa(faixas[var]),
                "nota": d["notas"][var], "nota_max": nmax, "peso": peso,
                "pontos": d["notas"][var] * peso, "maximo": nmax * peso,
            })
        st.markdown(barras_notas(linhas), unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(resumo_grid([
        ("Proponente",      _esc(d.get("nome_proponente") or "—")),
        ("Renda total",     brl(d.get("renda_total", 0))),
        ("Ato Urba",        brl(d.get("ato_urba", 0))),
        ("Valor da proposta", brl(d.get("valor_proposta", 0))),
        ("1ª mensal",       brl(d.get("primeira_mensal", 0))),
        ("Score SPC",       _esc(d.get("score_proponente") or "—")),
        ("Estado civil",    _esc(rotulo_faixa(d.get("estado_civil")) or "—")),
        ("Clientes na renda", str(1 + int(d.get("qtd_clientes_adicionais") or 0))),
    ]), unsafe_allow_html=True)

    if d.get("preenchimento_manual"):
        st.caption(f"Preenchido manualmente: {d['preenchimento_manual']} — fica registrado no histórico.")

    # ════════════════════════════════════════════════════════
    # ESTRATÉGIAS DE MELHORIA
    # ════════════════════════════════════════════════════════
    if d["classificacao"] != "BAIXO RISCO":
        st.divider()
        faltam_mod   = max(0, lim["moderado"] - d["score_final"])
        faltam_baixo = max(0, lim["baixo"] - d["score_final"])
        partes = []
        if faltam_mod:
            partes.append(f"faltam <b>{faltam_mod} pts</b> para risco moderado")
        partes.append(f"faltam <b>{faltam_baixo} pts</b> para baixo risco")
        secao("lampada", "Como melhorar esta venda", "; ".join(partes).capitalize() + ".", LARANJA)

        cenarios = montar_cenarios(
            d["score_final"], d["notas"], d["renda_total"],
            d["primeira_mensal"], d["ato_urba"], d["valor_proposta"], params,
        )
        if cenarios:
            st.markdown("".join(
                cenario_item(c["Variável"], c["Ajuste"], c["Ganho"], c["NovoScore"], c["NovaClassificacao"])
                for c in cenarios[:8]
            ), unsafe_allow_html=True)
            st.caption("Sugestões são simulações: não alteram dados do cliente.")
        else:
            st.caption("Ato e comprometimento já estão na melhor faixa possível.")

    # ════════════════════════════════════════════════════════
    # SALVAR
    # ════════════════════════════════════════════════════════
    st.divider()
    b1, b2, _ = st.columns([1.3, 1.1, 1.6], gap="small")

    with b1:
        if st.button("Confirmar e salvar no histórico", icon=":material/save:", type="primary",
                     use_container_width=True, key=f"sim_salvar_{v}"):
            try:
                salvar_simulacao(d, usuario["email"], usuario["nome"])
                st.session_state["sim_msg"] = "Simulação salva no histórico."
                _limpar_formulario()
                st.rerun()
            except Exception:
                logger.exception("Erro ao salvar simulação")
                st.error("Não foi possível salvar agora. Tente novamente em instantes.")

    with b2:
        st.button("Nova simulação (sem salvar)", icon=":material/restart_alt:", type="secondary",
                  use_container_width=True, key=f"sim_nova_{v}", on_click=_limpar_formulario)
