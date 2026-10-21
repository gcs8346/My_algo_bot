import streamlit as st
from pathlib import Path

st.set_page_config(page_title="TOPU TOWER - FINAL", layout="wide", initial_sidebar_state="collapsed")

html_path = Path(__file__).parent / "index.html"
html_code = html_path.read_text(encoding="utf-8")

st.components.v1.html(html_code, height=2000, scrolling=True)