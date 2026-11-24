from __future__ import annotations
# utils.py
# Score de Vendas Urba
# Funções auxiliares — cálculos, formatações, extração SPC, cenários

import os
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import pdfplumber
import streamlit as st

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")

# ============================================================
# PARÂMETROS DO SCORE
# ------------------------------------------------------------
# Valores PADRÃO. Os valores em uso ficam no banco (tabela
# parametros_score) e são editados na aba "Parâmetros".
# As faixas (ex.: "ATÉ 10%") são fixas; o que muda é a nota
# de cada faixa, o peso de cada variável e os limites.
# ============================================================
VARIAVEIS = {
    "score_credito":         "Score de Crédito (SPC)",
    "ato":                   "% do Ato",
    "comprometimento_renda": "Comprometimento de Renda",
    "idade":                 "Faixa Etária",
    "estado_civil":          "Estado Civil",
}

PESOS = {
    "score_credito":         5,
    "ato":                   5,
    "comprometimento_renda": 4,
    "idade":                 1,
    "estado_civil":          1,
}

NOTAS_SCORE = {
    "A - B": 5,
    "C - D": 3,
    "E - F": 1,
}

NOTAS_ATO = {
    "ACIMA DE 4%": 5,
    "3% A 4%":     4,
    "2% A 3%":     3,
    "1% A 2%":     2,
    "ABAIXO DE 1%":1,
}

NOTAS_COMPROMETIMENTO = {
    "ATÉ 10%":       5,
    "10% A 20%":     4,
    "20% A 30%":     3,
    "30% A 50%":     2,
    "50% A 100%":    1,
    "ACIMA DE 100%": 1,
}

NOTAS_IDADE = {
    "ATÉ 25 ANOS":  2,
    "25 A 35 ANOS": 1,
    "35 A 45 ANOS": 3,
    "45 A 60 ANOS": 4,
    "60+ ANOS":     5,
}

NOTAS_ESTADO_CIVIL = {
    "CASADO(A)":     3,
    "DIVORCIADO(A)": 2,
    "SOLTEIRO(A)":   1,
}

PARAMETROS_PADRAO = {
    "pesos": dict(PESOS),
    "notas": {
        "score_credito":         dict(NOTAS_SCORE),
        "ato":                   dict(NOTAS_ATO),
        "comprometimento_renda": dict(NOTAS_COMPROMETIMENTO),
        "idade":                 dict(NOTAS_IDADE),
        "estado_civil":          dict(NOTAS_ESTADO_CIVIL),
    },
    "limites": {"baixo": 54, "moderado": 33},
}

NOTA_MAX_PERMITIDA = 10
PESO_MAX_PERMITIDO = 20


def rotulo_faixa(texto) -> str:
    """'ACIMA DE 4%' → 'Acima de 4%' · 'SOLTEIRO(A)' → 'Solteiro(a)' (só exibição)."""
    t = str(texto or "").strip()
    if re.fullmatch(r"[A-F]\s*-\s*[A-F]", t.upper()):  # faixas de score: "C - D"
        return t.upper()
    t = t.lower()
    return t[:1].upper() + t[1:] if t else ""


def normalizar_parametros(bruto: dict | None) -> dict:
    """
    Junta o que veio do banco com o padrão. Garante que todas as
    variáveis/faixas existam e que tudo seja inteiro (evita quebrar
    o cálculo se o JSON salvo estiver incompleto).
    """
    bruto = bruto or {}
    pesos_b  = bruto.get("pesos")   or {}
    notas_b  = bruto.get("notas")   or {}
    lim_b    = bruto.get("limites") or {}

    def _int(v, padrao):
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            return padrao

    pesos = {k: _int(pesos_b.get(k), v) for k, v in PARAMETROS_PADRAO["pesos"].items()}
    notas = {
        var: {f: _int((notas_b.get(var) or {}).get(f), n) for f, n in faixas.items()}
        for var, faixas in PARAMETROS_PADRAO["notas"].items()
    }
    limites = {
        "baixo":    _int(lim_b.get("baixo"),    PARAMETROS_PADRAO["limites"]["baixo"]),
        "moderado": _int(lim_b.get("moderado"), PARAMETROS_PADRAO["limites"]["moderado"]),
    }
    return {"pesos": pesos, "notas": notas, "limites": limites}


def nota_maxima(params: dict, variavel: str) -> int:
    return max(params["notas"][variavel].values() or [0])


