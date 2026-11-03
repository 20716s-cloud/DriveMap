
import streamlit as st
import folium
import time

from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

from map_engine import (
    find_location,
    get_route,
    get_car_position,
    get_passed_route
)

# =========================
# 1. 기본 설정
# =========================

st.set_page_config(
    page_title="DriveMap",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #10151d;
    color: white;
}
[data-testid="stMetric"] {
    background: #202a38;
    padding: 15px;
    border-radius: 12px;
}
h1, h2, h3 {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 2. 세션 데이터
# =========================

defaults = {
    "route": None,
    "running": False,
    "progress": 0.0,
    "speed": 60,
    "scale": 10,
    "last_tick": None,
    "start_name": "수원역",
    "end_name": "강남역"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================
# 3. 주행 거리 계산
# =========================

if st.session_state.running and st.session_state.route:

    now = time.monotonic()
    previous = st.session_state.last_tick

    if previous is not None:

        elapsed = min(now - previous, 2.0)

        movement = (
            st.session_state.speed / 3.6
            * elapsed
            * st.session_state.scale
        )

        total = st.session_state.route["distance"]

        st.session_state.progress = min(
            total,
            st.session_state.progress + movement
        )

    st.session_state.last_tick = now

    if (
        st.session_state.progress
        >= st.session_state.route["distance"]
    ):
        st.session_state.running = False
        st.session_state.last_tick = None

# =========================
# 4. 메인 화면
# =========================

st.title("🚗 DriveMap")
st.caption("REAL ROAD DRIVING SIMULATOR")

st.divider()

st.subheader("📍 출발지와 목적지")

col1, col2 = st.columns(2)

with col1:
    start_name = st.text_input(
        "출발지",
        value=st.session_state.start_name
    )

with col2:
    end_name = st.text_input(
        "목적지",
        value=st.session_state.end_name
    )

# =========================
# 5. 경로 검색
# =========================

if st.button("🗺️ 실제 도로 경로 검색", use_container_width=True):

    if not start_name.strip() or not end_name.strip():
        st.error("출발지와 목적지를 입력해 주세요.")

    else:

        try:
            with st.spinner("실제 도로를 검색하고 있습니다..."):

                start = find_location(start_name)
                end = find_location(end_name)

                if start is None or end is None:
                    st.error("장소를 찾을 수 없습니다.")

                else:
                    route = get_route(start, end)

                    if route is None:
                        st.error("도로 경로를 찾지 못했습니다.")

                    else:
                        st.session_state.route = route
                        st.session_state.start_name = start_name
                        st.session_state.end_name = end_name
                        st.session_state.progress = 0.0
                        st.session_state.running = False
                        st.session_state.last_tick = None

                        st.rerun()

        except Exception as e:
            st.error(f"경로 검색 오류: {e}")

# =========================
# 6. 주행 시스템
# =========================

if st.session_state.route:

    route = st.session_state.route
    coordinates = route["coordinates"]
    total_distance = route["distance"]

    st.divider()
    st.subheader("🎮 자동차 주행 시스템")

    col1, col2 = st.columns(2)

    with col1:
        speed = st.slider(
            "🚘 자동차 속도",
            min_value=0,
            max_value=200,
            value=st.session_state.speed,
            step=5,
            format="%d km/h"
        )

    with col2:
        scale = st.select_slider(
            "⏩ 게임 시간 배속",
            options=[1, 5, 10, 30, 60],
            value=st.session_state.scale,
            format_func=lambda x: f"{x}배속"
        )

    st.session_state.speed = speed
    st.session_state.scale = scale

    # ---------------------
    # 주행 버튼
    # ---------------------

    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("▶ 주행 시작", use_container_width=True):

            if st.session_state.progress < total_distance:
                st.session_state.running = True
                st.session_state.last_tick = time.monotonic()
                st.rerun()

    with b2:
        if st.button("⏸ 일시정지", use_container_width=True):

            st.session_state.running = False
            st.session_state.last_tick = None
            st.rerun()

    with b3:
        if st.button("↻ 처음부터", use_container_width=True):

            st.session_state.progress = 0.0
            st.session_state.running = False
            st.session_state.last_tick = None
            st.rerun()

    # =====================
    # 7. 주행 정보
    # =====================

    progress = st.session_state.progress
    remaining = max(0, total_distance - progress)

    if speed > 0:
        eta = remaining / (speed / 3.6)

        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)

        eta_text = f"{hours}시간 {minutes}분"
    else:
        eta_text = "정차 중"

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("현재 속도", f"{speed} km/h")
    c2.metric("전체 거리", f"{total_distance / 1000:.2f} km")
    c3.metric("주행 거리", f"{progress / 1000:.2f} km")
    c4.metric("남은 거리", f"{remaining / 1000:.2f} km")

    st.markdown(f"### ⏱️ 예상 남은 시간: {eta_text}")

    st.progress(
        min(1.0, progress / total_distance)
    )

    # =====================
    # 8. 실제 지도
    # =====================

    car_position = get_car_position(
        coordinates,
        progress
    )

    driving_map = folium.Map(
        location=car_position,
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # 전체 경로

    full_route = [
        [p[1], p[0]]
        for p in coordinates
    ]

    folium.PolyLine(
        full_route,
        color="#2678ff",
        weight=6,
        opacity=0.8,
        tooltip="주행 경로"
    ).add_to(driving_map)

    # 지나온 경로

    passed = get_passed_route(
        coordinates,
        progress
    )

    if len(passed) > 1:

        folium.PolyLine(
            passed,
            color="#20c997",
            weight=7,
            tooltip="주행 완료 구간"
        ).add_to(driving_map)

    # 출발지

    folium.Marker(
        full_route[0],
        tooltip="출발지",
        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(driving_map)

    # 목적지

    folium.Marker(
        full_route[-1],
        tooltip="목적지",
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(driving_map)

    # 자동차

    folium.Marker(
        car_position,
        tooltip="현재 자동차 위치",
        icon=folium.DivIcon(
            html="""
            <div style="
                font-size:30px;
                width:40px;
                height:40px;
                text-align:center;
                text-shadow:1px 1px 3px white;
            ">🚗</div>
            """,
            icon_size=(40, 40),
            icon_anchor=(20, 20)
        )
    ).add_to(driving_map)

    st.subheader("🗺️ 실제 도로 주행 지도")

    st_folium(
        driving_map,
        width=None,
        height=600,
        returned_objects=[],
        key="drivemap"
    )

    st.caption(
        "지도: OpenStreetMap | 도로 경로: OSRM"
    )

    # =====================
    # 9. 주행 완료
    # =====================

    if progress >= total_distance:
        st.success("🏁 목적지에 도착했습니다!")

    # 자동 갱신

    if st.session_state.running:

        st_autorefresh(
            interval=1000,
            key="drive_refresh"
        )

else:

    st.info(
        "출발지와 목적지를 입력한 후 경로 검색을 눌러 주세요."
    )

    st.markdown("""
    ### 🚘 DriveMap 기능

    - 실제 대한민국 도로 지도
    - 자동차 아이콘 이동
    - 주행 속도 조절
    - 이동 거리 계산
    - 남은 거리 표시
    - 예상 도착 시간
    - 주행 시작 및 일시정지
    """)
