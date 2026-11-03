
import streamlit as st
import folium
import json
import streamlit.components.v1 as components

from branca.element import Element

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
    min-height: 45px;
    font-weight: bold;
}

div.stButton > button p {
    color: white !important;
}

div.stButton > button:hover {
    background: #3b526f;
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
# 6. 주행 지도
# =====================================

if st.session_state.route:

    route = st.session_state.route

    coordinates = route["coordinates"]
    total_distance = route["distance"]

    st.divider()
    st.subheader("🎮 자동차 주행 시스템")

    st.info(
        "지도 안의 주행 버튼과 속도 조절 기능을 이용해 주세요."
    )

    # OSRM 좌표를 위도, 경도 순서로 변경
    route_points = [
        [point[1], point[0]]
        for point in coordinates
    ]

    # =================================
    # 7. Folium 지도 생성
    # =================================

    driving_map = folium.Map(
        location=route_points[0],
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    # 전체 경로
    folium.PolyLine(
        route_points,
        color="#2678ff",
        weight=6,
        opacity=0.85
    ).add_to(driving_map)

    # 출발지
    folium.Marker(
        route_points[0],
        tooltip="출발지",
        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(driving_map)

    # 목적지
    folium.Marker(
        route_points[-1],
        tooltip="목적지",
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(driving_map)

    driving_map.fit_bounds(route_points)

    # =================================
    # 8. JavaScript 주행 시스템
    # =================================

    route_json = json.dumps(route_points)

    map_name = driving_map.get_name()

    panel_html = """
    <div id="drive-panel" style="
        position:fixed;
        top:12px;
        left:12px;
        right:12px;
        z-index:9999;
        background:rgba(16,21,29,0.96);
        color:white;
        padding:16px;
        border-radius:14px;
        border:1px solid #52647c;
        font-family:Arial,sans-serif;
        box-shadow:0 3px 15px rgba(0,0,0,0.35);
    ">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            flex-wrap:wrap;
            gap:10px;
        ">
            <strong style="font-size:20px;">
                🚗 DriveMap
            </strong>

            <span id="drive-status"
                style="color:#20c997;font-weight:bold;">
                대기 중
            </span>
        </div>

        <div style="
            display:grid;
            grid-template-columns:repeat(4,1fr);
            gap:8px;
            margin-top:14px;
        ">

            <div style="background:#263448;padding:10px;border-radius:8px;">
                <small>전체 거리</small>
                <div id="total-distance">0 km</div>
            </div>

            <div style="background:#263448;padding:10px;border-radius:8px;">
                <small>주행 거리</small>
                <div id="driven-distance">0 km</div>
            </div>

            <div style="background:#263448;padding:10px;border-radius:8px;">
                <small>남은 거리</small>
                <div id="remaining-distance">0 km</div>
            </div>

            <div style="background:#263448;padding:10px;border-radius:8px;">
                <small>예상 시간</small>
                <div id="eta">-</div>
            </div>

        </div>

        <div style="margin-top:14px;">
            <label>자동차 속도</label>
            <strong id="speed-value"
                style="float:right;">60 km/h</strong>

            <input id="speed-control"
                type="range"
                min="0"
                max="200"
                step="5"
                value="60"
                style="width:100%;accent-color:#2678ff;">
        </div>

        <div style="margin-top:10px;">
            <label>게임 시간 배속</label>

            <select id="scale-control"
                style="
                    width:100%;
                    padding:8px;
                    margin-top:5px;
                    background:#263448;
                    color:white;
                    border:1px solid #52647c;
                    border-radius:7px;
                ">
                <option value="1">1배속</option>
                <option value="5">5배속</option>
                <option value="10" selected>10배속</option>
                <option value="30">30배속</option>
                <option value="60">60배속</option>
            </select>
        </div>

        <div style="
            display:flex;
            gap:8px;
            margin-top:14px;
        ">

            <button id="start-button" style="
                flex:1;
                padding:12px;
                border:0;
                border-radius:8px;
                background:#087f5b;
                color:white;
                font-weight:bold;
                cursor:pointer;
            ">▶ 시작</button>

            <button id="pause-button" style="
                flex:1;
                padding:12px;
                border:0;
                border-radius:8px;
                background:#b7791f;
                color:white;
                font-weight:bold;
                cursor:pointer;
            ">⏸ 정지</button>

            <button id="reset-button" style="
                flex:1;
                padding:12px;
                border:0;
                border-radius:8px;
                background:#b83232;
                color:white;
                font-weight:bold;
                cursor:pointer;
            ">↻ 초기화</button>

        </div>

        <div style="
            height:7px;
            background:#34445a;
            border-radius:10px;
            margin-top:14px;
            overflow:hidden;
        ">
            <div id="progress-bar" style="
                height:100%;
                width:0%;
                background:#20c997;
            "></div>
        </div>

    </div>
    """

    driving_map.get_root().html.add_child(
        Element(panel_html)
    )

    # =================================
    # 9. 자동차 애니메이션
    # =================================

    javascript = """
    (function() {

        const map = MAP_NAME;
        const points = ROUTE_POINTS;
        const totalMeters = TOTAL_DISTANCE;

        let progress = 0;
        let running = false;
        let lastTime = null;
        let animationId = null;

        const segmentLengths = [];
        let accumulated = [0];

        function distance(a, b) {
            const R = 6371000;
            const rad = x => x * Math.PI / 180;

            const dLat = rad(b[0] - a[0]);
            const dLon = rad(b[1] - a[1]);

            const value =
                Math.sin(dLat / 2) ** 2 +
                Math.cos(rad(a[0])) *
                Math.cos(rad(b[0])) *
                Math.sin(dLon / 2) ** 2;

            return 2 * R * Math.asin(Math.sqrt(value));
        }

        for (let i = 0; i < points.length - 1; i++) {

            const length = distance(points[i], points[i + 1]);

            segmentLengths.push(length);

            accumulated.push(
                accumulated[accumulated.length - 1] + length
            );
        }

        function getPosition(meters) {

            for (let i = 0; i < segmentLengths.length; i++) {

                if (accumulated[i + 1] >= meters) {

                    const length = segmentLengths[i];

                    const ratio = length > 0
                        ? (meters - accumulated[i]) / length
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

        const carIcon = L.divIcon({
            html: '<div style="font-size:32px;width:40px;height:40px;text-align:center;">🚗</div>',
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });

        const car = L.marker(points[0], {
            icon: carIcon,
            zIndexOffset: 1000
        }).addTo(map);

        const passedLine = L.polyline([], {
            color: "#20c997",
            weight: 7,
            opacity: 1
        }).addTo(map);

        const speedInput = document.getElementById("speed-control");
        const scaleInput = document.getElementById("scale-control");

        const status = document.getElementById("drive-status");

        function updateDisplay() {

            const speed = Number(speedInput.value);
            const scale = Number(scaleInput.value);

            const remaining = Math.max(0, totalMeters - progress);

            document.getElementById("speed-value").textContent =
                speed + " km/h";

            document.getElementById("total-distance").textContent =
                (totalMeters / 1000).toFixed(2) + " km";

            document.getElementById("driven-distance").textContent =
                (progress / 1000).toFixed(2) + " km";

            document.getElementById("remaining-distance").textContent =
                (remaining / 1000).toFixed(2) + " km";

            const effectiveSpeed = speed * scale;

            if (effectiveSpeed > 0 && running) {

                const seconds = remaining / (effectiveSpeed / 3.6);

                const hours = Math.floor(seconds / 3600);
                const minutes = Math.floor((seconds % 3600) / 60);

                document.getElementById("eta").textContent =
                    hours + "시간 " + minutes + "분";

            } else if (remaining <= 0) {

                document.getElementById("eta").textContent = "도착";

            } else {

                document.getElementById("eta").textContent = "정지 중";
            }

            document.getElementById("progress-bar").style.width =
                (progress / totalMeters * 100) + "%";
        }

        function updateCar() {

            const position = getPosition(progress);

            car.setLatLng(position);

            const passedPoints = [];

            for (let i = 0; i < points.length; i++) {

                if (accumulated[i] <= progress) {
                    passedPoints.push(points[i]);
                }
            }

            passedPoints.push(position);

            passedLine.setLatLngs(passedPoints);

        }

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

            progress += speed / 3.6 * scale * elapsed;

            if (progress >= totalMeters) {

                progress = totalMeters;
                running = false;
                status.textContent = "🏁 목적지 도착";
                status.style.color = "#20c997";
                lastTime = null;

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

        function startDrive() {

            if (progress >= totalMeters) {
                progress = 0;
                updateCar();
            }

            if (running) return;

            running = true;
            lastTime = null;

            status.textContent = "🚗 주행 중";

            animationId = requestAnimationFrame(animate);
        }

        function pauseDrive() {

            running = false;
            lastTime = null;

            if (animationId !== null) {
                cancelAnimationFrame(animationId);
            }

            status.textContent = "⏸ 일시정지";

            updateDisplay();
        }

        function resetDrive() {

            pauseDrive();

            progress = 0;

            updateCar();
            updateDisplay();

            status.textContent = "대기 중";
            status.style.color = "#20c997";
        }

        document.getElementById("start-button")
            .addEventListener("click", startDrive);

        document.getElementById("pause-button")
            .addEventListener("click", pauseDrive);

        document.getElementById("reset-button")
            .addEventListener("click", resetDrive);

        speedInput.addEventListener("input", updateDisplay);
        scaleInput.addEventListener("change", updateDisplay);

        updateCar();
        updateDisplay();

    })();
    """

    javascript = (
        javascript
        .replace("MAP_NAME", map_name)
        .replace("ROUTE_POINTS", route_json)
        .replace("TOTAL_DISTANCE", str(total_distance))
    )

    driving_map.get_root().script.add_child(
        Element(javascript)
    )

    # =================================
    # 10. 지도 표시
    # =================================

    st.subheader("🗺️ 실제 도로 주행 지도")

    map_html = driving_map.get_root().render()

    components.html(
        map_html,
        height=850,
        scrolling=False
    )

    st.caption(
        "지도: OpenStreetMap | 도로 경로: OSRM"
    )

else:

    st.info(
        "출발지와 목적지를 입력한 후 실제 도로 경로 검색을 눌러 주세요."
    )

    st.markdown("""
    ### 🚘 DriveMap 주요 기능

    - 실제 대한민국 도로 지도
    - 자동차 아이콘 실시간 이동
    - 주행 속도 조절
    - 게임 시간 배속
    - 주행 거리 및 남은 거리
    - 예상 도착 시간
    - 주행 시작 및 일시정지
    """)
