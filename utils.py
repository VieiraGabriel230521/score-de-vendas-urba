from __future__ import annotations
# utils.py
# Score de Vendas Urba
# Funções auxiliares — cálculos, formatações, extração SPC, cenários

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
# ============================================================
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
    "60+ ANOS":     5,
    "45 A 60 ANOS": 4,
    "35 A 45 ANOS": 3,
    "ATÉ 25 ANOS":  2,
    "25 A 35 ANOS": 1,
}

NOTAS_ESTADO_CIVIL = {
    "CASADO(A)":     3,
    "DIVORCIADO(A)": 2,
    "SOLTEIRO(A)":   1,
}

# Pontuação máxima possível
SCORE_MAX = (
    5 * PESOS["score_credito"]         +
    5 * PESOS["ato"]                   +
    5 * PESOS["comprometimento_renda"] +
    5 * PESOS["idade"]                 +
    3 * PESOS["estado_civil"]
)

# Limites de classificação
LIMITE_BAIXO    = 54
LIMITE_MODERADO = 33


# ============================================================
# FORMATAÇÃO
# ============================================================

def brl(valor) -> str:
    """Formata um número como moeda brasileira. Ex: 1234.5 → R$ 1.234,50"""
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def formatar_cpf(digitos: str) -> str:
    """Formata 11 dígitos como CPF. Ex: 12345678901 → 123.456.789-01"""
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def float_para_moeda_input(v) -> str:
    """Converte float para string no formato de input de moeda. Ex: 1234.5 → 1.234,50"""
    return f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def moeda_para_float(valor) -> float:
    """Converte string de moeda brasileira para float. Ex: R$ 1.234,50 → 1234.5"""
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
    """Remove acentos, normaliza espaços e converte para maiúsculas."""
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
    """
    Widget de input formatado como moeda brasileira.
    Retorna o valor como float.
    """
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
    """Calcula a idade a partir da data de nascimento."""
    hoje = datetime.now(TIMEZONE_BRASILIA).date()
    return (
        hoje.year - nascimento.year
        - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    )


def faixa_etaria(idade: int) -> str:
    """Retorna a faixa etária a partir da idade."""
    if idade <= 25: return "ATÉ 25 ANOS"
    if idade <= 35: return "25 A 35 ANOS"
    if idade <= 45: return "35 A 45 ANOS"
    if idade <= 60: return "45 A 60 ANOS"
    return "60+ ANOS"


def faixa_comprometimento(percentual: float) -> str:
    """Retorna a faixa de comprometimento de renda."""
    if percentual <= 10:  return "ATÉ 10%"
    if percentual <= 20:  return "10% A 20%"
    if percentual <= 30:  return "20% A 30%"
    if percentual <= 50:  return "30% A 50%"
    if percentual <= 100: return "50% A 100%"
    return "ACIMA DE 100%"


def faixa_ato(percentual: float) -> str:
    """Retorna a faixa do ato em relação ao valor da proposta."""
    if percentual > 4:  return "ACIMA DE 4%"
    if percentual >= 3: return "3% A 4%"
    if percentual >= 2: return "2% A 3%"
    if percentual >= 1: return "1% A 2%"
    return "ABAIXO DE 1%"


def mapear_score(letra: str):
    """Converte letra do score SPC para faixa. Ex: 'A' → 'A - B'"""
    letra = (letra or "").strip().upper()
    if letra in ("A", "B"): return "A - B"
    if letra in ("C", "D"): return "C - D"
    if letra in ("E", "F"): return "E - F"
    return None


def normalizar_estado_civil(ec: str) -> str:
    """Normaliza o estado civil para o padrão do sistema."""
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
) -> dict:
    """
    Monta o dicionário de notas para cada variável do score.
    Retorna dict com as notas individuais.
    """
    return {
        "score_credito":         NOTAS_SCORE.get(score_proponente, 0),
        "ato":                   NOTAS_ATO.get(faixa_at, 0),
        "comprometimento_renda": NOTAS_COMPROMETIMENTO.get(faixa_comp, 0),
        "idade":                 NOTAS_IDADE.get(faixa_idade, 0),
        "estado_civil":          NOTAS_ESTADO_CIVIL.get(estado_civil, 0),
    }


def calcular_score_total(notas: dict) -> int:
    """Calcula o score total ponderado."""
    return sum(notas[k] * PESOS[k] for k in PESOS)


