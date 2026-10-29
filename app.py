
import random
import streamlit as st

st.set_page_config(
    page_title="GOLDEN ROOM",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Design ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

.stApp {
    background:
        radial-gradient(ellipse at 50% 0%, #282116 0%, #101010 42%, #090909 100%);
    color: #f5f0e5;
    font-family: 'DM Sans', sans-serif;
}
.block-container {
    max-width: 1120px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}
h1, h2, h3 {
    color: #f4d58a !important;
}
.brand {
    text-align: center;
    color: #d6b66d;
    font-size: 12px;
    letter-spacing: 6px;
    font-weight: 700;
}
.hero {
    text-align: center;
    padding: 14px 0 26px;
}
.hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(36px, 6vw, 62px);
    letter-spacing: 2px;
    margin: 8px 0;
}
.hero p {
    color: #aaa397;
    font-size: 14px;
}
.balance-card {
    background: linear-gradient(135deg, #211d14, #121212);
    border: 1px solid #8f7138;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
}
.balance-label {
    color: #b9a779;
    font-size: 12px;
    letter-spacing: 3px;
}
.balance-value {
    color: #f2d38a;
    font-size: 34px;
    font-weight: 700;
    margin-top: 4px;
}
.game-card {
    background: rgba(25, 25, 25, .85);
    border: 1px solid #393226;
    border-radius: 16px;
    padding: 22px;
    min-height: 130px;
}
.game-card h3 { margin-top: 0; }
div.stButton > button {
    background: linear-gradient(135deg, #e7cb83, #b18a3d);
    color: #17130b;
    border: 0;
    border-radius: 9px;
    font-weight: 700;
    min-height: 44px;
    transition: .2s;
}
div.stButton > button:hover {
    background: #f7e4ad;
    color: #111;
    border: 0;
}
div[data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #393226;
}
button[data-baseweb="tab"] {
    color: #c5bda9;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #f4d58a;
}
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] > div,
div[data-testid="stSlider"] {
    color: #f5f0e5;
}
hr { border-color: #393226; }
.small-note {
    text-align: center;
    color: #777064;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Game state ----------
if "balance" not in st.session_state:
    st.session_state.balance = 1000
if "history" not in st.session_state:
    st.session_state.history = []
if "roulette_result" not in st.session_state:
    st.session_state.roulette_result = "?"
if "slot_result" not in st.session_state:
    st.session_state.slot_result = ["❔", "❔", "❔"]
if "card_result" not in st.session_state:
    st.session_state.card_result = None

def record(game, bet, message, change):
    st.session_state.history.insert(0, {
        "게임": game,
        "베팅": f"{bet:,} C",
        "결과": message,
        "변동": f"{change:+,} C",
        "잔액": f"{st.session_state.balance:,} C",
    })
    st.session_state.history = st.session_state.history[:10]

def take_bet(bet):
    if bet < 10:
        st.warning("최소 베팅은 10 코인입니다.")
        return False
    if bet > st.session_state.balance:
        st.warning("보유한 코인보다 큰 금액은 사용할 수 없습니다.")
        return False
    st.session_state.balance -= bet
    return True

def add_coins(amount):
    st.session_state.balance += amount

# ---------- Header ----------
st.markdown("""
<div class="hero">
    <div class="brand">THE PRIVATE CLUB</div>
    <h1>GOLDEN ROOM</h1>
    <p>A world of classic games. Play with virtual coins only.</p>
</div>
""", unsafe_allow_html=True)

left, center, right = st.columns([1, 1.25, 1])
with center:
    st.markdown(f"""
    <div class="balance-card">
        <div class="balance-label">YOUR VIRTUAL BALANCE</div>
        <div class="balance-value">◈ {st.session_state.balance:,} C</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.markdown("### CHOOSE YOUR TABLE")
st.caption("모든 코인은 가상 코인이며 현금 가치가 없습니다.")

bet = st.number_input(
    "베팅 금액 (C)",
    min_value=10,
    max_value=max(10, st.session_state.balance),
    value=min(50, max(10, st.session_state.balance)),
    step=10,
)

roulette_tab, slot_tab, card_tab = st.tabs([
    "♠  ROULETTE",
    "✦  SLOT MACHINE",
    "♥  CARD DUEL",
])

# ---------- Roulette ----------
with roulette_tab:
    st.markdown("## Roulette")
    st.write("빨강, 검정, 홀수 또는 짝수를 선택하세요.")
    st.markdown("""
    <div class="game-card">
        <h3>🔴 🔴 ⚫ ⚫</h3>
        <p>맞히면 베팅 금액의 2배를 돌려받습니다.</p>
        <p style="color:#a99d83;font-size:13px;">0이 나오면 모든 선택에 대해 패배합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    choice = st.selectbox(
        "예측 선택",
        ["빨강", "검정", "홀수", "짝수"],
        key="roulette_choice",
    )

    if st.button("SPIN ROULETTE", key="spin_roulette", use_container_width=True):
        if take_bet(int(bet)):
            number = random.randint(0, 36)
            red_numbers = {
                1, 3, 5, 7, 9, 12, 14, 16, 18,
                19, 21, 23, 25, 27, 30, 32, 34, 36
            }
            color = "초록" if number == 0 else (
                "빨강" if number in red_numbers else "검정"
            )
            st.session_state.roulette_result = f"{number} · {color}"

            if number != 0:
                won = (
                    (choice == "빨강" and color == "빨강")
                    or (choice == "검정" and color == "검정")
                    or (choice == "홀수" and number % 2 == 1)
                    or (choice == "짝수" and number % 2 == 0)
                )
            else:
                won = False

            if won:
                change = int(bet)
                add_coins(int(bet) * 2)
                message = f"승리! {number} · {color}"
                st.success(f"🎉 {message} — +{change:,} 코인")
            else:
                change = -int(bet)
                message = f"패배. {number} · {color}"
                st.error(f"{message} — {change:,} 코인")

            record("룰렛", int(bet), message, change)

    st.markdown(f"### 결과: **{st.session_state.roulette_result}**")

# ---------- Slots ----------
with slot_tab:
    st.markdown("## Slot Machine")
    st.write("세 개의 기호를 맞춰 보세요.")
    st.markdown("""
    <div class="game-card">
        <h3>🍒　💎　7️⃣</h3>
        <p>세 개 일치: 베팅액의 5배 지급</p>
        <p>두 개 일치: 베팅액의 2배 지급</p>
        <p style="color:#a99d83;font-size:13px;">배수는 베팅액을 포함한 총 반환 금액입니다.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✦  SPIN SLOTS  ✦", key="spin_slots", use_container_width=True):
        if take_bet(int(bet)):
            symbols = ["🍒", "💎", "7️⃣", "🔔", "⭐", "🍀"]
            reels = [random.choice(symbols) for _ in range(3)]
            st.session_state.slot_result = reels

            counts = [reels.count(x) for x in set(reels)]
            if 3 in counts:
                multiplier = 5
                message = "잭팟! 세 기호 일치"
            elif 2 in counts:
                multiplier = 2
                message = "당첨! 두 기호 일치"
            else:
                multiplier = 0
                message = "아쉽지만 다음 기회에"

            payout = int(bet) * multiplier
            add_coins(payout)
            change = payout - int(bet)

            if multiplier:
                st.success(f"{message} — 총 {payout:,} 코인 반환")
            else:
                st.error(f"{message} — {int(bet):,} 코인 사용")

            record("슬롯", int(bet), message, change)

    st.markdown(
        f"<div style='text-align:center;font-size:56px;padding:18px;'>{'　'.join(st.session_state.slot_result)}</div>",
        unsafe_allow_html=True,
    )

# ---------- Card Duel ----------
with card_tab:
    st.markdown("## Card Duel")
    st.write("카드를 한 장씩 뽑습니다. 숫자가 더 높은 쪽이 승리합니다.")
    st.markdown("""
    <div class="game-card">
        <h3>🂡  VS  🂱</h3>
        <p>승리: 베팅액의 2배 반환</p>
        <p>무승부: 베팅액 반환</p>
        <p style="color:#a99d83;font-size:13px;">카드 값은 A가 가장 높고, 2가 가장 낮습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("DRAW CARDS", key="draw_cards", use_container_width=True):
        if take_bet(int(bet)):
            player = random.randint(2, 14)
            dealer = random.randint(2, 14)

            def card_name(value):
                return {11: "J", 12: "Q", 13: "K", 14: "A"}.get(
                    value, str(value)
                )

            if player > dealer:
                payout = int(bet) * 2
                change = int(bet)
                message = "승리"
                add_coins(payout)
                st.success(f"승리! +{change:,} 코인")
            elif player == dealer:
                payout = int(bet)
                change = 0
                message = "무승부"
                add_coins(payout)
                st.info("무승부! 베팅 금액을 돌려받았습니다.")
            else:
                payout = 0
                change = -int(bet)
                message = "패배"
                st.error(f"패배 — {int(bet):,} 코인 사용")

            st.session_state.card_result = (
                f"내 카드: {card_name(player)}　|　"
                f"딜러 카드: {card_name(dealer)}"
            )
            record("카드", int(bet), message, change)

    if st.session_state.card_result:
        st.markdown(f"### {st.session_state.card_result}")

# ---------- History ----------
st.divider()
st.markdown("## RECENT ACTIVITY")

if st.session_state.history:
    st.dataframe(
        st.session_state.history,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("아직 게임 기록이 없습니다. 첫 게임을 시작해 보세요.")

st.write("")
if st.button("↻  RESET GAME", use_container_width=True):
    st.session_state.balance = 1000
    st.session_state.history = []
    st.session_state.roulette_result = "?"
    st.session_state.slot_result = ["❔", "❔", "❔"]
    st.session_state.card_result = None
    st.rerun()

st.markdown("""
<hr>
<div class="small-note">
    GOLDEN ROOM · VIRTUAL COINS ONLY · NO REAL-MONEY GAMBLING
</div>
""", unsafe_allow_html=True)

    st.error(
        "game.html 파일을 app.py와 같은 폴더에 추가해 주세요."
    )
