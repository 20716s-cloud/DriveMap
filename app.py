
import json
import math
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="DriveMap",
    page_icon="🚘",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background:#090d13;color:#eef3f8}
section[data-testid="stSidebar"] {background:#101722}
div[data-testid="stMetric"] {
 background:#141c27;border:1px solid #273546;
 border-radius:12px;padding:12px
}
</style>
""", unsafe_allow_html=True)

st.title("🚘 DriveMap")
st.caption("Kakao Roadview Driving Simulator")

with st.sidebar:
    st.subheader("경로 설정")
    origin = st.text_input("출발지", "수원역")
    destination = st.text_input("목적지", "광교호수공원")

    st.subheader("차량 설정")
    efficiency = st.number_input(
        "연비 (km/L)", min_value=1.0,
        max_value=60.0, value=12.0
    )
    starting_fuel = st.number_input(
        "시작 연료 (L)", min_value=0.0,
        max_value=200.0, value=35.0
    )
    fuel_price = st.number_input(
        "연료 가격 (원/L)", min_value=500,
        max_value=5000, value=1700
    )

    search = st.button(
        "경로 검색", type="primary",
        use_container_width=True
    )


@st.cache_data(ttl=3600)
def geocode(place):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": place + ", South Korea",
            "format": "jsonv2",
            "limit": 1
        },
        headers={"User-Agent": "DriveMapStudentProject/1.0"},
        timeout=20
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(f"장소를 찾지 못했습니다: {place}")

    return {
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"]),
        "name": results[0]["display_name"]
    }


@st.cache_data(ttl=900)
def get_route(lon1, lat1, lon2, lat2):
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
    )
    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson"
        },
        timeout=30
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != "Ok" or not result.get("routes"):
        raise ValueError("운전 경로를 찾지 못했습니다.")

    route = result["routes"][0]

    return {
        "distance_m": route["distance"],
        "duration_s": route["duration"],
        "coordinates": route["geometry"]["coordinates"]
    }


if "drive_data" not in st.session_state:
    st.session_state.drive_data = None

if search:
    try:
        if not origin.strip() or not destination.strip():
            raise ValueError("출발지와 목적지를 입력하세요.")

        with st.spinner("경로를 검색하고 있습니다..."):
            start = geocode(origin.strip())
            end = geocode(destination.strip())
            route = get_route(
                start["lon"], start["lat"],
                end["lon"], end["lat"]
            )

        st.session_state.drive_data = {
            "start": start,
            "end": end,
            "route": route,
            "origin": origin.strip(),
            "destination": destination.strip()
        }

    except Exception as e:
        st.error(f"경로 검색 실패: {e}")


data = st.session_state.drive_data

if data:
    start = data["start"]
    end = data["end"]
    route = data["route"]

    distance_km = route["distance_m"] / 1000
    duration_min = route["duration_s"] / 60
    fuel_estimate = distance_km / efficiency
    cost_estimate = fuel_estimate * fuel_price

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("도로 거리", f"{distance_km:.1f} km")
    c2.metric("기본 예상 시간", f"{duration_min:.0f}분")
    c3.metric("예상 연료", f"{fuel_estimate:.2f} L")
    c4.metric("예상 연료비", f"{cost_estimate:,.0f}원")

    try:
        kakao_key = st.secrets["KAKAO_MAPS_API_KEY"]
    except Exception:
        kakao_key = ""

    if not kakao_key:
        st.warning(
            "카카오 JavaScript 키가 설정되지 않았습니다. "
            "Streamlit Settings → Secrets에 "
            "KAKAO_MAPS_API_KEY를 설정하세요."
        )

    st.subheader("1인칭 카카오 로드뷰 운전")
    st.caption(
        "W/↑ 가속 · S/↓ 또는 Space 브레이크 · "
        "A/← 왼쪽 · D/→ 오른쪽"
    )

    # 경로 좌표를 브라우저로 전달
    coords_json = json.dumps(route["coordinates"])
    config_json = json.dumps({
        "distanceKm": distance_km,
        "durationMin": duration_min,
        "efficiency": efficiency,
        "fuelLiters": starting_fuel,
        "fuelPrice": fuel_price
    })

    key_json = json.dumps(kakao_key)

    game_html = r"""
<div id="driveGame" style="
    background:#0a0f16;color:white;
    font-family:Arial,sans-serif;
    border-radius:14px;overflow:hidden;
">
  <div style="height:500px;position:relative;background:#111">
    <div id="roadview" style="height:100%;width:100%"></div>

    <div id="loading" style="
      position:absolute;top:50%;left:50%;
      transform:translate(-50%,-50%);
      background:#101722eF;padding:14px;
      border-radius:10px;z-index:5;
    ">카카오 로드뷰를 불러오는 중...</div>

    <div style="
      position:absolute;top:12px;left:12px;
      z-index:3;pointer-events:none;
      background:#101722e8;padding:10px;
      border-radius:10px;font-size:13px;
    ">
      <b>DRIVEMAP</b><br>
      <span id="status">준비 중</span>
    </div>

    <div style="
      position:absolute;top:12px;right:12px;
      z-index:3;pointer-events:none;
      background:#101722e8;padding:10px;
      border-radius:10px;text-align:right;
    ">
      속도 <b><span id="speed">0</span> km/h</b><br>
      연료 <b><span id="fuel">--</span> L</b>
    </div>

    <!-- 화면 위에 표시하는 가상 맞은편 차량 -->
    <div style="
      position:absolute;inset:0;overflow:hidden;
      pointer-events:none;z-index:2;
    ">
      <div class="traffic car1">🚙</div>
      <div class="traffic car2">🚗</div>
      <div class="traffic car3">🚐</div>
    </div>

    <div style="
      position:absolute;bottom:12px;left:12px;right:12px;
      z-index:3;display:flex;justify-content:space-between;
      pointer-events:none;gap:8px;
    ">
      <div class="info">
        남은 거리<br><b id="remaining">--</b>
      </div>
      <div class="info">
        예상 연료비<br><b id="cost">--</b>
      </div>
    </div>
  </div>

  <style>
    .info {
      background:#101722eF;padding:8px 12px;
      border-radius:9px;font-size:12px;
    }
    .traffic {
      position:absolute;left:54%;bottom:25%;
      font-size:34px;opacity:0;
      filter:drop-shadow(0 3px 3px #0008);
    }
    .car1 {animation:pass 9s linear infinite}
    .car2 {animation:pass 12s linear 3s infinite}
    .car3 {animation:pass 15s linear 6s infinite}
    @keyframes pass {
      0% {left:53%;bottom:43%;opacity:0;transform:scale(.3)}
      15% {opacity:1}
      80% {opacity:1}
      100% {left:70%;bottom:5%;opacity:0;transform:scale(1.8)}
    }
    .driveButton {
      background:#172332;color:white;
      border:1px solid #34485f;
      border-radius:10px;height:48px;
      padding:0 14px;min-width:55px;
      touch-action:none;
    }
  </style>

  <div style="
    background:#0e141d;padding:12px;
    display:flex;justify-content:center;
    gap:8px;flex-wrap:wrap;
  ">
    <button class="driveButton" data-key="ArrowLeft">◀</button>
    <button class="driveButton" data-key="ArrowDown">브레이크</button>
    <button class="driveButton" data-key="ArrowUp"
      style="background:#0878c8">▲ 가속</button>
    <button class="driveButton" data-key="ArrowRight">▶</button>
    <button class="driveButton" id="reset">다시 시작</button>
  </div>

  <div style="
    background:#0e141d;color:#aab8c8;
    padding:0 12px 12px;font-size:12px;
  ">
    키보드를 사용하려면 운전 화면을 한 번 클릭하세요.
  </div>
</div>

<script>
(() => {
  const KEY = KAKAO_KEY_DATA;
  const coords = ROUTE_DATA;
  const cfg = CONFIG_DATA;
  const $ = id => document.getElementById(id);

  let roadview = null;
  let roadviewClient = null;
  let speed = 0;
  let progress = 0;
  let fuel = cfg.fuelLiters;
  let keys = {};
  let last = performance.now();
  let headingOffset = 0;
  let lastUpdate = 0;
  let currentSegment = -1;
  let pending = false;

  const rad = d => d * Math.PI / 180;

  function distance(a, b) {
    const R = 6371000;
    const dLat = rad(b[1] - a[1]);
    const dLon = rad(b[0] - a[0]);
    const v = Math.sin(dLat / 2) ** 2
      + Math.cos(rad(a[1])) * Math.cos(rad(b[1]))
      * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(v));
  }

  function bearing(a, b) {
    const p1 = rad(a[1]), p2 = rad(b[1]);
    const dl = rad(b[0] - a[0]);
    const y = Math.sin(dl) * Math.cos(p2);
    const x = Math.cos(p1) * Math.sin(p2)
      - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
    return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  }

  const cumulative = [0];
  for (let i = 1; i < coords.length; i++) {
    cumulative.push(
      cumulative[i - 1] + distance(coords[i - 1], coords[i])
    );
  }
  const totalMeters = cumulative[cumulative.length - 1];

  function pointAt(meters) {
    let i = 0;
    while (
      i < cumulative.length - 2 &&
      cumulative[i + 1] < meters
    ) i++;

    const span = cumulative[i + 1] - cumulative[i];
    const t = span > 0
      ? (meters - cumulative[i]) / span : 0;

    return {
      i,
      lat: coords[i][1] + (coords[i + 1][1] - coords[i][1]) * t,
      lng: coords[i][0] + (coords[i + 1][0] - coords[i][0]) * t,
      heading: bearing(coords[i], coords[i + 1])
    };
  }

  function updateRoad(force = false) {
    if (!roadview || pending || progress >= 1) return;

    const loc = pointAt(progress * totalMeters);
    const now = performance.now();

    // 일정 거리마다 가장 가까운 카카오 로드뷰 지점을 검색
    if (!force && loc.i === currentSegment) {
      roadview.setViewpoint({
        pan: (loc.heading + headingOffset + 360) % 360,
        tilt: 0,
        zoom: 0
      });
      return;
    }

    if (!force && now - lastUpdate < 1800) return;

    currentSegment = loc.i;
    lastUpdate = now;
    pending = true;

    const position = new kakao.maps.LatLng(loc.lat, loc.lng);

    roadviewClient.getNearestPanoId(
      position, 100,
      function(panoId) {
        pending = false;

        if (panoId) {
          roadview.setPanoId(panoId, position);
          roadview.setViewpoint({
            pan: (loc.heading + headingOffset + 360) % 360,
            tilt: 0,
            zoom: 0
          });
          $("loading").style.display = "none";
          $("status").textContent = "카카오 로드뷰 연결됨";
        } else {
          $("status").textContent =
            "주변 로드뷰 없음 · 다음 지점을 찾는 중";
        }
      }
    );
  }

  function initKakao() {
    const start = new kakao.maps.LatLng(
      coords[0][1], coords[0][0]
    );

    roadview = new kakao.maps.Roadview(
      $("roadview"),
      {pan: 0, tilt: 0, zoom: 0}
    );
    roadviewClient = new kakao.maps.RoadviewClient();

    kakao.maps.event.addListener(roadview, "init", function() {
      updateRoad(true);
    });

    roadviewClient.getNearestPanoId(start, 100, function(panoId) {
      if (panoId) {
        roadview.setPanoId(panoId, start);
        roadview.setViewpoint({pan: 0, tilt: 0, zoom: 0});
        $("loading").style.display = "none";
        $("status").textContent = "로드뷰 준비 완료";
      } else {
        $("loading").textContent =
          "출발지 주변에 로드뷰가 없습니다.";
      }
    });
  }

  window.initDriveMap = initKakao;

  function loadKakao() {
    if (!KEY) {
      $("loading").textContent =
        "카카오 JavaScript 키를 설정해 주세요.";
      return;
    }

    const script = document.createElement("script");
    script.src =
      "https://dapi.kakao.com/v2/maps/sdk.js?appkey="
      + encodeURIComponent(KEY)
      + "&autoload=false";
    script.onload = function() {
      kakao.maps.load(initKakao);
    };
    script.onerror = function() {
      $("loading").textContent =
        "카카오 SDK 로딩 실패: 키와 도메인을 확인하세요.";
    };
    document.head.appendChild(script);
  }

  window.addEventListener("keydown", e => {
    const k = e.key.toLowerCase();
    if (
      ["arrowup", "arrowdown", "arrowleft", "arrowright", " "]
        .includes(k) || e.code === "Space"
    ) e.preventDefault();
    keys[k] = true;
    if (e.code === "Space") keys.space = true;
  });

  window.addEventListener("keyup", e => {
    keys[e.key.toLowerCase()] = false;
    if (e.code === "Space") keys.space = false;
  });

  document.querySelectorAll("[data-key]").forEach(button => {
    const k = button.dataset.key.toLowerCase();
    const down = e => {
      e.preventDefault();
      keys[k] = true;
    };
    const up = e => {
      e.preventDefault();
      keys[k] = false;
    };
    button.addEventListener("pointerdown", down);
    button.addEventListener("pointerup", up);
    button.addEventListener("pointerleave", up);
    button.addEventListener("pointercancel", up);
  });

  $("reset").addEventListener("click", () => {
    speed = 0;
    progress = 0;
    fuel = cfg.fuelLiters;
    headingOffset = 0;
    currentSegment = -1;
    updateRoad(true);
  });

  function frame(now) {
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;

    const up = keys.w || keys.arrowup;
    const down = keys.s || keys.arrowdown || keys.space;
    const left = keys.a || keys.arrowleft;
    const right = keys.d || keys.arrowright;

    if (up) speed = Math.min(100, speed + 25 * dt);
    else speed = Math.max(0, speed - 5 * dt);

    if (down) speed = Math.max(0, speed - 55 * dt);

    const steer = (right ? 1 : 0) - (left ? 1 : 0);
    headingOffset += steer * 40 * dt;
    headingOffset = Math.max(-60, Math.min(60, headingOffset));

    if (!left && !right) headingOffset *= Math.pow(0.94, dt * 60);

    if (speed > 0 && progress < 1) {
      const meters = speed / 3.6 * dt;
      progress = Math.min(1, progress + meters / Math.max(totalMeters, 1));
      fuel = Math.max(
        0, fuel - meters / 1000 / Math.max(cfg.efficiency, 1)
      );

      updateRoad();
    }

    $("speed").textContent = Math.round(speed);
    $("fuel").textContent = fuel.toFixed(2);
    $("remaining").textContent =
      (cfg.distanceKm * (1 - progress)).toFixed(2) + " km";
    $("cost").textContent =
      Math.round((cfg.fuelLiters - fuel) * cfg.fuelPrice)
      .toLocaleString() + "원";

    if (progress >= 1) $("status").textContent = "목적지 도착";

    requestAnimationFrame(frame);
  }

  loadKakao();
  requestAnimationFrame(frame);
})();
</script>
"""

    game_html = (
        game_html
        .replace("KAKAO_KEY_DATA", key_json)
        .replace("ROUTE_DATA", coords_json)
        .replace("CONFIG_DATA", config_json)
    )

    components.html(game_html, height=680, scrolling=False)

    st.subheader("실제 도로 경로")

    route_map = folium.Map(
        location=[start["lat"], start["lon"]],
        zoom_start=13
    )
    points = [(lat, lon) for lon, lat in route["coordinates"]]

    folium.PolyLine(
        points, color="#159cff", weight=5
    ).add_to(route_map)

    folium.Marker(
        [start["lat"], start["lon"]],
        tooltip="출발지"
    ).add_to(route_map)

    folium.Marker(
        [end["lat"], end["lon"]],
        tooltip="목적지"
    ).add_to(route_map)

    route_map.fit_bounds(points)

    st_folium(
        route_map,
        height=420,
        use_container_width=True
    )

    st.caption(
        "학습용 시뮬레이터입니다. "
        "가상 차량 애니메이션은 실제 교통 상황과 연동되지 않습니다."
    )

else:
    st.info(
        "출발지와 목적지를 입력한 뒤 경로 검색을 눌러 주세요."
    )
