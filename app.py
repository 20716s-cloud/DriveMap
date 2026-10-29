
import json
import math
import requests
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="DriveMap | Kart Drive",
    page_icon="🏎️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #0b0e13;
    color: #f4f6fa;
}
[data-testid="stSidebar"] {
    background: #121720;
}
h1, h2, h3, p, label {
    color: #f4f6fa;
}
div.stButton > button {
    background: #e7ff4f;
    color: #111;
    border: none;
    border-radius: 10px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

st.title("🏎️ DriveMap")
st.caption("PLAN YOUR ROUTE · START YOUR ENGINE")

# -------------------------------
# 실제 출발지 / 도착지 검색
# -------------------------------

def geocode(place):
    url = "https://nominatim.openstreetmap.org/search"
    response = requests.get(
        url,
        params={"q": place, "format": "jsonv2", "limit": 1},
        headers={"User-Agent": "DriveMapStudentProject/1.0"},
        timeout=15
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        return None

    return [
        float(results[0]["lat"]),
        float(results[0]["lon"]),
        results[0]["display_name"]
    ]


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
            "steps": "false"
        },
        timeout=25
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route = data["routes"][0]

    return {
        "distance_km": route["distance"] / 1000,
        "duration_min": route["duration"] / 60,
        "coordinates": [
            [point[1], point[0]]
            for point in route["geometry"]["coordinates"]
        ]
    }


with st.sidebar:
    st.header("🗺️ ROUTE SETUP")
    start_text = st.text_input(
        "출발지",
        placeholder="예: 수원역"
    )
    end_text = st.text_input(
        "도착지",
        placeholder="예: 에버랜드"
    )
    fuel_price = st.number_input(
        "휘발유 가격 (원/L)",
        min_value=0,
        value=1700,
        step=10
    )
    fuel_efficiency = st.number_input(
        "연비 (km/L)",
        min_value=1.0,
        value=12.0,
        step=0.5
    )

    search_clicked = st.button(
        "경로 검색",
        use_container_width=True
    )

if search_clicked:
    if not start_text.strip() or not end_text.strip():
        st.error("출발지와 도착지를 모두 입력해 주세요.")
    else:
        try:
            with st.spinner("실제 경로를 검색하고 있습니다..."):
                start_point = geocode(start_text.strip())
                end_point = geocode(end_text.strip())

                if not start_point or not end_point:
                    st.error(
                        "장소를 찾지 못했습니다. "
                        "더 구체적인 주소나 장소명을 입력해 주세요."
                    )
                else:
                    route_data = get_route(start_point, end_point)

                    if not route_data:
                        st.error("경로를 찾지 못했습니다.")
                    else:
                        st.session_state["route_data"] = route_data
                        st.session_state["start_point"] = start_point
                        st.session_state["end_point"] = end_point
                        st.session_state["start_text"] = start_text
                        st.session_state["end_text"] = end_text
                        st.session_state["fuel_price"] = fuel_price
                        st.session_state["fuel_efficiency"] = fuel_efficiency

        except requests.RequestException:
            st.error(
                "경로 검색 서버에 연결하지 못했습니다. "
                "잠시 후 다시 시도해 주세요."
            )

# -------------------------------
# 경로 정보
# -------------------------------

route_data = st.session_state.get("route_data")

if not route_data:
    st.markdown("## 당신의 다음 드라이브를 시작하세요.")
    st.write(
        "왼쪽에서 출발지와 도착지를 입력하고 경로를 검색해 주세요. "
        "검색이 완료되면 게임 화면과 실제 경로 정보를 확인할 수 있습니다."
    )
    st.info(
        "게임 도로는 가상으로 생성됩니다. "
        "실제 경로는 거리 계산과 지도 표시를 위해 사용됩니다."
    )
    st.stop()

distance = route_data["distance_km"]
duration = route_data["duration_min"]
fuel_cost = (
    distance / st.session_state["fuel_efficiency"]
) * st.session_state["fuel_price"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("ROUTE DISTANCE", f"{distance:.1f} km")
m2.metric("EST. TIME", f"{duration:.0f} min")
m3.metric("EST. FUEL COST", f"{fuel_cost:,.0f}원")
m4.metric("GAME MODE", "ARCADE")

st.divider()

# -------------------------------
# 아케이드 카트 게임
# -------------------------------

st.subheader("🏁 ARCADE DRIVE")
st.caption(
    "조작: ← → 또는 A/D · 가속: ↑ 또는 W · 감속: ↓ 또는 S · "
    "게임 화면을 한 번 클릭한 후 조작하세요."
)

game_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    background: #090d12;
    color: white;
    font-family: Arial, sans-serif;
    overflow: hidden;
}
#wrap {
    width: 100%;
    position: relative;
    border-radius: 14px;
    overflow: hidden;
    background: #101820;
}
canvas {
    display: block;
    width: 100%;
    height: 520px;
    outline: none;
}
#hud {
    position: absolute;
    inset: 12px 12px auto 12px;
    display: flex;
    justify-content: space-between;
    gap: 8px;
    pointer-events: none;
}
.panel {
    background: rgba(8,12,18,.78);
    border: 1px solid rgba(255,255,255,.15);
    padding: 10px 13px;
    border-radius: 10px;
    min-width: 90px;
}
.small {
    font-size: 10px;
    color: #aab5c5;
    letter-spacing: 1px;
}
.value {
    font-size: 20px;
    font-weight: 900;
    margin-top: 3px;
}
#bottom {
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}
#bar {
    height: 7px;
    background: #333c47;
    border-radius: 20px;
    flex: 1;
    overflow: hidden;
}
#progress {
    height: 100%;
    width: 0%;
    background: #e7ff4f;
}
#overlay {
    position: absolute;
    inset: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    background: rgba(4,8,13,.62);
}
#card {
    text-align: center;
    padding: 25px;
    width: min(360px, 90%);
    border: 1px solid #3b4654;
    background: rgba(14,19,27,.95);
    border-radius: 16px;
}
#card h1 { margin: 0 0 8px; font-size: 30px; }
#card p { color: #b9c3d0; font-size: 13px; line-height: 1.6; }
button {
    border: 0;
    background: #e7ff4f;
    color: #111;
    border-radius: 9px;
    font-weight: 900;
    padding: 12px 20px;
    cursor: pointer;
    font-size: 14px;
}
#controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    padding: 10px;
    background: #0d1219;
}
.control {
    background: #202936;
    color: white;
    border: 1px solid #3a4656;
    border-radius: 10px;
    width: 58px;
    height: 44px;
    font-size: 20px;
    touch-action: none;
    user-select: none;
}
#hint {
    font-size: 11px;
    color: #9da9b8;
    text-align: center;
    padding: 0 8px 10px;
    background: #0d1219;
}
@media(max-width:600px) {
    canvas { height: 440px; }
    .panel { min-width: 0; padding: 7px; }
    .value { font-size: 16px; }
    .small { font-size: 8px; }
}
</style>
</head>
<body>
<div id="wrap">
    <canvas id="game" tabindex="0"></canvas>
    <div id="hud">
        <div class="panel">
            <div class="small">SPEED</div>
            <div class="value"><span id="speed">0</span> <span style="font-size:11px">km/h</span></div>
        </div>
        <div class="panel">
            <div class="small">FUEL</div>
            <div class="value"><span id="fuel">100</span>%</div>
        </div>
        <div class="panel">
            <div class="small">DISTANCE</div>
            <div class="value"><span id="remain">--</span> km</div>
        </div>
    </div>
    <div id="bottom">
        <span class="small">ROUTE</span>
        <div id="bar"><div id="progress"></div></div>
        <span id="percent" class="small">0%</span>
    </div>
    <div id="overlay">
        <div id="card">
            <h1 id="headline">READY, DRIVER?</h1>
            <p id="message">가속 페달을 밟고 도로 위를 달려보세요.<br>다른 차량과 도로 가장자리를 조심하세요.</p>
            <button id="start">START RACE →</button>
        </div>
    </div>
