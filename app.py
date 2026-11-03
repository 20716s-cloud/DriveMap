
import streamlit as st
import folium
import requests
import math
import time

from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="DriveMap",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #101318;
    color: white;
}
[data-testid="stMetric"] {
    background: #1c222b;
    padding: 18px;
    border-radius: 12px;
}
h1, h2, h3 {
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🚗 DriveMap")
st.caption("REAL ROAD DRIVING SIMULATOR")

# -----------------------------
# 지오코딩: 장소 이름 -> 좌표
# -----------------------------
@st.cache_data(ttl=3600)
def find_location(place):
    url = "https://nominatim.openstreetmap.org/search"

    response = requests.get(
        url,
        params={
            "q": place,
            "format": "json",
            "limit": 1,
            "countrycodes": "kr"
        },
        headers={
            "User-Agent": "DriveMapStudentProject/1.0"
        },
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    if not data:
        return None

    return [
        float(data[0]["lat"]),
        float(data[0]["lon"])
    ]


# -----------------------------
# 실제 도로 경로 검색
# -----------------------------
@st.cache_data(ttl=1800)
def get_route(start, end):

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start[1]},{start[0]};{end[1]},{end[0]}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        },
        timeout=30
    )

    response.raise_for_status()
    result = response.json()

    if result["code"] != "Ok":
        return None

    route = result["routes"][0]

    return {
        "coordinates": route["geometry"]["coordinates"],
        "distance": route["distance"],
        "duration": route["duration"]
    }


# -----------------------------
# 두 좌표 사이 거리 계산
# -----------------------------
def distance_between(a, b):

    radius = 6371000

    lat1 = math.radians(a[0])
    lat2 = math.radians(b[0])

    dlat = math.radians(b[0] - a[0])
    dlon = math.radians(b[1] - a[1])

    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(
        math.sqrt(value),
        math.sqrt(1 - value)
    )


# -----------------------------
# 경로상 자동차 위치 계산
# -----------------------------
def get_car_position(coordinates, progress):

    traveled = 0

    for i in range(len(coordinates) - 1):

        a = [
            coordinates[i][1],
            coordinates[i][0]
        ]

        b = [
            coordinates[i + 1][1],
            coordinates[i + 1][0]
        ]

        segment = distance_between(a, b)

        if traveled + segment >= progress:

            ratio = (
                (progress - traveled) / segment
                if segment > 0 else 0
            )

            lat = a[0] + (b[0] - a[0]) * ratio
            lon = a[1] + (b[1] - a[1]) * ratio

            return [lat, lon]

        traveled += segment

    return [
        coordinates[-1][1],
        coordinates[-1][0]
    ]


