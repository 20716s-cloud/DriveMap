import json
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="DriveMap Drive",
    page_icon="🚘",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #090d13;
    color: #eef3f8;
}
section[data-testid="stSidebar"] {
    background: #101722;
}
h1, h2, h3 {
    color: #f4f7fb;
}
div[data-testid="stMetric"] {
    background: #141c27;
    border: 1px solid #273546;
    border-radius: 14px;
    padding: 12px;
}
div.stButton > button {
    border-radius: 10px;
    min-height: 44px;
}
</style>
""", unsafe_allow_html=True)

st.title("🚘 DriveMap | Drive Mode")
st.caption("직접 운전 · 실제 도로 경로 · 거리 · 시간 · 연료 추정")
st.divider()

with st.sidebar:
    st.subheader("목적지 설정")

    origin_text = st.text_input("출발지", "수원역")
    destination_text = st.text_input("목적지", "광교호수공원")

    st.subheader("차량 설정")

    efficiency = st.number_input(
        "연비 (km/L)",
        min_value=1.0,
        max_value=60.0,
        value=12.0,
        step=0.5
    )

    fuel_liters = st.number_input(
        "현재 연료량 (L)",
        min_value=0.0,
        max_value=200.0,
        value=35.0,
        step=1.0
    )

    fuel_price = st.number_input(
        "연료 가격 (원/L)",
        min_value=500,
        max_value=5000,
        value=1700,
        step=50
    )

    find_button = st.button(
        "경로 검색 및 운전 시작",
        type="primary",
        use_container_width=True
    )


@st.cache_data(ttl=3600, show_spinner=False)
def find_place(name):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": name + ", South Korea",
            "format": "jsonv2",
            "limit": 1
        },
        headers={
            "User-Agent": "DriveMapSchoolProject/3.0"
        },
        timeout=20
    )

    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(f"장소를 찾지 못했습니다: {name}")

    place = results[0]

    return {
        "lat": float(place["lat"]),
        "lon": float(place["lon"]),
        "label": place["display_name"]
    }


@st.cache_data(ttl=900, show_spinner=False)
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
        raise ValueError("이 구간의 운전 경로를 찾지 못했습니다.")

    route = result["routes"][0]

    return {
        "distance_m": float(route["distance"]),
        "duration_s": float(route["duration"]),
        "coordinates": route["geometry"]["coordinates"]
    }


if "drive_data" not in st.session_state:
    st.session_state.drive_data = None


if find_button:
    try:
        if not origin_text.strip() or not destination_text.strip():
            raise ValueError("출발지와 목적지를 모두 입력해 주세요.")

        with st.spinner("실제 도로 경로를 검색하고 있습니다..."):
            start = find_place(origin_text.strip())
            end = find_place(destination_text.strip())

            route = get_route(
                start["lon"],
                start["lat"],
                end["lon"],
                end["lat"]
            )

        st.session_state.drive_data = {
            "start": start,
            "end": end,
            "route": route,
            "origin": origin_text.strip(),
            "destination": destination_text.strip()
        }

    except Exception as e:
        st.error(f"경로 검색 실패: {e}")
        st.info("장소명을 더 구체적으로 입력하거나 잠시 후 다시 시도해 주세요.")


data = st.session_state.drive_data


if data:
    start = data["start"]
    end = data["end"]
    route = data["route"]

    distance_km = route["distance_m"] / 1000
    base_minutes = route["duration_s"] / 60
    fuel_estimate = distance_km / efficiency
    cost_estimate = fuel_estimate * fuel_price

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("실제 도로 거리", f"{distance_km:.1f} km")
    col2.metric("기본 예상 시간", f"{int(base_minutes)}분")
    col3.metric("예상 연료 소비", f"{fuel_estimate:.2f} L")
    col4.metric("예상 연료비", f"{cost_estimate:,.0f}원")

    st.markdown("### 직접 운전하기")

    st.markdown(
        "**조작법:** `W` 또는 `↑` 가속 · "
        "`S` 또는 `↓` 브레이크 · "
        "`A`/`D` 또는 `←`/`→` 조향 · "
        "`Space` 브레이크"
    )

    coords_json = json.dumps(route["coordinates"])

    config_json = json.dumps({
        "distanceKm": distance_km,
        "durationMin": base_minutes,
        "efficiency": efficiency,
        "fuelLiters": fuel_liters,
        "fuelPrice": fuel_price,
        "origin": data["origin"],
        "destination": data["destination"]
    })

    game_html = r"""