</div>
<div id="controls">
    <button class="control" id="left">◀</button>
    <button class="control" id="brake">▼</button>
    <button class="control" id="gas">▲</button>
    <button class="control" id="right">▶</button>
</div>
<div id="hint">W / ↑ 가속 · S / ↓ 감속 · A / ← 좌회전 · D / → 우회전</div>

<script>
const DISTANCE = __DISTANCE__;
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

let W = 900, H = 520;
let running = false;
let finished = false;
let speed = 0;
let fuel = 100;
let progress = 0;
let playerX = 0;
let roadPhase = 0;
let elapsed = 0;
let lastTime = 0;
let traffic = [];
let keys = {};
let steering = 0;

function resize() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    W = Math.max(320, rect.width);
    H = Math.max(350, rect.height);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
window.addEventListener("resize", resize);
resize();

function roadCenter(y) {
    const t = 1 - y / H;
    return W * 0.5 +
        Math.sin(roadPhase + t * 2.4) * W * 0.11 * t +
        Math.sin(roadPhase * 0.5 + t * 5) * W * 0.035 * t;
}
function roadHalf(y) {
    const t = 1 - y / H;
    return W * (0.09 + 0.39 * t);
}
function polygon(points, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i=1; i<points.length; i++) ctx.lineTo(points[i][0], points[i][1]);
    ctx.closePath();
    ctx.fill();
}
function drawTree(x,y,s) {
    ctx.fillStyle = "#563b28";
    ctx.fillRect(x-s*.08,y,s*.16,s*.45);
    ctx.fillStyle = "#176d46";
    ctx.beginPath();
    ctx.moveTo(x,y-s*.65);
    ctx.lineTo(x-s*.36,y+s*.08);
    ctx.lineTo(x+s*.36,y+s*.08);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "#278b50";
    ctx.beginPath();
    ctx.moveTo(x,y-s*.95);
    ctx.lineTo(x-s*.26,y-s*.15);
    ctx.lineTo(x+s*.26,y-s*.15);
    ctx.closePath();
    ctx.fill();
}
function drawWorld(dt) {
    const sky = ctx.createLinearGradient(0,0,0,H*.55);
    sky.addColorStop(0,"#70c7ff");
    sky.addColorStop(1,"#d5f2ff");
    ctx.fillStyle = sky;
    ctx.fillRect(0,0,W,H);

    // Sun and distant hills
    ctx.fillStyle = "#fff3a4";
    ctx.beginPath();
    ctx.arc(W*.82,H*.14,Math.min(W,H)*.055,0,Math.PI*2);
    ctx.fill();

    polygon([[0,H*.43],[W*.13,H*.22],[W*.29,H*.42],
             [W*.46,H*.24],[W*.65,H*.43],[W*.84,H*.25],
             [W,H*.42],[W,H*.6],[0,H*.6]],"#87a9a0");

    ctx.fillStyle = "#43985a";
    ctx.fillRect(0,H*.43,W,H*.57);

    const horizon = H*.43;
    const stripes = 18;
    for (let i=0;i<stripes;i++) {
        const y = horizon + (H-horizon)*i/stripes;
        const y2 = horizon + (H-horizon)*(i+1)/stripes;
        const c1 = roadCenter(y), c2 = roadCenter(y2);
        const r1 = roadHalf(y), r2 = roadHalf(y2);
        const alternate = Math.floor((roadPhase*5+i))%2===0;
        polygon([[0,y],[c1-r1,y],[c2-r2,y2],[0,y2]],
                alternate ? "#3c9550" : "#348748");
        polygon([[c1+r1,y],[W,y],[W,y2],[c2+r2,y2]],
                alternate ? "#3c9550" : "#348748");
    }

    // Road surface
    polygon([[roadCenter(horizon)-roadHalf(horizon),horizon],
             [roadCenter(H)-roadHalf(H),H],
             [roadCenter(H)+roadHalf(H),H],
             [roadCenter(horizon)+roadHalf(horizon),horizon]],"#555c66");

    // Road edge strips
    for (const side of [-1,1]) {
        polygon([
            [roadCenter(horizon)+side*roadHalf(horizon),horizon],
            [roadCenter(H)+side*roadHalf(H),H],
            [roadCenter(H)+side*(roadHalf(H)+W*.018),H],
            [roadCenter(horizon)+side*(roadHalf(horizon)+W*.018),horizon]
        ],"#f5f5ed");
    }

    // Dashed lane markings
    for(let i=0;i<15;i++) {
        const t = ((i/15 + roadPhase*.15)%1);
        const y = horizon + Math.pow(t,1.65)*(H-horizon);
        const h = 3 + t*18;
        const center = roadCenter(y);
        const half = roadHalf(y);
        for(let lane=1;lane<=2;lane++) {
            const x = center-half+half*2*lane/3;
            ctx.fillStyle = "#f5f3dc";
            ctx.fillRect(x-1.5-t*2,y,3+t*4,h);
        }
    }

    // Decorative roadside trees
    for(let i=0;i<16;i++) {
        const t = ((i/16 + roadPhase*.055)%1);
        const y = horizon + Math.pow(t,1.8)*(H-horizon);
        const s = 8 + t*58;
        const c = roadCenter(y), r = roadHalf(y);
        const side = i%2===0 ? -1 : 1;
        const x = c + side*(r + 22 + t*35);
        drawTree(x,y,s);
    }
}

