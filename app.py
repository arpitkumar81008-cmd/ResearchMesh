"""
app.py — ResearchMesh: Evidence-Backed Autonomous Research Agent

A clean, modern, professional light-themed research workbench.
- Polished light aesthetic with soft atmospheric backdrops (#F8FAFC background, crisp #FFFFFF cards)
- Subtle depth, 1px hairline borders (#E2E8F0), and refined drop-shadows
- Zero AI slop / hype copy — tool-first, dignified, high-clarity typography
- Modal search dialog with Enter-to-run and auto-close
- Queue and parallel execution support
- Resilient multi-model Gemini reasoning fallback
"""
from __future__ import annotations

import concurrent.futures
import importlib
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv

import exporter
import research_engine as engine
from models import ResearchReport, SourceReference

# Ensure fresh module reload
try:
    importlib.reload(engine)
except Exception:
    pass

load_dotenv()

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMesh — Evidence-Backed Research Agent",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Modern Light Design System CSS ────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Typography & Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* ── Soothing Pastel Canvas & Seamless Padding ── */
html, body, .stApp, [data-testid="stAppViewContainer"], .main, [data-testid="stHeader"], [data-testid="stBottom"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background-color: #EEF2F6 !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(224, 231, 255, 0.45) 0%, transparent 55%),
        radial-gradient(at 100% 100%, rgba(224, 242, 254, 0.4) 0%, transparent 55%),
        radial-gradient(rgba(148, 163, 184, 0.12) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 24px 24px !important;
    background-attachment: fixed !important;
    color: #0F172A !important;
    -webkit-font-smoothing: antialiased;
}

/* ── Main Container Constraints & Seamless Padding ── */
.main .block-container {
    max-width: 1160px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    background: transparent !important;
}

/* ── Sidebar: Calming Off-White with Clean Border ── */
[data-testid="stSidebar"] {
    background-color: #F8FAFC !important;
    border-right: 1px solid #D8E0E9 !important;
    box-shadow: 1px 0 4px rgba(0, 0, 0, 0.02) !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.75rem !important;
    padding-bottom: 3rem !important;
    background: transparent !important;
}

[data-testid="stSidebar"] * {
    color: #334155 !important;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #0F172A !important;
}

/* ── Typography Scale ── */
h1 {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    font-size: clamp(2.1rem, 3.6vw, 3rem) !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.2 !important;
    color: #0F172A !important;
}

h2 {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: #0F172A !important;
    margin-bottom: 0.5rem !important;
}

h3 {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #0F172A !important;
}

p, li {
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
    color: #475569 !important;
}

/* ── Primary Action Buttons (Deep Slate Pill) ── */
.stFormSubmitButton > button {
    background: #0F172A !important;
    border: 1px solid #0F172A !important;
    border-radius: 9999px !important;
    padding: 0 28px !important;
    height: 46px !important;
    min-height: 46px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.stFormSubmitButton > button:hover {
    background: #1E293B !important;
    border-color: #1E293B !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.15) !important;
}

.stFormSubmitButton > button:active {
    transform: scale(0.99) !important;
}

.stFormSubmitButton > button p,
.stFormSubmitButton > button span,
.stFormSubmitButton > button div {
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14.5px !important;
    font-weight: 600 !important;
    margin: 0 !important;
    line-height: 1 !important;
}

/* ── Secondary & Download Buttons ── */
.stButton > button,
.stDownloadButton > button {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 9999px !important;
    padding: 8px 20px !important;
    min-height: 40px !important;
    color: #0F172A !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: #F8FAFC !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(0.99) !important;
}

.stButton > button p,
.stButton > button span,
.stButton > button div,
.stDownloadButton > button p,
.stDownloadButton > button span {
    color: #0F172A !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    margin: 0 !important;
}

/* ── Inputs, Textarea & BaseWeb Containers ── */
.stTextInput [data-baseweb="base-input"],
.stTextInput [data-baseweb="input"],
.stTextInput > div > div,
.stTextArea [data-baseweb="base-input"],
.stTextArea [data-baseweb="textarea"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05) !important;
    transition: all 0.2s ease !important;
}

.stTextInput [data-baseweb="base-input"]:focus-within,
.stTextArea [data-baseweb="base-input"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

.stTextInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    border: none !important;
    font-size: 14.5px !important;
    color: #0F172A !important;
    padding: 10px 14px !important;
    line-height: 1.5 !important;
}

.stTextArea textarea {
    border-radius: 10px !important;
    padding: 14px 18px !important;
}

/* ── High-Contrast, Easily Legible Placeholders (Fix for Low Contrast) ── */
input::placeholder,
textarea::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
[data-baseweb="input"] input::placeholder,
[data-baseweb="base-input"] input::placeholder {
    color: #475569 !important; /* Dark Slate-600: strong contrast against white & pastel */
    opacity: 1 !important;
    font-weight: 500 !important;
}

::-webkit-input-placeholder {
    color: #475569 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}
::-moz-placeholder {
    color: #475569 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}
:-ms-input-placeholder {
    color: #475569 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}

/* ── Selectbox & Dropdowns ── */
[data-testid="stSelectbox"] > div > div {
    background-color: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 8px !important;
    color: #0F172A !important;
}

/* ── Bento Metrics Cards ── */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px -2px rgba(0, 0, 0, 0.02) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stMetric"]:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 6px 18px -3px rgba(15, 23, 42, 0.06) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stMetricLabel"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: #64748B !important;
    margin-bottom: 4px !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
}

/* ── Modern Light Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px !important;
    background-color: #F1F5F9 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #E2E8F0 !important;
    display: inline-flex !important;
    width: auto !important;
    margin-bottom: 1.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    background-color: transparent !important;
    border: none !important;
    white-space: nowrap !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span {
    color: #0F172A !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Card Expanders ── */
.stExpander {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
    transition: all 0.2s ease !important;
}

.stExpander:hover {
    border-color: #CBD5E1 !important;
}

.stExpander details summary {
    padding: 15px 18px !important;
    font-weight: 600 !important;
    color: #0F172A !important;
    font-size: 14.5px !important;
    background-color: transparent !important;
}

.stExpander details summary:hover {
    background-color: #F8FAFC !important;
}

.stExpander details[open] summary {
    border-bottom: 1px solid #E2E8F0 !important;
}

.stExpander .streamlit-expanderContent {
    padding: 18px !important;
    background-color: #FFFFFF !important;
}

/* ── Engineering Terminal / Status Box ── */
[data-testid="stStatus"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 14px !important;
    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08) !important;
}

/* ── Monospace Code Badges ── */
code {
    font-family: 'JetBrains Mono', monospace !important;
    background-color: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 5px !important;
    padding: 2px 6px !important;
    font-size: 12px !important;
    color: #0F172A !important;
}

/* ── Crisp Hairline Dividers ── */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 32px 0 !important;
}

/* ── Dataframe Styling ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    background-color: #FFFFFF !important;
}

/* ── Segmented Radio Filter Control ── */
div[role="radiogroup"] {
    background: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 9999px !important;
    padding: 3px !important;
    display: inline-flex !important;
    gap: 3px !important;
}

div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 9999px !important;
    padding: 5px 14px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
}

div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.6) !important;
}