def score_maximo(params: dict | None = None) -> int:
    p = params or PARAMETROS_PADRAO
    return sum(nota_maxima(p, var) * p["pesos"][var] for var in p["pesos"])


def validar_parametros(params: dict) -> list[str]:
    """Retorna a lista de problemas (vazia = parâmetros válidos)."""
    erros = []
    for var, peso in params["pesos"].items():
        if not 0 <= peso <= PESO_MAX_PERMITIDO:
            erros.append(f"Peso de {VARIAVEIS[var]} deve ficar entre 0 e {PESO_MAX_PERMITIDO}.")
    for var, faixas in params["notas"].items():
        for faixa, nota in faixas.items():
            if not 0 <= nota <= NOTA_MAX_PERMITIDA:
                erros.append(f"Nota de {VARIAVEIS[var]} / {faixa} deve ficar entre 0 e {NOTA_MAX_PERMITIDA}.")
    if sum(params["pesos"].values()) <= 0:
        erros.append("Pelo menos uma variável precisa ter peso maior que zero.")
    mx  = score_maximo(params)
    lim = params["limites"]
    if lim["moderado"] <= 0:
        erros.append("O limite de Risco Moderado precisa ser maior que zero.")
    if lim["baixo"] <= lim["moderado"]:
        erros.append("O limite de Baixo Risco precisa ser maior que o de Risco Moderado.")
    if lim["baixo"] > mx:
        erros.append(f"O limite de Baixo Risco ({lim['baixo']}) passa do máximo possível ({mx} pontos).")
    return erros


# Compatibilidade: valores padrão (use score_maximo(params) no cálculo)
SCORE_MAX       = score_maximo(PARAMETROS_PADRAO)
LIMITE_BAIXO    = PARAMETROS_PADRAO["limites"]["baixo"]
LIMITE_MODERADO = PARAMETROS_PADRAO["limites"]["moderado"]


# ============================================================
# FORMATAÇÃO
# ============================================================

def brl(valor) -> str:
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def float_para_moeda_input(v) -> str:
    return f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def moeda_para_float(valor) -> float:
    if valor is None:
        return 0.0
    s = str(valor).strip().replace("R$", "").replace(" ", "")
    if not s:
        return 0.0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        if s.count(".") > 1:
            s = s.replace(".", "")
    try:
        return max(0.0, float(s))
    except Exception:
        return 0.0