<div id="driveGame" style="
    width:100%;
    background:#070b11;
    border-radius:16px;
    overflow:hidden;
    position:relative;
    font-family:Arial,sans-serif;
    color:#f5f8fc;
">
    <div style="position:relative;height:520px">
        <canvas id="screen" style="
            display:block;
            width:100%;
            height:100%;
        "></canvas>

        <div style="
            position:absolute;
            top:12px;
            left:12px;
            background:#101925dd;
            padding:10px 12px;
            border-radius:10px;
            font-size:13px;
        ">
            <b>DRIVEMAP · COCKPIT VIEW</b><br>
            <span id="status">READY</span>
        </div>

        <div style="
            position:absolute;
            top:12px;
            right:12px;
            background:#101925dd;
            padding:10px 12px;
            border-radius:10px;
            text-align:right;
            font-size:13px;
        ">
            <div>SPEED <b><span id="speed">0</span> km/h</b></div>
            <div>FUEL <b><span id="fuel">--</span> L</b></div>
        </div>

        <div style="
            position:absolute;
            bottom:12px;
            left:12px;
            right:12px;
            display:flex;
            justify-content:space-between;
            gap:8px;
            pointer-events:none;
        ">
            <div style="
                background:#101925dd;
                padding:8px 10px;
                border-radius:9px;
                font-size:12px;
            ">
                거리 <b id="leftDist">--</b>
            </div>

            <div style="
                background:#101925dd;
                padding:8px 10px;
                border-radius:9px;
                font-size:12px;
            ">
                예상 연료비 <b id="liveCost">--</b>
            </div>
        </div>
    </div>

    <div style="
        padding:12px;
        display:flex;
        align-items:center;
        justify-content:center;
        gap:10px;
        flex-wrap:wrap;
        background:#0e141d;
    ">
        <button data-key="ArrowLeft" style="
            width:64px;height:52px;
            border:1px solid #334459;
            background:#1a2635;
            color:white;border-radius:12px;
            font-size:22px;
        ">◀</button>

        <button data-key="ArrowDown" style="
            width:64px;height:52px;
            border:1px solid #334459;
            background:#1a2635;
            color:white;border-radius:12px;
            font-size:20px;
        ">▼</button>

        <button data-key="ArrowUp" style="
            width:76px;height:52px;
            border:1px solid #1687d9;
            background:#0878c8;
            color:white;border-radius:12px;
            font-size:20px;
        ">▲ 가속</button>

        <button data-key="ArrowRight" style="
            width:64px;height:52px;
            border:1px solid #334459;
            background:#1a2635;
            color:white;border-radius:12px;
            font-size:22px;
        ">▶</button>

        <button id="reset" style="
            height:52px;padding:0 16px;
            border:1px solid #7e3b42;
            background:#452027;
            color:white;border-radius:12px;
        ">다시 시작</button>
    </div>

    <div style="
        padding:0 14px 14px;
        background:#0e141d;
        color:#9daec1;
        font-size:12px;
    ">
        키보드: W/↑ 가속 · S/↓ 감속 · A/← 왼쪽 ·
        D/→ 오른쪽 · Space 브레이크.
        화면을 한 번 클릭한 뒤 키보드를 사용하세요.
    </div>
</div>

