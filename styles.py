# styles.py
# Score de Vendas Urba
# CSS global — identidade visual Urba unificada

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
    """Converte uma imagem local para base64 (uso em HTML)."""
    try:
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return ""


# ============================================================
# CSS GLOBAL
# ============================================================
def aplicar_estilos() -> None:
    """Injeta o CSS global da identidade visual Urba."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── VARIÁVEIS ── */
    :root {
        --urba-verde:        #079D56;
        --urba-verde-escuro: #056B3A;
        --urba-laranja:      #FF8C23;
        --card-border:       rgba(7,157,86,.22);
        --text-main:         #2D2D2D;
        --text-muted:        #6B7280;
        --bg-white:          #FFFFFF;
        --bg-light:          #F4F6F8;
        --bg-green-soft:     #F0FBF5;
        --border-light:      #E2E8F0;
        --border-input:      #CBD5E0;
    }

    /* ── RESET TEMA ESCURO ── */
    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    .main, .block-container,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"] {
        background-color: var(--bg-white) !important;
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── TIRA BARRA DO TOPO ── */
    #MainMenu,
    header[data-testid="stHeader"],
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display:     none       !important;
        visibility:  hidden     !important;
        height:      0          !important;
    }

    /* ── LAYOUT ── */
    .block-container {
        max-width:      1380px  !important;
        padding-top:    1.5rem  !important;
        padding-bottom: 3rem    !important;
    }

    /* ── TIPOGRAFIA ── */
    h1, h2, h3, h4 {
        color:       var(--urba-verde-escuro) !important;
        font-weight: 800                      !important;
        letter-spacing: -0.02em;
    }
    p, li, span, td, th {
        color: var(--text-main) !important;
    }
    label,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span {
        color:       #374151 !important;
        font-weight: 600     !important;
        font-size:   .85rem  !important;
    }
    [data-testid="stCaptionContainer"] p,
    small, .caption {
        color: var(--text-muted) !important;
    }

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, var(--urba-verde-escuro) 0%, var(--urba-verde) 100%
        ) !important;
        border-right: none !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.25) !important;
    }
    section[data-testid="stSidebar"] button {
        background:   rgba(255,255,255,0.15) !important;
        color:        #FFFFFF               !important;
        border:       1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px                  !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: rgba(255,255,255,0.25) !important;
    }

    /* ── INPUTS ── */
    input, textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="base-input"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background-color: var(--bg-white)    !important;
        color:            var(--text-main)   !important;
        border:           1.5px solid var(--border-input) !important;
        border-radius:    8px                !important;
        font-family:      'Inter', sans-serif !important;
    }
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"] > div {
        background-color: var(--bg-white)    !important;
        border:           1.5px solid var(--border-input) !important;
        border-radius:    8px                !important;
    }
    input:focus,
    [data-baseweb="input"]:focus-within,
    [data-baseweb="base-input"]:focus-within {
        border-color: var(--urba-verde)                  !important;
        box-shadow:   0 0 0 3px rgba(7,157,86,0.15)      !important;
    }

    /* ── SELECT / DROPDOWN ── */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] > div > div {
        background-color: var(--bg-white)    !important;
        color:            var(--text-main)   !important;
        border:           1.5px solid var(--border-input) !important;
        border-radius:    8px                !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color:            var(--text-main)   !important;
        background-color: var(--bg-white)    !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"],
    [data-baseweb="menu"] ul {
        background-color: var(--bg-white)    !important;
        border:           1px solid var(--border-input) !important;
        border-radius:    8px                !important;
        box-shadow:       0 4px 16px rgba(0,0,0,0.10)   !important;
    }
    [role="option"],
    [data-baseweb="menu"] li {
        background-color: var(--bg-white)    !important;
        color:            var(--text-main)   !important;
    }
    [role="option"]:hover,
    [data-baseweb="menu"] li:hover {
        background-color: var(--bg-green-soft) !important;
        color:            var(--urba-verde-escuro) !important;
    }

    /* ── NUMBER INPUT ── */
    [data-testid="stNumberInput"] {
        background-color: var(--bg-white) !important;
    }
    [data-testid="stNumberInput"] > div {
        background-color: var(--bg-white)    !important;
        border:           1.5px solid var(--border-input) !important;
        border-radius:    8px                !important;
    }
    [data-testid="stNumberInput"] button {
        background-color: #F4F6F8            !important;
        color:            var(--text-main)   !important;
        border:           1px solid var(--border-input) !important;
    }
    [data-testid="stNumberInput"] button:hover {
        background-color: #E8F5EE            !important;
        color:            var(--urba-verde-escuro) !important;
    }

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploaderDropzone"] {
        background-color: var(--bg-green-soft) !important;
        border:           2px dashed var(--urba-verde) !important;
        border-radius:    10px               !important;
        color:            var(--text-main)   !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: var(--text-main) !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: var(--urba-verde)  !important;
        color:            #FFFFFF            !important;
        border:           none               !important;
        border-radius:    6px                !important;
    }

    /* ── EXPANDER ── */
    [data-testid="stExpander"],
    [data-testid="stExpander"] > div,
    details, details > div,
    details > summary {
        background-color: var(--bg-white)    !important;
        color:            var(--text-main)   !important;
        border:           1px solid var(--border-light) !important;
        border-radius:    10px               !important;
    }
    details > summary {
        font-weight:  600                    !important;
        color:        var(--text-main)       !important;
        padding:      10px 14px              !important;
    }
    details[open] > summary {
        border-bottom: 1px solid var(--border-light) !important;
        border-radius: 10px 10px 0 0         !important;
    }
    details > div * {
        color:            var(--text-main)   !important;
        background-color: var(--bg-white)    !important;
    }
    details > div label,
    details > div p,
    details > div span {
        color: #374151 !important;
    }
    details > div [data-baseweb="input"] > div,
    details > div [data-baseweb="base-input"] > div {
        background-color: var(--bg-white)    !important;
        border:           1.5px solid var(--border-input) !important;
    }
    details > div input {
        background-color: var(--bg-white)    !important;
        color:            var(--text-main)   !important;
    }

    /* ── CONTAINERS / CARDS ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #F8FAFB            !important;
        border:           1px solid var(--border-light) !important;
        border-radius:    12px               !important;
        color:            var(--text-main)   !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] * {
        color: var(--text-main) !important;
    }

    /* ── MÉTRICAS ── */
    div[data-testid="stMetric"] {
        min-height:    108px                 !important;
        padding:       13px 15px             !important;
        border:        1px solid var(--card-border) !important;
        border-left:   4px solid var(--urba-verde)  !important;
        border-radius: 12px                  !important;
        background:    var(--bg-white)       !important;
    }
    [data-testid="stMetricLabel"] p {
        color:     var(--text-muted) !important;
        font-size: .82rem            !important;
    }
    [data-testid="stMetricValue"] {
        color:       var(--text-main) !important;
        font-size:   1.4rem           !important;
        font-weight: 700              !important;
    }
    [data-testid="stMetricDelta"] {
        color: var(--urba-verde) !important;
    }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] *,
    .stDataFrame, iframe {
        background-color: var(--bg-white) !important;
        color:            var(--text-main) !important;
    }

    /* ── ALERTAS ── */
    [data-testid="stAlert"] {
        border-radius:    10px !important;
        border-left-width: 4px !important;
    }

    /* ── BOTÕES ── */
    .stButton > button {
        font-family:   'Inter', sans-serif !important;
        font-weight:   700                 !important;
        border-radius: 9px                 !important;
        min-height:    42px                !important;
        transition:    all .18s ease       !important;
    }
    .stButton > button[kind="primary"] {
        background-color: var(--urba-verde) !important;
        color:            #FFFFFF           !important;
        border:           none              !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--urba-verde-escuro)          !important;
        box-shadow:       0 4px 12px rgba(7,157,86,0.30)    !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: var(--bg-white)   !important;
        color:            var(--urba-verde) !important;
        border:           1.5px solid var(--urba-verde) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--bg-green-soft) !important;
    }
    .stDownloadButton > button {
        background-color: var(--urba-laranja) !important;
        color:            #FFFFFF             !important;
        border:           none                !important;
        font-weight:      700                 !important;
        border-radius:    9px                 !important;
    }
    .stDownloadButton > button:hover {
        background-color: #e07a1a !important;
    }

    /* ── DIVIDER ── */
    hr { border-color: var(--border-light) !important; }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar       { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #F4F6F8; }
    ::-webkit-scrollbar-thumb { background: #CBD5E0; border-radius: 3px; }

    /* ══════════════════════════════════════════
       COMPONENTES CUSTOMIZADOS
    ══════════════════════════════════════════ */

    /* ── HERO BANNER ── */
    .urba-hero {
        display:         flex;
        align-items:     center;
        gap:             28px;
        flex-wrap:       wrap;
        border-radius:   18px;
        padding:         22px 28px;
        margin-bottom:   22px;
        background:      var(--urba-verde);
        border-bottom:   5px solid var(--urba-laranja);
        color:           #FFFFFF;
    }
    .urba-hero img        { height: 64px; width: auto; }
    .urba-hero-texto      { flex: 1 1 320px; }
    .urba-kicker {
        font-size:      .78rem;
        font-weight:    800;
        letter-spacing: .12em;
        text-transform: uppercase;
        color:          #FFD9B3;
        margin-bottom:  5px;
    }
    .urba-title {
        font-size:   clamp(1.6rem, 3vw, 2.35rem);
        font-weight: 800;
        line-height: 1.08;
        margin:      0;
        color:       #FFFFFF !important;
    }
    .urba-subtitle {
        color:      rgba(255,255,255,.88);
        font-size:  .98rem;
        margin-top: 8px;
    }

    /* ── LOGIN CARD ── */
    .login-card {
        border:        1px solid var(--card-border);
        border-top:    5px solid var(--urba-verde);
        border-radius: 18px;
        padding:       32px 28px 24px 28px;
        background:    var(--bg-white);
        box-shadow:    0 8px 28px rgba(7,157,86,.10);
        margin-top:    6vh;
        text-align:    center;
    }
    .login-card img   { height: 58px; width: auto; margin-bottom: 14px; }
    .login-kicker {
        font-size:      .78rem;
        font-weight:    800;
        letter-spacing: .12em;
        text-transform: uppercase;
        color:          var(--urba-laranja);
    }
    .login-title {
        font-size:   1.8rem;
        font-weight: 800;
        margin:      6px 0;
        color:       #12301F !important;
    }
    .login-sub {
        color:         var(--text-muted);
        margin-bottom: 8px;
    }

    /* ── CARD RESUMO ── */
    .card-resumo {
        border:        1px solid var(--card-border);
        border-left:   4px solid var(--urba-verde);
        border-radius: 10px;
        background:    var(--bg-white);
        padding:       10px 14px 8px 14px;
        min-height:    72px;
    }
    .card-label {
        font-size:      .72rem;
        font-weight:    700;
        text-transform: uppercase;
        letter-spacing: .07em;
        color:          var(--text-muted);
        margin-bottom:  4px;
        white-space:    nowrap;
        overflow:       hidden;
        text-overflow:  ellipsis;
    }
    .card-valor {
        font-size:     1.05rem;
        font-weight:   800;
        color:         #12301F;
        white-space:   nowrap;
        overflow:      hidden;
        text-overflow: ellipsis;
    }

    /* ── CARDS DE RISCO ── */
    .risco-baixo {
        background:    #E8F5E9;
        border-left:   4px solid #079D56;
        border-radius: 8px;
        padding:       10px 14px;
        margin-bottom: 6px;
    }
    .risco-moderado {
        background:    #FFF8E1;
        border-left:   4px solid #FFC107;
        border-radius: 8px;
        padding:       10px 14px;
        margin-bottom: 6px;
    }
    .risco-alto {
        background:    #FFEBEE;
        border-left:   4px solid #E53935;
        border-radius: 8px;
        padding:       10px 14px;
        margin-bottom: 6px;
    }

    /* ── OBS BOX ── */
    .obs-box {
        background:    #F0FFF6;
        border:        1px solid #B2DFCC;
        border-radius: 8px;
        padding:       8px 12px;
        font-size:     .88rem;
        color:         #12301F;
        margin-top:    6px;
    }
    .obs-label {
        font-size:      .70rem;
        font-weight:    800;
        text-transform: uppercase;
        letter-spacing: .07em;
        color:          var(--urba-verde);
        margin-bottom:  3px;
    }

    /* ── BADGE DE PERFIL ── */
    .badge-perfil {
        display:       inline-block;
        background:    rgba(255,255,255,.20);
        border-radius: 20px;
        padding:       2px 10px;
        font-size:     .72rem;
        font-weight:   700;
        color:         #FFFFFF;
        letter-spacing: .06em;
    }

    /* ── RODAPÉ ── */
    .urba-footer {
        text-align:   center;
        padding:      24px 0 8px;
        margin-top:   32px;
        border-top:   1px solid var(--border-light);
    }
    .urba-footer-marca {
        color:       var(--urba-verde);
        font-weight: 800;
        font-size:   .9rem;
    }
    .urba-footer-info {
        color:     #9CA3AF;
        font-size: .82rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# COMPONENTES HTML REUTILIZÁVEIS
# ============================================================

def hero_banner(subtitulo: str = "Avaliação estruturada do risco de distrato no momento da venda.") -> None:
    """Renderiza o hero banner verde com logo e título."""
    logo_b64  = imagem_base64(LOGO_BRANCO)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="Urba">'
        if logo_b64 else ""
    )
    st.markdown(f"""
    <div class="urba-hero">
        {logo_html}
        <div class="urba-hero-texto">
            <div class="urba-kicker">Projeto Defensores do Contrato</div>
            <div class="urba-title">Simulador de Score de Vendas</div>
            <div class="urba-subtitle">{subtitulo}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def login_card() -> None:
    """Renderiza o cabeçalho do card de login."""
    logo_b64  = imagem_base64(LOGO_COLORIDO)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="Urba">'
        if logo_b64 else
        '<div style="font-size:2rem;font-weight:900;color:#079D56;">Urba</div>'
    )
    st.markdown(f"""
    <div class="login-card">
        {logo_html}
        <div class="login-kicker">Projeto Defensores do Contrato</div>
        <div class="login-title">Simulador de Score de Vendas</div>
        <div class="login-sub">Identifique-se com suas credenciais para continuar.</div>
    </div>
    """, unsafe_allow_html=True)


def card_resumo(label: str, valor: str) -> str:
    """Retorna HTML de um card de resumo (label + valor)."""
    return f"""
    <div class="card-resumo">
        <div class="card-label">{label}</div>
        <div class="card-valor" title="{valor}">{valor}</div>
    </div>
    """


def rodape(versao: str = "V1.0") -> None:
    """Renderiza o rodapé do sistema."""
    st.markdown(f"""
    <div class="urba-footer">
        <span class="urba-footer-marca">Urba</span>
        <span class="urba-footer-info">
            &nbsp;•&nbsp;Simulador de Score de Vendas {versao}
            &nbsp;•&nbsp;Projeto Defensores do Contrato
        </span>
    </div>
    """, unsafe_allow_html=True)