def classificar_score(score: int) -> tuple[str, str]:
    """
    Classifica o score em risco.
    Retorna (classificacao, cor) onde cor é 'green', 'orange' ou 'red'.
    """
    if score >= LIMITE_BAIXO:    return "BAIXO RISCO",    "green"
    if score >= LIMITE_MODERADO: return "RISCO MODERADO", "orange"
    return "ALTO RISCO", "red"


# ============================================================
# EXTRAÇÃO DO SPC (PDF)
# ============================================================

def extrair_dados_spc(pdf_file) -> dict:
    """
    Extrai dados do relatório SPC a partir de um arquivo PDF.
    Retorna dict com: score_letra, score_faixa, renda_presumida,
                      data_nascimento, cpf, texto_extraido.
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

    # Tenta nas tabelas primeiro
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

    # Fallback: busca no texto corrido
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

    # ── CPF ──
    cpf = None
    for padrao in [
        r"\bCPF\s*[:\-]?\s*(\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-\/]?\d{2})\b",
        r"\b(\d{3}\.\d{3}\.\d{3}[-\/]\d{2})\b",
    ]:
        m = re.search(padrao, texto_norm, flags=re.I)
        if m:
            digitos = re.sub(r"\D", "", m.group(1))
            if len(digitos) == 11:
                cpf = formatar_cpf(digitos)
                break

    return {
        "score_letra":    score_letra,
        "score_faixa":    score_faixa,
        "renda_presumida": renda,
        "data_nascimento": data_nascimento,
        "cpf":            cpf,
        "texto_extraido": texto_completo,
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
) -> list[dict]:
    """
    Gera sugestões de ajuste para melhorar o score.
    Retorna lista de cenários ordenados por impacto.
    """
    cenarios = []

    # ── Cenários de Ato ──
    for pct_meta, faixa_meta in [
        (1.00, "1% A 2%"),
        (2.00, "2% A 3%"),
        (3.00, "3% A 4%"),
        (4.01, "ACIMA DE 4%"),
    ]:
        nova_nota = NOTAS_ATO[faixa_meta]
        ganho     = (nova_nota - notas["ato"]) * PESOS["ato"]
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

    # ── Cenários de Comprometimento ──
    for limite, faixa_meta in [
        (50,  "30% A 50%"),
        (30,  "20% A 30%"),
        (20,  "10% A 20%"),
        (10,  "ATÉ 10%"),
    ]:
        nova_nota   = NOTAS_COMPROMETIMENTO[faixa_meta]
        ganho       = (nova_nota - notas["comprometimento_renda"]) * PESOS["comprometimento_renda"]
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

    # ── Enriquece com classificação resultante ──
    for c in cenarios:
        classificacao, _ = classificar_score(c["NovoScore"])
        c["NovaClassificacao"] = (
            "🟢 BAIXO RISCO"    if classificacao == "BAIXO RISCO"    else
            "🟡 RISCO MODERADO" if classificacao == "RISCO MODERADO" else
            "🔴 ALTO RISCO"
        )
        c["AtingeModerado"] = c["NovoScore"] >= LIMITE_MODERADO
        c["AtingeBaixo"]    = c["NovoScore"] >= LIMITE_BAIXO

    # Ordena: prioriza quem atinge moderado → baixo → maior ganho
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
    """Normaliza nome de coluna para comparação."""
    nome = str(nome or "").strip()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = nome.lower()
    nome = re.sub(r"[_\-]+", " ", nome)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome


def mapear_colunas_xlsx(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tenta mapear colunas de um Excel para os nomes padrão
    'Empreendimento' e 'Unidade'.
    """
    mapa = {}
    for col in df.columns:
        ck = chave_coluna(col)
        if ck in {"empreendimento", "empreendimentos", "nome empreendimento"}:
            mapa[col] = "Empreendimento"
        elif ck in {"unidade", "unidades", "quadra lote", "quadra/lote"}:
            mapa[col] = "Unidade"
    return df.rename(columns=mapa)


def rotulo_unidade(unidade: str, empreendimento: str) -> str:
    """
    Remove o prefixo do empreendimento do nome da unidade
    para exibição mais limpa no selectbox.
    """
    texto = str(unidade or "").strip()
    emp   = str(empreendimento or "").strip()
    if emp and texto.upper().startswith(emp.upper()):
        curto = texto[len(emp):].lstrip(" -–—")
        if curto:
            return curto
    return texto