<script>
(() => {
    const canvas = document.getElementById('screen');
    const ctx = canvas.getContext('2d');

    const coords = ROUTE_DATA;
    const cfg = CONFIG_DATA;

    const $ = id => document.getElementById(id);

    let keys = {};
    let speed = 0;
    let lateral = 0;
    let progress = 0;
    let fuel = cfg.fuelLiters;
    let last = performance.now();
    let steer = 0;

    const path = [];

    const sample = coords.filter((p, i) =>
        i === 0 ||
        i === coords.length - 1 ||
        i % Math.max(1, Math.floor(coords.length / 500)) === 0
    );

    const lon0 = sample[0][0];
    const lat0 = sample[0][1];
    const cos = Math.cos(lat0 * Math.PI / 180);

    for (const p of sample) {
        path.push({
            x: (p[0] - lon0) * 111320 * cos,
            y: (p[1] - lat0) * 110570
        });
    }

    let lengths = [0];
    let total = 0;

    for (let i = 1; i < path.length; i++) {
        total += Math.hypot(
            path[i].x - path[i - 1].x,
            path[i].y - path[i - 1].y
        );

        lengths.push(total);
    }

    function resize() {
        const r = canvas.getBoundingClientRect();

        canvas.width = Math.max(320, r.width * devicePixelRatio);
        canvas.height = Math.max(260, r.height * devicePixelRatio);

        ctx.setTransform(
            devicePixelRatio,
            0,
            0,
            devicePixelRatio,
            0,
            0
        );
    }

    window.addEventListener('resize', resize);
    resize();

    function keyDown(e) {
        if (
            ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' ']
                .includes(e.key) ||
            e.code === 'Space'
        ) {
            e.preventDefault();
        }

        keys[e.key.toLowerCase()] = true;

        if (e.code === 'Space') {
            keys.space = true;
        }
    }

    function keyUp(e) {
        keys[e.key.toLowerCase()] = false;

        if (e.code === 'Space') {
            keys.space = false;
        }
    }

    window.addEventListener('keydown', keyDown);
    window.addEventListener('keyup', keyUp);

    canvas.tabIndex = 0;

    canvas.addEventListener('click', () => canvas.focus());

    document.querySelectorAll('[data-key]').forEach(btn => {
        const k = btn.dataset.key.toLowerCase();

        const down = e => {
            e.preventDefault();
            keys[k] = true;
        };

        const up = e => {
            e.preventDefault();
            keys[k] = false;
        };

        btn.addEventListener('pointerdown', down);
        btn.addEventListener('pointerup', up);
        btn.addEventListener('pointerleave', up);
        btn.addEventListener('pointercancel', up);
    });

    $('reset').addEventListener('click', () => {
        speed = 0;
        lateral = 0;
        progress = 0;
        fuel = cfg.fuelLiters;
    });

    function draw(now) {
        const dt = Math.min((now - last) / 1000, 0.05);
        last = now;

        const up = keys.w || keys.arrowup;
        const down = keys.s || keys.arrowdown || keys.space;

        const left = keys.a || keys.arrowleft;
        const right = keys.d || keys.arrowright;

        if (up) {
            speed = Math.min(150, speed + 42 * dt);
        } else {
            speed = Math.max(0, speed - 10 * dt);
        }

        if (down) {
            speed = Math.max(0, speed - 75 * dt);
        }

        steer = (right ? 1 : 0) - (left ? 1 : 0);

        lateral += steer * dt * (0.6 + speed / 55);
        lateral *= Math.pow(0.985, dt * 60);

        progress = Math.min(
            1,
            progress + (speed / 3.6) * dt / Math.max(total, 1)
        );

        fuel = Math.max(
            0,
            fuel - (
                speed > 0
                    ? (speed / 3.6 / Math.max(cfg.efficiency, 1))
                      * dt / 3600
                    : 0
            )
        );

        const w = canvas.clientWidth;
        const h = canvas.clientHeight;

        ctx.clearRect(0, 0, w, h);

        // 하늘
        const sky = ctx.createLinearGradient(0, 0, 0, h * 0.65);
        sky.addColorStop(0, '#172b43');
        sky.addColorStop(1, '#9db5c6');

        ctx.fillStyle = sky;
        ctx.fillRect(0, 0, w, h * 0.62);

        // 지면
        ctx.fillStyle = '#203a32';
        ctx.fillRect(0, h * 0.62, w, h * 0.38);

        // 먼 배경
        ctx.fillStyle = '#314a4d';
        ctx.beginPath();
        ctx.moveTo(0, h * 0.62);

        for (let x = 0; x <= w + 40; x += 40) {
            ctx.lineTo(
                x,
                h * (0.46 + Math.sin(x * 0.013) * 0.035)
            );
        }

        ctx.lineTo(w, h * 0.62);
        ctx.closePath();
        ctx.fill();

        // 도로
        const horizon = h * 0.42;
        const bottom = h * 1.04;
        const center = w * 0.5 - lateral * 24;

        ctx.fillStyle = '#303944';
        ctx.beginPath();
        ctx.moveTo(center - w * 0.09, horizon);
        ctx.lineTo(center + w * 0.09, horizon);
        ctx.lineTo(center + w * 0.72, bottom);
        ctx.lineTo(center - w * 0.72, bottom);
        ctx.closePath();
        ctx.fill();

        // 도로 가장자리
        ctx.strokeStyle = '#e8edf2';
        ctx.lineWidth = 3;
        ctx.beginPath();

        ctx.moveTo(center - w * 0.09, horizon);
        ctx.lineTo(center - w * 0.72, bottom);

        ctx.moveTo(center + w * 0.09, horizon);
        ctx.lineTo(center + w * 0.72, bottom);

        ctx.stroke();

        // 차선
        for (let i = 0; i < 10; i++) {
            const z = (
                (i / 10 + (progress * speed / 110)) % 1
            );

            const y = horizon + (bottom - horizon) * z * z;
            const dashH = 2 + z * 25;

            ctx.fillStyle = '#f5f4dc';

            ctx.fillRect(
                center,
                y - dashH / 2,
                Math.max(1, z * 4),
                dashH
            );
        }

        // 도로 주변 나무
        for (let i = 0; i < 12; i++) {
            const z = ((i / 12 + progress * 0.5) % 1);
            const y = horizon + (bottom - horizon) * z * z;
            const dx = w * 0.12 + w * 0.5 * z * z;
            const size = 5 + z * 26;

            ctx.fillStyle = i % 2 ? '#1b322c' : '#28463a';

            ctx.beginPath();
            ctx.moveTo(center - dx, y);
            ctx.lineTo(center - dx - size * 0.35, y - size);
            ctx.lineTo(center - dx + size * 0.35, y - size);
            ctx.closePath();
            ctx.fill();

            ctx.beginPath();
            ctx.moveTo(center + dx, y);
            ctx.lineTo(center + dx - size * 0.35, y - size);
            ctx.lineTo(center + dx + size * 0.35, y - size);
            ctx.closePath();
            ctx.fill();
        }

        // 운전석 대시보드
        ctx.fillStyle = '#111923';
        ctx.beginPath();
        ctx.moveTo(0, h * 0.88);
        ctx.quadraticCurveTo(w * 0.5, h * 0.76, w, h * 0.88);
        ctx.lineTo(w, h);
        ctx.lineTo(0, h);
        ctx.closePath();
        ctx.fill();

        // 계기판
        ctx.fillStyle = '#273443';
        ctx.beginPath();
        ctx.ellipse(
            w * 0.5,
            h * 0.91,
            w * 0.19,
            h * 0.12,
            0,
            Math.PI,
            Math.PI * 2
        );
        ctx.fill();

        // 핸들
        ctx.strokeStyle = '#070b10';
        ctx.lineWidth = Math.max(8, w * 0.018);

        ctx.beginPath();
        ctx.ellipse(
            w * 0.5,
            h * 0.98,
            w * 0.12,
            h * 0.13,
            steer * 0.12,
            Math.PI * 1.08,
            Math.PI * 1.92
        );
        ctx.stroke();

        ctx.strokeStyle = '#3c4c5e';
        ctx.lineWidth = 3;

        ctx.beginPath();
        ctx.moveTo(w * 0.5, h * 0.98);
        ctx.lineTo(w * 0.5 - steer * 25, h * 0.91);

        ctx.moveTo(w * 0.5, h * 0.98);
        ctx.lineTo(w * 0.5 + steer * 25, h * 0.91);

        ctx.stroke();

        // 주행 정보
        const remaining = Math.max(
            0,
            cfg.distanceKm * (1 - progress)
        );

        $('speed').textContent = Math.round(speed);
        $('fuel').textContent = fuel.toFixed(1);
        $('leftDist').textContent = remaining.toFixed(1) + ' km';

        $('liveCost').textContent = Math.round(
            (cfg.fuelLiters - fuel) * cfg.fuelPrice
        ).toLocaleString() + '원';

        $('status').textContent =
            progress >= 1
                ? '목적지 도착'
                : speed > 0
                    ? '주행 중'
                    : '정차 중';

        // 미니맵
        const bx = 14;
        const by = h - 84;
        const bw = 105;
        const bh = 48;

        ctx.fillStyle = '#0b121bcc';
        ctx.fillRect(bx, by, bw, bh);

        ctx.strokeStyle = '#41b8ff';
        ctx.lineWidth = 2;
        ctx.beginPath();

        for (
            let i = 0;
            i < path.length;
            i += Math.max(1, Math.floor(path.length / 80))
        ) {
            const p = path[i];

            const x = bx + bw / 2 + (p.x - path[0].x) * 0.001;
            const y = by + bh / 2 - (p.y - path[0].y) * 0.001;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.stroke();

        ctx.fillStyle = '#5df0a2';
        ctx.beginPath();

        ctx.arc(
            bx + 12 + progress * (bw - 24),
            by + bh / 2,
            4,
            0,
            Math.PI * 2
        );

        ctx.fill();

        requestAnimationFrame(draw);
    }

    requestAnimationFrame(draw);
})();
</script>
"""

    game_html = (
        game_html
        .replace("ROUTE_DATA", coords_json)
        .replace("CONFIG_DATA", config_json)
    )

    components.html(game_html, height=680, scrolling=False)

    map_col, details_col = st.columns([1.15, 0.85])

    with map_col:
        st.subheader("실제 도로 경로")

        route_map = folium.Map(
            location=[start["lat"], start["lon"]],
            zoom_start=12,
            tiles="OpenStreetMap"
        )

        route_points = [
            (lat, lon)
            for lon, lat in route["coordinates"]
        ]

        folium.PolyLine(
            route_points,
            color="#159cff",
            weight=6,
            opacity=0.9
        ).add_to(route_map)

        folium.Marker(
            [start["lat"], start["lon"]],
            tooltip="출발지",
            popup=data["origin"],
            icon=folium.Icon(color="green")
        ).add_to(route_map)

        folium.Marker(
            [end["lat"], end["lon"]],
            tooltip="목적지",
            popup=data["destination"],
            icon=folium.Icon(color="red")
        ).add_to(route_map)

        route_map.fit_bounds(route_points)

        st_folium(
            route_map,
            height=420,
            use_container_width=True,
            returned_objects=[]
        )

    with details_col:
        st.subheader("주행 정보")

        st.write(f"**출발:** {data['origin']}")
        st.write(f"**목적지:** {data['destination']}")
        st.write(f"**도로 거리:** {distance_km:.1f} km")
        st.write(f"**기본 예상 시간:** 약 {int(base_minutes)}분")
        st.write(f"**예상 연료 소비:** {fuel_estimate:.2f} L")
        st.write(f"**예상 연료비:** {cost_estimate:,.0f}원")

        st.caption(
            "게임 내 속도와 조향은 시뮬레이션입니다. "
            "실제 교통 상황에 따라 이동 시간은 달라집니다."
        )

else:
    st.subheader("경로를 검색해 운전을 시작하세요")

    st.write(
        "왼쪽에서 출발지와 목적지를 입력한 뒤 "
        "**경로 검색 및 운전 시작**을 누르세요."
    )

    st.markdown("""
    - **1인칭 운전석 화면**에서 키보드 또는 화면 버튼으로 직접 조작
    - 실제 도로 지도와 목적지 경로 표시
    - 남은 거리, 예상 시간, 연료 소비량과 비용 계산
    """)

    st.info("예시: 수원역 → 광교호수공원")

st.divider()

st.caption(
    "DriveMap은 학습용 주행 시뮬레이터입니다. "
    "실제 운전 중에는 사용하지 마세요."
)
