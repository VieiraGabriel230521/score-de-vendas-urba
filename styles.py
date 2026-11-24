# styles.py
# Score de Vendas Urba
# Identidade visual Urba (padrão "Território de marca"):
#   - Verde #079D56 + Laranja #FF8C23 como protagonistas
#   - Fundo off-white #EDE9E3, cards brancos
#   - Gradiente 45° #004D3F → #007751 só no topo/login (como a capa)
#   - Assinatura da marca: forma preenchida + contorno deslocado
#   - Grafismos de "casinhas" em contorno (rotação 0/45/90/135°)
#   - Fonte Verdana (fonte de sistema autorizada pelo manual): nada de
#     fonte externa → página mais leve
#
# V2.0 — redesign completo. Todo o HTML é estático e inline (sem JS,
# sem bibliotecas de gráfico), para manter o app leve.

from __future__ import annotations

import base64
import html
import math
from functools import lru_cache

import streamlit as st

# ============================================================
# PALETA URBA
# ============================================================
VERDE          = "#079D56"
VERDE_ESCURO   = "#006B3F"
VERDE_PROFUNDO = "#004D3F"
VERDE_MEDIO    = "#007751"
VERDE_CLARO    = "#B9DFC9"
LARANJA        = "#FF8C23"
AMARELO        = "#FFB91A"
LIMAO          = "#82EB5C"
AGUA           = "#00D38D"
PINK           = "#F7287C"
OFFWHITE       = "#EDE9E3"
TEXTO          = "#1B1712"
CINZA_70       = "#4D4D4D"
CINZA_60       = "#666666"
CINZA_50       = "#808080"
LINHA          = "#DDD6CB"

# Compatibilidade com nomes antigos
COR_VERDE        = VERDE
COR_VERDE_ESCURO = VERDE_ESCURO
COR_LARANJA      = LARANJA

LOGO_COLORIDO = "assets/logo_urba.png"         # verde + laranja (fundo claro)
LOGO_BRANCO   = "assets/logo_urba_branco.png"  # branco + laranja (fundo verde)

# Cores por classificação de risco (só cores da paleta)
RISCO = {
    "green":  {"cor": VERDE,   "escura": VERDE_ESCURO, "suave": "#E3F3EA", "rotulo": "Baixo risco"},
    "orange": {"cor": LARANJA, "escura": "#B35A0A",    "suave": "#FFEEDD", "rotulo": "Risco moderado"},
    "red":    {"cor": PINK,    "escura": "#B0124F",    "suave": "#FDE3EE", "rotulo": "Alto risco"},
}


def cor_por_classificacao(classificacao: str) -> str:
    c = str(classificacao or "").upper()
    if "BAIXO" in c:
        return "green"
    if "MODERADO" in c:
        return "orange"
    return "red"


def esc(valor) -> str:
    return html.escape(str(valor), quote=True)


def limpar_html(trecho: str) -> str:
    """
    Junta o HTML em uma linha só. Sem isso, o Markdown do Streamlit trata
    linhas com 4+ espaços de recuo como bloco de código e mostra o HTML cru.
    """
    return " ".join(l.strip() for l in str(trecho).splitlines() if l.strip())


def html_md(trecho: str) -> None:
    st.markdown(limpar_html(trecho), unsafe_allow_html=True)


# ============================================================
# UTILITÁRIOS
# ============================================================
@lru_cache(maxsize=8)
def imagem_base64(caminho: str) -> str:
    try:
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return ""


def logo_img(versao: str = "colorido", altura: int = 36) -> str:
    caminho = LOGO_BRANCO if versao == "branco" else LOGO_COLORIDO
    b64 = imagem_base64(caminho)
    if not b64:
        return ""
    return (f'<img src="data:image/png;base64,{b64}" alt="Urba" '
            f'style="height:{altura}px;width:auto;display:block;">')


# ------------------------------------------------------------
# Ícones (traço, estilo da marca) — SVG inline, sem fonte externa
# ------------------------------------------------------------
_ICONES = {
    "casa":        '<path d="M3 10.5 12 3l9 7.5V21H3z"/><path d="M9.5 21v-6h5v6"/>',
    "usuario":     '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/>',
    "usuarios":    '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.5 3-5.5 6.5-5.5s6.5 2 6.5 5.5"/><path d="M15.5 4.8a3.5 3.5 0 0 1 0 6.4M17.5 14.8c2.4.6 4 2.4 4 5.2"/>',
    "documento":   '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
    "moeda":       '<circle cx="12" cy="12" r="9"/><path d="M14.8 9.2c-.4-1-1.5-1.6-2.8-1.6-1.6 0-2.8.8-2.8 2.1 0 2.9 5.8 1.6 5.8 4.5 0 1.3-1.3 2.2-3 2.2-1.4 0-2.6-.6-3-1.7M12 6v1.6M12 16.4V18"/>',
    "grafico":     '<path d="M3 21h18"/><path d="M6 17v-5M11 17V7M16 17v-8M21 17V4"/>',
    "alvo":        '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "lampada":     '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
    "salvar":      '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/>',
    "ajustes":     '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
    "calculadora": '<rect x="5" y="3" width="14" height="18" rx="2.5"/><path d="M8.5 7.5h7M8.5 12h.01M12 12h.01M15.5 12h.01M8.5 16h.01M12 16h.01M15.5 16h.01"/>',
    "lista":       '<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
    "predio":      '<path d="M3 21h18"/><path d="M5 21V9l7-5 7 5v12"/><path d="M9.5 21v-5h5v5M9.5 11h.01M14.5 11h.01"/>',
    "escudo":      '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "check":       '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16.5 9.5"/>',
    "alerta":      '<path d="M12 3.5 22 20H2z"/><path d="M12 10v4.5M12 17.3h.01"/>',
    "historico":   '<path d="M3.5 12a8.5 8.5 0 1 0 2.5-6"/><path d="M3 4v4h4M12 7.5V12l3 2"/>',
    "upload":      '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5"/><path d="M4 15v5h16v-5"/>',
}


