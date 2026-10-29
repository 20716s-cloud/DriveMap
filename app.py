
import json
import time
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
.stApp {
    background: #0a0d12;
    color: #eef3f8;
}
section[data-testid="stSidebar"] {
    background: #10151d;
}
h1, h2, h3 {
    color: #f4f7fb;
}
div[data-testid="stMetric"] {
    background: #141b25;
    border: 1px solid #263344;
    border-radius: 14px;
    padding: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🚘 DriveMap")
st.caption("REAL ROUTE / 3D DRIVE / FUEL ESTIMATOR")
st.divider()

# -----------------------------
# 1. 주행 설정
# -----------------------------
with st.sidebar:
    st.subheader("ROUTE")

    origin_text = st.text_input(
        "출발지", value="수원역"
    )

    destination_text = st.text_input(
        "목적지", value="광교호수공원"
    )

    st.subheader("VEHICLE")

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
        "경로 검색",
        type="primary",
        use_container_width=True
    )


# -----------------------------
# 2. 실제 지도에서 장소 검색
# -----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def find_place(place_name):
    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": "DriveMapSchoolProject/2.0"
    }

    response = requests.get(
        url,
        params={
            "q": place_name + ", South Korea",
            "format": "jsonv2",
            "limit": 1
        },
        headers=headers,
        timeout=20
    )

    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(
            "장소를 찾을 수 없습니다. "
            "더 구체적인 장소명을 입력해 주세요."
        )

    item = results[0]

    return {
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "label": item["display_name"]
    }


