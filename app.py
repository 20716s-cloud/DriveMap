
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DriveMap | Open World",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container {
        max-width: 1200px;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚘 DriveMap")
st.caption("OPEN WORLD · FREE DRIVE · ARCADE EXPERIENCE")

game = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    background: #090e14;
    color: #f3f7fc;
    font-family: Arial, sans-serif;
    overflow: hidden;
}
.game {
    width: 100%;
    border: 1px solid #293849;
    border-radius: 15px;
    overflow: hidden;
    background: #111923;
}
.hud {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 10px;
    align-items: center;
    padding: 12px 14px;
    background: #111923;
}
.brand {
    font-size: 11px;
    color: #5be6b5;
    letter-spacing: 2px;
    font-weight: bold;
}
.subtitle {
    margin-top: 4px;
    font-size: 12px;
    color: #93a6bb;
}
.metric {
    min-width: 70px;
    text-align: right;
}
.metric-label {
    font-size: 10px;
    color: #8ea2b8;
    letter-spacing: 1px;
}
.metric-value {
    font-size: 20px;
    font-weight: bold;
    margin-top: 4px;
}
#speed { color: #5be6b5; }
.scene {
    position: relative;
    width: 100%;
    background: #8bc5e6;
}
canvas {
    display: block;
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
    outline: none;
    touch-action: none;
}
.overlay {
    position: absolute;
    top: 12px;
    left: 12px;
    padding: 7px 10px;
    background: #0b1525c9;
    border: 1px solid #ffffff22;
    border-radius: 7px;
    font-size: 11px;
    color: #d6e5f5;
    pointer-events: none;
}
.overlay span { color: #5be6b5; }
.bottom {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    padding: 12px;
    background: #111923;
}
.panel {
    border: 1px solid #28394b;
    border-radius: 11px;
    padding: 10px;
    background: #0c131c;
}
.panel-title {
    color: #8fa6bd;
    font-size: 10px;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}
.steer {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
}
button {
    min-height: 42px;
    border-radius: 8px;
    border: 1px solid #34475c;
    background: #1a2838;
    color: white;
    font-weight: bold;
    font-size: 14px;
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    touch-action: none;
}
button:hover { background: #293d52; }
button:active, button.active {
    background: #286b5b;
    border-color: #5be6b5;
}
.controls {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
}
.controls button { min-height: 46px; }
.go {
    background: #5be6b5;
    color: #06261d;
    border-color: #5be6b5;
}
.go:hover { background: #83f3ce; }
.reset { grid-column: 1 / -1; }
.help {
    padding: 0 13px 13px;
    background: #111923;
    color: #91a5ba;
    font-size: 11px;
    line-height: 1.6;
}
@media (max-width: 520px) {
    .hud { gap: 6px; padding: 10px; }
    .metric { min-width: 55px; }
    .metric-value { font-size: 16px; }
    .subtitle { font-size: 10px; }
    .bottom { gap: 7px; padding: 7px; }
    .panel { padding: 7px; }
    button { min-height: 38px; }
}
</style>
</head>
<body>
<div class="game">
    <div class="hud">
        <div>
            <div class="brand">DRIVEMAP / WORLD 01</div>
            <div class="subtitle">Open Road · Free Drive</div>
        </div>
        <div class="metric">
            <div class="metric-label">SPEED</div>
            <div class="metric-value"><span id="speed">0</span><span style="font-size:10px"> KM/H</span></div>
        </div>
        <div class="metric">
            <div class="metric-label">DISTANCE</div>
            <div class="metric-value"><span id="distance">0.00</span><span style="font-size:10px"> KM</span></div>
        </div>
    </div>

    <div class="scene">
        <canvas id="world" width="960" height="540" tabindex="0"
                aria-label="가상 주행 게임. W A S D 또는 방향키로 운전합니다."></canvas>
        <div class="overlay">MODE <span>FREE DRIVE</span> &nbsp;·&nbsp; <span id="state">READY</span></div>
    </div>

    <div class="bottom">
        <div class="panel">
            <div class="panel-title">STEERING</div>
            <div class="steer">
                <div></div>
                <button data-key="up">▲</button>
                <div></div>
                <button data-key="left">◀</button>
                <button data-key="down">▼</button>
                <button data-key="right">▶</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">DRIVE CONTROL</div>
            <div class="controls">
                <button class="go" data-key="up">ACCELERATE</button>
                <button data-key="down">BRAKE</button>
                <button data-key="left">LEFT</button>
                <button data-key="right">RIGHT</button>
                <button id="reset" class="reset">↻ RESTART DRIVE</button>
            </div>
        </div>
    </div>
    <div class="help">
        키보드: W / ↑ 가속 · S / ↓ 감속 · A / ← 좌회전 · D / → 우회전
        <br>도로 밖으로 나가면 감속됩니다. 게임 화면을 클릭한 뒤 키보드를 사용하세요.
    </div>
</div>

<script>
(() => {
"use strict";

const canvas = document.getElementById("world");
const ctx = canvas.getContext("2d");
const speedEl = document.getElementById("speed");
const distEl = document.getElementById("distance");
const stateEl = document.getElementById("state");

const W = canvas.width, H = canvas.height;
const horizon = 205;
const keys = new Set();

let speed = 0;
let distance = 0;
let playerX = 0;
let roadTravel = 0;
let steering = 0;
let last = performance.now();
let elapsed = 0;
let running = true;

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

function curveAt(z) {
    return Math.sin(z * 0.00045) * 0.8
         + Math.sin(z * 0.00019 + 1.7) * 0.6
         + Math.sin(z * 0.0009) * 0.18;
}

function project(z, side) {
    const depth = 1 / (1 + z * 0.0038);
    const y = horizon + (H - horizon) * (1 - depth);
    const roadHalf = 390 * (1 - depth) + 22;
    const center = W / 2
        + (curveAt(roadTravel + z) - curveAt(roadTravel)) * 180;
    return {
        x: center + side * roadHalf,
        y,
        half: roadHalf,
        center,
        depth
    };
}

function polygon(points, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1]);
    }
    ctx.closePath();
    ctx.fill();
}

function drawSky() {
    const sky = ctx.createLinearGradient(0, 0, 0, horizon + 60);
    sky.addColorStop(0, "#3979a8");
    sky.addColorStop(0.65, "#8cc9e8");
    sky.addColorStop(1, "#d3e8ef");
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, horizon + 70);

    // distant mountains
    polygon([
        [0, horizon + 30], [90, 155], [170, 191],
        [260, 135], [360, 193], [480, 149],
        [590, 190], [710, 133], [840, 186],
        [960, 150], [960, horizon + 70], [0, horizon + 70]
    ], "#7899a0");

    polygon([
        [0, horizon + 45], [130, 180], [230, 206],
        [350, 172], [460, 210], [590, 175],
        [730, 205], [860, 170], [960, 205],
        [960, horizon + 70], [0, horizon + 70]
    ], "#63846e");

    // sun
    ctx.fillStyle = "#fff1c3";
    ctx.beginPath();
    ctx.arc(780, 78, 27, 0, Math.PI * 2);
    ctx.fill();
}

function drawWorld() {
    ctx.fillStyle = "#547f48";
    ctx.fillRect(0, horizon, W, H - horizon);

    // roadside ground strips
    const bands = 55;
    for (let i = 0; i < bands; i++) {
        const z1 = i * 13;
        const z2 = (i + 1) * 13;
        const a = project(z1, -1);
        const b = project(z1, 1);
        const c = project(z2, 1);
        const d = project(z2, -1);

        const stripe = Math.floor((roadTravel + z1) / 65) % 2;
        polygon([[0,a.y],[W,a.y],[W,c.y],[0,d.y]],
            stripe ? "#527d46" : "#5c884c");

        // gravel shoulder
        polygon([
            [a.x - 10, a.y], [a.x + 10, a.y],
            [d.x + 10, d.y], [d.x - 10, d.y]
        ], "#b9b8a1");
        polygon([
            [b.x - 10, b.y], [b.x + 10, b.y],
            [c.x + 10, c.y], [c.x - 10, c.y]
        ], "#b9b8a1");
    }

    // road segments with perspective
    for (let i = 0; i < bands; i++) {
        const z1 = i * 13;
        const z2 = (i + 1) * 13;
        const l1 = project(z1, -1);
        const r1 = project(z1, 1);
        const l2 = project(z2, -1);
        const r2 = project(z2, 1);

        const stripe = Math.floor((roadTravel + z1) / 85) % 2;
        polygon([
            [l1.x,l1.y],[r1.x,r1.y],[r2.x,r2.y],[l2.x,l2.y]
        ], stripe ? "#343a42" : "#30363e");

        // white road edge lines
        const edgeWidth = Math.max(1, l1.depth * 5);
        polygon([
            [l1.x,l1.y],[l1.x+edgeWidth,l1.y],
            [l2.x+edgeWidth,l2.y],[l2.x,l2.y]
        ], "#f0f0dc");
        polygon([
            [r1.x-edgeWidth,r1.y],[r1.x,r1.y],
            [r2.x,r2.y],[r2.x-edgeWidth,r2.y]
        ], "#f0f0dc");

        // center dashed line
        if (Math.floor((roadTravel + z1) / 65) % 2 === 0) {
            const width = Math.max(1, l1.depth * 5);
            polygon([
                [l1.center-width/2,l1.y],
                [l1.center+width/2,l1.y],
                [l2.center+width/2,l2.y],
                [l2.center-width/2,l2.y]
            ], "#f7e8a4");
        }
    }

    // trees and small roadside objects
    for (let i = 0; i < 36; i++) {
        const z = ((i * 57 + roadTravel * 0.9) % 690 + 690) % 690;
        const side = i % 2 === 0 ? -1 : 1;
        const p = project(z, side * 1.34);
        const size = 8 + p.depth * 40;
        const sway = Math.sin(i * 9.2) * 10 * p.depth;
        const x = p.x + sway;
        const y = p.y;

        if (x < -100 || x > W + 100) continue;

        // tree trunk
        ctx.fillStyle = "#584735";
        ctx.fillRect(x - size * .08, y - size * .35,
                     size * .16, size * .4);

        // tree crown
        polygon([
            [x, y - size * 1.65],
            [x - size * .55, y - size * .45],
            [x + size * .55, y - size * .45]
        ], i % 3 === 0 ? "#27583e" : "#34734a");

        polygon([
            [x, y - size * 1.3],
            [x - size * .4, y - size * .3],
            [x + size * .4, y - size * .3]
        ], "#4b9058");
    }
}

function drawCar() {
    const x = W / 2 + playerX * 220;
    const y = H - 105;
    const sway = steering * 9;

    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(-steering * 0.07);

    // shadow
    ctx.fillStyle = "#0007";
    ctx.beginPath();
    ctx.ellipse(0, 39, 70, 15, 0, 0, Math.PI * 2);
    ctx.fill();

    // wheels
    ctx.fillStyle = "#15191f";
    ctx.fillRect(-55 + sway, 4, 20, 45);
    ctx.fillRect(35 + sway, 4, 20, 45);

    // body
    polygon([
        [-48, 43], [-55, 14], [-42, -15],
        [-28, -44], [28, -44], [42, -15],
        [55, 14], [48, 43]
    ], "#d83f4c");

    // roof / rear window
    polygon([
        [-30, -14], [-20, -38], [20, -38],
        [30, -14], [36, 4], [-36, 4]
    ], "#243e52");

    // back glass reflection
    polygon([
        [-23, -31], [23, -31], [29, -14], [-29, -14]
    ], "#6c9eaf");

    // rear lights
    ctx.fillStyle = "#ffb6a7";
    ctx.fillRect(-43, 20, 13, 8);
    ctx.fillRect(30, 20, 13, 8);

    // plate
    ctx.fillStyle = "#e8e8e0";
    ctx.fillRect(-12, 24, 24, 7);

    ctx.restore();
}

function drawSpeedometer() {
    const cx = W - 80, cy = H - 78;
    ctx.fillStyle = "#07121ccc";
    ctx.beginPath();
    ctx.arc(cx, cy, 43, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "#5be6b5";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(cx, cy, 35, Math.PI * .75, Math.PI * .75 +
            Math.PI * 1.5 * speed / 180);
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.font = "bold 19px Arial";
    ctx.fillText(Math.round(speed), cx, cy + 2);
    ctx.fillStyle = "#a9bdce";
    ctx.font = "9px Arial";
    ctx.fillText("KM/H", cx, cy + 17);
}

function draw() {
    ctx.clearRect(0, 0, W, H);
    drawSky();
    drawWorld();
    drawCar();
    drawSpeedometer();
}

function update(dt) {
    const up = keys.has("up");
    const down = keys.has("down");
    const left = keys.has("left");
    const right = keys.has("right");

    if (up) speed += 55 * dt;
    else speed -= 8 * dt;

    if (down) speed -= 95 * dt;
    speed = clamp(speed, 0, 180);

    const turnInput = (right ? 1 : 0) - (left ? 1 : 0);
    steering += (turnInput - steering) * Math.min(1, dt * 6);

    const movement = speed / 3.6 * dt;
    distance += movement / 1000;
    roadTravel += movement * 2.6;

    // road departure slows the car
    playerX += steering * dt * (0.25 + speed / 90);
    if (Math.abs(playerX) > 0.78) {
        speed = Math.max(0, speed - 35 * dt);
        playerX = clamp(playerX, -1.25, 1.25);
        stateEl.textContent = "OFF ROAD";
    } else if (speed > 1) {
        stateEl.textContent = "DRIVING";
    } else {
        stateEl.textContent = "READY";
    }

    speedEl.textContent = Math.round(speed);
    distEl.textContent = distance.toFixed(2);
}

function frame(now) {
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;

    if (running) update(dt);
    draw();
    requestAnimationFrame(frame);
}

const keyMap = {
    ArrowUp: "up", w: "up", W: "up",
    ArrowDown: "down", s: "down", S: "down",
    ArrowLeft: "left", a: "left", A: "left",
    ArrowRight: "right", d: "right", D: "right"
};

document.addEventListener("keydown", event => {
    const action = keyMap[event.key];
    if (action) {
        event.preventDefault();
        keys.add(action);
    }
});

document.addEventListener("keyup", event => {
    const action = keyMap[event.key];
    if (action) {
        event.preventDefault();
        keys.delete(action);
    }
});

window.addEventListener("blur", () => keys.clear());

document.querySelectorAll("[data-key]").forEach(button => {
    const action = button.dataset.key;

    const start = event => {
        event.preventDefault();
        keys.add(action);
        button.classList.add("active");
        canvas.focus();
    };

    const stop = event => {
        event.preventDefault();
        keys.delete(action);
        button.classList.remove("active");
    };

    button.addEventListener("pointerdown", start);
    button.addEventListener("pointerup", stop);
    button.addEventListener("pointercancel", stop);
    button.addEventListener("pointerleave", stop);
});

document.getElementById("reset").addEventListener("click", () => {
    speed = 0;
    distance = 0;
    playerX = 0;
    roadTravel = 0;
    steering = 0;
    keys.clear();
    stateEl.textContent = "READY";
    speedEl.textContent = "0";
    distEl.textContent = "0.00";
    canvas.focus();
});

canvas.addEventListener("click", () => canvas.focus());

draw();
requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""

components.html(game, height=760, scrolling=False)

st.caption(
    "DriveMap Open World · 가상 주행 시뮬레이션 · "
    "실제 도로 및 차량 물리와는 다릅니다."
)
