            start = geocode(start_text)
            end = geocode(end_text)
            route = get_route(start["lon"], start["lat"], end["lon"], end["lat"])
            st.session_state.route_data = {"start": start, "end": end, "route": route}
    except Exception as exc:
        st.error(f"경로를 불러오지 못했습니다. 장소 이름을 더 구체적으로 입력하거나 잠시 후 다시 시도해 주세요. ({exc})")

data = st.session_state.route_data
if data:
    start, end, route = data["start"], data["end"], data["route"]
    distance_km = route["distance_m"] / 1000
    duration_min = route["duration_s"] / 60
    hours = int(duration_min // 60)
    mins = int(round(duration_min % 60))
    fuel_used = distance_km / fuel_efficiency
    cost = fuel_used * fuel_price
    fuel_left = starting_fuel - fuel_used

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("도로 거리", f"{distance_km:.1f} km")
    c2.metric("예상 소요 시간", f"{hours}시간 {mins}분" if hours else f"{mins}분")
    c3.metric("예상 연료 소비", f"{fuel_used:.2f} L")
    c4.metric("예상 연료비", f"{cost:,.0f}원")

    if fuel_left < 0:
        st.warning(f"현재 입력한 연료량으로는 약 {-fuel_left:.1f} L 부족할 수 있습니다. 출발 전 주유를 고려하세요.")
    else:
        st.success(f"예상 도착 시 연료 잔량: 약 {fuel_left:.1f} L (연료량과 연비가 일정하다고 가정)")

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("실제 지도 경로")
        m = folium.Map(location=[start["lat"], start["lon"]], zoom_start=12, tiles="OpenStreetMap")
        points = [(lat, lon) for lon, lat in route["coordinates"]]
        folium.PolyLine(points, color="#12a8ff", weight=6, opacity=0.9, tooltip="추천 경로").add_to(m)
        folium.Marker([start["lat"], start["lon"]], tooltip="출발지", popup=start_text, icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker([end["lat"], end["lon"]], tooltip="목적지", popup=end_text, icon=folium.Icon(color="red", icon="flag")).add_to(m)
        if points:
            m.fit_bounds(points)
        st_folium(m, height=430, use_container_width=True, returned_objects=[])

    with right:
        st.subheader("3D 주행 미리보기")
        st.caption("아래 화면은 실제 경로의 모양을 단순화해 3D 도로로 표현합니다. 실제 건물·차선 정보와 동일한 시뮬레이터는 아닙니다.")
        coords_json = json.dumps(route["coordinates"])
        components.html(f"""
<div id="drive3d" style="width:100%;height:430px;border-radius:14px;overflow:hidden;background:#080d14;position:relative">
  <div style="position:absolute;z-index:2;top:10px;left:12px;color:#e8f3ff;font:12px Arial;background:#111b29cc;padding:7px 10px;border-radius:8px">DRIVEMAP · 3D PREVIEW</div>
  <div style="position:absolute;z-index:2;bottom:10px;left:12px;color:#b9c8d8;font:12px Arial">마우스로 회전 · 휠로 확대/축소</div>
</div>
<script type="module">
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import {{ OrbitControls }} from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';
const root = document.getElementById('drive3d');
const coords = {coords_json};
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080d14);
scene.fog = new THREE.Fog(0x080d14, 80, 260);
const camera = new THREE.PerspectiveCamera(55, root.clientWidth/root.clientHeight, 0.1, 1000);
camera.position.set(0, 18, 30);
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(root.clientWidth, root.clientHeight);
renderer.shadowMap.enabled = true;
root.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xc6e4ff, 0x18202b, 2.0));
const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(10,30,15); scene.add(sun);
const grid = new THREE.GridHelper(240, 48, 0x22354a, 0x142333); grid.position.y=-0.08; scene.add(grid);
const coords2 = coords.filter((p,i)=>i===0 || i===coords.length-1 || i%Math.max(1,Math.floor(coords.length/180))===0);
const lon0=coords2[0][0], lat0=coords2[0][1];
const scaleX=Math.cos(lat0*Math.PI/180)*111.32, scaleZ=110.57;
let raw=coords2.map(p=>new THREE.Vector3((p[0]-lon0)*scaleX*1.0,0,(p[1]-lat0)*scaleZ*-1.0));
if(raw.length<2) raw=[new THREE.Vector3(-20,0,0),new THREE.Vector3(20,0,0)];
const box=new THREE.Box3().setFromPoints(raw); const center=box.getCenter(new THREE.Vector3());
raw=raw.map(p=>p.sub(center));
const length=raw.length;
const path=new THREE.CatmullRomCurve3(raw);
const pts=path.getPoints(Math.max(100,Math.min(600,length*4)));
const roadGeo=new THREE.BufferGeometry().setFromPoints(pts);
const roadMat=new THREE.LineBasicMaterial({{color:0x687483,linewidth:3}});
const roadLine=new THREE.Line(roadGeo,roadMat); roadLine.position.y=0.04; scene.add(roadLine);
// Wider road ribbon following the actual route shape
const ribbonVerts=[], ribbonIndices=[];
for(let i=0;i<pts.length;i++){{
 const tangent=path.getTangent(i/(pts.length-1)).normalize();
 const side=new THREE.Vector3(-tangent.z,0,tangent.x).normalize();
 const p=pts[i];
 ribbonVerts.push(p.x+side.x*3.4,0,p.z+side.z*3.4,p.x-side.x*3.4,0,p.z-side.z*3.4);
 if(i<pts.length-1){{let a=i*2,b=a+1,c=a+2,d=a+3;ribbonIndices.push(a,b,c,b,d,c);}}
}}
const rg=new THREE.BufferGeometry(); rg.setAttribute('position',new THREE.Float32BufferAttribute(ribbonVerts,3)); rg.setIndex(ribbonIndices); rg.computeVertexNormals();
const road=new THREE.Mesh(rg,new THREE.MeshStandardMaterial({{color:0x26313d,roughness:0.95,side:THREE.DoubleSide}})); road.position.y=0.02; scene.add(road);
// dashed center line
for(let i=0;i<pts.length;i+=8){{const p=pts[i]; const dash=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.025,1.1),new THREE.MeshBasicMaterial({{color:0xe6edf5}}));dash.position.set(p.x,0.08,p.z);dash.rotation.y=Math.atan2(path.getTangent(i/(pts.length-1)).x,path.getTangent(i/(pts.length-1)).z);scene.add(dash);}}
function marker(pos,color){{const mesh=new THREE.Mesh(new THREE.CylinderGeometry(0.45,0.45,0.25,18),new THREE.MeshStandardMaterial({{color}}));mesh.position.set(pos.x,0.3,pos.z);scene.add(mesh);}}
marker(pts[0],0x38d982); marker(pts[pts.length-1],0xff5a67);
const car=new THREE.Group();
const body=new THREE.Mesh(new THREE.BoxGeometry(1.5,0.55,2.7),new THREE.MeshStandardMaterial({{color:0x12a8ff,metalness:0.25,roughness:0.35}}));body.position.y=0.72;car.add(body);
const cabin=new THREE.Mesh(new THREE.BoxGeometry(1.05,0.5,1.1),new THREE.MeshStandardMaterial({{color:0x9bdcff,metalness:0.1,roughness:0.2}}));cabin.position.set(0,1.18,-0.1);car.add(cabin);
for(const x of [-0.82,0.82]) for(const z of [-0.82,0.82]){{const w=new THREE.Mesh(new THREE.CylinderGeometry(0.27,0.27,0.18,16),new THREE.MeshStandardMaterial({{color:0x080a0d}}));w.rotation.z=Math.PI/2;w.position.set(x,0.42,z);car.add(w);}}
scene.add(car);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(0,0,0);
const lookAt=new THREE.Vector3();
let t=0, last=performance.now();
function animate(now){{requestAnimationFrame(animate); const dt=Math.min((now-last)/1000,0.05);last=now;t=(t+dt*0.035)%(1); const p=path.getPointAt(t); const tangent=path.getTangentAt(t);car.position.set(p.x,0,p.z);car.rotation.y=Math.atan2(tangent.x,tangent.z); if(!controls.userInteracting){{camera.position.lerp(new THREE.Vector3(p.x+12, p.y+13, p.z+17),0.018);controls.target.lerp(p,0.025);}}controls.update();renderer.render(scene,camera);}}
controls.userInteracting=false;
controls.addEventListener('start',()=>controls.userInteracting=true);
controls.addEventListener('end',()=>{{setTimeout(()=>controls.userInteracting=false,2500);}});
window.addEventListener('resize',()=>{{camera.aspect=root.clientWidth/root.clientHeight;camera.updateProjectionMatrix();renderer.setSize(root.clientWidth,root.clientHeight);}});
animate(performance.now());
</script>
""", height=450, scrolling=False)

    with st.expander("계산 기준 보기"):
        st.write(f"- 경로 거리: {distance_km:.2f} km")
        st.write(f"- 연료 소비 추정: 거리 ÷ 연비 = {distance_km:.2f} ÷ {fuel_efficiency:.1f} = {fuel_used:.2f} L")
        st.write(f"- 연료비 추정: 소비 연료 × 리터당 가격 = {cost:,.0f}원")
        st.write(f"- 출발지 검색 결과: {start['label']}")
        st.write(f"- 목적지 검색 결과: {end['label']}")
else:
    st.markdown("### 시작하기")
    st.write("왼쪽에서 출발지와 목적지를 입력한 뒤 **경로 찾기**를 누르세요.")
    st.write("예시: 출발지 `수원역`, 목적지 `광교호수공원`")
    st.markdown("""
    **현재 포함된 기능**
    - 실제 도로 데이터를 기반으로 한 경로 탐색
    - 도로 거리와 기본 경로 시간
    - 연비·연료 가격·현재 연료량 입력

