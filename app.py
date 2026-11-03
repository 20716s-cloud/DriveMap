
import streamlit as st
import streamlit.components.v1 as components
import json

from map_engine import find_location, get_route

# =====================================
# 1. 기본 설정
# =====================================

st.set_page_config(
    page_title="DriveMap",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #10151d;
    color: white;
}

h1, h2, h3, p, label {
    color: white !important;
}

div.stButton > button {
    background: #263448;
    color: white !important;
    border: 1px solid #52647c;
    border-radius: 10px;
    min-height: 48px;
    font-weight: bold;
}

div.stButton > button p {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================
# 2. 세션 데이터
# =====================================

if "route" not in st.session_state:
    st.session_state.route = None

if "start_name" not in st.session_state:
    st.session_state.start_name = "수원역"

if "end_name" not in st.session_state:
    st.session_state.end_name = "강남역"

# =====================================
# 3. 제목
# =====================================

st.title("🚗 DriveMap")
st.caption("REAL ROAD DRIVING SIMULATOR")

st.divider()

# =====================================
# 4. 출발지와 목적지
# =====================================

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

# =====================================
# 5. 경로 검색
# =====================================

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

                        st.success("경로 검색 완료!")

        except Exception as e:
            st.error(f"경로 검색 오류: {e}")

# =====================================
# 6. 주행 시뮬레이터
# =====================================

if st.session_state.route:

    route = st.session_state.route

    route_points = [
        [point[1], point[0]]
        for point in route["coordinates"]
    ]

    total_distance = float(route["distance"])

    if total_distance <= 0 or len(route_points) < 2:
        st.error("올바른 주행 경로를 불러오지 못했습니다.")

    else:

        st.divider()
        st.subheader("🎮 자동차 주행 시스템")

        st.info(
            "지도 안의 속도 조절과 주행 버튼을 이용해 주세요."
        )

        # =====================================
        # 7. HTML 지도와 자동차 제어
        # =====================================

        html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<link
 rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>

<script
 src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>

<style>
* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    font-family: Arial, sans-serif;
    background: #10151d;
}

#map {
    width: 100%;
    height: 850px;
    background: #dce3e8;
}

#panel {
    position: absolute;
    top: 12px;
    left: 12px;
    right: 12px;
    z-index: 1000;

    background: rgba(16, 21, 29, 0.96);
    color: white;

    padding: 15px;
    border-radius: 13px;
    border: 1px solid #52647c;

    box-shadow: 0 3px 15px rgba(0,0,0,0.35);
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
}

.header strong {
    font-size: 21px;
}

#status {
    color: #20c997;
    font-weight: bold;
}

.information {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 13px;
}

.info-box {
    background: #263448;
    padding: 10px;
    border-radius: 8px;
    min-width: 0;
}

.info-box small {
    color: #bdc8d8;
}

.info-box div {
    margin-top: 5px;
    font-size: 16px;
    font-weight: bold;
    overflow-wrap: anywhere;
}

.control {
    margin-top: 13px;
}

.control label {
    display: block;
    margin-bottom: 7px;
    font-size: 14px;
}

input[type="range"] {
    width: 100%;
    accent-color: #2678ff;
}

select {
    width: 100%;
    padding: 9px;
    border-radius: 7px;
    background: #263448;
    color: white;
    border: 1px solid #52647c;
}

.buttons {
    display: flex;
    gap: 8px;
    margin-top: 14px;
}

.buttons button {
    flex: 1;
    padding: 13px 5px;
    border: 0;
    border-radius: 8px;
    color: white;
    font-weight: bold;
    font-size: 14px;
    cursor: pointer;
}

#start {
    background: #087f5b;
}

#pause {
    background: #b7791f;
}

#reset {
    background: #b83232;
}

.buttons button:hover {
    filter: brightness(1.2);
}

#progress-background {
    height: 8px;
    background: #34445a;
    border-radius: 10px;
    margin-top: 14px;
    overflow: hidden;
}

#progress-bar {
    height: 100%;
    width: 0%;
    background: #20c997;
}

#map-error {
    display: none;
    padding: 10px;
    color: #ffaaaa;
}

@media(max-width: 600px) {
    .information {
        grid-template-columns: repeat(2, 1fr);
    }

    #map {
        height: 950px;
    }
}
</style>
</head>

<body>

<div id="map"></div>