def icone(nome: str, cor: str = VERDE, tam: int = 20, traco: float = 2) -> str:
    corpo = _ICONES.get(nome, _ICONES["casa"])
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{cor}" stroke-width="{traco}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{corpo}</svg>')


# ------------------------------------------------------------
# Grafismo da marca: "casinhas" em contorno
# ------------------------------------------------------------
def _casinha(cx: float, cy: float, tam: float, rot: int, cor: str, opac: float = 1.0, traco: float = 3) -> str:
    w, h = tam, tam
    pts = [(-w/2, h/2), (-w/2, -h*0.05), (0, -h/2), (w/2, -h*0.05), (w/2, h/2)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    return (f'<path d="{d}" transform="translate({cx} {cy}) rotate({rot})" fill="none" '
            f'stroke="{cor}" stroke-opacity="{opac}" stroke-width="{traco}" stroke-linejoin="round"/>')


def grafismo_casinhas(largura: int = 520, altura: int = 150, escala: float = 1.0) -> str:
    """Composição fixa de 5 casinhas sem sobreposição (2 cores: limão e laranja)."""
    s = escala
    casas = [
        (70,  80,  62, 0,   LIMAO,   .85),
        (170, 50,  40, 45,  LARANJA, 1.0),
        (255, 98,  78, 0,   LIMAO,   .55),
        (360, 46,  46, 135, LIMAO,   .85),
        (450, 100, 58, 90,  LARANJA, .9),
    ]
    paths = "".join(_casinha(x*s, y*s, t*s, r, c, o, 3*s if s >= 1 else 3) for x, y, t, r, c, o in casas)
    return (f'<svg viewBox="0 0 {largura*s:.0f} {altura*s:.0f}" width="{largura*s:.0f}" '
            f'height="{altura*s:.0f}" aria-hidden="true">{paths}</svg>')


# ============================================================
# CSS GLOBAL
# ============================================================
_CSS = """
<style>
:root{
  --verde:#079D56; --verde-escuro:#006B3F; --verde-profundo:#004D3F; --verde-medio:#007751;
  --verde-claro:#B9DFC9; --verde-suave:#E3F3EA;
  --laranja:#FF8C23; --laranja-suave:#FFEEDD; --amarelo:#FFB91A; --limao:#82EB5C; --pink:#F7287C;
  --offwhite:#EDE9E3; --texto:#1B1712; --cinza70:#4D4D4D; --cinza60:#666666; --cinza50:#808080;
  --linha:#DDD6CB; --linha-suave:#ECE7DF;
  --raio:12px; --raio-sm:9px;
  --sombra:0 1px 2px rgba(27,23,18,.05), 0 6px 18px rgba(27,23,18,.06);
  --fonte: Verdana, Geneva, "DejaVu Sans", Tahoma, sans-serif;
}

/* ---------- Base ---------- */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"]{
  background:var(--offwhite) !important;
}
/* Fonte: definida no tema (.streamlit/config.toml). Aqui só o reforço
   leve na raiz — sem seletor universal, que pesava no recálculo de estilo. */
html, body, [data-testid="stApp"]{ font-family:var(--fonte); }
[data-testid="stApp"]{ color:var(--texto); }

/* Esconde cromo do Streamlit e a sidebar (navegação é no topo) */
#MainMenu, header[data-testid="stHeader"], footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"]{ display:none !important; }

.block-container, [data-testid="stMainBlockContainer"]{
  max-width:1280px !important; padding:1.1rem 2rem 2.5rem !important;
}

/* ---------- Tipografia ---------- */
h1,h2,h3,h4{ color:var(--verde) !important; font-weight:700 !important; letter-spacing:-.01em; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, .stRadio label p{
  color:var(--cinza70) !important; font-weight:700 !important; font-size:.76rem !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p{ color:var(--cinza60) !important; font-size:.76rem !important; }
[data-testid="stMarkdownContainer"] p{ font-size:.86rem; }

/* ---------- Containers / cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]),
div[data-testid="stVerticalBlockBorderWrapper"][class*="border"]{
  border-radius:var(--raio) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]{ border-color:var(--linha) !important; }
/* Cards das etapas com a mesma altura lado a lado */
div[data-testid="stColumn"]:has([class*="st-key-card_"]) > div[data-testid="stVerticalBlock"],
div[data-testid="stColumn"]:has([class*="st-key-card_"]) > div > div[data-testid="stVerticalBlock"],
div[data-testid="stColumn"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card_"]),
div[data-testid="stColumn"] [class*="st-key-card_"]{ height:100%; }
div[class*="st-key-card"]{
  background:#fff; border:1px solid var(--linha); border-radius:var(--raio);
  padding:18px 18px 14px; box-shadow:var(--sombra);
}
[data-testid="stExpander"] details{
  background:#fff; border:1px solid var(--linha) !important; border-radius:var(--raio) !important;
}
[data-testid="stExpander"] summary p{ font-weight:700; color:var(--verde-escuro) !important; font-size:.85rem; }
hr{ border-color:var(--linha) !important; margin:1.1rem 0 !important; }

/* ---------- Inputs ---------- */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div,
div[data-baseweb="textarea"], [data-testid="stNumberInputContainer"]{
  background:#fff !important; border-radius:var(--raio-sm) !important;
}
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"]{
  border:1.5px solid var(--linha) !important; transition:border-color .15s, box-shadow .15s;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"]:focus-within{
  border-color:var(--verde) !important; box-shadow:0 0 0 3px rgba(7,157,86,.14) !important;
}
/* Streamlit mais novo (react-aria): mesmos estilos */
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"], .react-aria-ComboBox [role="group"],
[data-testid="stDateInputField"]{
  background:#fff !important; border:1.5px solid var(--linha) !important; border-radius:var(--raio-sm) !important;
  transition:border-color .15s, box-shadow .15s;
}
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stNumberInputContainer"]:focus-within,
.react-aria-ComboBox [role="group"]:focus-within{
  border-color:var(--verde) !important; box-shadow:0 0 0 3px rgba(7,157,86,.14) !important;
}
[data-testid="InputInstructions"]{ display:none !important; }
input, textarea{ color:var(--texto) !important; font-size:.86rem !important; }
input::placeholder{ color:#A39D94 !important; }
[data-testid="stNumberInput"] button{ background:#fff !important; border:none !important; }
[data-testid="stNumberInput"] button:hover{ background:var(--verde-suave) !important; }

/* Upload */
[data-testid="stFileUploaderDropzone"]{
  background:#FAF8F5 !important; border:1.5px dashed #CFC7BA !important; border-radius:var(--raio) !important;
  padding:12px !important;
}
[data-testid="stFileUploaderDropzone"]:hover{ border-color:var(--verde) !important; background:var(--verde-suave) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span, [data-testid="stFileUploaderDropzoneInstructions"] small{ font-size:.74rem !important; }

/* ---------- Botões (sem deslocamento no hover: clique nunca "escapa") ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button{
  border-radius:var(--raio-sm) !important; font-weight:700 !important; font-size:.82rem !important;
  min-height:42px; transition:background-color .15s, box-shadow .15s, border-color .15s, color .15s !important;
}
button[kind^="primary"], [data-testid^="stBaseButton-primary"]{
  background:linear-gradient(45deg, var(--verde-escuro), var(--verde)) !important;
  border:none !important; color:#fff !important; box-shadow:0 2px 8px rgba(7,157,86,.25) !important;
}
button[kind^="primary"] *, [data-testid^="stBaseButton-primary"] *{ color:#fff !important; }
button[kind^="primary"]:hover, [data-testid^="stBaseButton-primary"]:hover{ box-shadow:0 4px 14px rgba(7,157,86,.35) !important; filter:brightness(1.04); }
button[kind^="primary"]:disabled, [data-testid^="stBaseButton-primary"]:disabled{
  background:#CFC7BA !important; box-shadow:none !important; filter:none; cursor:not-allowed;
}
button[kind^="secondary"], [data-testid^="stBaseButton-secondary"]{
  background:#fff !important; border:1.5px solid var(--verde) !important; color:var(--verde-escuro) !important;
}
button[kind^="secondary"] *, [data-testid^="stBaseButton-secondary"] *{ color:var(--verde-escuro) !important; }
button[kind^="secondary"]:hover, [data-testid^="stBaseButton-secondary"]:hover{ background:var(--verde-suave) !important; }
button[kind="tertiary"], [data-testid="stBaseButton-tertiary"]{ color:var(--verde-escuro) !important; }

/* ---------- Navegação (abas em pílula) ---------- */
/* Barra de abas "flutuante" dentro do topo verde: pílula de vidro,
   aba ativa em branco com animação ao trocar de página */
div[class*="st-key-navbar"]{
  margin:-74px 0 18px; padding:0 30px; box-sizing:border-box; position:relative; z-index:3; align-items:center;
}
div[class*="st-key-nav_tabs"]{
  width:fit-content !important; flex:0 1 auto !important; gap:4px !important;
  background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.14);
  border-radius:999px; padding:5px; backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  box-shadow:0 8px 24px rgba(0,40,30,.25);
}
div[class*="st-key-navbar"] .stButton > button{
  min-height:38px !important; height:38px; padding:0 18px !important; border-radius:999px !important;
  font-size:.8rem !important; white-space:nowrap; box-shadow:none !important;
  transition:background-color .2s ease, color .2s ease, box-shadow .2s ease !important;
}
div[class*="st-key-nav_tabs"] button[kind^="secondary"], div[class*="st-key-nav_tabs"] [data-testid^="stBaseButton-secondary"]{
  background:transparent !important; border:none !important;
}
div[class*="st-key-nav_tabs"] button[kind^="secondary"] *, div[class*="st-key-nav_tabs"] [data-testid^="stBaseButton-secondary"] *{
  color:rgba(255,255,255,.82) !important;
}
div[class*="st-key-nav_tabs"] button[kind^="secondary"]:hover, div[class*="st-key-nav_tabs"] [data-testid^="stBaseButton-secondary"]:hover{
  background:rgba(255,255,255,.12) !important;
}
div[class*="st-key-nav_tabs"] button[kind^="secondary"]:hover *{ color:#fff !important; }
div[class*="st-key-nav_tabs"] button[kind^="primary"], div[class*="st-key-nav_tabs"] [data-testid^="stBaseButton-primary"]{
  background:#fff !important; filter:none !important;
  box-shadow:0 2px 10px rgba(0,0,0,.18), inset 0 -2px 0 var(--laranja) !important;
  animation:u-pop .32s cubic-bezier(.2,.9,.3,1.3);
}
div[class*="st-key-nav_tabs"] button[kind^="primary"] *, div[class*="st-key-nav_tabs"] [data-testid^="stBaseButton-primary"] *{
  color:var(--verde-escuro) !important;
}
div[class*="st-key-nav_tabs"] button[kind^="primary"] [data-testid="stIconMaterial"]{ color:var(--laranja) !important; }
div[class*="st-key-nav_sair"] button{
  background:transparent !important; border:1px solid rgba(255,255,255,.35) !important;
}
div[class*="st-key-nav_sair"] button *{ color:#fff !important; }
div[class*="st-key-nav_sair"] button:hover{ background:var(--laranja) !important; border-color:var(--laranja) !important; }
@keyframes u-pop{ from{ transform:scale(.9); opacity:.55; } to{ transform:scale(1); opacity:1; } }
@keyframes u-sobe{ from{ transform:translateY(8px); opacity:0; } to{ transform:none; opacity:1; } }
.u-secao{ animation:u-sobe .2s ease-out; }

/* ---------- Alertas ---------- */
[data-testid="stAlert"] > div{ border-radius:var(--raio) !important; font-size:.84rem; }
[data-testid="stAlertContentSuccess"]{ color:var(--verde-escuro) !important; }

/* ---------- Tabelas ---------- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{ border:1px solid var(--linha); border-radius:var(--raio); overflow:hidden; background:#fff; }

/* ---------- Componentes HTML ---------- */
.u-hero{
  position:relative; overflow:hidden; border-radius:18px;
  background:linear-gradient(45deg, #004D3F 0%, #007751 100%);
  padding:22px 30px 86px; display:flex; align-items:center; gap:26px; min-height:112px;
}
.u-hero-graf{ position:absolute; right:215px; top:4px; opacity:.9; pointer-events:none; }
.u-hero > div:not(.u-hero-graf):first-of-type{ flex-shrink:0; }
.u-hero-sep{ width:1px; align-self:stretch; background:rgba(255,255,255,.25); }
.u-hero-kicker{ color:var(--laranja); font-weight:700; font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; margin-bottom:4px; }
.u-hero-title{ color:#fff; font-weight:700; font-size:1.45rem; line-height:1.15; letter-spacing:-.01em; }
.u-hero-sub{ color:rgba(255,255,255,.82); font-size:.8rem; margin-top:4px; }
.u-hero-user{ margin-left:auto; position:relative; z-index:1; display:flex; align-items:center; gap:10px;
  background:rgba(0,0,0,.18); border:1px solid rgba(255,255,255,.18); border-radius:999px; padding:6px 14px 6px 6px; }
.u-avatar{ width:32px; height:32px; border-radius:50%; background:var(--laranja); color:#fff; font-weight:700;
  display:flex; align-items:center; justify-content:center; font-size:.8rem; }
.u-hero-user-nome{ color:#fff; font-weight:700; font-size:.78rem; line-height:1.2; }
.u-hero-user-perfil{ color:var(--limao); font-size:.64rem; font-weight:700; letter-spacing:.05em; }

.u-secao{ display:flex; align-items:center; gap:12px; margin:6px 0 14px; }
.u-secao-ico{ width:38px; height:38px; border-radius:10px; background:#fff; border:1px solid var(--linha);
  display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.u-secao-tit{ color:var(--verde); font-weight:700; font-size:1.05rem; letter-spacing:-.01em; line-height:1.2; }
.u-secao-sub{ color:var(--cinza60); font-size:.76rem; margin-top:2px; }

.u-colhead{ display:flex; align-items:center; gap:8px; padding-bottom:10px; margin-bottom:12px; border-bottom:2px solid var(--linha-suave); }
.u-colhead span{ color:var(--verde-escuro); font-weight:700; font-size:.86rem; }
.u-colhead-num{ width:22px; height:22px; border-radius:50%; background:var(--laranja); color:#fff !important;
  font-size:.7rem !important; display:flex; align-items:center; justify-content:center; }

.u-dado{ background:var(--verde-suave); border-radius:10px; padding:10px 12px; margin:8px 0 10px; }
.u-dado-tit{ color:var(--verde-escuro); font-weight:700; font-size:.7rem; letter-spacing:.05em; text-transform:uppercase; margin-bottom:6px; display:flex; gap:6px; align-items:center; }
.u-dado-row{ display:flex; justify-content:space-between; gap:10px; font-size:.76rem; padding:3px 0; border-top:1px solid rgba(7,157,86,.12); }
.u-dado-row:first-of-type{ border-top:none; }
.u-dado-row b{ color:var(--texto); text-align:right; }
.u-dado-row span{ color:var(--cinza60); }
.u-dado-row .falta{ color:#B35A0A; font-weight:700; }

/* Assinatura da marca: card preenchido + contorno deslocado */
.u-sig{ position:relative; margin:0 0 8px 7px; }
.u-sig::before{ content:""; position:absolute; left:-7px; top:7px; right:7px; bottom:-7px;
  border:2.5px solid var(--sig, var(--laranja)); border-radius:var(--raio); }
.u-sig > .u-sig-card{ position:relative; background:#fff; border-radius:var(--raio); border:1px solid var(--linha); }

.u-kpi{ padding:14px 16px; min-height:92px; }
.u-kpi-lab{ color:var(--cinza60); font-size:.7rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
.u-kpi-val{ color:var(--texto); font-size:1.35rem; font-weight:700; margin-top:6px; letter-spacing:-.01em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.u-kpi-det{ font-size:.7rem; font-weight:700; margin-top:4px; }

.u-chip{ display:inline-block; border-radius:999px; padding:3px 10px; font-size:.68rem; font-weight:700; letter-spacing:.03em; }

.u-resumo{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; }
.u-resumo-item{ background:#fff; border:1px solid var(--linha); border-radius:10px; padding:10px 12px; min-width:0; }
.u-resumo-lab{ color:var(--cinza60); font-size:.66rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }
.u-resumo-val{ color:var(--texto); font-size:.86rem; font-weight:700; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.u-score{ padding:18px 18px 16px; text-align:center; }
.u-score-badge{ display:inline-flex; align-items:center; gap:8px; border-radius:999px; padding:7px 16px; font-weight:700; font-size:.85rem; letter-spacing:.03em; }
.u-score-leg{ display:flex; justify-content:center; gap:14px; margin-top:12px; flex-wrap:wrap; }
.u-score-leg span{ font-size:.66rem; color:var(--cinza60); display:flex; align-items:center; gap:5px; }
.u-score-leg i{ width:9px; height:9px; border-radius:3px; display:inline-block; }

.u-barras{ padding:16px 18px 10px; }
.u-barra{ display:grid; grid-template-columns: 190px 1fr 92px; align-items:center; gap:14px; padding:9px 0; border-top:1px solid var(--linha-suave); }
.u-barra:first-child{ border-top:none; }
.u-barra-nome{ font-size:.8rem; font-weight:700; color:var(--texto); }
.u-barra-meta{ font-size:.68rem; color:var(--cinza60); margin-top:2px; }
.u-barra-trilho{ height:10px; background:var(--linha-suave); border-radius:999px; overflow:hidden; }
.u-barra-fill{ height:100%; border-radius:999px; }
.u-barra-pts{ text-align:right; font-size:.82rem; font-weight:700; color:var(--texto); }
.u-barra-pts small{ color:var(--cinza50); font-weight:400; font-size:.7rem; }

.u-cenario{ display:grid; grid-template-columns: 34px 1fr auto; gap:12px; align-items:center; background:#fff;
  border:1px solid var(--linha); border-radius:10px; padding:10px 14px; margin-bottom:8px; }
.u-cenario-ico{ width:34px; height:34px; border-radius:9px; background:var(--laranja-suave); display:flex; align-items:center; justify-content:center; }
.u-cenario-var{ font-size:.68rem; color:var(--cinza60); font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
.u-cenario-txt{ font-size:.8rem; color:var(--texto); margin-top:2px; }
.u-cenario-res{ text-align:right; white-space:nowrap; }
.u-cenario-ganho{ color:var(--verde); font-weight:700; font-size:.9rem; }

.u-faltando{ display:flex; gap:10px; align-items:flex-start; background:#FFF6EC; border:1px solid #FFD6AE; border-radius:10px; padding:10px 14px; font-size:.78rem; color:#7A3E06; }
.u-faltando b{ color:#7A3E06; }

.u-footer{ margin-top:34px; padding-top:14px; border-top:1px solid var(--linha); display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; }
.u-footer span{ font-size:.68rem; color:var(--cinza60); }
.u-footer b{ color:var(--laranja); font-size:.78rem; }

@media (max-width: 1150px){ .u-hero-graf{ display:none; } }
@media (max-width: 900px){
  .u-hero-graf{ display:none; }
  .u-resumo{ grid-template-columns:repeat(2, minmax(0,1fr)); }
  .u-barra{ grid-template-columns: 1fr 80px; }
  .u-barra-trilho{ grid-column: 1 / span 2; }
  .block-container, [data-testid="stMainBlockContainer"]{ padding:.8rem .9rem 2rem !important; }
  div[class*="st-key-navbar"]{ margin:-70px 0 14px; padding:0 12px; flex-wrap:nowrap !important; }
  div[class*="st-key-nav_tabs"]{ flex-wrap:nowrap !important; overflow-x:auto; max-width:calc(100vw - 110px); scrollbar-width:none; }
  div[class*="st-key-nav_tabs"]::-webkit-scrollbar{ display:none; }
  div[class*="st-key-navbar"] .stButton > button{ padding:0 12px !important; }
  div[class*="st-key-nav_sair"] button p{ display:none; }
  .u-hero{ flex-wrap:wrap; padding:18px 18px 84px; gap:12px; }
  .u-hero-sep, .u-hero-sub{ display:none; }
  .u-hero-title{ font-size:1.15rem; }
  .u-hero-user{ margin-left:0; }
}
</style>
"""


def aplicar_estilos() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


# ============================================================
# COMPONENTES
# ============================================================
def hero_banner(usuario: dict | None = None,
                titulo: str = "Simulador de Score de Vendas",
                subtitulo: str = "Avaliação estruturada do risco de distrato no momento da venda.") -> None:
    user_html = ""
    if usuario:
        nome = str(usuario.get("nome") or "")
        iniciais = "".join(p[0] for p in nome.split()[:2]).upper() or "U"
        perfil = "Administrador" if usuario.get("perfil") == "ADMINISTRADOR" else "Vendedor"
        user_html = f"""
        <div class="u-hero-user">
          <div class="u-avatar">{esc(iniciais)}</div>
          <div><div class="u-hero-user-nome">{esc(nome)}</div>
               <div class="u-hero-user-perfil">{perfil.upper()}</div></div>
        </div>"""
    html_md(f"""
    <div class="u-hero">
      <div class="u-hero-graf">{grafismo_casinhas(520, 150, 0.62)}</div>
      <div style="position:relative;z-index:1;">{logo_img("branco", 38)}</div>
      <div class="u-hero-sep"></div>
      <div style="position:relative;z-index:1;">
        <div class="u-hero-kicker">Projeto Classificador de Vendas</div>
        <div class="u-hero-title">{esc(titulo)}</div>
        <div class="u-hero-sub">{esc(subtitulo)}</div>
      </div>
      {user_html}
    </div>
    """)


# ============================================================
# LOGIN — visual inspirado na SpellUI (Light Rays, Animated Gradient,
# Blur Reveal, Shimmer Text, Rich Button, Label Input), refeito em CSS
# puro: sem React, sem JS, sem WebGL. Só transform/opacity animados
# (leve para a GPU) e tudo desligado com "reduzir movimento".
# ============================================================
_CSS_LOGIN = """
<style>
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"]{
  background:#00261F !important;
}
.block-container, [data-testid="stMainBlockContainer"]{ max-width:1180px !important; }
[data-testid="stHorizontalBlock"]{ position:relative; z-index:2; }

/* ---------- Fundo: gradiente animado + raios de luz + grade ---------- */
.lg-bg{ position:fixed; inset:0; z-index:0; overflow:hidden; pointer-events:none;
  background:radial-gradient(120% 95% at 78% 0%, #007751 0%, #004D3F 42%, #00261F 100%); }
.lg-blob{ position:absolute; border-radius:50%; filter:blur(80px); will-change:transform;
  animation:lg-flutua 20s ease-in-out infinite alternate; }
.lg-b1{ width:560px; height:560px; background:#079D56; opacity:.55; left:-160px; top:-180px; }
.lg-b2{ width:460px; height:460px; background:#82EB5C; opacity:.20; right:4%; bottom:-200px; animation-duration:24s; }
.lg-b3{ width:300px; height:300px; background:#FF8C23; opacity:.12; left:58%; top:60%; animation-duration:28s; animation-direction:alternate-reverse; }
.lg-raios{ position:absolute; inset:-25% -10% 0 -10%; transform-origin:62% 0%;
  background:repeating-conic-gradient(from 150deg at 62% 0%, rgba(130,235,92,.13) 0deg 1.6deg, transparent 1.6deg 7deg);
  -webkit-mask-image:radial-gradient(70% 75% at 62% 0%, #000 0%, transparent 72%);
          mask-image:radial-gradient(70% 75% at 62% 0%, #000 0%, transparent 72%);
  animation:lg-raios 16s ease-in-out infinite alternate; }
.lg-grade{ position:absolute; inset:0;
  background-image:linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px),
                   linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px);
  background-size:56px 56px;
  -webkit-mask-image:radial-gradient(80% 70% at 30% 60%, #000 10%, transparent 75%);
          mask-image:radial-gradient(80% 70% at 30% 60%, #000 10%, transparent 75%); }
.lg-casa{ position:absolute; animation:lg-boia 9s ease-in-out infinite; }
@keyframes lg-flutua{ 0%{ transform:translate(0,0) scale(1); } 100%{ transform:translate(90px,60px) scale(1.15); } }
@keyframes lg-raios{ 0%{ transform:rotate(-4deg); opacity:.7; } 100%{ transform:rotate(5deg); opacity:1; } }
@keyframes lg-boia{ 0%,100%{ transform:translateY(0); } 50%{ transform:translateY(-14px); } }

/* ---------- Lado esquerdo ---------- */
.lg-hero{ position:relative; padding:10px 8px 10px 0; }
.lg-badge{ display:inline-flex; align-items:center; gap:8px; margin-top:44px;
  padding:6px 14px 6px 8px; border-radius:999px; font-size:.72rem; font-weight:700; color:#fff;
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.16);
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); }
.lg-badge i{ width:8px; height:8px; border-radius:50%; background:#82EB5C; box-shadow:0 0 0 4px rgba(130,235,92,.18);
  animation:lg-pulsa 2.2s ease-in-out infinite; }
@keyframes lg-pulsa{ 0%,100%{ box-shadow:0 0 0 3px rgba(130,235,92,.25); } 50%{ box-shadow:0 0 0 7px rgba(130,235,92,0); } }
.lg-titulo{ color:#fff; font-weight:700; font-size:3.1rem; line-height:1.07; letter-spacing:-.035em; margin-top:18px; }
.lg-titulo span{ display:inline-block; opacity:0; filter:blur(12px); transform:translateY(14px);
  animation:lg-revela .9s cubic-bezier(.2,.7,.2,1) forwards; }
@keyframes lg-revela{ to{ opacity:1; filter:blur(0); transform:none; } }
.lg-brilho{ background:linear-gradient(100deg, #82EB5C 0%, #82EB5C 35%, #F6FFE9 50%, #FFB91A 65%, #FF8C23 100%);
  background-size:220% 100%; -webkit-background-clip:text; background-clip:text; color:transparent !important;
  animation:lg-revela .9s cubic-bezier(.2,.7,.2,1) forwards, lg-shimmer 3.2s 1.6s ease-in-out infinite !important; }
@keyframes lg-shimmer{ 0%{ background-position:100% 0; } 100%{ background-position:-120% 0; } }

/* ---------- Cartão do formulário ---------- */
div[class*="st-key-login_box"]{
  position:relative; border-radius:26px; padding:34px 32px 28px;
  border:1.5px solid transparent;   /* borda em gradiente verde-limão → laranja */
  background:linear-gradient(#fff, #fff) padding-box,
             linear-gradient(135deg, #82EB5C, rgba(7,157,86,.25) 45%, #FF8C23) border-box;
  box-shadow:0 30px 80px rgba(0,15,10,.55);
  animation:lg-card .8s .25s cubic-bezier(.2,.7,.2,1) both;
}
@keyframes lg-card{ from{ opacity:0; transform:translateY(22px); } to{ opacity:1; transform:none; } }
div[class*="st-key-login_box"] [data-testid="stForm"]{ border:none !important; padding:0 !important; }
.lg-card-tit{ color:#1B1712; font-weight:700; font-size:1.55rem; letter-spacing:-.025em; margin:2px 0 4px; }
.lg-card-sub{ color:#808080; font-size:.8rem; margin-bottom:8px; }

/* Label Input: anel laranja no foco */
div[class*="st-key-login_box"] div[data-baseweb="input"], div[class*="st-key-login_box"] div[data-baseweb="base-input"],
div[class*="st-key-login_box"] [data-testid="stTextInputRootElement"]{
  border-radius:12px !important; background:#FAF8F5 !important; min-height:46px; }
div[class*="st-key-login_box"] [data-testid="stTextInputRootElement"] input{ background:transparent !important; }
div[class*="st-key-login_box"] div[data-baseweb="input"]:focus-within,
div[class*="st-key-login_box"] [data-testid="stTextInputRootElement"]:focus-within{
  border-color:#FF8C23 !important; background:#fff !important; box-shadow:0 0 0 4px rgba(255,140,35,.16) !important; }

/* Rich Button: camadas, brilho interno e reflexo que atravessa no hover */
div[class*="st-key-login_box"] [data-testid="stFormSubmitButton"] > button{
  position:relative; overflow:hidden; min-height:50px !important; border-radius:14px !important; font-size:.9rem !important;
  background:linear-gradient(180deg, #12B565 0%, #079D56 45%, #006B3F 100%) !important;
  border:1px solid #005A35 !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.35), inset 0 -2px 0 rgba(0,0,0,.15), 0 10px 24px rgba(7,157,86,.35) !important;
  margin-top:6px; }
div[class*="st-key-login_box"] [data-testid="stFormSubmitButton"] > button::after{
  content:""; position:absolute; top:0; bottom:0; width:40%; left:-60%;
  background:linear-gradient(100deg, transparent, rgba(255,255,255,.35), transparent); transform:skewX(-20deg);
  transition:left .6s ease; }
div[class*="st-key-login_box"] [data-testid="stFormSubmitButton"] > button:hover::after{ left:120%; }
div[class*="st-key-login_box"] [data-testid="stFormSubmitButton"] > button:hover{
  box-shadow:inset 0 1px 0 rgba(255,255,255,.35), inset 0 -2px 0 rgba(0,0,0,.15), 0 14px 32px rgba(7,157,86,.5) !important; }
.lg-rodape{ display:flex; align-items:center; justify-content:center; gap:8px; margin-top:16px;
  color:#A39D94; font-size:.7rem; }

@media (max-width: 900px){
  .lg-casa{ display:none; }
  .lg-titulo{ font-size:2.1rem; }
  .lg-badge{ margin-top:22px; }
  .lg-hero{ padding:0 0 8px; }
}
@media (prefers-reduced-motion: reduce){
  .lg-bg *, .lg-hero *, div[class*="st-key-login_box"]{ animation:none !important; }
  .lg-titulo span{ opacity:1; filter:none; transform:none; }
}
</style>
"""


def aplicar_estilos_login() -> None:
    st.markdown(_CSS_LOGIN, unsafe_allow_html=True)


def _casa_svg(tam: int, rot: int, cor: str, opac: float) -> str:
    return (f'<svg width="{tam}" height="{tam}" viewBox="-30 -30 60 60" aria-hidden="true">'
            f'{_casinha(0, 0, 38, rot, cor, opac, 2.4)}</svg>')


def login_fundo() -> None:
    casas = [  # (left, top, tamanho, rotação, cor, opacidade, atraso)
        ("6%",  "78%", 64, 0,   LIMAO,   .45, 0),
        ("47%", "10%", 46, 45,  LARANJA, .55, 1.5),
        ("88%", "16%", 70, 0,   LIMAO,   .35, 3),
        ("93%", "70%", 52, 135, LARANJA, .45, 2),
        ("52%", "86%", 40, 90,  LIMAO,   .40, 4),
    ]
    casas_html = "".join(
        f'<div class="lg-casa" style="left:{l};top:{t};animation-delay:-{d}s">{_casa_svg(sz, r, c, o)}</div>'
        for l, t, sz, r, c, o, d in casas
    )
    html_md(f"""
    <div class="lg-bg">
      <div class="lg-blob lg-b1"></div><div class="lg-blob lg-b2"></div><div class="lg-blob lg-b3"></div>
      <div class="lg-raios"></div><div class="lg-grade"></div>{casas_html}
    </div>""")


def login_hero() -> None:
    palavras = ["Simulador", "de", "<br>"]
    spans, atraso = [], 0.15
    for p in palavras:
        if p == "<br>":
            spans.append("<br>")
            continue
        spans.append(f'<span style="animation-delay:{atraso:.2f}s">{p}</span>&nbsp;')
        atraso += 0.12
    spans.append(f'<span class="lg-brilho" style="animation-delay:{atraso:.2f}s">Score de Vendas</span>')
    html_md(f"""
    <div class="lg-hero">
      {logo_img("branco", 46)}
      <div class="lg-badge"><i></i>Projeto Classificador de Vendas</div>
      <div class="lg-titulo">{"".join(spans)}</div>
    </div>""")


def login_cabecalho() -> str:
    return limpar_html("""
    <div class="lg-card-tit">Acessar</div>
    <div class="lg-card-sub">Use seu e-mail corporativo.</div>""")


def login_rodape() -> str:
    return limpar_html(f'<div class="lg-rodape">{icone("escudo", "#A39D94", 14, 2)} Acesso restrito à equipe Urba</div>')


def secao(icon: str, titulo: str, subtitulo: str = "", cor: str = VERDE) -> None:
    sub = f'<div class="u-secao-sub">{subtitulo}</div>' if subtitulo else ""
    html_md(f"""
    <div class="u-secao">
      <div class="u-secao-ico">{icone(icon, cor, 20)}</div>
      <div><div class="u-secao-tit">{titulo}</div>{sub}</div>
    </div>
    """)


# compatibilidade
def secao_titulo(icon: str, titulo: str, subtitulo: str = "") -> None:
    secao(icon, titulo, subtitulo)


def col_header(numero: int | str, texto: str) -> None:
    html_md(f"""
    <div class="u-colhead"><span class="u-colhead-num">{numero}</span><span>{texto}</span></div>
    """)


def kpi(label: str, valor: str, detalhe: str = "", cor_sig: str = LARANJA, cor_det: str = CINZA_60) -> str:
    det = f'<div class="u-kpi-det" style="color:{cor_det}">{detalhe}</div>' if detalhe else ""
    return limpar_html(f"""
    <div class="u-sig" style="--sig:{cor_sig}"><div class="u-sig-card u-kpi">
      <div class="u-kpi-lab">{label}</div>
      <div class="u-kpi-val" title="{esc(valor)}">{valor}</div>{det}
    </div></div>""")


def chip(texto: str, cor: str, fundo: str) -> str:
    return f'<span class="u-chip" style="color:{cor};background:{fundo}">{esc(texto)}</span>'


def chip_risco(classificacao: str) -> str:
    r = RISCO[cor_por_classificacao(classificacao)]
    return chip(str(classificacao).capitalize() if classificacao else "—", r["escura"], r["suave"])


def resumo_grid(itens: list[tuple[str, str]]) -> str:
    cel = "".join(
        f'<div class="u-resumo-item"><div class="u-resumo-lab">{lab}</div>'
        f'<div class="u-resumo-val" title="{esc(val)}">{val}</div></div>'
        for lab, val in itens
    )
    return limpar_html(f'<div class="u-resumo">{cel}</div>')


# compatibilidade
def card_resumo(label: str, valor: str) -> str:
    return resumo_grid([(label, valor)])


def _arco(cx, cy, r, f0, f1):
    a0, a1 = math.pi * (1 - f0), math.pi * (1 - f1)
    x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy - r * math.sin(a1)
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 0 1 {x1:.2f} {y1:.2f}"


def gauge_score(score: int, maximo: int, lim_moderado: int, lim_baixo: int) -> str:
    """Velocímetro em SVG: faixas alto/moderado/baixo + ponteiro no score."""
    maximo = max(int(maximo), 1)
    f = min(max(score / maximo, 0), 1)
    fm, fb = lim_moderado / maximo, lim_baixo / maximo
    cx, cy, r = 150, 150, 118
    gap = .006
    faixas = (
        f'<path d="{_arco(cx, cy, r, 0, max(fm-gap, 0))}" stroke="{PINK}" stroke-width="22" fill="none" stroke-opacity=".9"/>'
        f'<path d="{_arco(cx, cy, r, fm+gap, max(fb-gap, fm+gap))}" stroke="{LARANJA}" stroke-width="22" fill="none" stroke-opacity=".9"/>'
        f'<path d="{_arco(cx, cy, r, fb+gap, 1)}" stroke="{VERDE}" stroke-width="22" fill="none" stroke-opacity=".9"/>'
    )
    ang = math.pi * (1 - f)
    mx, my = cx + r * math.cos(ang), cy - r * math.sin(ang)
    marcas = ""
    for val, ff in ((lim_moderado, fm), (lim_baixo, fb)):
        a = math.pi * (1 - ff)
        tx, ty = cx + (r + 26) * math.cos(a), cy - (r + 26) * math.sin(a) + 4
        marcas += f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="11" fill="{CINZA_60}" text-anchor="middle" font-family="Verdana">{val}</text>'
    return limpar_html(f"""
    <svg viewBox="0 -8 300 180" width="100%" style="max-width:320px;display:block;margin:0 auto;" aria-label="Score {score} de {maximo}">
      {faixas}
      {marcas}
      <circle cx="{mx:.1f}" cy="{my:.1f}" r="15" fill="#fff" stroke="{TEXTO}" stroke-width="3.5"/>
      <circle cx="{mx:.1f}" cy="{my:.1f}" r="5" fill="{TEXTO}"/>
      <text x="{cx}" y="{cy-22}" font-size="48" font-weight="700" fill="{TEXTO}" text-anchor="middle" font-family="Verdana">{score}</text>
      <text x="{cx}" y="{cy}" font-size="12" fill="{CINZA_60}" text-anchor="middle" font-family="Verdana">de {maximo} pontos</text>
      <text x="{cx-r}" y="{cy+18}" font-size="10" fill="{CINZA_50}" text-anchor="middle" font-family="Verdana">0</text>
      <text x="{cx+r}" y="{cy+18}" font-size="10" fill="{CINZA_50}" text-anchor="middle" font-family="Verdana">{maximo}</text>
    </svg>""")


def card_score(score: int, maximo: int, classificacao: str, cor: str, lim_moderado: int, lim_baixo: int) -> str:
    r = RISCO.get(cor, RISCO["red"])
    ico = {"green": "check", "orange": "alerta", "red": "alerta"}.get(cor, "alerta")
    pct = round(score / max(maximo, 1) * 100)
    return limpar_html(f"""
    <div class="u-sig" style="--sig:{r['cor']}"><div class="u-sig-card u-score">
      {gauge_score(score, maximo, lim_moderado, lim_baixo)}
      <div class="u-score-badge" style="background:{r['suave']};color:{r['escura']}">
        {icone(ico, r['escura'], 18)} {esc(classificacao)}
      </div>
      <div style="font-size:.72rem;color:{CINZA_60};margin-top:8px;">{pct}% da pontuação máxima</div>
      <div class="u-score-leg">
        <span><i style="background:{PINK}"></i>Alto &lt; {lim_moderado}</span>
        <span><i style="background:{LARANJA}"></i>Moderado {lim_moderado}–{lim_baixo-1}</span>
        <span><i style="background:{VERDE}"></i>Baixo ≥ {lim_baixo}</span>
      </div>
    </div></div>""")


def barras_notas(linhas: list[dict]) -> str:
    """linhas: [{nome, faixa, nota, nota_max, peso, pontos, maximo}]"""
    itens = ""
    for l in linhas:
        frac = l["pontos"] / l["maximo"] if l["maximo"] else 0
        cor = VERDE if frac >= .75 else (LARANJA if frac >= .4 else PINK)
        itens += f"""
        <div class="u-barra">
          <div><div class="u-barra-nome">{esc(l['nome'])}</div>
               <div class="u-barra-meta">{esc(l['faixa'])} · nota {l['nota']}/{l['nota_max']} · peso {l['peso']}</div></div>
          <div class="u-barra-trilho"><div class="u-barra-fill" style="width:{frac*100:.0f}%;background:{cor}"></div></div>
          <div class="u-barra-pts">{l['pontos']} <small>/ {l['maximo']} pts</small></div>
        </div>"""
    return limpar_html(f'<div class="u-sig" style="--sig:{LIMAO}"><div class="u-sig-card u-barras">{itens}</div></div>')


def cenario_item(variavel: str, ajuste: str, ganho: int, novo_score: int, nova_class: str) -> str:
    return limpar_html(f"""
    <div class="u-cenario">
      <div class="u-cenario-ico">{icone("lampada", LARANJA, 18)}</div>
      <div><div class="u-cenario-var">{esc(variavel)}</div><div class="u-cenario-txt">{esc(ajuste)}</div></div>
      <div class="u-cenario-res"><div class="u-cenario-ganho">+{ganho} pts</div>
        <div style="margin-top:4px;font-size:.7rem;color:{CINZA_60}">vai a {novo_score} · {chip_risco(nova_class)}</div></div>
    </div>""")


def aviso_faltando(campos: list[str]) -> str:
    return limpar_html(f"""
    <div class="u-faltando">{icone("alerta", LARANJA, 18)}
      <div>Para calcular, falta: <b>{esc(", ".join(campos))}</b></div></div>""")


def rodape(versao: str = "V2.0") -> None:
    html_md(f"""
    <div class="u-footer">
      <span>Simulador de Score de Vendas {esc(versao)} · Projeto Classificador de Vendas · Comercial · Processos</span>
      <b>Urba</b>
    </div>
    """)
