import json
import math
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="DriveMap 3D", page_icon="🚗", layout="wide")

st.markdown("""
<style>
.stApp {background:#0b0e12;color:#f2f4f8}
section[data-testid="stSidebar"] {background:#11161d}
div[data-testid="stMetric"] {background:#141a22;border:1px solid #27313d;padding:14px;border-radius:14px}
h1,h2,h3 {color:#f4f7fb}
</style>
""", unsafe_allow_html=True)

st.title("🚗 DriveMap 3D")
st.caption("실제 도로 경로 · 3D 주행 미리보기 · 거리 · 예상 시간 · 연료 계산")
st.info("경로는 OpenStreetMap 도로 데이터를 이용해 계산합니다. 교통 정체는 반영되지 않으며, 연료와 도착 시간은 추정치입니다.")

with st.sidebar:
    st.header("주행 설정")
    start_text = st.text_input("출발지", "수원역")
    end_text = st.text_input("목적지", "광교호수공원")
    fuel_efficiency = st.number_input("차량 연비 (km/L)", min_value=1.0, max_value=50.0, value=12.0, step=0.5)
    fuel_price = st.number_input("연료 가격 (원/L)", min_value=500, max_value=5000, value=1700, step=50)
    starting_fuel = st.number_input("현재 연료량 (L)", min_value=0.0, max_value=150.0, value=40.0, step=1.0)
    search = st.button("경로 찾기", type="primary", use_container_width=True)

@st.cache_data(ttl=3600, show_spinner=False)
def geocode(place):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "DriveMap3DStudentProject/1.0 (route planning demo)"}
    response = requests.get(url, params={"q": place + ", South Korea", "format": "jsonv2", "limit": 1}, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"장소를 찾지 못했습니다: {place}")
    return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "label": data[0]["display_name"]}

@st.cache_data(ttl=900, show_spinner=False)
def get_route(start_lon, start_lat, end_lon, end_lat):
    url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    response = requests.get(url, params={"overview": "full", "geometries": "geojson", "steps": "true"}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise ValueError("이 출발지와 목적지 사이의 경로를 찾지 못했습니다.")
    route = payload["routes"][0]
    return {
        "distance_m": route["distance"],
        "duration_s": route["duration"],
        "coordinates": route["geometry"]["coordinates"],
        "legs": route.get("legs", [])
    }

if "route_data" not in st.session_state:
    st.session_state.route_data = None
if search:
    try:
        with st.spinner("실제 도로 경로를 검색하고 있습니다..."):
            start = geocode(start_text)
            end = geocode(end_text)
            route = get_route(start["lon"], start["lat"], end["lon"], end["lat"])
            st.session_state.route_data = {"start": start, "end": end, "route": route}
    except Exception as exc:
        st.error(f"경로를 불러오지 못했습니다. 장소 이름을 더 구체적으로 입력하거나 잠시 후 다시 시도해 주세요. ({exc})")

data = st.session_state.route_data
if data:
    start, end, route = data["start"], data["end"], data["route"]
    distance_km = route["distance_m"] / 1000
    duration_min = route["duration_s"] / 60
    hours = int(duration_min // 60)
    mins = int(round(duration_min % 60))
    fuel_used = distance_km / fuel_efficiency
    cost = fuel_used * fuel_price
    fuel_left = starting_fuel - fuel_used

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("도로 거리", f"{distance_km:.1f} km")
    c2.metric("예상 소요 시간", f"{hours}시간 {mins}분" if hours else f"{mins}분")
    c3.metric("예상 연료 소비", f"{fuel_used:.2f} L")
    c4.metric("예상 연료비", f"{cost:,.0f}원")

    if fuel_left < 0:
        st.warning(f"현재 입력한 연료량으로는 약 {-fuel_left:.1f} L 부족할 수 있습니다. 출발 전 주유를 고려하세요.")
    else:
        st.success(f"예상 도착 시 연료 잔량: 약 {fuel_left:.1f} L (연료량과 연비가 일정하다고 가정)")

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("실제 지도 경로")