<div id="panel">

    <div class="header">
        <strong>🚗 DriveMap</strong>
        <span id="status">대기 중</span>
    </div>

    <div class="information">

        <div class="info-box">
            <small>전체 거리</small>
            <div id="total">0 km</div>
        </div>

        <div class="info-box">
            <small>주행 거리</small>
            <div id="driven">0 km</div>
        </div>

        <div class="info-box">
            <small>남은 거리</small>
            <div id="remaining">0 km</div>
        </div>

        <div class="info-box">
            <small>예상 시간</small>
            <div id="eta">-</div>
        </div>

    </div>

    <div class="control">
        <label>
            자동차 속도:
            <strong id="speed-value">60 km/h</strong>
        </label>

        <input
            id="speed"
            type="range"
            min="0"
            max="200"
            step="5"
            value="60"
        >
    </div>

    <div class="control">
        <label>게임 시간 배속</label>

        <select id="scale">
            <option value="1">1배속</option>
            <option value="5">5배속</option>
            <option value="10" selected>10배속</option>
            <option value="30">30배속</option>
            <option value="60">60배속</option>
        </select>
    </div>

    <div class="buttons">
        <button id="start">▶ 주행 시작</button>
        <button id="pause">⏸ 일시정지</button>
        <button id="reset">↻ 처음부터</button>
    </div>

    <div id="progress-background">
        <div id="progress-bar"></div>
    </div>

    <div id="map-error"></div>

</div>

