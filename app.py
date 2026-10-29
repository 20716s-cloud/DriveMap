
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(
    page_title="NEON BREACH",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.stApp {
    background: #080b12;
    color: #edf4ff;
}
.block-container {
    max-width: 1600px;
    padding: 1rem 1rem 0;
}
header, footer, #MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style="letter-spacing:3px;margin-bottom:0">
NEON <span style="color:#d7ff55">BREACH</span>
</h1>
<p style="color:#9eafc7">TACTICAL FPS · TRAINING PROTOTYPE</p>
""", unsafe_allow_html=True)

game_file = Path(__file__).parent / "game.html"

if game_file.exists():
    components.html(
        game_file.read_text(encoding="utf-8"),
        height=760,
        scrolling=False
    )
else:
    st.warning(
        "같은 저장소에 game.html 파일을 먼저 만들어 주세요."
    )