div[role="radiogroup"] label[data-checked="true"],
div[role="radiogroup"] label:has(input:checked) {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

div[role="radiogroup"] label p,
div[role="radiogroup"] label span {
    color: #0F172A !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

div[role="radiogroup"] input[type="radio"] {
    display: none !important;
}

/* ── Bento Grid System ── */
.rm-bento-grid {
    display: grid !important;
    grid-template-columns: repeat(12, 1fr) !important;
    gap: 16px !important;
    margin-bottom: 40px !important;
}
.rm-bento-card {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 24px 26px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px -2px rgba(0, 0, 0, 0.03) !important;
    position: relative !important;
    overflow: hidden !important;
    transition: all 0.2s ease !important;
}
.rm-bento-card:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.08) !important;
    transform: translateY(-1px) !important;
}
.rm-col-7 { grid-column: span 7 !important; }
.rm-col-5 { grid-column: span 5 !important; }
.rm-col-4 { grid-column: span 4 !important; }
.rm-col-6 { grid-column: span 6 !important; }
.rm-col-12 { grid-column: span 12 !important; }

@media (max-width: 900px) {
    .rm-bento-grid {
        grid-template-columns: 1fr !important;
    }
    .rm-col-7, .rm-col-5, .rm-col-4, .rm-col-6, .rm-col-12 {
        grid-column: span 1 !important;
    }
}

/* ── Modal Dialog Overlay & Container ── */
div[data-testid="stDialog"],
div[data-testid="stModal"],
div[role="dialog"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 16px !important;
    box-shadow: 0 25px 60px -15px rgba(15, 23, 42, 0.2) !important;
    backdrop-filter: blur(16px) !important;
    color: #0F172A !important;
}

div[data-testid="stDialog"] header,
div[data-testid="stModal"] header {
    background: transparent !important;
    border-bottom: 1px solid #E2E8F0 !important;
    padding-bottom: 12px !important;
    margin-bottom: 16px !important;
}

div[data-testid="stDialog"] header h2,
div[data-testid="stModal"] header h2 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    margin: 0 !important;
}

div[data-testid="stDialog"] button[aria-label="Close"],
div[data-testid="stModal"] button[aria-label="Close"] {
    color: #64748B !important;
    border-radius: 9999px !important;
}
div[data-testid="stDialog"] button[aria-label="Close"]:hover,
div[data-testid="stModal"] button[aria-label="Close"]:hover {
    background: #F1F5F9 !important;
    color: #0F172A !important;
}

/* ── Streamlit Chrome Controls: Keep Sidebar Controls Fully Visible ── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { visibility: hidden !important; }

header, [data-testid="stHeader"] {
    background: transparent !important;
    visibility: visible !important;
    height: 3.2rem !important;
    z-index: 99 !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
}

/* ── Sidebar Expand Button (Streamlit 1.40+ & Legacy) ── */
[data-testid="stExpandSidebarButton"],
button[data-testid="stExpandSidebarButton"],
button[aria-label="Expand sidebar"],
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1) !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    min-height: 36px !important;
    margin-left: 12px !important;
    margin-top: 6px !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stExpandSidebarButton"]:hover,
button[aria-label="Expand sidebar"]:hover,
[data-testid="collapsedControl"]:hover {
    background: #F8FAFC !important;
    border-color: #2563EB !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.18) !important;
    transform: scale(1.05) !important;
}

[data-testid="stExpandSidebarButton"] svg,
button[aria-label="Expand sidebar"] svg,
[data-testid="collapsedControl"] svg {
    fill: #0F172A !important;
    stroke: #0F172A !important;
    width: 20px !important;
    height: 20px !important;
}