# -----------------------------
# 세션 상태
# -----------------------------
defaults = {
    "route": None,
    "running": False,
    "progress": 0.0,
    "speed": 60,
    "last_tick": None,
    "start_name": "",
    "end_name": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# 출발지 및 목적지
# -----------------------------
st.subheader("📍 주행 경로 설정")

col1, col2 = st.columns(2)

with col1:
    start_name = st.text_input(
        "출발지",
        value="수원역"
    )

with col2:
    end_name = st.text_input(
        "목적지",
        value="강남역"
    )

if st.button("🗺️ 실제 도로 경로 검색", use_container_width=True):

    if not start_name.strip() or not end_name.strip():
        st.error("출발지와 목적지를 입력해 주세요.")

    else:
        with st.spinner("실제 도로 경로를 검색하고 있습니다..."):

            try:
                start = find_location(start_name)
                end = find_location(end_name)

                if start is None or end is None:
                    st.error("장소를 찾을 수 없습니다. 다른 이름으로 검색해 주세요.")

                else:
                    route = get_route(start, end)

                    if route is None:
                        st.error("도로 경로를 찾을 수 없습니다.")

                    else:
                        st.session_state.route = route
                        st.session_state.progress = 0.0
                        st.session_state.running = False
                        st.session_state.last_tick = None
                        st.session_state.start_name = start_name
                        st.session_state.end_name = end_name

                        st.rerun()

            except requests.RequestException as e:
                st.error(f"지도 서버 연결 오류: {e}")


# -----------------------------
# 주행 기능
# -----------------------------
if st.session_state.route:

    route = st.session_state.route

    total_distance = route["distance"]
    coordinates = route["coordinates"]

    st.divider()
    st.subheader("🏁 주행 컨트롤")

    speed = st.slider(
        "자동차 속도 (km/h)",
        min_value=0,
        max_value=200,
        value=st.session_state.speed,
        step=5
    )

    st.session_state.speed = speed

    # 시뮬레이션 시간 배속
    time_scale = st.select_slider(
        "시뮬레이션 시간 배속",
        options=[1, 5, 10, 30, 60],
        value=10,
        format_func=lambda x: f"{x}배속"
    )

    # 이전 주기의 경과 시간만큼 이동
    now = time.time()

    if st.session_state.running:

        if st.session_state.last_tick is not None:

            elapsed = min(
                now - st.session_state.last_tick,
                2.0
            )

            movement = (
                st.session_state.speed
                / 3.6
                * elapsed
                * time_scale
            )

            st.session_state.progress = min(
                total_distance,
                st.session_state.progress + movement
            )

        st.session_state.last_tick = now

        if st.session_state.progress >= total_distance:
            st.session_state.running = False
            st.session_state.last_tick = None

    # 버튼
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("▶ 주행 시작", use_container_width=True):
            if st.session_state.progress < total_distance:
                st.session_state.running = True
                st.session_state.last_tick = time.time()
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

    # -------------------------
    # 주행 거리 및 시간
    # -------------------------
    progress = st.session_state.progress

    remaining = max(
        0,
        total_distance - progress
    )

    if speed > 0:
        remaining_seconds = (
            remaining / (speed / 3.6)
        )
    else:
        remaining_seconds = 0

    hours = int(remaining_seconds // 3600)
    minutes = int((remaining_seconds % 3600) // 60)

    st.divider()

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "현재 속도",
        f"{speed} km/h"
    )

    m2.metric(
        "전체 거리",
        f"{total_distance / 1000:.2f} km"
    )

    m3.metric(
        "주행 거리",
        f"{progress / 1000:.2f} km"
    )

    m4.metric(
        "남은 거리",
        f"{remaining / 1000:.2f} km"
    )

    st.markdown(
        f"### ⏱️ 예상 남은 시간: {hours}시간 {minutes}분"
    )

    st.progress(
        min(1.0, progress / total_distance)
    )

    # -------------------------
    # 지도 생성
    # -------------------------
    car_position = get_car_position(
        coordinates,
        progress
    )

    map_center = car_position

    driving_map = folium.Map(
        location=map_center,
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # 전체 경로
    folium.PolyLine(
        locations=[
            [point[1], point[0]]
            for point in coordinates
        ],
        color="#2678FF",
        weight=6,
        opacity=0.8,
        tooltip="전체 주행 경로"
    ).add_to(driving_map)

    # 출발지
    folium.Marker(
        [
            coordinates[0][1],
            coordinates[0][0]
        ],
        tooltip="출발지",
        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(driving_map)

    # 목적지
    folium.Marker(
        [
            coordinates[-1][1],
            coordinates[-1][0]
        ],
        tooltip="목적지",
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(driving_map)

    # 자동차
    folium.Marker(
        location=car_position,
        tooltip="현재 자동차 위치",
        icon=folium.DivIcon(
            html="""
            <div style="
                font-size:30px;
                text-align:center;
                width:40px;
                transform:translate(-50%,-50%);
                text-shadow:1px 1px 3px white;
            ">🚗</div>
            """,
            icon_size=(40, 40),
            icon_anchor=(20, 20)
        )
    ).add_to(driving_map)

    st.subheader("🗺️ 실시간 주행 지도")

    st_folium(
        driving_map,
        width=None,
        height=600,
        key=f"drive_map_{int(progress)}",
        returned_objects=[]
    )

    st.caption(
        "지도 데이터: OpenStreetMap | 경로 데이터: OSRM"
    )

    # 자동 갱신
    if st.session_state.running:
        st_autorefresh(
            interval=1000,
            limit=None,
            key="drive_refresh"
        )

    if progress >= total_distance:
        st.success("🏁 목적지에 도착했습니다!")

else:

    st.info(
        "출발지와 목적지를 입력하고 실제 도로 경로를 검색해 주세요."
    )

    st.markdown("""
    ### DriveMap 기능
    - 실제 도로 지도 표시
    - 자동차 아이콘 이동
    - 속도에 따른 주행 거리 계산
    - 남은 거리 및 예상 시간 표시
    - 주행 시작 및 일시정지
    """)
