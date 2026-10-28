# pages/simulador.py
# Score de Vendas Urba — Página do simulador

from __future__ import annotations

import pandas as pd
import streamlit as st

from db import carregar_empreendimentos, salvar_simulacao
from styles import card_resumo, col_header, secao_titulo
from utils import (
    LIMITE_BAIXO,
    LIMITE_MODERADO,
    NOTAS_ESTADO_CIVIL,
    PESOS,
    SCORE_MAX,
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
    rotulo_unidade,
)


def pagina_simulador(usuario: dict) -> None:

    # ── Título da seção ──────────────────────────────────────
    secao_titulo("🧮", "Dados da Simulação",
                 "Preencha as informações abaixo para calcular o score de risco da venda.")

    # ── Carrega empreendimentos ──────────────────────────────
    cadastro = carregar_empreendimentos()

    # ── Formulário — 4 colunas ───────────────────────────────
    col_emp, col_cliente, col_proposta, col_renda = st.columns(4, gap="medium")

    # ── EMPREENDIMENTO ───────────────────────────────────────
    with col_emp:
        col_header("🏘️", "Empreendimento")

        if cadastro.empty:
            st.warning("Nenhum empreendimento cadastrado. Solicite ao administrador.")
            empreendimento = ""
            unidade        = ""
        else:
            empreendimentos = sorted(
                cadastro["empreendimento"]
                .dropna().astype(str).str.strip()
                .loc[lambda x: x.ne("")].unique().tolist()
            )
            empreendimento = st.selectbox(
                "Empreendimento *",
                [""] + empreendimentos,
                index=0,
                key="sim_empreendimento",
            )
            if empreendimento:
                unidades = sorted(
                    cadastro.loc[
                        cadastro["empreendimento"].astype(str).str.strip()
                        == str(empreendimento).strip(),
                        "unidade",
                    ]
                    .dropna().astype(str).str.strip()
                    .loc[lambda x: x.ne("")].unique().tolist(),
                    key=lambda x: x.zfill(30),
                )
            else:
                unidades = []

            unidade = st.selectbox(
                "Unidade *",
                [""] + unidades,
                index=0,
                disabled=not bool(empreendimento),
                key="sim_unidade",
                format_func=lambda v: rotulo_unidade(v, empreendimento) if v else "Selecione a unidade",
            )
            if unidade:
                st.caption(f"📍 {rotulo_unidade(unidade, empreendimento)}")

    # ── PERFIL DO CLIENTE ────────────────────────────────────
    with col_cliente:
        col_header("👤", "Perfil do Cliente")
        st.caption("Anexe o relatório SPC do proponente.")

        pdf_prop = st.file_uploader(
            "SPC do Proponente *",
            type=["pdf"],
            key="sim_pdf_prop",
        )

        score_proponente = None
        renda_proponente = 0.0
        nascimento       = None
        idade            = None
        faixa_idade      = None
        cpf_proponente   = ""

        if pdf_prop:
            try:
                with st.spinner("Lendo SPC do proponente..."):
                    dados = extrair_dados_spc(pdf_prop)

                score_proponente = dados.get("score_faixa")
                renda_proponente = float(dados.get("renda_presumida") or 0)
                nascimento       = dados.get("data_nascimento")
                cpf_proponente   = dados.get("cpf") or ""

                if nascimento:
                    idade       = calcular_idade(nascimento)
                    faixa_idade = faixa_etaria(idade)

                st.markdown("""
                <div style='font-weight:700; font-size:.82rem; color:#056B3A;
                            text-transform:uppercase; letter-spacing:.06em;
                            margin:12px 0 8px;'>
                    ✅ Dados identificados no SPC
                </div>
                """, unsafe_allow_html=True)

                with st.container(border=True):
                    st.caption("CPF do Proponente")
                    st.markdown(f"**{cpf_proponente}**" if cpf_proponente else "*Não localizado*")
                    if nascimento:
                        st.caption("Data de Nascimento")
                        st.markdown(
                            f"**{nascimento.strftime('%d/%m/%Y')}** "
                            f"— {idade} anos — {faixa_idade}"
                        )
                    else:
                        st.warning("Data de nascimento não localizada.")
                    st.caption("Score SPC")
                    st.markdown(
                        f"**{dados.get('score_letra') or '—'} → {score_proponente}**"
                        if score_proponente else "*Não localizado*"
                    )
                    st.caption("Renda Presumida")
                    st.markdown(
                        f"**{brl(renda_proponente)}**"
                        if renda_proponente > 0 else "*Não localizada*"
                    )
            except Exception as e:
                st.error(f"Falha na leitura do SPC: {e}")

        if pdf_prop and not cpf_proponente:
            cpf_proponente = st.text_input(
                "CPF — preenchimento manual",
                placeholder="000.000.000-00",
                key="sim_cpf_manual",
            ).strip()

        if pdf_prop and not score_proponente:
            score_proponente = st.selectbox(
                "Score SPC — preenchimento manual",
                ["", "A - B", "C - D", "E - F"],
                key="sim_score_manual",
            ) or None

        if pdf_prop and renda_proponente <= 0:
            renda_proponente = campo_moeda(
                "Renda Presumida — manual (R$)",
                "sim_renda_manual",
            )

        estado_civil = st.selectbox(
            "Estado Civil *",
            ["", "SOLTEIRO(A)", "DIVORCIADO(A)", "CASADO(A)"],
            index=0,
            key="sim_estado_civil",
        )

    # ── DADOS DA PROPOSTA ────────────────────────────────────
    with col_proposta:
        col_header("📋", "Dados da Proposta")

        ato_urba        = campo_moeda("Ato Urba (R$) *",                      "sim_ato_urba")
        valor_proposta  = campo_moeda("Valor da Proposta / Líquido CV (R$) *", "sim_valor_proposta")
        primeira_mensal = campo_moeda("Valor da 1ª Mensal (R$) *",             "sim_primeira_mensal")

    # ── COMPOSIÇÃO DE RENDA ──────────────────────────────────
    with col_renda:
        col_header("💰", "Composição de Renda")
        st.caption("Use somente quando houver cliente adicional compondo renda.")

        qtd_adicionais = st.number_input(
            "Clientes adicionais",
            min_value=0, max_value=4,
            value=0, step=1,
            key="sim_qtd_adicionais",
        )

        rendas_adicionais = []
        for i in range(int(qtd_adicionais)):
            numero = i + 2
            with st.expander(f"👤 Cliente {numero}", expanded=True):
                pdf_add   = st.file_uploader(
                    f"SPC — Cliente {numero}",
                    type=["pdf"],
                    key=f"sim_pdf_add_{numero}",
                )
                renda_add = 0.0
                if pdf_add:
                    try:
                        d_add     = extrair_dados_spc(pdf_add)
                        renda_add = float(d_add.get("renda_presumida") or 0)
                        if renda_add > 0:
                            st.success(f"Renda identificada: {brl(renda_add)}")
                        else:
                            st.warning("Renda não localizada no SPC.")
                    except Exception as e:
                        st.error(f"Falha na leitura: {e}")
                if pdf_add and renda_add <= 0:
                    renda_add = campo_moeda(
                        f"Renda manual — Cliente {numero} (R$)",
                        f"sim_renda_add_manual_{numero}",
                    )
                rendas_adicionais.append(renda_add)

    # ── Cálculos instantâneos ────────────────────────────────
    renda_total = renda_proponente + sum(rendas_adicionais)
    perc_ato    = ato_urba / valor_proposta * 100 if valor_proposta > 0 else 0
    perc_comp   = primeira_mensal / renda_total * 100 if renda_total > 0 else 0
    faixa_at    = faixa_ato(perc_ato)
    faixa_comp  = faixa_comprometimento(perc_comp)

    st.divider()

    # ── Métricas rápidas ─────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("% do Ato",        f"{perc_ato:.2f}%",  faixa_at)
    m2.metric("Comprometimento", f"{perc_comp:.2f}%", faixa_comp)
    m3.metric("Renda Total",     brl(renda_total))
    m4.metric("Faixa Etária",    faixa_idade or "—")

    # ── Validação ────────────────────────────────────────────
    faltando = []
    if not empreendimento:   faltando.append("Empreendimento")
    if not unidade:          faltando.append("Unidade")
    if not nascimento:       faltando.append("Data de Nascimento")
    if not estado_civil:     faltando.append("Estado Civil")
    if not pdf_prop:         faltando.append("SPC do Proponente")
    if not score_proponente: faltando.append("Score SPC do Proponente")
    if renda_total <= 0:     faltando.append("Renda Presumida")
    if valor_proposta <= 0:  faltando.append("Valor da Proposta")
    if primeira_mensal <= 0: faltando.append("1ª Mensal")

    if faltando:
        st.info(f"⚠️ Preencha/valide: **{', '.join(faltando)}**")

    _, col_btn = st.columns([3, 1])
    with col_btn:
        calcular = st.button(
            "🧮 CALCULAR SIMULAÇÃO",
            type="primary",
            use_container_width=True,
            disabled=bool(faltando),
            key="sim_calcular",
        )

    # ── Cálculo do score ─────────────────────────────────────
    if calcular:
        notas         = calcular_notas(score_proponente, faixa_at, faixa_comp, faixa_idade, estado_civil)
        score_final   = calcular_score_total(notas)
        classificacao, cor = classificar_score(score_final)

        st.session_state.resultado = {
            "notas":                   notas,
            "score_final":             score_final,
            "classificacao":           classificacao,
            "cor":                     cor,
            "empreendimento":          empreendimento,
            "unidade":                 unidade,
            "cpf_proponente":          cpf_proponente,
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
        }

    # ── Resultado ────────────────────────────────────────────
    if not st.session_state.resultado:
        return

    d = st.session_state.resultado
    st.divider()

    # ── Resumo ───────────────────────────────────────────────
    secao_titulo("📊", "Resumo da Simulação")

    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(card_resumo("Empreendimento",    d.get("empreendimento", "—")), unsafe_allow_html=True)
    r2.markdown(card_resumo("Unidade",           rotulo_unidade(d.get("unidade",""), d.get("empreendimento",""))), unsafe_allow_html=True)
    r3.markdown(card_resumo("CPF do Proponente", d.get("cpf_proponente") or "—"), unsafe_allow_html=True)
    r4.markdown(card_resumo("Renda Total",       brl(d.get("renda_total", 0))), unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(card_resumo("Faixa Etária",        d.get("faixa_idade") or "—"),     unsafe_allow_html=True)
    s2.markdown(card_resumo("Estado Civil",         d.get("estado_civil") or "—"),    unsafe_allow_html=True)
    s3.markdown(card_resumo("Score do Proponente",  d.get("score_proponente") or "—"),unsafe_allow_html=True)
    s4.markdown(card_resumo("Ato Urba",             brl(d.get("ato_urba", 0))),       unsafe_allow_html=True)

    t1, t2, t3, t4 = st.columns(4)
    t1.markdown(card_resumo("% do Ato",          f"{d.get('perc_ato',0):.2f}%"),   unsafe_allow_html=True)
    t2.markdown(card_resumo("1ª Mensal",          brl(d.get("primeira_mensal",0))), unsafe_allow_html=True)
    t3.markdown(card_resumo("Comprometimento",    f"{d.get('perc_comp',0):.2f}%"), unsafe_allow_html=True)
    t4.markdown(card_resumo("Valor da Proposta",  brl(d.get("valor_proposta",0))),  unsafe_allow_html=True)

    # ── Avaliação de Risco ───────────────────────────────────
    st.divider()
    secao_titulo("🎯", "Avaliação de Risco")

    col_score, col_detalhe = st.columns([1, 2], gap="large")

    with col_score:
        score_final   = d["score_final"]
        cor           = d["cor"]
        classificacao = d["classificacao"]

        bg  = {"green": "#E8F5EE", "orange": "#FFF4E5", "red": "#FFF0F0"}[cor]
        brd = {"green": "#079D56", "orange": "#FF8C23", "red": "#C0392B"}[cor]
        txt = {"green": "#056B3A", "orange": "#B45309", "red": "#922B21"}[cor]
        ico = {"green": "✅",      "orange": "⚠️",      "red": "❌"}[cor]
        pct = round(score_final / SCORE_MAX * 100)

        st.markdown(f"""
        <div style="background:{bg}; border:2px solid {brd};
                    border-radius:16px; padding:28px 24px;
                    text-align:center; box-shadow:0 4px 16px rgba(0,0,0,.08);">
            <div style="font-size:2.4rem; margin-bottom:8px;">{ico}</div>
            <div style="font-size:3rem; font-weight:900; color:{txt};
                        line-height:1; margin-bottom:4px;">
                {score_final}
            </div>
            <div style="font-size:.82rem; color:#6B7280; margin-bottom:12px;">
                de {SCORE_MAX} pontos ({pct}%)
            </div>
            <div style="background:{brd}; border-radius:20px;
                        height:8px; margin:0 auto 14px; width:80%;
                        overflow:hidden;">
                <div style="background:rgba(255,255,255,.5);
                            height:100%; width:{pct}%;
                            border-radius:20px;"></div>
            </div>
            <div style="font-size:1.05rem; font-weight:900;
                        color:{txt}; letter-spacing:.04em;">
                {classificacao}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_detalhe:
        labels = {
            "score_credito":         "Score de Crédito",
            "ato":                   "% do Ato",
            "comprometimento_renda": "Comprometimento de Renda",
            "idade":                 "Faixa Etária",
            "estado_civil":          "Estado Civil",
        }
        max_nota = {
            "score_credito": 5, "ato": 5,
            "comprometimento_renda": 5, "idade": 5, "estado_civil": 3,
        }
        detalhes = [
            {
                "Variável": labels[var],
                "Nota":     f"{d['notas'][var]}/{max_nota[var]}",
                "Peso":     peso,
                "Pontos":   d["notas"][var] * peso,
                "Máximo":   max_nota[var] * peso,
            }
            for var, peso in PESOS.items()
        ]
        st.dataframe(
            pd.DataFrame(detalhes),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Variável": st.column_config.TextColumn("Variável", width="medium"),
                "Nota":     st.column_config.TextColumn("Nota",     width="small"),
                "Peso":     st.column_config.NumberColumn("Peso",   width="small"),
                "Pontos":   st.column_config.NumberColumn("Pontos", width="small"),
                "Máximo":   st.column_config.NumberColumn("Máximo", width="small"),
            },
        )

    # ── Estratégias ──────────────────────────────────────────
    if d["classificacao"] != "BAIXO RISCO":
        st.divider()
        secao_titulo("💡", "Estratégias de Estruturação da Venda",
                     "Sugestões para melhorar o score desta simulação.")

        e1, e2 = st.columns(2)
        e1.metric("Pontos para Risco Moderado", f"+{max(0, LIMITE_MODERADO - d['score_final'])}")
        e2.metric("Pontos para Baixo Risco",    f"+{max(0, LIMITE_BAIXO - d['score_final'])}")

        cenarios = montar_cenarios(
            d["score_final"], d["notas"], d["renda_total"],
            d["primeira_mensal"], d["ato_urba"], d["valor_proposta"],
        )
        if cenarios:
            df_c = pd.DataFrame(cenarios)
            df_c["Ganho"]     = df_c["Ganho"].map(lambda x: f"+{x}")
            df_c["NovoScore"] = df_c["NovoScore"].map(str)
            st.dataframe(
                df_c[["Variável","Ajuste","Ganho","NovoScore","NovaClassificacao"]]
                .head(12)
                .rename(columns={
                    "NovoScore":         "Novo Score",
                    "NovaClassificacao": "Nova Classificação",
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Variável":           st.column_config.TextColumn("Variável",           width="medium"),
                    "Ajuste":             st.column_config.TextColumn("Ajuste",             width="large"),
                    "Ganho":              st.column_config.TextColumn("Ganho",              width="small"),
                    "Novo Score":         st.column_config.TextColumn("Novo Score",         width="small"),
                    "Nova Classificação": st.column_config.TextColumn("Nova Classificação", width="medium"),
                },
            )
            st.caption("⚠️ Sugestões são simulações contrafactuais. Não alteram dados cadastrais do cliente.")

    # ── Salvar ───────────────────────────────────────────────
    st.divider()
    secao_titulo("💾", "Salvar Simulação",
                 "Registra esta simulação no histórico administrativo.")

    if st.button(
        "✅ CONFIRMAR E SALVAR NO HISTÓRICO",
        type="primary",
        key="sim_salvar",
    ):
        try:
            salvar_simulacao(d, usuario["email"], usuario["nome"])
            st.success("✅ Simulação salva com sucesso no histórico.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