<script>
(function() {

    const points = ROUTE_DATA;
    const totalDistance = TOTAL_DATA;

    const status = document.getElementById("status");
    const speedInput = document.getElementById("speed");
    const scaleInput = document.getElementById("scale");

    let progress = 0;
    let running = false;
    let lastTime = null;
    let animationId = null;

    // 지도 생성
    const map = L.map("map", {
        zoomControl: true
    });

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        }
    ).addTo(map);

    // 경로 표시
    const fullLine = L.polyline(points, {
        color: "#2678ff",
        weight: 6,
        opacity: 0.9
    }).addTo(map);

    map.fitBounds(fullLine.getBounds(), {
        padding: [30, 30]
    });

    // 출발지
    L.marker(points[0])
        .addTo(map)
        .bindTooltip("출발지");

    // 목적지
    L.marker(points[points.length - 1])
        .addTo(map)
        .bindTooltip("목적지");

    // 거리 계산
    function distance(a, b) {

        const R = 6371000;

        const rad = value => value * Math.PI / 180;

        const dLat = rad(b[0] - a[0]);
        const dLon = rad(b[1] - a[1]);

        const value =
            Math.sin(dLat / 2) ** 2 +
            Math.cos(rad(a[0])) *
            Math.cos(rad(b[0])) *
            Math.sin(dLon / 2) ** 2;

        return 2 * R * Math.asin(Math.sqrt(value));
    }

    // 경로 구간별 거리
    const lengths = [];
    const cumulative = [0];

    for (let i = 0; i < points.length - 1; i++) {

        const length = distance(
            points[i],
            points[i + 1]
        );

        lengths.push(length);

        cumulative.push(
            cumulative[cumulative.length - 1] + length
        );
    }

    // 실제 경로 길이 사용
    const geometryDistance =
        cumulative[cumulative.length - 1];

    // 진행 거리에 따른 자동차 위치
    function getPosition(meters) {

        for (let i = 0; i < lengths.length; i++) {

            if (cumulative[i + 1] >= meters) {

                const length = lengths[i];

                const ratio = length > 0
                    ? (meters - cumulative[i]) / length
                    : 0;

                return [
                    points[i][0] +
                    (points[i + 1][0] - points[i][0]) * ratio,

                    points[i][1] +
                    (points[i + 1][1] - points[i][1]) * ratio
                ];
            }
        }

        return points[points.length - 1];
    }

    // 자동차 아이콘
    const carIcon = L.divIcon({

        className: "",

        html: `
            <div style="
                font-size:32px;
                width:42px;
                height:42px;
                text-align:center;
                filter:drop-shadow(1px 2px 2px #555);
            ">🚗</div>
        `,

        iconSize: [42, 42],
        iconAnchor: [21, 21]
    });

    const car = L.marker(points[0], {
        icon: carIcon,
        zIndexOffset: 1000
    }).addTo(map);

    // 지나온 길
    const passedLine = L.polyline([], {
        color: "#20c997",
        weight: 7
    }).addTo(map);

    // 거리와 시간 표시
    function updateDisplay() {

        const speed = Number(speedInput.value);
        const scale = Number(scaleInput.value);

        const remaining = Math.max(
            0,
            totalDistance - progress
        );

        document.getElementById("speed-value").textContent =
            speed + " km/h";

        document.getElementById("total").textContent =
            (totalDistance / 1000).toFixed(2) + " km";

        document.getElementById("driven").textContent =
            (progress / 1000).toFixed(2) + " km";

        document.getElementById("remaining").textContent =
            (remaining / 1000).toFixed(2) + " km";

        const effectiveSpeed = speed * scale;

        if (remaining <= 0) {

            document.getElementById("eta").textContent = "도착";

        } else if (effectiveSpeed > 0) {

            const seconds =
                remaining / (effectiveSpeed / 3.6);

            const hours = Math.floor(seconds / 3600);

            const minutes = Math.floor(
                (seconds % 3600) / 60
            );

            document.getElementById("eta").textContent =
                hours + "시간 " + minutes + "분";

        } else {

            document.getElementById("eta").textContent =
                "정차 중";
        }

        document.getElementById("progress-bar").style.width =
            (progress / totalDistance * 100) + "%";
    }

    // 자동차와 지나온 길 업데이트
    function updateCar() {

        const position = getPosition(progress);

        car.setLatLng(position);

        const passed = [];

        for (let i = 0; i < points.length; i++) {

            if (cumulative[i] <= progress) {
                passed.push(points[i]);
            }
        }

        passed.push(position);

        passedLine.setLatLngs(passed);
    }

    // 애니메이션
    function animate(timestamp) {

        if (!running) return;

        if (lastTime === null) {
            lastTime = timestamp;
        }

        const elapsed = Math.min(
            (timestamp - lastTime) / 1000,
            0.1
        );

        lastTime = timestamp;

        const speed = Number(speedInput.value);
        const scale = Number(scaleInput.value);

        progress +=
            speed / 3.6 * scale * elapsed;

        if (progress >= totalDistance) {

            progress = totalDistance;
            running = false;
            lastTime = null;

            status.textContent = "🏁 목적지 도착";
            status.style.color = "#20c997";

        } else {

            status.textContent = "🚗 주행 중";
            status.style.color = "#20c997";
        }

        updateCar();
        updateDisplay();

        if (running) {
            animationId = requestAnimationFrame(animate);
        }
    }

    // 시작 버튼
    document.getElementById("start")
        .addEventListener("click", function() {

            if (running) return;

            if (progress >= totalDistance) {
                progress = 0;
                updateCar();
            }

            if (Number(speedInput.value) === 0) {
                status.textContent = "속도를 설정해 주세요";
                return;
            }

            running = true;
            lastTime = null;

            status.textContent = "🚗 주행 중";

            animationId =
                requestAnimationFrame(animate);
        });

    // 일시정지
    document.getElementById("pause")
        .addEventListener("click", function() {

            running = false;
            lastTime = null;

            if (animationId !== null) {
                cancelAnimationFrame(animationId);
            }

            status.textContent = "⏸ 일시정지";

            updateDisplay();
        });

    // 처음부터
    document.getElementById("reset")
        .addEventListener("click", function() {

            running = false;
            lastTime = null;

            if (animationId !== null) {
                cancelAnimationFrame(animationId);
            }

            progress = 0;

            updateCar();
            updateDisplay();

            status.textContent = "대기 중";
            status.style.color = "#20c997";
        });

    speedInput.addEventListener(
        "input",
        updateDisplay
    );

    scaleInput.addEventListener(
        "change",
        updateDisplay
    );

    // 초기 화면
    updateCar();
    updateDisplay();

    setTimeout(function() {
        map.invalidateSize();
    }, 300);

    // 지도 오류 확인
    if (geometryDistance <= 0) {
        document.getElementById("map-error").style.display = "block";
        document.getElementById("map-error").textContent =
            "경로 거리 계산에 실패했습니다.";
    }

})();
</script>

</body>
</html>
"""

        html = html.replace(
            "ROUTE_DATA",
            json.dumps(route_points)
        )

        html = html.replace(
            "TOTAL_DATA",
            str(total_distance)
        )

        # =====================================
        # 8. 지도 표시
        # =====================================

        st.subheader("🗺️ 실제 도로 주행 지도")

        components.html(
            html,
            height=870,
            scrolling=False
        )

        st.caption(
            "지도: OpenStreetMap | 도로 경로: OSRM"
        )

else:

    st.info(
        "출발지와 목적지를 입력하고 실제 도로 경로 검색을 눌러 주세요."
    )

    st.markdown("""
    ### 🚘 DriveMap 기능

    - 실제 도로 지도
    - 자동차 아이콘 이동
    - 속도 조절
    - 게임 시간 배속
    - 주행 거리 계산
    - 남은 거리 표시
    - 예상 도착 시간
    - 주행 시작 및 일시정지
    """)