def normalizar_texto(texto: str) -> str:
    texto = texto or ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.upper().replace("\xa0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


# ============================================================
# CAMPO DE MOEDA (widget Streamlit)
# ============================================================

def _normalizar_campo_moeda(chave: str) -> None:
    st.session_state[chave] = float_para_moeda_input(
        moeda_para_float(st.session_state.get(chave, "0,00"))
    )


def campo_moeda(label: str, chave: str, valor_inicial: float = 0.0, ajuda: str = None) -> float:
    if chave not in st.session_state:
        st.session_state[chave] = float_para_moeda_input(valor_inicial)

    st.text_input(
        label,
        key=chave,
        on_change=_normalizar_campo_moeda,
        args=(chave,),
        help=ajuda,
        placeholder="0,00",
    )
    return moeda_para_float(st.session_state[chave])


# ============================================================
# FAIXAS E CLASSIFICAÇÕES
# ============================================================

def calcular_idade(nascimento) -> int:
    hoje = datetime.now(TIMEZONE_BRASILIA).date()
    return (
        hoje.year - nascimento.year
        - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    )


def faixa_etaria(idade: int) -> str:
    if idade <= 25: return "ATÉ 25 ANOS"
    if idade <= 35: return "25 A 35 ANOS"
    if idade <= 45: return "35 A 45 ANOS"
    if idade <= 60: return "45 A 60 ANOS"
    return "60+ ANOS"


def faixa_comprometimento(percentual: float) -> str:
    if percentual <= 10:  return "ATÉ 10%"
    if percentual <= 20:  return "10% A 20%"
    if percentual <= 30:  return "20% A 30%"
    if percentual <= 50:  return "30% A 50%"
    if percentual <= 100: return "50% A 100%"
    return "ACIMA DE 100%"


def faixa_ato(percentual: float) -> str:
    if percentual > 4:  return "ACIMA DE 4%"
    if percentual >= 3: return "3% A 4%"
    if percentual >= 2: return "2% A 3%"
    if percentual >= 1: return "1% A 2%"
    return "ABAIXO DE 1%"


def mapear_score(letra: str):
    letra = (letra or "").strip().upper()
    if letra in ("A", "B"): return "A - B"
    if letra in ("C", "D"): return "C - D"
    if letra in ("E", "F"): return "E - F"
    return None


def normalizar_estado_civil(ec: str) -> str:
    ec = str(ec or "").strip().upper()
    if "CASAD"  in ec: return "CASADO(A)"
    if "DIVORC" in ec: return "DIVORCIADO(A)"
    return "SOLTEIRO(A)"


# ============================================================
# CÁLCULO DO SCORE
# ============================================================

def calcular_notas(
    score_proponente: str,
    faixa_at: str,
    faixa_comp: str,
    faixa_idade: str,
    estado_civil: str,
    params: dict | None = None,
) -> dict:
    n = (params or PARAMETROS_PADRAO)["notas"]
    return {
        "score_credito":         n["score_credito"].get(score_proponente, 0),
        "ato":                   n["ato"].get(faixa_at, 0),
        "comprometimento_renda": n["comprometimento_renda"].get(faixa_comp, 0),
        "idade":                 n["idade"].get(faixa_idade, 0),
        "estado_civil":          n["estado_civil"].get(estado_civil, 0),
    }


def calcular_score_total(notas: dict, params: dict | None = None) -> int:
    pesos = (params or PARAMETROS_PADRAO)["pesos"]
    return sum(notas[k] * pesos[k] for k in pesos)


def classificar_score(score: int, params: dict | None = None) -> tuple[str, str]:
    lim = (params or PARAMETROS_PADRAO)["limites"]
    if score >= lim["baixo"]:    return "BAIXO RISCO",    "green"
    if score >= lim["moderado"]: return "RISCO MODERADO", "orange"
    return "ALTO RISCO", "red"


# ============================================================
# EXTRAÇÃO DO SPC (PDF)
# SEGURANÇA: CPF NÃO É EXTRAÍDO NEM ARMAZENADO
# Extraímos apenas: nome completo, score, renda, data nascimento
# ============================================================

def extrair_dados_spc(pdf_file) -> dict:
    """
    Extrai dados do relatório SPC a partir de um arquivo PDF.
    Retorna dict com: score_letra, score_faixa, renda_presumida,
                      data_nascimento, nome_completo, texto_extraido.

    IMPORTANTE: CPF não é extraído nem retornado por política de
    proteção de dados. Nenhum dado de CPF é armazenado no sistema.
    """
    pdf_file.seek(0)
    paginas = []
    tabelas = []

    with pdfplumber.open(pdf_file) as pdf:
        for numero, page in enumerate(pdf.pages, start=1):
            texto = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            paginas.append(texto)
            try:
                for tabela in page.extract_tables() or []:
                    tabelas.append((numero, tabela))
            except Exception:
                pass

    texto_completo = "\n".join(paginas)
    texto_norm     = normalizar_texto(texto_completo)

    # ── Score de crédito ──
    score_letra = None
    for padrao in [
        r"\bRISCO\s+DE\s+CREDITO\s*[:\-]?\s*([A-F])\b",
        r"\bRISCO\s+DE\s+CREDITO\b[\s\S]{0,80}?\b([A-F])\b",
    ]:
        m = re.search(padrao, texto_norm, flags=re.I)
        if m:
            score_letra = m.group(1).upper()
            break
    score_faixa = mapear_score(score_letra)

    # ── Renda presumida ──
    renda = None

    for _, tabela in tabelas:
        for linha in tabela:
            celulas   = [normalizar_texto(str(x)) if x is not None else "" for x in linha]
            linha_str = " | ".join(celulas)
            if "RENDA PRESUMIDA" in linha_str and "SPC BRASIL" in linha_str:
                candidatos = re.findall(
                    r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})", linha_str
                )
                if candidatos:
                    renda = moeda_para_float(candidatos[-1])
                    if renda and renda > 0:
                        break
        if renda and renda > 0:
            break

    if not renda:
        for padrao in [
            r"RENDA\s+PRESUMIDA\s*-\s*SPC\s+BRASIL[\s\S]{0,160}?"
            r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})",
            r"RENDA\s+PRESUMIDA\s*:?\s*(?:_+\s*)?"
            r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})",
        ]:
            m = re.search(padrao, texto_norm, flags=re.I)
            if m:
                renda = moeda_para_float(m.group(1))
                if renda and renda > 0:
                    break

    # ── Data de nascimento ──
    data_nascimento = None
    for padrao in [
        r"(?:DATA\s+DE\s+NASCIMENTO|DT\.?\s*NASCIMENTO|NASCIMENTO)"
        r"\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{4})",
        r"(?:DATA\s+DE\s+NASCIMENTO|DT\.?\s*NASCIMENTO|NASCIMENTO)"
        r"[\s\S]{0,50}?(\d{1,2}/\d{1,2}/\d{4})",
    ]:
        m = re.search(padrao, texto_norm, flags=re.I)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%d/%m/%Y").date()
                hoje = datetime.now(TIMEZONE_BRASILIA).date()
                if dt <= hoje and dt.year >= 1900:
                    data_nascimento = dt
                    break
            except Exception:
                pass

    # ── Nome Completo ──
    # Extraímos o nome para identificação amigável, SEM CPF
    nome_completo = None
    for padrao in [
        r"(?:NOME\s+COMPLETO|NOME\s+DO\s+CONSUMIDOR|NOME\s+DO\s+CLIENTE|NOME)\s*[:\-]?\s*([A-Z][A-Z\s]{5,60}?)(?:\n|DATA|CPF|NASCIMENTO|$)",
        r"(?:CONSULTA\s+REALIZADA\s+PARA|RELATORIO\s+DE)\s*[:\-]?\s*([A-Z][A-Z\s]{5,60}?)(?:\n|CPF|DATA|$)",
    ]:
        m = re.search(padrao, texto_norm, flags=re.I | re.MULTILINE)
        if m:
            candidato = m.group(1).strip()
            # Filtra resultados que parecem ser nomes válidos (2+ palavras, sem números)
            palavras = candidato.split()
            if len(palavras) >= 2 and not any(c.isdigit() for c in candidato):
                nome_completo = " ".join(palavras[:5])  # máximo 5 palavras
                break

    # Fallback: tenta pegar o nome nas primeiras linhas do PDF
    if not nome_completo:
        for linha in texto_completo.split("\n")[:20]:
            linha_norm = normalizar_texto(linha)
            # Linha com 2-5 palavras, só letras, sem palavras-chave do SPC
            palavras = linha_norm.split()
            palavras_chave_spc = {
                "SPC", "BRASIL", "RELATORIO", "CONSULTA", "SCORE",
                "CREDITO", "SERASA", "CNPJ", "CPF", "DATA", "RENDA",
                "PAGINA", "EMISSAO", "VALIDADE", "CADASTRO"
            }
            if (
                2 <= len(palavras) <= 6
                and not any(c.isdigit() for c in linha_norm)
                and not any(p in palavras_chave_spc for p in palavras)
                and len(linha_norm) >= 8
            ):
                nome_completo = linha_norm.strip()
                break

    return {
        "score_letra":     score_letra,
        "score_faixa":     score_faixa,
        "renda_presumida": renda,
        "data_nascimento": data_nascimento,
        "nome_completo":   nome_completo,   # ← substitui CPF
        "texto_extraido":  texto_completo,
        # CPF removido por política de proteção de dados
    }


