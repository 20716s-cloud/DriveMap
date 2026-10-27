
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DriveMap | GPS Drive",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚗 DriveMap")
st.caption("REAL GPS TRACKING · YOUR JOURNEY")

st.info(
    "휴대폰에서 위치 권한을 허용하면 현재 위치와 이동 경로를 "
    "지도에 표시합니다. 처음에는 정차 상태에서 테스트하세요."
)

html_code = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link
 rel="stylesheet"
 href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #10151d;
    color: white;
}

.panel {
    padding: 16px;
    background: #171f2b;
    border: 1px solid #2d394a;
    border-radius: 14px;
    margin-bottom: 12px;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
}

.label {
    font-size: 12px;
    color: #9eafc3;
    margin-bottom: 8px;
}

.value {
    font-size: clamp(16px, 4vw, 24px);
    font-weight: bold;
    overflow-wrap: anywhere;
}

.unit {
    font-size: 12px;
    color: #9eafc3;
}

#map {
    width: 100%;
    height: 420px;
    border-radius: 14px;
    border: 1px solid #2d394a;
}

.buttons {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}

button {
    flex: 1;
    padding: 13px 8px;
    border: 0;
    border-radius: 9px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
}

#start {
    background: #49dfac;
    color: #10251f;
}

#stop, #reset {
    background: #293647;
    color: white;
}

#status {
    font-size: 13px;
    line-height: 1.6;
    color: #aabbd0;
    margin-top: 12px;
}