/* ── Sidebar Collapse Button (Inside Sidebar Header) ── */
[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapseButton"],
button[aria-label="Collapse sidebar"] {
    visibility: visible !important;
    display: inline-flex !important;
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    padding: 4px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarCollapseButton"]:hover,
button[aria-label="Collapse sidebar"]:hover {
    background: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #2563EB !important;
}

[data-testid="stSidebarCollapseButton"] svg,
button[aria-label="Collapse sidebar"] svg {
    fill: #0F172A !important;
    stroke: #0F172A !important;
}

/* ── Prevent Button Text Truncation (No "Ad...", "Set...", "New R...") ── */
.stButton > button {
    white-space: nowrap !important;
    padding: 6px 14px !important;
    min-height: 38px !important;
}
.stButton > button p,
.stButton > button span,
.stButton > button div {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    font-size: 13px !important;
    font-weight: 550 !important;
}

/* ── Suggested Inquiries Pills: Allow Clean Wrapping ── */
div[data-testid="stButton"]:has(button[key^="prompt_"]) button {
    height: auto !important;
    min-height: 46px !important;
    padding: 8px 12px !important;
    border-radius: 12px !important;
}
div[data-testid="stButton"]:has(button[key^="prompt_"]) button p {
    white-space: normal !important;
    word-break: normal !important;
    text-align: center !important;
    line-height: 1.35 !important;
    font-size: 12.5px !important;
    overflow: visible !important;
}

/* ── Omnibar Search Trigger on Home Page ── */
div[data-testid="stButton"]:has(button[key="main_cmd_trigger"]) button {
    background: #FFFFFF !important;
    border: 1.5px solid #94A3B8 !important;
    border-radius: 9999px !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.07) !important;
    height: 48px !important;
}
div[data-testid="stButton"]:has(button[key="main_cmd_trigger"]) button p {
    color: #1E293B !important;
    font-size: 14.5px !important;
    font-weight: 550 !important;
}
div[data-testid="stButton"]:has(button[key="main_cmd_trigger"]) button:hover {
    border-color: #2563EB !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.12) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def html_block(content: str) -> None:
    """Safely renders raw HTML in Streamlit without triggering CommonMark 4-space code block rules."""
    cleaned = "\n".join(line.strip() for line in content.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# ── Session State Initialisation ──────────────────────────────────────────────
_DEFAULTS = {
    "reports": {},               # dict: report_id -> {id, question, report, sources, logs, created_at, domain_type}
    "active_report_id": None,    # active report ID
    "research_queue": [],        # list: [{id, question, domain_type, max_sources, use_web_agent, created_at}]
    "pipeline_logs": [],
    "last_question": "",
    "dialog_prefill": "",
    "show_tour": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Migrate legacy single report if present
if "report" in st.session_state and st.session_state["report"] and not st.session_state.get("reports"):
    legacy_id = "rep-legacy-1"
    st.session_state.reports[legacy_id] = {
        "id": legacy_id,
        "question": st.session_state.get("last_question", "Previous Research"),
        "report": st.session_state["report"],
        "sources": st.session_state.get("sources", []),
        "logs": st.session_state.get("pipeline_logs", []),
        "created_at": datetime.now().strftime("%H:%M:%S"),
        "domain_type": "web",
    }
    st.session_state.active_report_id = legacy_id


def get_active_keys() -> Tuple[str, str]:
    """Retrieves API keys from session state or environment."""
    tf_k = st.session_state.get("sb_tinyfish_key") or os.getenv("TINYFISH_API_KEY", "")
    gm_k = st.session_state.get("sb_gemini_key") or os.getenv("GEMINI_API_KEY", "")
    return tf_k.strip(), gm_k.strip()


# ── API Credentials Setup Modal (@st.dialog) ──────────────────────────────────
@st.dialog("Configure API Credentials", width="medium")
def api_keys_dialog():
    st.markdown(
        """
        <p style="font-size:13.5px; color:#475569; line-height:1.55; margin-bottom:14px;">
            ResearchMesh requires a <strong>TinyFish</strong> API key (for parallel web crawling) and a <strong>Google Gemini</strong> key (for cross-examination synthesis).
            Your keys are kept securely in your browser session and are never saved to disk or logged.
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("api_keys_modal_form", clear_on_submit=False):
        cur_tf = st.session_state.get("sb_tinyfish_key") or os.getenv("TINYFISH_API_KEY", "")
        cur_gm = st.session_state.get("sb_gemini_key") or os.getenv("GEMINI_API_KEY", "")

        tf_val = st.text_input(
            "TinyFish API Key",
            value=cur_tf,
            type="password",
            placeholder="tf_live_... or sk-tinyfish-...",
            help="Get your key at agent.tinyfish.ai/api-keys",
        )
        st.markdown(
            '<a href="https://agent.tinyfish.ai/api-keys" target="_blank" style="font-size:12px; color:#2563EB; text-decoration:none;">↗ Get free TinyFish API key</a>',
            unsafe_allow_html=True,
        )

        gm_val = st.text_input(
            "Google Gemini API Key",
            value=cur_gm,
            type="password",
            placeholder="AIzaSy...",
            help="Get your free key at aistudio.google.com/app/apikey",
        )
        st.markdown(
            '<a href="https://aistudio.google.com/app/apikey" target="_blank" style="font-size:12px; color:#2563EB; text-decoration:none;">↗ Get free Google AI Studio key</a>',
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            save_k = st.form_submit_button("Save Credentials", use_container_width=True)
        with col_s2:
            clear_k = st.form_submit_button("Clear", use_container_width=True)

    if save_k:
        st.session_state["sb_tinyfish_key"] = tf_val.strip()
        st.session_state["sb_gemini_key"] = gm_val.strip()
        st.toast("Credentials saved for this session!", icon="✅")
        time.sleep(0.4)
        st.rerun()

    if clear_k:
        st.session_state["sb_tinyfish_key"] = ""
        st.session_state["sb_gemini_key"] = ""
        st.toast("Credentials cleared.", icon="ℹ️")
        time.sleep(0.4)
        st.rerun()


# ── Pipeline Settings & Configuration Modal (@st.dialog) ──────────────────────
@st.dialog("Pipeline Settings & Parameters", width="medium")
def pipeline_settings_dialog():
    st.markdown(
        """
        <p style="font-size:13.5px; color:#475569; line-height:1.55; margin-bottom:12px;">
            Configure your research depth, target search index, and autonomous agent behavior.
            You can also open or collapse the full sidebar anytime using the <strong>☰</strong> button at the top-left of the screen.
        </p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("pipeline_settings_modal_form", clear_on_submit=False):
        st.markdown(
            "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-bottom:6px;'>Target Search Index</p>",
            unsafe_allow_html=True,
        )
        cur_dom = st.session_state.get("sb_domain_type", "web")
        dom_idx = ["web", "news", "research_paper"].index(cur_dom) if cur_dom in ["web", "news", "research_paper"] else 0
        new_dom = st.selectbox(
            "Search Index",
            options=["web", "news", "research_paper"],
            index=dom_idx,
            format_func=lambda x: {
                "web": "Global Web (General)",
                "news": "News & Verified Media",
                "research_paper": "Academic & Preprints",
            }[x],
            label_visibility="collapsed",
        )

        st.markdown(
            "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-top:14px; margin-bottom:6px;'>Corpus Depth</p>",
            unsafe_allow_html=True,
        )
        cur_src = st.session_state.get("sb_max_sources", 5)
        new_src = st.slider(
            "Max Sources to Synthesize",
            min_value=3,
            max_value=8,
            value=int(cur_src),
            step=1,
            help="Higher source depth broadens cross-examination but takes slightly longer to scrape.",
        )

        st.markdown(
            "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-top:14px; margin-bottom:6px;'>Agent Escalation</p>",
            unsafe_allow_html=True,
        )
        cur_agent = bool(st.session_state.get("sb_use_web_agent", False))
        new_agent = st.checkbox(
            "Enable Autonomous Web Agent Escalation",
            value=cur_agent,
            help="Uses TinyFish Web Agent to autonomously bypass Cloudflare gates, cookie prompts, and JS hydration walls.",
        )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        saved = st.form_submit_button("Save Settings", use_container_width=True)

    if saved:
        st.session_state["sb_domain_type"] = new_dom
        st.session_state["sb_max_sources"] = new_src
        st.session_state["sb_use_web_agent"] = new_agent
        st.toast("Settings saved successfully!", icon="✅")
        time.sleep(0.4)
        st.rerun()


# ── Pop-Up Search Modal Dialog (@st.dialog) ───────────────────────────────────
@st.dialog("Launch Research Inquiry", width="large")
def search_dialog(prefill: str = ""):
    st.markdown(
        """
        <p style="font-size:14px; color:#475569; line-height:1.55; margin-bottom:14px;">
            Enter your question, comparative topic, or hypothesis.
            Press <strong style="color:#0F172A;">Enter</strong> to run immediately in this modal, or add to queue.
        </p>
        """,
        unsafe_allow_html=True,
    )

    tf_active, gm_active = get_active_keys()
    needs_keys = not (tf_active and gm_active)

    with st.form("modal_research_form", clear_on_submit=False):
        q_text = st.text_input(
            "Research Question",
            value=prefill,
            placeholder="e.g. What are the documented health effects and formaldehyde exposure risks of keratin hair treatments?",
            label_visibility="collapsed",
            key="modal_question_input",
        )

        if needs_keys:
            st.markdown(
                """
                <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:10px 14px; margin-bottom:12px;">
                    <div style="font-size:12.5px; font-weight:600; color:#1D4ED8;">🔑 API Credentials Required</div>
                    <div style="font-size:12px; color:#3B82F6; margin-top:2px;">Enter your free TinyFish and Gemini keys below. They are saved in your browser session for this run.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            k_c1, k_c2 = st.columns(2)
            with k_c1:
                tf_inline = st.text_input(
                    "TinyFish API Key",
                    type="password",
                    value=tf_active,
                    placeholder="tf_live_... or sk-tinyfish-...",
                    key="modal_inline_tf",
                )
            with k_c2:
                gm_inline = st.text_input(
                    "Google Gemini API Key",
                    type="password",
                    value=gm_active,
                    placeholder="AIzaSy...",
                    key="modal_inline_gm",
                )
        else:
            tf_inline, gm_inline = "", ""

        with st.expander("Pipeline Routing & Source Parameters", expanded=False):
            opt_c1, opt_c2, opt_c3 = st.columns([1.5, 1, 1.2])
            with opt_c1:
                cur_domain = st.session_state.get("sb_domain_type", "web")
                domain_opts = ["web", "news", "research_paper"]
                d_idx = domain_opts.index(cur_domain) if cur_domain in domain_opts else 0
                dlg_domain = st.selectbox(
                    "Target Index",
                    options=domain_opts,
                    index=d_idx,
                    format_func=lambda x: {
                        "web": "Global Web (General)",
                        "news": "News & Verified Media",
                        "research_paper": "Academic & Preprints",
                    }[x],
                    key="modal_domain_select",
                )
            with opt_c2:
                dlg_sources = st.number_input(
                    "Max Sources",
                    min_value=3,
                    max_value=8,
                    value=int(st.session_state.get("sb_max_sources", 5)),
                    step=1,
                    key="modal_sources_num",
                )
            with opt_c3:
                dlg_web_agent = st.checkbox(
                    "Autonomous Web Agent",
                    value=bool(st.session_state.get("sb_use_web_agent", False)),
                    help="Deploy Chromium browser agent to bypass paywalls, cookie overlays, and dynamic tabs on blocked URLs",
                    key="modal_web_agent_chk",
                )

        btn_c1, btn_c2 = st.columns([2, 1])
        with btn_c1:
            run_btn = st.form_submit_button(
                "Start Research (Enter)",
                use_container_width=True,
            )
        with btn_c2:
            queue_btn = st.form_submit_button(
                "+ Add to Queue",
                use_container_width=True,
            )

    if queue_btn:
        clean_q = q_text.strip()
        if not clean_q:
            st.error("Please enter a research prompt to queue.")
            return
        item_id = f"q-{uuid.uuid4().hex[:6]}"
        st.session_state.research_queue.append({
            "id": item_id,
            "question": clean_q,
            "domain_type": dlg_domain,
            "max_sources": dlg_sources,
            "use_web_agent": dlg_web_agent,
            "created_at": datetime.now().strftime("%H:%M:%S"),
        })
        st.toast(f"Added to Research Queue ({len(st.session_state.research_queue)} pending)", icon="📋")
        time.sleep(0.4)
        st.rerun()

    if run_btn:
        clean_q = q_text.strip()
        if not clean_q:
            st.error("Please enter a research question to initiate discovery.")
            return

        tf_key, gm_key = get_active_keys()
        if not tf_key and tf_inline.strip():
            st.session_state["sb_tinyfish_key"] = tf_inline.strip()
            tf_key = tf_inline.strip()
        if not gm_key and gm_inline.strip():
            st.session_state["sb_gemini_key"] = gm_inline.strip()
            gm_key = gm_inline.strip()

        if not tf_key:
            st.error("TinyFish API key is missing. Enter it above or click '🔑 Add API Keys' in the top bar.")
            return
        if not gm_key:
            st.error("Gemini API key is missing. Enter it above or click '🔑 Add API Keys' in the top bar.")
            return

        engine.set_api_keys(tf_key, gm_key)

        with st.status("Executing Research Pipeline...", expanded=True) as status_box:
            logs = []
            def ui_log(msg: str) -> None:
                logs.append(msg)
                st.write(msg)

            try:
                st.write("Stage 0: Expanding prompt into balanced dual-perspective search queries...")
                try:
                    queries = engine.generate_search_queries(clean_q, status_callback=ui_log)
                except TypeError:
                    queries = engine.generate_search_queries(clean_q)

                for q in queries:
                    ui_log(f"• Query: `{q}`")

                st.write("Stage 1 & 2: Discovering web sources via TinyFish & extracting clean content...")
                sources_data, source_refs = engine.gather_evidence(
                    question=clean_q,
                    queries=queries,
                    max_sources=dlg_sources,
                    use_web_agent=dlg_web_agent,
                    domain_type=dlg_domain,
                    status_callback=ui_log,
                )

                if not sources_data:
                    status_box.update(label="No retrievable evidence found.", state="error")
                    st.error("No sources could be fetched. Try rephrasing your query or checking your TinyFish key.")
                    return

                ui_log(f"Stage 4: Cross-examining claims across {len(sources_data)} sources with Gemini...")
                try:
                    report = engine.synthesize_report(
                        question=clean_q,
                        sources_data=sources_data,
                        status_callback=ui_log,
                    )
                except TypeError:
                    report = engine.synthesize_report(
                        question=clean_q,
                        sources_data=sources_data,
                    )

                rep_id = f"rep-{uuid.uuid4().hex[:6]}"
                st.session_state.reports[rep_id] = {
                    "id": rep_id,
                    "question": clean_q,
                    "report": report,
                    "sources": source_refs,
                    "logs": logs,
                    "created_at": datetime.now().strftime("%H:%M:%S"),
                    "domain_type": dlg_domain,
                }
                st.session_state.active_report_id = rep_id

                corr = sum(1 for c in report.claims if c.status == "Corroborated")
                conf = sum(1 for c in report.claims if c.status == "Conflicting")
                status_box.update(
                    label=f"✓ Complete — {len(source_refs)} sources analyzed ({corr} corroborated, {conf} conflicting)",
                    state="complete",
                    expanded=False,
                )
                st.toast("Research complete. Loading findings...", icon="✅")
                time.sleep(0.5)
                st.rerun()  # Closes modal dialog and displays active dashboard
            except Exception as exc:
                status_box.update(label="Pipeline Execution Error", state="error")
                st.error(f"Error: {exc}")


# ── Sticky Top Navigation Bar ─────────────────────────────────────────────────
has_keys = bool(get_active_keys()[0] and get_active_keys()[1])
nav_c1, nav_c2, nav_c3, nav_c4, nav_c5 = st.columns([2.0, 0.9, 1.2, 1.1, 1.2])
with nav_c1:
    html_block(
        """
        <div style="display:flex; align-items:center; gap:8px; padding: 4px 0; white-space:nowrap;">
            <div style="width:26px; height:26px; border-radius:7px; background:#0F172A; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; color:#FFFFFF;">
                RM
            </div>
            <span style="font-family:'Plus Jakarta Sans', sans-serif; font-weight:700; font-size:15px; letter-spacing:-0.02em; color:#0F172A;">
                ResearchMesh
            </span>
            <span style="font-family:'JetBrains Mono', monospace; font-size:10.5px; font-weight:500; padding:2px 7px; border-radius:5px; background:#F1F5F9; border:1px solid #E2E8F0; color:#475569;">
                Workbench
            </span>
        </div>
        """
    )
with nav_c2:
    html_block(
        f"""
        <div style="display:flex; align-items:center; justify-content:flex-end; height:100%; gap:5px; font-family:'JetBrains Mono', monospace; font-size:11px; color:{'#15803D' if has_keys else '#D97706'}; white-space:nowrap; padding-top:6px;">
            <span style="display:inline-block; width:6px; height:6px; border-radius:9999px; background:{'#16A34A' if has_keys else '#F59E0B'};"></span>
            {'Ready' if has_keys else 'Add Keys'}
        </div>
        """
    )
with nav_c3:
    key_btn_label = "🔑 Keys Active" if has_keys else "🔑 API Keys"
    if st.button(key_btn_label, key="nav_keys_btn", use_container_width=True):
        api_keys_dialog()
with nav_c4:
    if st.button("⚙️ Settings", key="nav_settings_btn", use_container_width=True, help="Configure pipeline search index, corpus depth, and agent"):
        pipeline_settings_dialog()
with nav_c5:
    if st.button("+ Research", key="nav_launch_btn", use_container_width=True):
        search_dialog()


# ── Sidebar Controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 2px 0 14px 0;">
            <div style="font-size:11px; font-family:'JetBrains Mono', monospace; font-weight:600; color:#2563EB; letter-spacing:0.04em; margin-bottom:4px;">
                CONFIGURATION
            </div>
            <h3 style="font-size: 17px; font-weight: 700; color: #0F172A; margin:0;">
                Pipeline Settings
            </h3>
            <p style="font-size: 13px; color: #64748B; margin: 3px 0 0 0;">
                Discovery &amp; Reasoning Parameters
            </p>
            <p style="font-size: 11px; color: #94A3B8; margin: 6px 0 0 0; line-height:1.4;">
                Tip: Click <strong>&lt;</strong> to collapse. Click <strong>&gt;</strong> or <strong>⚙️ Settings</strong> to bring it back anytime.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown(
        "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-bottom:6px;'>API Credentials</p>",
        unsafe_allow_html=True,
    )
    tinyfish_key = st.text_input(
        "TinyFish API Key",
        value=st.session_state.get("sb_tinyfish_key") or os.getenv("TINYFISH_API_KEY", ""),
        type="password",
        placeholder="tf_live_... or sk-tinyfish-...",
        key="sb_tinyfish_key",
        help="Get your key at agent.tinyfish.ai/api-keys",
    )
    gemini_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.get("sb_gemini_key") or os.getenv("GEMINI_API_KEY", ""),
        type="password",
        placeholder="AIzaSy...",
        key="sb_gemini_key",
        help="Get your key at aistudio.google.com/app/apikey",
    )

    st.divider()

    st.markdown(
        "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-bottom:6px;'>Index Routing</p>",
        unsafe_allow_html=True,
    )
    cur_dom = st.session_state.get("sb_domain_type", "web")
    dom_idx = ["web", "news", "research_paper"].index(cur_dom) if cur_dom in ["web", "news", "research_paper"] else 0
    domain_type = st.selectbox(
        "Target Index",
        options=["web", "news", "research_paper"],
        index=dom_idx,
        format_func=lambda x: {
            "web": "Global Web (General)",
            "news": "News & Verified Media",
            "research_paper": "Academic & Preprints",
        }[x],
        key="sb_domain_type",
        label_visibility="collapsed",
    )
    st.caption(f"Active index: `{domain_type}`")

    max_sources = st.slider(
        "Corpus Depth (Max Sources)",
        min_value=3,
        max_value=8,
        value=int(st.session_state.get("sb_max_sources", 5)),
        step=1,
        key="sb_max_sources",
        help="Number of primary sources to retrieve and cross-examine.",
    )
    st.caption(f"Allocated sources: {max_sources}")

    st.divider()

    st.markdown(
        "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B; margin-bottom:6px;'>Escalation Ladder</p>",
        unsafe_allow_html=True,
    )
    use_web_agent = st.checkbox(
        "Enable Web Agent Escalation",
        value=bool(st.session_state.get("sb_use_web_agent", False)),
        key="sb_use_web_agent",
        help="Deploys TinyFish Web Agent to autonomously bypass paywalls, cookie prompts, and SPA hydration walls on blocked URLs.",
    )
    if use_web_agent:
        st.markdown(
            """
            <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:10px 12px; margin-top:8px;">
                <span style="font-family:'JetBrains Mono', monospace; font-size:11px; color:#1D4ED8; font-weight:600;">AGENT ACTIVE</span>
                <p style="font-size:12px; color:#1E40AF; margin:3px 0 0 0; line-height:1.4;">
                    Rescues blocked or dynamic pages using Chromium automation.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    with st.expander("User Guide & Verification Reference", expanded=False):
        st.markdown(
            """
            <div style="font-size:12.5px; line-height:1.6; color:#475569;">
                <strong style="color:#0F172A;">1. Query Formulation</strong><br>
                Provide factual, comparative, or contentious questions (e.g. <em>"What are the documented health effects of keratin hair treatments?"</em>).<br><br>
                <strong style="color:#0F172A;">2. Target Index Selection</strong><br>
                • <code>web</code>: Broad public coverage<br>
                • <code>news</code>: Verified media &amp; press releases<br>
                • <code>research_paper</code>: ArXiv, PubMed &amp; preprints<br><br>
                <strong style="color:#0F172A;">3. Web Agent Escalation</strong><br>
                Enable this to bypass cookie consents and dynamic JavaScript rendering on blocked URLs.<br><br>
                <strong style="color:#0F172A;">4. Claim Verification Standards</strong><br>
                • <span style="color:#15803D; font-weight:600;">✓ Corroborated</span>: 2+ sources independently agree<br>
                • <span style="color:#B91C1C; font-weight:600;">⚠️ Conflicting</span>: Sources present contradictory evidence<br>
                • <span style="color:#475569;">• Single-Source</span>: Only 1 reference found<br><br>
                <strong style="color:#0F172A;">5. Deliverable Export</strong><br>
                Download verified reports in publication Markdown or JSON.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="font-size:12px; color:#94A3B8; line-height:1.6; margin-top:14px;">
            <strong>ResearchMesh</strong><br>
            Powered by TinyFish &amp; Gemini
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center; padding: 20px 0 28px 0;">
        <div style="display:inline-flex; align-items:center; gap:6px; font-family:'JetBrains Mono', monospace; font-size:11.5px; font-weight:600; padding:3px 12px; border-radius:9999px; background:#EFF6FF; border:1px solid #BFDBFE; color:#1D4ED8; margin-bottom:14px;">
            Evidence Synthesis &amp; Verification
        </div>
        <h1 style="margin-bottom: 10px; color:#0F172A;">
            Deep Autonomous Research &amp; Fact Verification
        </h1>
        <p style="font-size: 16px; color: #475569; max-width: 660px; margin: 0 auto; line-height: 1.6;">
            Discovers web sources with <strong>TinyFish</strong>, extracts clean markdown, and cross-examines claims using <strong>Gemini</strong> to separate consensual evidence from conflicting reports.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Research Workspaces / Session Switcher ────────────────────────────────────
reports_map: Dict[str, dict] = st.session_state.get("reports", {})
active_id = st.session_state.get("active_report_id")

if reports_map:
    html_block(
        """
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#64748B;">
                RESEARCH WORKSPACES &amp; SESSIONS
            </span>
            <span style="font-family:'JetBrains Mono', monospace; font-size:11px; color:#94A3B8;">
                ACTIVE SESSIONS
            </span>
        </div>
        """
    )
    sess_ids = list(reports_map.keys())
    s_cols = st.columns(min(len(sess_ids) + 1, 6))
    for idx, r_id in enumerate(sess_ids[:5]):
        r_item = reports_map[r_id]
        q_label = r_item["question"]
        short_q = q_label[:22] + ("..." if len(q_label) > 22 else "")
        is_active = (r_id == active_id)
        with s_cols[idx]:
            if st.button(
                f"{'🟢 ' if is_active else '📄 '}{short_q}",
                key=f"sess_btn_{r_id}",
                use_container_width=True,
                help=f"Switch to: {q_label}",
            ):
                st.session_state.active_report_id = r_id
                st.rerun()
    with s_cols[min(len(sess_ids), 5)]:
        if st.button("+ New", key="sess_add_new_btn", use_container_width=True, help="Launch another research inquiry"):
            search_dialog()


# ── Research Queue Panel ──────────────────────────────────────────────────────
queue_items = st.session_state.get("research_queue", [])
if queue_items:
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    with st.container():
        q_count = len(queue_items)
        qc1, qc2, qc3 = st.columns([3, 1.2, 0.8])
        with qc1:
            st.markdown(
                f"""
                <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:12px 16px;">
                    <div style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#1D4ED8;">
                        RESEARCH QUEUE · {q_count} ITEM{'S' if q_count > 1 else ''} PENDING
                    </div>
                    <div style="font-size:13.5px; color:#1E3A8A; margin-top:3px; font-weight:500;">
                        Next: {queue_items[0]['question']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with qc2:
            if st.button("Run All (Parallel)", key="run_queue_parallel", use_container_width=True, help="Execute all queued inquiries in parallel using worker threads"):
                tf_k, gm_k = get_active_keys()
                if not tf_k or not gm_k:
                    st.error("API keys required in sidebar before executing queue.")
                else:
                    engine.set_api_keys(tf_k, gm_k)
                    with st.status(f"Executing {len(queue_items)} Parallel Research Cycles...", expanded=True) as q_status:
                        st.write(f"Dispatched {len(queue_items)} autonomous research workers concurrently...")
                        
                        def _worker(q_item):
                            q_text = q_item["question"]
                            try:
                                queries = engine.generate_search_queries(q_text)
                            except TypeError:
                                queries = engine.generate_search_queries(q_text)
                            s_data, s_refs = engine.gather_evidence(
                                question=q_text,
                                queries=queries,
                                max_sources=q_item.get("max_sources", 5),
                                use_web_agent=q_item.get("use_web_agent", False),
                                domain_type=q_item.get("domain_type", "web"),
                            )
                            try:
                                rep = engine.synthesize_report(
                                    question=q_text,
                                    sources_data=s_data,
                                )
                            except TypeError:
                                rep = engine.synthesize_report(
                                    question=q_text,
                                    sources_data=s_data,
                                )
                            return q_item["id"], q_text, rep, s_refs, q_item.get("domain_type", "web")

                        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(queue_items), 4)) as pool:
                            future_to_item = {pool.submit(_worker, it): it for it in queue_items}
                            for fut in concurrent.futures.as_completed(future_to_item):
                                orig_it = future_to_item[fut]
                                try:
                                    _, q_done, rep_done, s_done, dom_done = fut.result()
                                    new_id = f"rep-{uuid.uuid4().hex[:6]}"
                                    st.session_state.reports[new_id] = {
                                        "id": new_id,
                                        "question": q_done,
                                        "report": rep_done,
                                        "sources": s_done,
                                        "logs": [f"Completed in parallel on {dom_done} index"],
                                        "created_at": datetime.now().strftime("%H:%M:%S"),
                                        "domain_type": dom_done,
                                    }
                                    st.session_state.active_report_id = new_id
                                    st.write(f"✓ Completed: **{q_done}**")
                                except Exception as err:
                                    st.error(f"Error on '{orig_it['question']}': {err}")

                        st.session_state.research_queue = []
                        q_status.update(label="All parallel researches completed.", state="complete")
                        time.sleep(0.6)
                        st.rerun()
        with qc3:
            if st.button("Clear", key="clear_queue_btn", use_container_width=True):
                st.session_state.research_queue = []
                st.rerun()


# ── Command Search Launchpad Trigger ──────────────────────────────────────────
html_block(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; margin-bottom:8px;">
        <span style="font-family:'JetBrains Mono', monospace; font-size:11.5px; font-weight:600; color:#475569; text-transform:uppercase; letter-spacing:0.05em;">
            COMMAND SEARCH LAUNCHPAD
        </span>
        <span style="font-family:'JetBrains Mono', monospace; font-size:11px; color:#94A3B8;">
            MODAL POP-UP · PRESS ENTER TO RUN
        </span>
    </div>
    """
)
cmd_col1, cmd_col2 = st.columns([4.8, 1.4])
with cmd_col1:
    if st.button(
        "🔍 Type a research question, comparison, or hypothesis... (Click to launch)",
        key="main_cmd_trigger",
        use_container_width=True,
    ):
        search_dialog()
with cmd_col2:
    if st.button(
        "Launch Pop-up",
        key="main_cmd_btn",
        use_container_width=True,
    ):
        search_dialog()

# ── Starter Prompt Pills ──
html_block(
    """
    <div style="display:flex; align-items:center; gap:8px; margin: 12px 0 16px 0; flex-wrap:wrap;">
        <span style="font-family:'JetBrains Mono', monospace; font-size:11px; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;">
            Suggested Inquiries:
        </span>
    </div>
    """
)

p_col1, p_col2, p_col3 = st.columns(3)
with p_col1:
    if st.button("Keratin health & exposure risks", key="prompt_1", use_container_width=True):
        search_dialog(prefill="What are the documented health effects and formaldehyde exposure risks of keratin hair treatments?")
with p_col2:
    if st.button("Solid-state vs lithium batteries", key="prompt_2", use_container_width=True):
        search_dialog(prefill="What is the commercial readiness and energy density comparison between solid-state batteries and lithium-ion in 2025/2026?")
with p_col3:
    if st.button("Browser agent security sandboxes", key="prompt_3", use_container_width=True):
        search_dialog(prefill="What are the current best practices and runtime sandbox standards for autonomous AI browser agents?")

with st.expander("Pipeline Methodology & Execution Flow", expanded=False):
    html_block(
        """
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:18px; margin-top:6px;">
            <h4 style="margin-top:0; color:#0F172A; font-size:15px;">Evidence-Backed Research Architecture</h4>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:14px; margin-top:12px;">
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#2563EB;">STAGE 1 · DECOMPOSITION</span>
                    <p style="font-size:13px; color:#475569; margin:4px 0 0 0; line-height:1.5;">
                        Decomposes query into balanced factual and counter-argument search vectors to prevent confirmation bias.
                    </p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#2563EB;">STAGE 2 · DISCOVERY &amp; FETCH</span>
                    <p style="font-size:13px; color:#475569; margin:4px 0 0 0; line-height:1.5;">
                        TinyFish discovers verified sources and extracts noise-free markdown, bypassing dynamic barriers with headless Chromium agents.
                    </p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#15803D;">STAGE 3 · CROSS-EXAMINATION</span>
                    <p style="font-size:13px; color:#475569; margin:4px 0 0 0; line-height:1.5;">
                        Gemini cross-examines evidence into Corroborated, Conflicting, or Single-Source claims with direct quotes and citations.
                    </p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#7C3AED;">STAGE 4 · EXPORT</span>
                    <p style="font-size:13px; color:#475569; margin:4px 0 0 0; line-height:1.5;">
                        Exports fully verified Markdown dossiers and structured JSON schemas ready for downstream publishing.
                    </p>
                </div>
            </div>
        </div>
        """
    )


# ── Active Report View OR Asymmetric Bento Landing Page ───────────────────────
active_data = reports_map.get(active_id) if active_id else None
report: Optional[ResearchReport] = active_data["report"] if active_data else None
sources: List[SourceReference] = active_data["sources"] if active_data else []

if report is None:
    # ── High-Craft Bento Grid (Landing Showcase) ──────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#2563EB; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">
                CAPABILITIES &amp; ARCHITECTURE
            </div>
            <h2 style="margin:0; color:#0F172A;">Engineered for Autonomous Evidence Synthesis</h2>
            <p style="margin:4px 0 0 0; color:#64748B;">
                Transforming open-web sprawl into structured, verifiable intelligence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 12-Column Asymmetric Bento Grid
    html_block(
        """
        <div class="rm-bento-grid">
            <div class="rm-bento-card rm-col-7">
                <div style="display:inline-block; font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#1D4ED8; background:#EFF6FF; border:1px solid #BFDBFE; padding:3px 10px; border-radius:6px; margin-bottom:12px;">STAGE 01 · MULTI-INDEX SEARCH</div>
                <h3 style="margin-top:0; margin-bottom:8px; font-size:19px; color:#0F172A;">Multi-Index Discovery</h3>
                <p style="color:#475569; font-size:14px; line-height:1.6; margin-bottom:16px;">Expands inquiries into balanced, complementary queries targeting primary findings, contrarian data, and edge cases across web, news, and academic indices.</p>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; background:#F1F5F9; border:1px solid #E2E8F0; padding:4px 9px; border-radius:6px; color:#334155;">Dual-vector expansion</span>
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; background:#F1F5F9; border:1px solid #E2E8F0; padding:4px 9px; border-radius:6px; color:#334155;">Domain index routing</span>
                    <span style="font-family:'JetBrains Mono', monospace; font-size:11px; background:#F1F5F9; border:1px solid #E2E8F0; padding:4px 9px; border-radius:6px; color:#334155;">URL deduplication</span>
                </div>
            </div>
            <div class="rm-bento-card rm-col-5">
                <div style="display:inline-block; font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#7C3AED; background:#F5F3FF; border:1px solid #DDD6FE; padding:3px 10px; border-radius:6px; margin-bottom:12px;">STAGE 02 · RESCUE AGENT</div>
                <h3 style="margin-top:0; margin-bottom:8px; font-size:19px; color:#0F172A;">Autonomous Web Agent</h3>
                <p style="color:#475569; font-size:14px; line-height:1.6; margin-bottom:16px;">When simple HTTP fetches hit Cloudflare gates, cookie prompts, or dynamic JavaScript tabs, the pipeline deploys a headless Chromium agent to extract evidence.</p>
                <div style="font-family:'JetBrains Mono', monospace; font-size:11.5px; color:#475569; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:8px 10px;">tf_client.agent.run(url=target)</div>
            </div>
            <div class="rm-bento-card rm-col-4">
                <div style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#15803D; margin-bottom:10px;">STAGE 03 · VERIFICATION</div>
                <h3 style="margin-top:0; margin-bottom:6px; font-size:17px; color:#0F172A;">Deterministic Conflicts</h3>
                <p style="color:#475569; font-size:13.5px; line-height:1.55; margin:0;">Categorizes claims strictly into Corroborated, Conflicting, or Single-Source, highlighting precisely where sources disagree.</p>
            </div>
            <div class="rm-bento-card rm-col-4">
                <div style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#0284C7; margin-bottom:10px;">STAGE 04 · CHRONOLOGY</div>
                <h3 style="margin-top:0; margin-bottom:6px; font-size:17px; color:#0F172A;">Automated Timeline</h3>
                <p style="color:#475569; font-size:13.5px; line-height:1.55; margin:0;">Extracts dates and chronological milestones across all sources, ordering them with direct source provenance.</p>
            </div>
            <div class="rm-bento-card rm-col-4">
                <div style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#9333EA; margin-bottom:10px;">STAGE 05 · DELIVERABLES</div>
                <h3 style="margin-top:0; margin-bottom:6px; font-size:17px; color:#0F172A;">Export Deliverables</h3>
                <p style="color:#475569; font-size:13.5px; line-height:1.55; margin:0;">Instant download in publication Markdown (with numbered bibliography) or machine-readable JSON for database pipelines.</p>
            </div>
        </div>
        """
    )
    st.stop()


# ── Active Report Dashboard ───────────────────────────────────────────────────
corroborated = sum(1 for c in report.claims if c.status == "Corroborated")
conflicting   = sum(1 for c in report.claims if c.status == "Conflicting")
single_src    = sum(1 for c in report.claims if c.status == "Single-Source")

st.markdown(
    f"""
    <div style="margin-bottom:18px; display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
            <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:#2563EB;">
                RESEARCH SYNTHESIS
            </span>
            <h2 style="font-size:23px; font-weight:700; color:#0F172A; margin:4px 0 0 0;">
                {report.question}
            </h2>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Metrics Row ──
bm1, bm2, bm3, bm4, bm5 = st.columns(5)
bm1.metric("Verified Sources", len(sources))
bm2.metric("Total Claims", len(report.claims))
bm3.metric("Corroborated", corroborated)
bm4.metric("Conflicting", conflicting)
bm5.metric("Single-Source", single_src)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)


# ── Modern Light Tabs ─────────────────────────────────────────────────────────
tab_summary, tab_claims, tab_timeline, tab_sources = st.tabs(
    ["Executive Summary", "Claims & Conflicts", "Chronology", "Provenance"]
)


# ════════════════════════════════════════════════════════════════════════════
# Tab 1: Executive Summary
# ════════════════════════════════════════════════════════════════════════════
with tab_summary:
    st.markdown(
        """
        <div style="background: #FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:26px 28px; box-shadow:0 1px 3px rgba(0,0,0,0.04); margin-bottom:24px;">
            <div style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#2563EB; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">
                SYNTHESIS REPORT
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(report.executive_summary)
    st.markdown("</div>", unsafe_allow_html=True)

    if report.follow_up_questions:
        st.markdown(
            """
            <h3 style="margin-bottom:4px; font-size:16.5px; color:#0F172A;">
                Divergent Research Vectors
            </h3>
            <p style="font-size:13.5px; color:#64748B; margin-bottom:12px;">
                Click any suggested angle below to pre-fill your next research inquiry:
            </p>
            """,
            unsafe_allow_html=True,
        )
        for i, fq in enumerate(report.follow_up_questions, 1):
            if st.button(f"🔍 {fq}", key=f"fq_{i}", use_container_width=True):
                st.session_state.dialog_prefill = fq
                search_dialog(prefill=fq)


# ════════════════════════════════════════════════════════════════════════════
# Tab 2: Claims & Conflict Matrix
# ════════════════════════════════════════════════════════════════════════════
with tab_claims:
    st.markdown(
        """
        <div style="margin-bottom:12px;">
            <h3 style="margin:0; font-size:17px; color:#0F172A;">Cross-Examined Claims</h3>
            <p style="font-size:13.5px; color:#64748B; margin:2px 0 0 0;">
                Consensual findings and disputed claims across all analyzed sources
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filter_status = st.radio(
        "Filter",
        options=["All", "Corroborated", "Conflicting", "Single-Source"],
        horizontal=True,
        label_visibility="collapsed",
    )

    filtered = (
        report.claims
        if filter_status == "All"
        else [c for c in report.claims if c.status == filter_status]
    )

    st.markdown(
        f"<p style='font-family:\"JetBrains Mono\", monospace; font-size:11.5px; color:#94A3B8; margin-bottom:16px;'>DISPLAYING {len(filtered)} OF {len(report.claims)} CLAIMS</p>",
        unsafe_allow_html=True,
    )

    for claim in filtered:
        # High clarity badge styles
        if claim.status == "Corroborated":
            badge_html = "<span style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; background:#F0FDF4; color:#15803D; border:1px solid #BBF7D0; padding:3px 9px; border-radius:6px;'>✓ CORROBORATED</span>"
        elif claim.status == "Conflicting":
            badge_html = "<span style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; background:#FEF2F2; color:#B91C1C; border:1px solid #FECACA; padding:3px 9px; border-radius:6px;'>⚠️ CONFLICTING</span>"
        else:
            badge_html = "<span style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:500; background:#F8FAFC; color:#475569; border:1px solid #E2E8F0; padding:3px 9px; border-radius:6px;'>• SINGLE-SOURCE</span>"

        with st.expander(
            f"{'⚠️ ' if claim.status == 'Conflicting' else ''}{claim.topic} — {claim.claim[:74]}{'...' if len(claim.claim) > 74 else ''}",
            expanded=(claim.status == "Conflicting"),
        ):
            support_tags = " ".join([f"<code>[{s}]</code>" for s in claim.supporting_sources])
            contra_tags = " ".join([f"<code style='color:#B91C1C; background:#FEF2F2; border-color:#FECACA;'>[{c}]</code>" for c in claim.contradicting_sources])

            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; flex-wrap:wrap;">
                    {badge_html}
                    {"<span style='font-size:13px; color:#475569;'>Supporting: " + support_tags + "</span>" if support_tags else ""}
                    {"<span style='font-size:13px; color:#B91C1C; font-weight:600;'>Contradicting: " + contra_tags + "</span>" if contra_tags else ""}
                </div>
                <div style="font-size:15px; font-weight:600; color:#0F172A; margin-bottom:12px; line-height:1.55;">
                    {claim.claim}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Conflict callout
            if claim.status == "Conflicting" and claim.conflict_explanation:
                st.markdown(
                    f"""
                    <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:12px 14px; margin-bottom:12px;">
                        <span style="font-family:'JetBrains Mono', monospace; font-size:11px; font-weight:600; color:#B91C1C; text-transform:uppercase; letter-spacing:0.04em;">
                            Contradiction Analysis
                        </span>
                        <p style="font-size:13.5px; color:#7F1D1D; margin:3px 0 0 0; line-height:1.5;">
                            {claim.conflict_explanation}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Direct evidence quotes
            if claim.evidence_quotes:
                st.markdown(
                    "<p style='font-family:\"JetBrains Mono\", monospace; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; color:#64748B; margin-bottom:6px;'>Verbatim Evidence Excerpts</p>",
                    unsafe_allow_html=True,
                )
                for q in claim.evidence_quotes:
                    st.markdown(
                        f"""
                        <div style="border-left:2px solid #2563EB; padding:7px 12px; margin-bottom:6px; font-size:13px; color:#334155; background:#F8FAFC; border-radius:0 6px 6px 0;">
                            {q}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ════════════════════════════════════════════════════════════════════════════
# Tab 3: Timeline
# ════════════════════════════════════════════════════════════════════════════
with tab_timeline:
    st.markdown(
        """
        <div style="margin-bottom:16px;">
            <h3 style="margin:0; font-size:17px; color:#0F172A;">Chronological Milestones</h3>
            <p style="font-size:13.5px; color:#64748B; margin:2px 0 0 0;">
                Temporal anchors and historical events extracted from the source corpus
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not report.timeline:
        st.markdown(
            """
            <div style="padding:28px; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; text-align:center;">
                <p style="font-size:14px; color:#64748B; margin:0;">
                    No datable chronological events were explicitly referenced in the source corpus.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        timeline_sorted = sorted(report.timeline, key=lambda e: e.date)
        st.markdown(
            """
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:10px 22px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
            """,
            unsafe_allow_html=True,
        )
        for event in timeline_sorted:
            src = next((s for s in sources if s.source_id == event.source_id), None)
            src_domain = src.domain if src else "source"
            src_url = src.url if src else "#"

            st.markdown(
                f"""
                <div style="display:flex; gap:20px; padding:14px 0; border-bottom:1px solid #F1F5F9; align-items:flex-start;">
                    <div style="min-width:120px;">
                        <span style="font-family:'JetBrains Mono', monospace; font-size:14px; font-weight:600; color:#0F172A;">
                            {event.date}
                        </span><br>
                        <a href="{src_url}" target="_blank" style="font-size:12px; color:#2563EB; text-decoration:none;">
                            [{event.source_id}] {src_domain} ↗
                        </a>
                    </div>
                    <div style="font-size:14px; color:#334155; line-height:1.55;">
                        {event.event}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Tab 4: Sources
# ════════════════════════════════════════════════════════════════════════════
with tab_sources:
    st.markdown(
        """
        <div style="margin-bottom:16px;">
            <h3 style="margin:0; font-size:17px; color:#0F172A;">Source Provenance</h3>
            <p style="font-size:13.5px; color:#64748B; margin:2px 0 0 0;">
                Full citation metadata and retrieval provenance for all analyzed pages
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    table_data = [
        {
            "ID": f"[{s.source_id}]",
            "Title": s.title,
            "Domain": s.domain,
            "Published": s.published_date or "—",
            "Method": s.retrieval_method,
        }
        for s in sorted(sources, key=lambda s: s.source_id)
    ]

    st.dataframe(
        table_data,
        width="stretch",
        hide_index=True,
        column_config={
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Domain": st.column_config.TextColumn("Domain", width="medium"),
            "Published": st.column_config.TextColumn("Published", width="small"),
            "Method": st.column_config.TextColumn("Method", width="medium"),
        },
    )

    st.markdown("<h4 style='font-size:15px; margin:24px 0 12px 0; color:#0F172A;'>Direct Source Links</h4>", unsafe_allow_html=True)
    for s in sorted(sources, key=lambda s: s.source_id):
        agent_pill = (
            "<span style='font-family:\"JetBrains Mono\", monospace; font-size:10px; font-weight:600; background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; padding:2px 7px; border-radius:5px;'>Web Agent</span>"
            if s.retrieval_method == "TinyFish Web Agent"
            else "<span style='font-family:\"JetBrains Mono\", monospace; font-size:10px; font-weight:500; background:#F1F5F9; color:#475569; border:1px solid #E2E8F0; padding:2px 7px; border-radius:5px;'>Fetch</span>"
        )
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div>
                    <span style="font-family:'JetBrains Mono', monospace; font-size:12px; color:#64748B; margin-right:8px;">[{s.source_id}]</span>
                    <a href="{s.url}" target="_blank" style="font-size:14px; font-weight:600; color:#0F172A; text-decoration:none;">
                        {s.title}
                    </a>
                    <div style="font-size:12px; color:#64748B; margin-top:2px;">
                        <code>{s.domain}</code> {(' · ' + s.published_date) if s.published_date else ''}
                    </div>
                </div>
                <div>
                    {agent_pill}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Export Bar ────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h3 style="margin:0; font-size:16.5px; color:#0F172A;">Export Findings</h3>
        <span style="font-family:'JetBrains Mono', monospace; font-size:11px; color:#64748B;">
            PUBLICATION MARKDOWN &amp; STRUCTURED JSON
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

exp1, exp2 = st.columns(2)
with exp1:
    md_report = exporter.to_markdown(report, sources).encode("utf-8")
    st.download_button(
        label="Download Markdown Report (.md)",
        data=md_report,
        file_name="researchmesh_report.md",
        mime="text/markdown",
        use_container_width=True,
        help="Self-contained report with citations and complete bibliography.",
    )

with exp2:
    json_data = exporter.to_json(report, sources).encode("utf-8")
    st.download_button(
        label="Download Structured JSON (.json)",
        data=json_data,
        file_name="researchmesh_evidence.json",
        mime="application/json",
        use_container_width=True,
        help="Machine-readable evidence bundle for downstream pipelines.",
    )
