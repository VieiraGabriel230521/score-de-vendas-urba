# styles.py
# Score de Vendas Urba
# CSS global — identidade visual Urba unificada

from __future__ import annotations

import base64
import os

import streamlit as st

# ============================================================
# CONSTANTES DE COR
# ============================================================
COR_VERDE         = "#079D56"
COR_VERDE_ESCURO  = "#056B3A"
COR_LARANJA       = "#FF8C23"
LOGO_COLORIDO     = "assets/logo_urba.png"
LOGO_BRANCO       = "assets/logo_urba_branco.png"


# ============================================================
# UTILITÁRIO — IMAGEM → BASE64
# ============================================================
def imagem_base64(caminho: str) -> str:
    try:
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return ""


# ============================================================
# CSS GLOBAL
# ============================================================
def aplicar_estilos() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── VARIÁVEIS ── */
    :root {
        --verde:         #079D56;
        --verde-escuro:  #056B3A;
        --verde-soft:    #F0FBF5;
        --verde-mid:     #E8F5EE;
        --laranja:       #FF8C23;
        --laranja-soft:  #FFF4E5;
        --text-main:     #1A1A2E;
        --text-muted:    #6B7280;
        --text-light:    #9CA3AF;
        --bg-white:      #FFFFFF;
        --bg-light:      #F8FAFC;
        --bg-card:       #FFFFFF;
        --border:        #E2E8F0;
        --border-input:  #D1D5DB;
        --shadow-sm:     0 1px 3px rgba(0,0,0,.08);
        --shadow-md:     0 4px 16px rgba(0,0,0,.10);
        --shadow-green:  0 4px 20px rgba(7,157,86,.18);
        --radius-sm:     8px;
        --radius-md:     12px;
        --radius-lg:     18px;
    }

    /* ── RESET GERAL ── */
    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    .main, .block-container {
        background-color: var(--bg-light) !important;
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── ESCONDE ELEMENTOS PADRÃO ── */
    #MainMenu,
    header[data-testid="stHeader"],
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* ── LAYOUT ── */
    .block-container {
        max-width: 1400px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* ── TIPOGRAFIA ── */
    h1, h2, h3, h4 {
        color: var(--verde-escuro) !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }
    p, li, span, td, th {
        color: var(--text-main) !important;
    }
    label,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: .83rem !important;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    [data-testid="stCaptionContainer"] p, small {
        color: var(--text-muted) !important;
        font-size: .82rem !important;
    }

    /* ══════════════════════════════════════
       SIDEBAR
    ══════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            160deg,
            #033D22 0%,
            var(--verde-escuro) 40%,
            var(--verde) 100%
        ) !important;
        border-right: none !important;
        box-shadow: 4px 0 24px rgba(0,0,0,.15) !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,.15) !important;
        margin: 12px 0 !important;
    }
    section[data-testid="stSidebar"] button {
        background: rgba(255,255,255,.12) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,.25) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        transition: all .2s ease !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: rgba(255,255,255,.22) !important;
        border-color: rgba(255,255,255,.45) !important;
        transform: translateY(-1px) !important;
    }

    /* ══════════════════════════════════════
       INPUTS
    ══════════════════════════════════════ */
    input, textarea,
    [data-baseweb="input"] input,
    [data-baseweb="base-input"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background-color: var(--bg-white) !important;
        color: var(--text-main) !important;
        border: 1.5px solid var(--border-input) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: .92rem !important;
        transition: border-color .2s, box-shadow .2s !important;
    }
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"] > div {
        background-color: var(--bg-white) !important;
        border: 1.5px solid var(--border-input) !important;
        border-radius: var(--radius-sm) !important;
    }
    input:focus,
    [data-baseweb="input"]:focus-within,
    [data-baseweb="base-input"]:focus-within {
        border-color: var(--verde) !important;
        box-shadow: 0 0 0 3px rgba(7,157,86,.12) !important;
    }

    /* ── SELECT ── */
    [data-baseweb="select"] > div {
        background-color: var(--bg-white) !important;
        color: var(--text-main) !important;
        border: 1.5px solid var(--border-input) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: var(--text-main) !important;
        background-color: var(--bg-white) !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background-color: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-md) !important;
    }
    [role="option"]:hover {
        background-color: var(--verde-soft) !important;
        color: var(--verde-escuro) !important;
    }

    /* ── NUMBER INPUT ── */
    [data-testid="stNumberInput"] > div {
        background-color: var(--bg-white) !important;
        border: 1.5px solid var(--border-input) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stNumberInput"] button {
        background-color: #F1F5F9 !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border) !important;
    }
    [data-testid="stNumberInput"] button:hover {
        background-color: var(--verde-mid) !important;
        color: var(--verde-escuro) !important;
    }

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploaderDropzone"] {
        background-color: var(--verde-soft) !important;
        border: 2px dashed var(--verde) !important;
        border-radius: var(--radius-md) !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: var(--verde) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
    }

    /* ── EXPANDER ── */
    [data-testid="stExpander"],
    details {
        background-color: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    details > summary {
        font-weight: 600 !important;
        color: var(--text-main) !important;
        padding: 10px 14px !important;
    }

    /* ── CONTAINERS ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* ══════════════════════════════════════
       MÉTRICAS
    ══════════════════════════════════════ */
    div[data-testid="stMetric"] {
        background: var(--bg-white) !important;
        border: 1px solid var(--border) !important;
        border-top: 3px solid var(--verde) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 18px !important;
        box-shadow: var(--shadow-sm) !important;
        transition: box-shadow .2s, transform .2s !important;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--text-muted) !important;
        font-size: .78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: .06em;
    }
    [data-testid="stMetricValue"] {
        color: var(--text-main) !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: .78rem !important;
        font-weight: 600 !important;
    }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] * {
        background-color: var(--bg-white) !important;
        color: var(--text-main) !important;
    }

    /* ── ALERTAS ── */
    [data-testid="stAlert"] {
        border-radius: var(--radius-md) !important;
        border-left-width: 4px !important;
        font-weight: 500 !important;
    }

    /* ══════════════════════════════════════
       BOTÕES
    ══════════════════════════════════════ */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        border-radius: var(--radius-sm) !important;
        min-height: 44px !important;
        letter-spacing: .04em !important;
        transition: all .2s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--verde) 0%, var(--verde-escuro) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(7,157,86,.30) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(7,157,86,.40) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: var(--bg-white) !important;
        color: var(--verde) !important;
        border: 2px solid var(--verde) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--verde-soft) !important;
        transform: translateY(-1px) !important;
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--laranja) 0%, #e07a1a 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: 0 2px 8px rgba(255,140,35,.30) !important;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 6px 20px rgba(255,140,35,.40) !important;
        transform: translateY(-2px) !important;
    }

    /* ── DIVIDER ── */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #F1F5F9; }
    ::-webkit-scrollbar-thumb { background: #CBD5E0; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    /* ══════════════════════════════════════
       HERO BANNER
    ══════════════════════════════════════ */
    .urba-hero {
        display: flex;
        align-items: center;
        gap: 24px;
        flex-wrap: wrap;
        border-radius: var(--radius-lg);
        padding: 28px 36px;
        margin-bottom: 24px;
        background: linear-gradient(135deg, #033D22 0%, var(--verde-escuro) 50%, var(--verde) 100%);
        border-bottom: 4px solid var(--laranja);
        box-shadow: var(--shadow-green);
        position: relative;
        overflow: hidden;
    }
    .urba-hero::before {
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 200px; height: 200px;
        background: rgba(255,255,255,.04);
        border-radius: 50%;
    }
    .urba-hero::after {
        content: '';
        position: absolute;
        bottom: -60px; right: 80px;
        width: 280px; height: 280px;
        background: rgba(255,255,255,.03);
        border-radius: 50%;
    }
    .urba-hero-logo {
        height: 60px;
        width: auto;
        filter: brightness(0) invert(1);
        z-index: 1;
    }
    .urba-hero-logo-text {
        font-size: 2.2rem;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: -0.04em;
        z-index: 1;
    }
    .urba-hero-texto {
        flex: 1 1 300px;
        z-index: 1;
    }
    .urba-kicker {
        display: inline-block;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: var(--laranja);
        background: rgba(255,140,35,.15);
        border: 1px solid rgba(255,140,35,.30);
        border-radius: 20px;
        padding: 3px 12px;
        margin-bottom: 10px;
    }
    .urba-title {
        font-size: clamp(1.5rem, 2.5vw, 2.1rem);
        font-weight: 900;
        line-height: 1.1;
        margin: 0 0 8px 0;
        color: #FFFFFF !important;
        letter-spacing: -0.03em;
    }
    .urba-subtitle {
        color: rgba(255,255,255,.80);
        font-size: .95rem;
        font-weight: 400;
        line-height: 1.5;
    }
    .urba-hero-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        z-index: 1;
    }
    .urba-hero-badge-num {
        font-size: 2rem;
        font-weight: 900;
        color: #FFFFFF;
        line-height: 1;
    }
    .urba-hero-badge-label {
        font-size: .68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .1em;
        color: rgba(255,255,255,.65);
        text-align: center;
    }

    /* ══════════════════════════════════════
       LOGIN CARD
    ══════════════════════════════════════ */
    .login-wrapper {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #033D22 0%, var(--verde-escuro) 60%, var(--verde) 100%);
    }
    .login-card {
        background: var(--bg-white);
        border-radius: 20px;
        padding: 40px 36px 32px;
        box-shadow: 0 20px 60px rgba(0,0,0,.25);
        text-align: center;
        max-width: 420px;
        width: 100%;
        border-top: 5px solid var(--verde);
    }
    .login-logo-area {
        margin-bottom: 20px;
    }
    .login-logo-area img {
        height: 56px;
        width: auto;
    }
    .login-logo-text {
        font-size: 2rem;
        font-weight: 900;
        color: var(--verde);
        letter-spacing: -0.04em;
    }
    .login-kicker {
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: var(--laranja);
        margin-bottom: 6px;
    }
    .login-title {
        font-size: 1.6rem;
        font-weight: 800;
        margin: 4px 0 6px;
        color: #12301F !important;
        letter-spacing: -0.02em;
    }
    .login-sub {
        color: var(--text-muted);
        font-size: .9rem;
        margin-bottom: 4px;
    }
    .login-divider {
        height: 1px;
        background: var(--border);
        margin: 20px 0;
    }

    /* ══════════════════════════════════════
       CARD RESUMO
    ══════════════════════════════════════ */
    .card-resumo {
        background: var(--bg-white);
        border: 1px solid var(--border);
        border-top: 3px solid var(--verde);
        border-radius: var(--radius-md);
        padding: 12px 16px;
        min-height: 76px;
        box-shadow: var(--shadow-sm);
        transition: box-shadow .2s, transform .2s;
    }
    .card-resumo:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    .card-label {
        font-size: .70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: var(--text-muted);
        margin-bottom: 6px;
    }
    .card-valor {
        font-size: 1rem;
        font-weight: 800;
        color: var(--text-main);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ══════════════════════════════════════
       SEÇÃO TÍTULO
    ══════════════════════════════════════ */
    .secao-titulo {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--verde-mid);
    }
    .secao-titulo-icon {
        width: 36px;
        height: 36px;
        background: var(--verde-soft);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    .secao-titulo-text {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--verde-escuro) !important;
        letter-spacing: -0.01em;
    }
    .secao-titulo-sub {
        font-size: .80rem;
        color: var(--text-muted);
        margin-top: 1px;
    }

    /* ══════════════════════════════════════
       CARDS DE RISCO
    ══════════════════════════════════════ */
    .risco-baixo {
        background: #E8F5E9;
        border-left: 4px solid #079D56;
        border-radius: var(--radius-sm);
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .risco-moderado {
        background: #FFF8E1;
        border-left: 4px solid #FFC107;
        border-radius: var(--radius-sm);
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .risco-alto {
        background: #FFEBEE;
        border-left: 4px solid #E53935;
        border-radius: var(--radius-sm);
        padding: 12px 16px;
        margin-bottom: 8px;
    }

    /* ── OBS BOX ── */
    .obs-box {
        background: #F0FFF6;
        border: 1px solid #B2DFCC;
        border-radius: var(--radius-sm);
        padding: 10px 14px;
        font-size: .88rem;
        color: #12301F;
        margin-top: 8px;
    }

    /* ── BADGE PERFIL ── */
    .badge-perfil {
        display: inline-block;
        background: rgba(255,255,255,.18);
        border: 1px solid rgba(255,255,255,.30);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: .70rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: .08em;
        text-transform: uppercase;
    }

    /* ── RODAPÉ ── */
    .urba-footer {
        text-align: center;
        padding: 28px 0 12px;
        margin-top: 40px;
        border-top: 1px solid var(--border);
    }
    .urba-footer-marca {
        color: var(--verde);
        font-weight: 900;
        font-size: .95rem;
        letter-spacing: -0.02em;
    }
    .urba-footer-info {
        color: var(--text-light);
        font-size: .82rem;
    }

    /* ── COL HEADER (formulário) ── */
    .col-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        background: var(--verde-soft);
        border-radius: var(--radius-sm);
        margin-bottom: 14px;
        border-left: 3px solid var(--verde);
    }
    .col-header-icon { font-size: 1.1rem; }
    .col-header-text {
        font-size: .88rem;
        font-weight: 800;
        color: var(--verde-escuro) !important;
        text-transform: uppercase;
        letter-spacing: .05em;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# COMPONENTES HTML REUTILIZÁVEIS
# ============================================================

def hero_banner(subtitulo: str = "Avaliação estruturada do risco de distrato no momento da venda.") -> None:
    logo_b64 = imagem_base64(LOGO_BRANCO)
    if logo_b64:
        logo_html = f'<img class="urba-hero-logo" src="data:image/png;base64,{logo_b64}" alt="Urba">'
    else:
        logo_html = '<div class="urba-hero-logo-text">Urba</div>'

    st.markdown(f"""
    <div class="urba-hero">
        {logo_html}
        <div class="urba-hero-texto">
            <div class="urba-kicker">🏆 Projeto Defensores do Contrato</div>
            <div class="urba-title">Simulador de Score de Vendas</div>
            <div class="urba-subtitle">{subtitulo}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def login_card() -> None:
    logo_b64 = imagem_base64(LOGO_COLORIDO)
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Urba">'
    else:
        logo_html = '<div class="login-logo-text">Urba</div>'

    st.markdown(f"""
    <div class="login-card">
        <div class="login-logo-area">{logo_html}</div>
        <div class="login-kicker">Projeto Defensores do Contrato</div>
        <div class="login-title">Simulador de Score de Vendas</div>
        <div class="login-sub">Identifique-se com suas credenciais para continuar.</div>
        <div class="login-divider"></div>
    </div>
    """, unsafe_allow_html=True)


def secao_titulo(icone: str, titulo: str, subtitulo: str = "") -> None:
    sub_html = f'<div class="secao-titulo-sub">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f"""
    <div class="secao-titulo">
        <div class="secao-titulo-icon">{icone}</div>
        <div>
            <div class="secao-titulo-text">{titulo}</div>
            {sub_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def col_header(icone: str, texto: str) -> None:
    st.markdown(f"""
    <div class="col-header">
        <span class="col-header-icon">{icone}</span>
        <span class="col-header-text">{texto}</span>
    </div>
    """, unsafe_allow_html=True)


def card_resumo(label: str, valor: str) -> str:
    return f"""
    <div class="card-resumo">
        <div class="card-label">{label}</div>
        <div class="card-valor" title="{valor}">{valor}</div>
    </div>
    """


def rodape(versao: str = "V1.0") -> None:
    st.markdown(f"""
    <div class="urba-footer">
        <span class="urba-footer-marca">Urba</span>
        <span class="urba-footer-info">
            &nbsp;•&nbsp;Simulador de Score de Vendas {versao}
            &nbsp;•&nbsp;Projeto Defensores do Contrato
            &nbsp;•&nbsp;© 2026
        </span>
    </div>
    """, unsafe_allow_html=True)
