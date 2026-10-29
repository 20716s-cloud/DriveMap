
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="DriveMap Kart", page_icon="🏎️", layout="wide")

st.markdown("""
<style>
.block-container {max-width:1200px;padding-top:1rem}
iframe {border:0}
</style>
""", unsafe_allow_html=True)

st.title("🏎️ DriveMap Kart")
st.caption("ARCADE RACING · DRIFT · BOOST · TIME ATTACK")

game = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
*{box-sizing:border-box}
body{margin:0;background:#101722;color:white;font-family:Arial,sans-serif}
.hud{display:flex;justify-content:space-between;gap:8px;padding:12px;background:#192434;border-radius:12px 12px 0 0;flex-wrap:wrap}
.metric{font-size:11px;color:#a9bbce}
.value{font-size:22px;font-weight:bold;color:#fff;margin-top:4px}
#speed{color:#56f0c0}
#boostbar,#driftbar{height:8px;background:#354355;border-radius:8px;overflow:hidden;margin-top:7px}
#boostfill{height:100%;width:0;background:linear-gradient(90deg,#23c8ff,#65ffcf)}
#driftfill{height:100%;width:0;background:#ffb84d}
canvas{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#79c8f0;outline:none;touch-action:none}
.controls{display:flex;gap:8px;flex-wrap:wrap;padding:12px;background:#192434;border-radius:0 0 12px 12px}
button{flex:1;min-width:95px;padding:12px 8px;border-radius:8px;border:1px solid #3b5069;background:#26374b;color:white;font-weight:bold;cursor:pointer;touch-action:none}
button:active,button.active{background:#197d69}
#boost{background:#087d69;border-color:#4fffd0}
.note{font-size:12px;color:#9eb2c8;line-height:1.7;padding:10px 2px}
</style>
</head>
<body>
<div class="hud">
  <div><div class="metric">SPEED</div><div class="value"><span id="speed">0</span> <small>KM/H</small></div></div>
  <div><div class="metric">LAP</div><div class="value" id="lap">1 / 3</div></div>
  <div><div class="metric">RACE TIME</div><div class="value" id="time">00:00.0</div></div>
  <div style="min-width:110px;flex:1">
    <div class="metric">BOOST</div><div id="boostbar"><div id="boostfill"></div></div>
    <div class="metric" style="margin-top:5px">DRIFT</div><div id="driftbar"><div id="driftfill"></div></div>
  </div>
</div>
<canvas id="game" width="960" height="540" tabindex="0"></canvas>
<div class="controls">
  <button data-key="left">◀ LEFT</button>
  <button data-key="down">▼ BRAKE</button>
  <button data-key="right">RIGHT ▶</button>
  <button data-key="up">▲ ACCELERATE</button>
  <button id="boost">⚡ BOOST SPACE</button>
  <button id="restart">↻ RESTART</button>
</div>
<div class="note">
  방향키 또는 WASD로 조작 · 코너에서 방향키를 누르며 가속하면 드리프트 게이지가 쌓여요.
  <br>게이지가 충분할 때 Space 또는 BOOST 버튼을 눌러 가속하세요. 트랙을 한 바퀴 돌면 랩이 증가합니다.
</div>

<script>
(() => {
const canvas=document.getElementById('game');
const ctx=canvas.getContext('2d');
const W=960,H=540;
const keys=new Set();
const el=id=>document.getElementById(id);

let speed=0,boost=0,drift=0,steer=0;
let progress=0,laps=0,raceTime=0;
let started=false,finished=false;
let last=performance.now(),boostTime=0;
const totalLaps=3;
const trackLength=2400;

// Track geometry: a looping oval with rounded corners
const track=[
 [480,90],[600,100],[710,145],[790,220],
 [815,300],[785,375],[710,425],[600,450],
 [480,455],[360,450],[250,425],[170,375],
 [145,300],[170,220],[250,145],[360,100]
];

function getTrack(t){
  const n=track.length;
  const x=t*n;
  const i=Math.floor(x)%n;
  const f=x-Math.floor(x);
  const a=track[i],b=track[(i+1)%n];
  return {x:a[0]+(b[0]-a[0])*f,y:a[1]+(b[1]-a[1])*f};
}
function drawTrack(){
  // grass background
  ctx.fillStyle='#438b48';ctx.fillRect(0,0,W,H);
  // grass pattern
  for(let i=0;i<180;i++){
    const x=(i*137)%W,y=(i*83)%H;
    ctx.fillStyle=i%2?'#4a964c':'#3d8142';
    ctx.fillRect(x,y,18,12);
  }
  // road outline
  ctx.lineCap='round';ctx.lineJoin='round';
  function pathTrack(offset,width,color){
    ctx.beginPath();
    for(let i=0;i<=track.length*8;i++){
      const p=getTrack(i/(track.length*8));
      const next=getTrack((i+0.01)/(track.length*8));
      const dx=next.x-p.x,dy=next.y-p.y;
      const len=Math.hypot(dx,dy)||1;
      const x=p.x-dy/len*offset,y=p.y+dx/len*offset;
      if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.closePath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();
  }
  pathTrack(0,155,'#d9dfe1');
  pathTrack(0,139,'#303944');
  pathTrack(0,4,'#f1dca0');
  // dashed lane line
  ctx.setLineDash([15,15]);
  pathTrack(0,2,'#b9c4ca');
  ctx.setLineDash([]);
  // curb blocks
  for(let i=0;i<track.length*8;i++){
    const p=getTrack(i/(track.length*8));
    const q=getTrack((i+0.004)/(track.length*8));
    const angle=Math.atan2(q.y-p.y,q.x-p.x);
    ctx.save();ctx.translate(p.x,p.y);ctx.rotate(angle);
    ctx.fillStyle=i%2?'#f4f4f4':'#f14f5c';
    ctx.fillRect(-5,-78,10,12);ctx.fillRect(-5,66,10,12);
    ctx.restore();
  }
  // scenery
  for(let i=0;i<40;i++){
    const x=(i*197+30)%W,y=(i*113+20)%H;
    const near=track.reduce((best,p)=>Math.min(best,Math.hypot(p[0]-x,p[1]-y)),999);
    if(near>110){
      ctx.fillStyle='#28603a';ctx.beginPath();ctx.arc(x,y,15,0,Math.PI*2);ctx.fill();
      ctx.fillStyle='#397c43';ctx.beginPath();ctx.arc(x-3,y-5,11,0,Math.PI*2);ctx.fill();
    }
  }
  // finish line at start of track
  const p=track[0];
  ctx.save();ctx.translate(p[0],p[1]);ctx.rotate(0);
  for(let i=0;i<10;i++){
    ctx.fillStyle=i%2?'#fff':'#20242a';
    ctx.fillRect(-7,-69+i*14,15,14);
  }
  ctx.restore();
}

function drawKart(){
  const p=getTrack(progress/trackLength);
  const next=getTrack((progress+2)/trackLength);
  const angle=Math.atan2(next.y-p.y,next.x-p.x)+steer*0.18;
  const x=p.x,y=p.y;
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);
  // shadow
  ctx.fillStyle='#0007';ctx.beginPath();ctx.ellipse(0,7,23,14,0,0,Math.PI*2);ctx.fill();
  // wheels
  ctx.fillStyle='#15191f';
  ctx.fillRect(-17,-17,10,14);ctx.fillRect(8,-17,10,14);
  ctx.fillRect(-17,8,10,14);ctx.fillRect(8,8,10,14);
  // kart body
  ctx.fillStyle='#f04456';
  ctx.beginPath();ctx.moveTo(0,-25);ctx.lineTo(16,-10);ctx.lineTo(15,18);
  ctx.lineTo(8,24);ctx.lineTo(-8,24);ctx.lineTo(-15,18);ctx.lineTo(-16,-10);
  ctx.closePath();ctx.fill();
  // cockpit
  ctx.fillStyle='#283c54';ctx.fillRect(-9,-6,18,13);
  ctx.fillStyle='#78d9ed';ctx.fillRect(-7,-4,14,6);
  // headlight
  ctx.fillStyle='#fff2b1';ctx.fillRect(-12,-22,7,4);ctx.fillRect(5,-22,7,4);
  if(boostTime>0){
    ctx.fillStyle='#55eaff';
    ctx.beginPath();ctx.moveTo(-6,22);ctx.lineTo(0,38+Math.random()*6);ctx.lineTo(6,22);ctx.fill();
  }
  ctx.restore();
}

function drawHUD(){
  ctx.fillStyle='#122033cc';ctx.fillRect(14,H-80,150,62);
  ctx.fillStyle='#fff';ctx.font='bold 13px Arial';ctx.fillText('RACE PROGRESS',25,H-58);
  ctx.fillStyle='#34465b';ctx.fillRect(25,H-46,128,9);
  ctx.fillStyle='#55e9bd';ctx.fillRect(25,H-46,128*(progress/trackLength%1),9);
  ctx.fillStyle='#fff';ctx.font='bold 12px Arial';
  ctx.fillText('DRIVEMAP KART',W-165,28);
  if(finished){
    ctx.fillStyle='#07121ddd';ctx.fillRect(220,185,520,150);
    ctx.textAlign='center';ctx.fillStyle='#62f5c3';ctx.font='bold 34px Arial';
    ctx.fillText('FINISH!',480,235);
    ctx.fillStyle='white';ctx.font='20px Arial';
    ctx.fillText('Time: '+formatTime(raceTime),480,277);
    ctx.font='14px Arial';ctx.fillText('RESTART를 눌러 다시 레이스하세요',480,308);
    ctx.textAlign='left';
  }
}

function formatTime(t){
  const m=Math.floor(t/60),s=(t%60).toFixed(1).padStart(4,'0');
  return String(m).padStart(2,'0')+':'+s;
}
function update(dt){
  if(finished)return;
  const up=keys.has('up'),down=keys.has('down');
  const left=keys.has('left'),right=keys.has('right');
  const turning=left||right;

  if(up){speed+=90*dt;started=true;}
  else speed-=14*dt;
  if(down)speed-=130*dt;
  speed=Math.max(0,Math.min(220,speed));

  if(turning&&up&&speed>40){
    drift=Math.min(100,drift+34*dt);
  }else{
    drift=Math.max(0,drift-20*dt);
  }

  if(boostTime>0){
    boostTime-=dt;
    speed=Math.min(250,speed+100*dt);
  }

  const steerInput=(right?1:0)-(left?1:0);
  steer+=(steerInput-steer)*Math.min(1,dt*7);

  const oldLap=Math.floor(progress/trackLength);
  progress+=speed*dt*(turning?0.85:1);
  const newLap=Math.floor(progress/trackLength);
  laps=newLap;

  if(newLap>=totalLaps){
    progress=trackLength*totalLaps;
    finished=true;
    speed=0;
  }

  if(started&&!finished)raceTime+=dt;

  el('speed').textContent=Math.round(speed);
  el('lap').textContent=Math.min(laps+1,totalLaps)+' / '+totalLaps;
  el('time').textContent=formatTime(raceTime);
  el('boostfill').style.width=boost+'%';
  el('driftfill').style.width=drift+'%';
}

function frame(now){
  const dt=Math.min((now-last)/1000,0.04);last=now;
  update(dt);
  drawTrack();drawKart();drawHUD();
  requestAnimationFrame(frame);
}

const map={
 ArrowUp:'up',w:'up',W:'up',
 ArrowDown:'down',s:'down',S:'down',
 ArrowLeft:'left',a:'left',A:'left',
 ArrowRight:'right',d:'right',D:'right'
};
document.addEventListener('keydown',e=>{
  if(map[e.key]){e.preventDefault();keys.add(map[e.key]);}
  if(e.code==='Space'){e.preventDefault();useBoost();}
});
document.addEventListener('keyup',e=>{
  if(map[e.key]){e.preventDefault();keys.delete(map[e.key]);}
});
window.addEventListener('blur',()=>keys.clear());

document.querySelectorAll('[data-key]').forEach(btn=>{
  const k=btn.dataset.key;
  const start=e=>{e.preventDefault();keys.add(k);btn.classList.add('active');};
  const stop=e=>{e.preventDefault();keys.delete(k);btn.classList.remove('active');};
  btn.addEventListener('pointerdown',start);
  btn.addEventListener('pointerup',stop);
  btn.addEventListener('pointerleave',stop);
  btn.addEventListener('pointercancel',stop);
});
function useBoost(){
  if(drift>=30){boostTime=1.7;drift=0;boost=Math.min(100,boost+35);}
  else if(boost>=30){boostTime=1.7;boost-=30;}
  else {boost=Math.min(100,boost+8);}
}
el('boost').addEventListener('pointerdown',e=>{e.preventDefault();useBoost();});
document.addEventListener('keydown',e=>{if(e.code==='Space'&&!e.repeat)useBoost();});

el('restart').addEventListener('click',()=>{
  speed=0;boost=0;drift=0;steer=0;progress=0;laps=0;
  raceTime=0;started=false;finished=false;boostTime=0;keys.clear();
});
requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""

components.html(game, height=760, scrolling=False)

st.caption("DriveMap Kart · 오리지널 아케이드 레이싱 게임")
