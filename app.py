
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DriveMap | Virtual Drive",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🚗 DriveMap")
st.caption("VIRTUAL DRIVE  /  MAP EXPLORATION")

st.write(
    "키보드 방향키 또는 WASD 키로 자동차를 움직이세요. "
    "지도 안을 클릭한 뒤 키보드를 사용하면 됩니다."
)

html_code = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    color: #f4f7fb;
    background: #0c1119;
    font-family: Arial, sans-serif;
}

.dashboard {
    background: #151d29;
    border: 1px solid #29384a;
    border-radius: 15px;
    padding: 16px;
    margin-bottom: 12px;
}

.top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.tag {
    color: #4ee0ae;
    font-size: 12px;
    letter-spacing: 1px;
    font-weight: bold;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.stat {
    background: #0d141e;
    padding: 12px;
    border-radius: 10px;
}

.label {
    font-size: 12px;
    color: #9baec4;
    margin-bottom: 7px;
}

.value {
    font-size: clamp(18px, 3.5vw, 27px);
    font-weight: bold;
}

.unit {
    font-size: 11px;
    color: #9baec4;
}

#map {
    width: 100%;
    height: 450px;
    border-radius: 15px;
    border: 1px solid #29384a;
    outline: none;
}

#map:focus {
    border-color: #4ee0ae;
}

.controls {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 12px;
}

.pad {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 52px);
    gap: 7px;
}

button {
    cursor: pointer;
    border: 1px solid #35455a;
    background: #202c3c;
    color: white;
    font-size: 17px;
    border-radius: 10px;
    font-weight: bold;
    touch-action: manipulation;
}

button:hover {
    background: #30445a;
}

button:active {
    background: #356c66;
    transform: scale(.97);
}

.up { grid-column: 2; grid-row: 1; }
.left { grid-column: 1; grid-row: 2; }
.down { grid-column: 2; grid-row: 2; }
.right { grid-column: 3; grid-row: 2; }

.actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.actions button {
    min-height: 43px;
    font-size: 13px;
}

.primary {
    color: #08251d;
    background: #4ee0ae;
    border: none;
}

.primary:hover { background: #75f0c5; }

#status {
    color: #a8bacd;
    font-size: 12px;
    line-height: 1.6;
    margin-top: 13px;
}

