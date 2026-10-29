
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(
    page_title="NEON BREACH: SURVIVAL",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp {
    background: #10130f;
    color: #e8eee5;
}
.block-container {
    max-width: 1700px;
    padding: 1rem 1rem 0;
}
header, footer, #MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style="margin:0;letter-spacing:3px">
NEON BREACH <span style="color:#b6d68a">SURVIVAL</span>
</h1>
<p style="color:#a5b09c;margin-top:4px">
TACTICAL SURVIVAL · SINGLE PLAYER
</p>
""", unsafe_allow_html=True)

game_path = Path(__file__).parent / "game.html"

if game_path.exists():
    components.html(
        game_path.read_text(encoding="utf-8"),
        height=760,
        scrolling=False,
    )
else:
    st.error(
        "game.html 파일을 app.py와 같은 폴더에 추가해 주세요."
    )
