
import streamlit as st
import pandas as pd

st.set_page_config(page_title="DriveMap", page_icon="🚗")

st.title("🚗 DriveMap")
st.write("나의 주행 기록을 관리하는 프로그램입니다.")

if "records" not in st.session_state:
    st.session_state.records = []

st.subheader("주행 정보 입력")

with st.form("drive_form"):
    start = st.text_input("출발지")
    end = st.text_input("도착지")
    distance = st.number_input(
        "이동 거리(km)", min_value=0.0, step=1.0
    )
    minutes = st.number_input(
        "주행 시간(분)", min_value=0, step=5
    )

    submitted = st.form_submit_button("주행 기록 저장")

if submitted:
    if not start.strip() or not end.strip():
        st.error("출발지와 도착지를 입력해 주세요.")
    elif distance <= 0 or minutes <= 0:
        st.error("이동 거리와 주행 시간은 0보다 커야 합니다.")
    else:
        speed = distance / (minutes / 60)

        record = {
            "출발지": start.strip(),
            "도착지": end.strip(),
            "이동 거리(km)": distance,
            "주행 시간(분)": minutes,
            "평균 속도(km/h)": round(speed, 2)
        }

        st.session_state.records.append(record)
        st.success("주행 기록이 저장되었습니다.")

st.subheader("주행 기록 목록")

if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    st.dataframe(df, use_container_width=True)

    selected = st.selectbox(
        "삭제할 기록 선택",
        range(len(st.session_state.records)),
        format_func=lambda i: (
            f"{i + 1}. "
            f"{st.session_state.records[i]['출발지']} → "
            f"{st.session_state.records[i]['도착지']}"
        )
    )

    if st.button("선택한 기록 삭제"):
        st.session_state.records.pop(selected)
        st.rerun()
else:
    st.info("아직 저장된 주행 기록이 없습니다.")