.car {
    font-size: 30px;
    line-height: 36px;
    text-align: center;
    filter: drop-shadow(0 2px 3px #0009);
}

@media (max-width: 560px) {
    #map { height: 380px; }
    .controls { grid-template-columns: 1fr; }
    .stats { gap: 5px; }
    .stat { padding: 9px; }
}
</style>
</head>

<body>
<div class="dashboard">
    <div class="top">
        <div>
            <div class="tag">DRIVEMAP ARCADE</div>
            <div style="font-size:22px;font-weight:bold;margin-top:5px">
                Free Drive
            </div>
        </div>
        <div style="font-size:12px;color:#9baec4">
            VIRTUAL MODE · GPS NOT REQUIRED
        </div>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="label">DISTANCE</div>
            <div class="value">
                <span id="distance">0</span>
                <span class="unit">m</span>
            </div>
        </div>
        <div class="stat">
            <div class="label">DRIVE TIME</div>
            <div class="value" id="time">00:00</div>
        </div>
        <div class="stat">
            <div class="label">SCORE</div>
            <div class="value" id="score">0</div>
            <div class="unit">POINTS</div>
        </div>
    </div>
</div>

<div id="map" tabindex="0"
     aria-label="가상 주행 지도. 클릭한 후 방향키로 이동하세요."></div>

<div class="controls">
    <div class="dashboard">
        <div class="label">DRIVING CONTROLS</div>
        <div class="pad">
            <button class="up" data-move="up" aria-label="위로 이동">▲</button>
            <button class="left" data-move="left" aria-label="왼쪽 이동">◀</button>
            <button class="down" data-move="down" aria-label="아래로 이동">▼</button>
            <button class="right" data-move="right" aria-label="오른쪽 이동">▶</button>
        </div>
        <div id="status">
            READY · 지도를 클릭하고 방향키 또는 WASD를 눌러 보세요.
        </div>
    </div>

    <div class="dashboard">
        <div class="label">GAME OPTIONS</div>
        <div class="actions">
            <button id="center">◎ 자동차 위치로 이동</button>
            <button id="reset" class="primary">↻ 새 주행 시작</button>
        </div>
        <div style="font-size:12px;color:#9baec4;line-height:1.6;margin-top:12px">
            한 번 누를 때마다 자동차가 이동합니다.
            지나온 경로는 파란색 선으로 기록됩니다.
        </div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
const map = L.map("map", {
    zoomControl: true
}).setView([37.5665, 126.9780], 17);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(map);

// 가상 주행 시작 위치: 서울 시내의 지도 좌표
const initial = L.latLng(37.5665, 126.9780);
let pos = L.latLng(initial.lat, initial.lng);
let path = [[pos.lat, pos.lng]];
let distance = 0;
let score = 0;
let moves = 0;
let startTime = null;
let timer = null;
let heading = 0;

// 자동차 아이콘
const carIcon = L.divIcon({
    className: "car",
    html: '<span id="car-emoji" style="display:block">🚗</span>',
    iconSize: [38, 38],
    iconAnchor: [19, 19]
});

const car = L.marker(pos, {
    icon: carIcon,
    keyboard: false
}).addTo(map);

const route = L.polyline(path, {
    color: "#168cff",
    weight: 5,
    opacity: 0.9
}).addTo(map);

const distanceEl = document.getElementById("distance");
const scoreEl = document.getElementById("score");
const timeEl = document.getElementById("time");
const statusEl = document.getElementById("status");

function updateDashboard() {
    distanceEl.textContent = Math.round(distance);
    scoreEl.textContent = score;
}

function updateTime() {
    if (!startTime) return;

    const seconds = Math.floor((Date.now() - startTime) / 1000);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;

    timeEl.textContent =
        String(mins).padStart(2, "0") + ":" +
        String(secs).padStart(2, "0");
}

function move(direction) {
    if (moves === 0) {
        startTime = Date.now();
        timer = setInterval(updateTime, 1000);
    }

    // 지도 좌표를 기준으로 약 15m씩 이동
    const meters = 15;
    const latScale = 111320;
    const lngScale = 111320 *
        Math.cos(pos.lat * Math.PI / 180);

    let dLat = 0;
    let dLng = 0;

    if (direction === "up") {
        dLat = meters / latScale;
        heading = 0;
    } else if (direction === "down") {
        dLat = -meters / latScale;
        heading = 180;
    } else if (direction === "left") {
        dLng = -meters / lngScale;
        heading = 270;
    } else if (direction === "right") {
        dLng = meters / lngScale;
        heading = 90;
    }

    pos = L.latLng(pos.lat + dLat, pos.lng + dLng);

    // 자동차 아이콘 방향 변경
    const emoji = document.getElementById("car-emoji");
    if (emoji) {
        emoji.style.transform = "rotate(" + heading + "deg)";
    }

    // 경로 누적 및 화면 갱신
    path.push([pos.lat, pos.lng]);
    route.setLatLngs(path);
    car.setLatLng(pos);

    distance += meters;
    score += 10;
    moves += 1;

    updateDashboard();

    statusEl.textContent =
        "DRIVING · 이동 " + moves +
        "회 · 누적 경로 " + path.length + "개 지점";

    // 자동차가 지도 화면 안에서 보이도록 이동
    map.panTo(pos, { animate: true, duration: 0.15 });
}

document.querySelectorAll("[data-move]").forEach(button => {
    button.addEventListener("click", () => {
        move(button.dataset.move);
        document.getElementById("map").focus();
    });
});

// 키보드: 방향키 또는 WASD
document.addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;

    const key = event.key.toLowerCase();

    const keys = {
        arrowup: "up",
        w: "up",
        arrowdown: "down",
        s: "down",
        arrowleft: "left",
        a: "left",
        arrowright: "right",
        d: "right"
    };

    if (keys[key]) {
        event.preventDefault();
        move(keys[key]);
    }
});

document.getElementById("center").addEventListener("click", () => {
    map.setView(pos, 17);
    statusEl.textContent = "자동차 위치를 지도 중앙에 표시했습니다.";
});

document.getElementById("reset").addEventListener("click", () => {
    if (timer) clearInterval(timer);

    pos = L.latLng(initial.lat, initial.lng);
    path = [[pos.lat, pos.lng]];
    distance = 0;
    score = 0;
    moves = 0;
    startTime = null;
    timer = null;
    heading = 0;

    car.setLatLng(pos);
    route.setLatLngs(path);

    const emoji = document.getElementById("car-emoji");
    if (emoji) emoji.style.transform = "rotate(0deg)";

    distanceEl.textContent = "0";
    scoreEl.textContent = "0";
    timeEl.textContent = "00:00";

    map.setView(pos, 17);
    statusEl.textContent =
        "READY · 새 주행을 시작하세요.";
});
</script>
</body>
</html>
"""

components.html(html_code, height=720, scrolling=False)

st.caption(
    "DriveMap Virtual Drive · 가상 주행 거리는 게임용 값이며 "
    "실제 이동 거리나 실제 도로 경로를 의미하지 않습니다."
)