.car-icon {
    font-size: 30px;
    line-height: 36px;
    text-align: center;
    filter: drop-shadow(0 2px 3px #0008);
}

@media (max-width: 480px) {
    #map { height: 380px; }
    .panel { padding: 12px; }
}
</style>
</head>

<body>
<div class="panel">
    <div class="stats">
        <div>
            <div class="label">주행 거리</div>
            <div class="value"><span id="distance">0.00</span>
                <span class="unit">km</span>
            </div>
        </div>

        <div>
            <div class="label">주행 시간</div>
            <div class="value" id="duration">00:00</div>
        </div>

        <div>
            <div class="label">GPS 정확도</div>
            <div class="value" id="accuracy">--</div>
            <div class="unit">미터</div>
        </div>
    </div>

    <div class="buttons">
        <button id="start">▶ 주행 시작</button>
        <button id="stop">■ 주행 종료</button>
        <button id="reset">↻ 초기화</button>
    </div>

    <div id="status">
        준비 완료 · 주행 시작을 누르면 GPS 권한을 요청합니다.
    </div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
const statusEl = document.getElementById("status");
const distanceEl = document.getElementById("distance");
const durationEl = document.getElementById("duration");
const accuracyEl = document.getElementById("accuracy");

const map = L.map("map").setView([36.5, 127.8], 7);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(map);

const carIcon = L.divIcon({
    className: "car-icon",
    html: "🚗",
    iconSize: [38, 38],
    iconAnchor: [19, 19]
});

let carMarker = null;
let routeLine = L.polyline([], {
    color: "#16a5ff",
    weight: 5,
    opacity: 0.9
}).addTo(map);

let routePoints = [];
let watchId = null;
let startedAt = null;
let elapsedBeforePause = 0;
let timerId = null;
let lastPoint = null;
let totalMeters = 0;
let tracking = false;

function distanceBetween(a, b) {
    const R = 6371000;
    const rad = x => x * Math.PI / 180;

    const dLat = rad(b.lat - a.lat);
    const dLon = rad(b.lng - a.lng);

    const x =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(rad(a.lat)) *
        Math.cos(rad(b.lat)) *
        Math.sin(dLon / 2) ** 2;

    return 2 * R * Math.atan2(
        Math.sqrt(x),
        Math.sqrt(1 - x)
    );
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const hours = Math.floor(mins / 60);

    if (hours > 0) {
        return String(hours).padStart(2, "0") + ":" +
            String(mins % 60).padStart(2, "0") + ":" +
            String(secs).padStart(2, "0");
    }

    return String(mins).padStart(2, "0") + ":" +
        String(secs).padStart(2, "0");
}

function updateTimer() {
    const elapsed = elapsedBeforePause +
        (startedAt ? (Date.now() - startedAt) / 1000 : 0);

    durationEl.textContent = formatTime(elapsed);
}

function onPosition(position) {
    if (!tracking) return;

    const coords = position.coords;

    const point = {
        lat: coords.latitude,
        lng: coords.longitude
    };

    accuracyEl.textContent = Math.round(coords.accuracy);

    if (coords.accuracy > 50) {
        statusEl.textContent =
            "GPS 정확도가 낮습니다. 더 정확한 위치를 기다리고 있어요.";
        return;
    }

    if (lastPoint) {
        const segment = distanceBetween(lastPoint, point);

        // GPS 오차로 인한 작은 흔들림을 줄입니다.
        if (segment < 3) return;

        // 큰 GPS 점프는 자동으로 경로에 추가하지 않습니다.
        if (segment > 500) {
            statusEl.textContent =
                "위치가 크게 변경되어 해당 지점을 건너뛰었습니다.";
            return;
        }

        totalMeters += segment;
    }

    lastPoint = point;
    routePoints.push([point.lat, point.lng]);

    if (!carMarker) {
        carMarker = L.marker(point, { icon: carIcon }).addTo(map);
        map.setView(point, 16);
    } else {
        carMarker.setLatLng(point);
    }

    routeLine.setLatLngs(routePoints);

    distanceEl.textContent = (totalMeters / 1000).toFixed(2);

    // 처음에는 현재 위치를 따라가고,
    // 사용자가 지도를 움직이면 자동 이동을 멈춥니다.
    if (routePoints.length === 1) {
        map.setView(point, 16);
    }

    statusEl.textContent =
        "GPS 추적 중 · 위치 정확도 약 " +
        Math.round(coords.accuracy) + "m";
}

function onGpsError(error) {
    const messages = {
        1: "위치 권한이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해 주세요.",
        2: "현재 위치를 확인할 수 없습니다. GPS를 확인해 주세요.",
        3: "GPS 응답 시간이 초과되었습니다. 다시 시도해 주세요."
    };

    statusEl.textContent =
        messages[error.code] || "GPS를 사용할 수 없습니다.";
}

document.getElementById("start").onclick = function () {
    if (!navigator.geolocation) {
        statusEl.textContent =
            "이 브라우저는 GPS 위치 기능을 지원하지 않습니다.";
        return;
    }

    if (tracking) return;

    tracking = true;
    startedAt = Date.now();

    statusEl.textContent = "위치 권한을 확인하고 있습니다.";

    watchId = navigator.geolocation.watchPosition(
        onPosition,
        onGpsError,
        {
            enableHighAccuracy: true,
            maximumAge: 1000,
            timeout: 20000
        }
    );

    timerId = setInterval(updateTimer, 1000);
};

document.getElementById("stop").onclick = function () {
    if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }

    if (startedAt) {
        elapsedBeforePause += (Date.now() - startedAt) / 1000;
        startedAt = null;
    }

    tracking = false;

    if (timerId) {
        clearInterval(timerId);
        timerId = null;
    }

    updateTimer();
    statusEl.textContent =
        "주행 추적을 종료했습니다. 기록은 현재 화면에만 남아 있습니다.";
};

document.getElementById("reset").onclick = function () {
    if (tracking) {
        statusEl.textContent = "초기화하려면 먼저 주행을 종료하세요.";
        return;
    }

    routePoints = [];
    lastPoint = null;
    totalMeters = 0;
    elapsedBeforePause = 0;
    startedAt = null;

    distanceEl.textContent = "0.00";
    durationEl.textContent = "00:00";
    accuracyEl.textContent = "--";

    routeLine.setLatLngs([]);

    if (carMarker) {
        map.removeLayer(carMarker);
        carMarker = null;
    }

    map.setView([36.5, 127.8], 7);
    statusEl.textContent = "새 주행을 시작할 준비가 되었습니다.";
};
</script>
</body>
</html>
"""

components.html(html_code, height=660, scrolling=False)

st.caption(
    "DriveMap 초기 GPS 버전 · 위치 권한이 필요합니다. "
    "주행 기록은 현재 화면에만 저장되며 새로고침하면 사라집니다."
)