# ============================================================
# CENÁRIOS DE MELHORIA
# ============================================================

def montar_cenarios(
    score_atual:    int,
    notas:          dict,
    renda_total:    float,
    mensal:         float,
    ato:            float,
    valor_proposta: float,
    params:         dict | None = None,
) -> list[dict]:
    p        = params or PARAMETROS_PADRAO
    pesos    = p["pesos"]
    lim      = p["limites"]
    cenarios = []

    for pct_meta, faixa_meta in [
        (1.00, "1% A 2%"),
        (2.00, "2% A 3%"),
        (3.00, "3% A 4%"),
        (4.01, "ACIMA DE 4%"),
    ]:
        nova_nota = p["notas"]["ato"][faixa_meta]
        ganho     = (nova_nota - notas["ato"]) * pesos["ato"]
        ato_alvo  = valor_proposta * pct_meta / 100
        adicional = max(0, ato_alvo - ato)

        if ganho > 0 and adicional > 0:
            cenarios.append({
                "Variável":  "Ato",
                "Ajuste":    (
                    f"Aumentar o ato para aprox. {brl(ato_alvo)} "
                    f"(+{brl(adicional)}; ≈{pct_meta:.2f}% da proposta)"
                ),
                "Ganho":     ganho,
                "NovoScore": score_atual + ganho,
            })

    for limite, faixa_meta in [
        (100, "50% A 100%"),
        (50,  "30% A 50%"),
        (30,  "20% A 30%"),
        (20,  "10% A 20%"),
        (10,  "ATÉ 10%"),
    ]:
        nova_nota   = p["notas"]["comprometimento_renda"][faixa_meta]
        ganho       = (nova_nota - notas["comprometimento_renda"]) * pesos["comprometimento_renda"]
        renda_alvo  = mensal / (limite / 100) if limite > 0 else 0
        mensal_alvo = renda_total * limite / 100

        if ganho > 0:
            cenarios.append({
                "Variável":  "Renda / Mensal",
                "Ajuste":    (
                    f"Para comprometimento ≤{limite}%: "
                    f"renda total ≈{brl(renda_alvo)} "
                    f"OU mensal ≤{brl(mensal_alvo)}"
                ),
                "Ganho":     ganho,
                "NovoScore": score_atual + ganho,
            })

    for c in cenarios:
        classificacao, _ = classificar_score(c["NovoScore"], p)
        c["NovaClassificacao"] = classificacao
        c["AtingeModerado"]    = c["NovoScore"] >= lim["moderado"]
        c["AtingeBaixo"]       = c["NovoScore"] >= lim["baixo"]

    return sorted(
        cenarios,
        key=lambda c: (
            not c["AtingeModerado"],
            not c["AtingeBaixo"],
            -c["Ganho"],
        ),
    )