function drawKart(x,y,scale,color,isPlayer) {
    ctx.save();
    ctx.translate(x,y);
    ctx.scale(scale,scale);

    // shadow
    ctx.fillStyle = "rgba(0,0,0,.28)";
    ctx.beginPath();
    ctx.ellipse(0,4,24,9,0,0,Math.PI*2);
    ctx.fill();

    // wheels
    ctx.fillStyle = "#15191f";
    ctx.fillRect(-23,-8,9,20);
    ctx.fillRect(14,-8,9,20);

    // kart body
    polygon([[-22,-18],[-15,-29],[15,-29],[22,-18],
             [18,7],[11,15],[-11,15],[-18,7]],color);

    // front bumper
    ctx.fillStyle = "#e9eef4";
    ctx.fillRect(-16,-28,32,5);

    // driver helmet
    ctx.fillStyle = "#ffdf9c";
    ctx.beginPath();
    ctx.arc(0,-18,10,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle = "#222b36";
    ctx.fillRect(-8,-20,16,5);

    if(isPlayer) {
        ctx.fillStyle = "#e7ff4f";
        ctx.fillRect(-19,5,38,4);
    }
    ctx.restore();
}

function spawnTraffic() {
    if(traffic.length < 7 && Math.random() < .025) {
        traffic.push({
            lane: (Math.random()-.5)*1.35,
            z: .05,
            color: ["#ff5252","#38bdf8","#ffb84d","#c084fc"][Math.floor(Math.random()*4)]
        });
    }
}

function drawTraffic(dt) {
    spawnTraffic();
    for(let i=traffic.length-1;i>=0;i--) {
        const car = traffic[i];
        car.z += dt * (0.09 + speed/850);
        if(car.z > .97) {
            traffic.splice(i,1);
            continue;
        }
        const y = H*.43 + Math.pow(car.z,1.7)*H*.57;
        const c = roadCenter(y), r = roadHalf(y);
        const x = c + car.lane*r*.78;
        const scale = .18 + car.z*.85;
        drawKart(x,y,scale,car.color,false);

        // collision check near player
        if(car.z > .82 && car.z < .94 &&
           Math.abs(x-(roadCenter(H*.84)+playerX*roadHalf(H*.84)*.7)) < 28*scale+18) {
            speed = Math.max(0,speed-28);
            traffic.splice(i,1);
        }
    }
}

function drawPlayer() {
    const y = H*.84;
    const x = roadCenter(y) + playerX*roadHalf(y)*.7;
    drawKart(x,y,1.25,"#e7ff4f",true);
}

function drawScene(dt) {
    drawWorld(dt);
    drawTraffic(dt);
    drawPlayer();
}

function updateHUD() {
    document.getElementById("speed").textContent = Math.round(speed);
    document.getElementById("fuel").textContent = Math.max(0,Math.round(fuel));
    const remaining = Math.max(0,DISTANCE*(1-progress));
    document.getElementById("remain").textContent = remaining.toFixed(1);
    document.getElementById("progress").style.width = (progress*100)+"%";
    document.getElementById("percent").textContent = Math.round(progress*100)+"%";
}

function showOverlay(title,message,buttonText) {
    document.getElementById("headline").textContent = title;
    document.getElementById("message").innerHTML = message;
    document.getElementById("start").textContent = buttonText;
    document.getElementById("overlay").style.display = "flex";
}

function resetGame() {
    speed=0; fuel=100; progress=0; playerX=0;
    roadPhase=0; elapsed=0; traffic=[];
    running=true; finished=false;
    document.getElementById("overlay").style.display="none";
    lastTime=performance.now();
    canvas.focus();
}

document.getElementById("start").addEventListener("click",resetGame);

function setKey(key, value) {
    keys[key]=value;
}
window.addEventListener("keydown",e=>{
    const k=e.key.toLowerCase();
    if(["arrowup","arrowdown","arrowleft","arrowright"," "].includes(k)) e.preventDefault();
    keys[k]=true;
});
window.addEventListener("keyup",e=>keys[e.key.toLowerCase()]=false);
window.addEventListener("blur",()=>keys={});

function bindButton(id,key) {
    const el=document.getElementById(id);
    el.addEventListener("pointerdown",e=>{
        e.preventDefault(); setKey(key,true);
    });
    ["pointerup","pointercancel","pointerleave"].forEach(evt=>{
        el.addEventListener(evt,()=>setKey(key,false));
    });
}
bindButton("left","arrowleft");
bindButton("right","arrowright");
bindButton("gas","arrowup");
bindButton("brake","arrowdown");

function loop(now) {
    const dt=Math.min((now-lastTime)/1000,.05);
    lastTime=now;

    if(running) {
        const gas=keys["arrowup"]||keys["w"];
        const brake=keys["arrowdown"]||keys["s"];
        const left=keys["arrowleft"]||keys["a"];
        const right=keys["arrowright"]||keys["d"];

        if(gas && fuel>0) speed += 42*dt;
        else speed -= 13*dt;
        if(brake) speed -= 75*dt;
        speed=Math.max(0,Math.min(180,speed));

        steering=(right?1:0)-(left?1:0);
        playerX += steering*dt*(0.8+speed/100);
        playerX=Math.max(-1.25,Math.min(1.25,playerX));

        // Road edge slows the kart
        if(Math.abs(playerX)>.94) speed=Math.max(0,speed-24*dt);

        roadPhase += dt*(.18+speed/150);
        elapsed += dt;

        // approximate fuel consumption and route progress
        const traveledKm = speed*dt/3600;
        progress += traveledKm/Math.max(DISTANCE,0.1);
        fuel -= traveledKm*100/Math.max(DISTANCE*0.08,0.5);
        fuel=Math.max(0,fuel);
        progress=Math.min(1,progress);

        if(progress>=1) {
            running=false; finished=true;
            showOverlay("FINISH! 🏁",
                "목적지에 도착했습니다.<br>주행 시간: "+Math.floor(elapsed)+"초",
                "RACE AGAIN ↻");
        } else if(fuel<=0) {
            running=false;
            showOverlay("OUT OF FUEL",
                "연료가 부족합니다.<br>다시 시작해 주행을 이어가세요.",
                "TRY AGAIN ↻");
        }

        updateHUD();
    }

    drawScene(dt);
    requestAnimationFrame(loop);
}

updateHUD();
showOverlay("READY, DRIVER?",
    "가속 페달을 밟고 도로 위를 달려보세요.<br>다른 차량과 도로 가장자리를 조심하세요.",
    "START RACE →");
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

game_html = game_html.replace(
    "__DISTANCE__",
    json.dumps(max(float(distance), 0.1))
)

components.html(game_html, height=625, scrolling=False)

# -------------------------------
# 실제 경로 지도
# -------------------------------

st.divider()
st.subheader("🗺️ 실제 경로")

start_point = st.session_state["start_point"]
end_point = st.session_state["end_point"]

route_map = folium.Map(
    location=[
        (start_point[0] + end_point[0]) / 2,
        (start_point[1] + end_point[1]) / 2
    ],
    zoom_start=10,
    tiles="OpenStreetMap"
)

folium.PolyLine(
    route_data["coordinates"],
    color="#3978ff",
    weight=5,
    opacity=0.9,
    tooltip="검색된 주행 경로"
).add_to(route_map)

folium.Marker(
    [start_point[0], start_point[1]],
    tooltip="출발지",
    popup=st.session_state["start_text"],
    icon=folium.Icon(color="green", icon="play")
).add_to(route_map)

folium.Marker(
    [end_point[0], end_point[1]],
    tooltip="도착지",
    popup=st.session_state["end_text"],
    icon=folium.Icon(color="red", icon="flag")
).add_to(route_map)

st_folium(
    route_map,
    use_container_width=True,
    height=430,
    returned_objects=[]
)

st.caption(
    "경로 데이터: OpenStreetMap / OSRM 공개 서비스. "
    "공개 서비스에는 이용 제한이 있으므로 과도한 요청을 피하세요."
)