# -----------------------------
# 3. 실제 도로 경로 계산
# -----------------------------
@st.cache_data(ttl=900, show_spinner=False)
def find_driving_route(
    start_lon,
    start_lat,
    end_lon,
    end_lat
):
    url = (
        "https://router.project-osrm.org/"
        "route/v1/driving/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
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

    if result.get("code") != "Ok":
        raise ValueError("주행 경로를 찾지 못했습니다.")

    route = result["routes"][0]

    return {
        "distance_m": float(route["distance"]),
        "duration_s": float(route["duration"]),
        "coordinates": route["geometry"]["coordinates"]
    }


# -----------------------------
# 4. 경로 검색 실행
# -----------------------------
if "drive_data" not in st.session_state:
    st.session_state.drive_data = None

if find_button:
    if not origin_text.strip() or not destination_text.strip():
        st.error("출발지와 목적지를 입력해 주세요.")
    else:
        try:
            with st.spinner("실제 도로 경로를 검색 중입니다..."):
                start = find_place(origin_text.strip())
                end = find_place(destination_text.strip())

                route = find_driving_route(
                    start["lon"],
                    start["lat"],
                    end["lon"],
                    end["lat"]
                )

            st.session_state.drive_data = {
                "start": start,
                "end": end,
                "route": route,
                "origin_name": origin_text.strip(),
                "destination_name": destination_text.strip()
            }

        except Exception as error:
            st.error(f"경로 검색 실패: {error}")
            st.info(
                "장소 이름을 구체적으로 입력하거나 "
                "잠시 후 다시 시도해 주세요."
            )


# -----------------------------
# 5. 주행 정보 계산
# -----------------------------
data = st.session_state.drive_data

if data:
    start = data["start"]
    end = data["end"]
    route = data["route"]

    distance_km = route["distance_m"] / 1000
    duration_min = round(route["duration_s"] / 60)

    fuel_used = distance_km / efficiency
    fuel_cost = fuel_used * fuel_price
    remaining_fuel = fuel_liters - fuel_used

    arrival_time = time.strftime(
        "%H:%M",
        time.localtime(time.time() + duration_min * 60)
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "이동 거리",
        f"{distance_km:.1f} km"
    )

    col2.metric(
        "예상 소요 시간",
        f"{duration_min}분"
    )

    col3.metric(
        "예상 연료 소비",
        f"{fuel_used:.2f} L"
    )

    col4.metric(
        "예상 연료비",
        f"{fuel_cost:,.0f}원"
    )

    if remaining_fuel < 0:
        st.warning(
            f"예상 연료가 {-remaining_fuel:.1f}L 부족합니다."
        )
    else:
        st.success(
            f"예상 도착 시각 {arrival_time} · "
            f"도착 시 연료 잔량 {remaining_fuel:.1f}L"
        )

    map_col, view_col = st.columns(2)

    # -----------------------------
    # 6. 실제 지도 표시
    # -----------------------------
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
            popup=data["origin_name"],
            icon=folium.Icon(color="green")
        ).add_to(route_map)

        folium.Marker(
            [end["lat"], end["lon"]],
            tooltip="목적지",
            popup=data["destination_name"],
            icon=folium.Icon(color="red")
        ).add_to(route_map)

        route_map.fit_bounds(route_points)

        st_folium(
            route_map,
            height=430,
            use_container_width=True,
            returned_objects=[]
        )

    # -----------------------------
    # 7. 3D 자동차 주행 화면
    # -----------------------------
    with view_col:
        st.subheader("3D 주행 미리보기")

        route_json = json.dumps(route["coordinates"])

        html = r"""
<div id="dm3d" style="
    height:430px;
    width:100%;
    border-radius:14px;
    overflow:hidden;
    background:#080d14;
    position:relative">
    <div style="
        position:absolute;
        z-index:2;
        top:12px;
        left:12px;
        background:#111b29dd;
        color:#eaf4ff;
        padding:8px 10px;
        border-radius:8px;
        font:12px Arial">
        DRIVEMAP 3D
    </div>
</div>

<script type="module">
import * as THREE from
'https://unpkg.com/three@0.160.0/build/three.module.js';

import { OrbitControls } from
'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';

const root = document.getElementById('dm3d');
const coords = ROUTE_DATA;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080d14);
scene.fog = new THREE.Fog(0x080d14, 90, 300);

const camera = new THREE.PerspectiveCamera(
    55,
    root.clientWidth / root.clientHeight,
    0.1,
    1000
);

camera.position.set(0, 20, 34);

const renderer = new THREE.WebGLRenderer({
    antialias: true
});

renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);

renderer.setSize(
    root.clientWidth,
    root.clientHeight
);

root.appendChild(renderer.domElement);

scene.add(
    new THREE.HemisphereLight(
        0xd7eaff,
        0x1a2430,
        2
    )
);

const light = new THREE.DirectionalLight(
    0xffffff,
    2
);

light.position.set(20, 35, 10);
scene.add(light);

const grid = new THREE.GridHelper(
    260, 52, 0x26384a, 0x172433
);

grid.position.y = -0.06;
scene.add(grid);

// Convert real route coordinates into a 3D path.
const sampled = coords.filter((p, i) =>
    i === 0 ||
    i === coords.length - 1 ||
    i % Math.max(
        1,
        Math.floor(coords.length / 160)
    ) === 0
);

const lon0 = sampled[0][0];
const lat0 = sampled[0][1];

let points = sampled.map(p =>
    new THREE.Vector3(
        (p[0] - lon0) *
            111.32 *
            Math.cos(lat0 * Math.PI / 180),
        0,
        -(p[1] - lat0) * 110.57
    )
);

if (points.length < 2) {
    points = [
        new THREE.Vector3(-20, 0, 0),
        new THREE.Vector3(20, 0, 0)
    ];
}

const bounds = new THREE.Box3().setFromPoints(points);
const center = bounds.getCenter(new THREE.Vector3());

points = points.map(p => p.sub(center));

const curve = new THREE.CatmullRomCurve3(points);
const curvePoints = curve.getPoints(400);

// Build a road ribbon following the route.
const vertices = [];
const indices = [];

for (let i = 0; i < curvePoints.length; i++) {
    const p = curvePoints[i];

    const tangent = curve
        .getTangent(i / (curvePoints.length - 1))
        .normalize();

    const side = new THREE.Vector3(
        -tangent.z, 0, tangent.x
    ).normalize();

    vertices.push(
        p.x + side.x * 3.5, 0.01,
        p.z + side.z * 3.5,

        p.x - side.x * 3.5, 0.01,
        p.z - side.z * 3.5
    );

    if (i < curvePoints.length - 1) {
        const a = i * 2;

        indices.push(
            a, a + 1, a + 2,
            a + 1, a + 3, a + 2
        );
    }
}

const roadGeometry = new THREE.BufferGeometry();

roadGeometry.setAttribute(
    'position',
    new THREE.Float32BufferAttribute(vertices, 3)
);

roadGeometry.setIndex(indices);
roadGeometry.computeVertexNormals();

const road = new THREE.Mesh(
    roadGeometry,
    new THREE.MeshStandardMaterial({
        color: 0x303b48,
        roughness: 0.95,
        side: THREE.DoubleSide
    })
);

scene.add(road);

// Start and destination markers.
function addMarker(point, color) {
    const marker = new THREE.Mesh(
        new THREE.CylinderGeometry(
            0.48, 0.48, 0.24, 20
        ),
        new THREE.MeshStandardMaterial({ color })
    );

    marker.position.set(point.x, 0.24, point.z);
    scene.add(marker);
}

addMarker(curvePoints[0], 0x35df8b);
addMarker(curvePoints[curvePoints.length - 1], 0xff596b);

// Simple 3D car model.
const car = new THREE.Group();

const body = new THREE.Mesh(
    new THREE.BoxGeometry(1.55, 0.55, 2.7),
    new THREE.MeshStandardMaterial({
        color: 0x159cff,
        metalness: 0.25,
        roughness: 0.35
    })
);

body.position.y = 0.7;
car.add(body);

const cabin = new THREE.Mesh(
    new THREE.BoxGeometry(1.08, 0.48, 1.15),
    new THREE.MeshStandardMaterial({
        color: 0x9bdcff,
        roughness: 0.25
    })
);

cabin.position.set(0, 1.16, -0.12);
car.add(cabin);

for (const x of [-0.82, 0.82]) {
    for (const z of [-0.82, 0.82]) {
        const wheel = new THREE.Mesh(
            new THREE.CylinderGeometry(
                0.26, 0.26, 0.18, 16
            ),
            new THREE.MeshStandardMaterial({
                color: 0x080a0d
            })
        );

        wheel.rotation.z = Math.PI / 2;
        wheel.position.set(x, 0.4, z);
        car.add(wheel);
    }
}

scene.add(car);

const controls = new OrbitControls(
    camera,
    renderer.domElement
);

controls.enableDamping = true;

let progress = 0;
let previousTime = performance.now();
let manualCamera = false;

controls.addEventListener(
    'start',
    () => manualCamera = true
);

controls.addEventListener(
    'end',
    () => setTimeout(
        () => manualCamera = false,
        2500
    )
);

function animate(now) {
    requestAnimationFrame(animate);

    const delta = Math.min(
        (now - previousTime) / 1000,
        0.05
    );

    previousTime = now;
    progress = (progress + delta * 0.025) % 1;

    const position = curve.getPointAt(progress);
    const tangent = curve.getTangentAt(progress);

    car.position.set(
        position.x, 0, position.z
    );

    car.rotation.y = Math.atan2(
        tangent.x, tangent.z
    );

    if (!manualCamera) {
        camera.position.lerp(
            new THREE.Vector3(
                position.x + 11,
                14,
                position.z + 17
            ),
            0.02
        );

        controls.target.lerp(position, 0.03);
    }

    controls.update();
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect =
        root.clientWidth / root.clientHeight;

    camera.updateProjectionMatrix();

    renderer.setSize(
        root.clientWidth,
        root.clientHeight
    );
});

animate(performance.now());
</script>
"""

        html = html.replace(
            "ROUTE_DATA",
            route_json
        )

        components.html(
            html,
            height=450,
            scrolling=False
        )

    with st.expander("연료 계산 기준"):
        st.write(
            f"연료 소비량 = {distance_km:.2f} km "
            f"÷ {efficiency:.1f} km/L "
            f"= {fuel_used:.2f} L"
        )

        st.write(
            f"예상 연료비 = {fuel_used:.2f} L "
            f"× {fuel_price:,}원 "
            f"= {fuel_cost:,.0f}원"
        )

        st.write(
            "지도: OpenStreetMap / "
            "경로: OSRM 공개 데모 서버"
        )

        st.caption(
            "교통 체증과 실제 운전 습관은 반영되지 않은 추정치입니다."
        )

else:
    st.subheader("목적지를 입력하고 주행을 시작하세요")

    st.write(
        "왼쪽 메뉴에서 출발지와 목적지를 입력한 다음 "
        "'경로 검색'을 누르세요."
    )

    st.markdown("""
    - 실제 도로 경로와 이동 거리
    - 예상 이동 시간과 도착 시각
    - 예상 연료 소비량과 연료비
    - 경로를 따라 움직이는 3D 자동차
    """)

    st.caption(
        "예시: 수원역 → 광교호수공원"
    )

st.divider()

st.caption(
    "DriveMap은 학습용 프로토타입입니다. "
    "실제 운전 중에는 화면을 조작하지 마세요."
)