# ============================================================
# EMPREENDIMENTOS — UTILITÁRIOS
# ============================================================

def chave_coluna(nome: str) -> str:
    nome = str(nome or "").strip()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = nome.lower()
    nome = re.sub(r"[_\-]+", " ", nome)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome


def mapear_colunas_xlsx(df: pd.DataFrame) -> pd.DataFrame:
    mapa = {}
    for col in df.columns:
        ck = chave_coluna(col)
        if ck in {"empreendimento", "empreendimentos", "nome empreendimento"}:
            mapa[col] = "Empreendimento"
        elif ck in {"unidade", "unidades", "quadra lote", "quadra/lote"}:
            mapa[col] = "Unidade"
    return df.rename(columns=mapa)


_RE_QUADRA = re.compile(r"\bQ(?:UADRA|DR?)?\.?\s*[-:ºª°]?\s*(\d+[A-Z]?|[A-Z]{1,2}\d*)\b")
_RE_LOTE   = re.compile(r"\bL(?:OTE|T)?\.?\s*[-:ºª°]?\s*(\d+[A-Z]?)\b")


def chave_natural(texto) -> list:
    """Ordena 'Q2' antes de 'Q10' (números como números)."""
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", str(texto or "").upper())]


def extrair_quadra_lote(unidade: str) -> tuple[str, str] | None:
    """'SMART URBA RESERVA - QUADRA 01 - LOTE 05' → ('01', '05'). None se não achar os dois."""
    t = normalizar_texto(unidade)
    mq, ml = _RE_QUADRA.search(t), _RE_LOTE.search(t)
    if not mq or not ml:
        return None
    return mq.group(1), ml.group(1)


def mapa_quadra_lote(unidades: list[str]) -> dict[tuple[str, str], str] | None:
    """
    {(quadra, lote): unidade} quando TODAS as unidades têm quadra e lote
    identificáveis e sem repetição. Senão None (a tela usa a lista simples).
    """
    mapa = {}
    for u in unidades:
        ql = extrair_quadra_lote(u)
        if ql is None or ql in mapa:
            return None
        mapa[ql] = u
    return mapa or None


def prefixo_comum(textos: list[str]) -> str:
    """Parte inicial repetida em todas as unidades (ex.: 'SMART URBA RESERVA - ')."""
    if len(textos) < 2:
        return ""
    pre = os.path.commonprefix([str(t) for t in textos])
    corte = pre.rfind("-")             # prefere cortar no separador " - "
    if corte <= 0:
        corte = pre.rfind(" ")         # senão, no último espaço
    return pre[:corte + 1] if corte > 0 else ""


def rotulo_unidade(unidade: str, empreendimento: str = "") -> str:
    texto = str(unidade or "").strip()
    ql = extrair_quadra_lote(texto)
    if ql:
        return f"Quadra {ql[0]} · Lote {ql[1]}"
    emp = str(empreendimento or "").strip()
    if emp and texto.upper().startswith(emp.upper()):
        curto = texto[len(emp):].lstrip(" -–—")
        if curto:
            return curto
    return texto
