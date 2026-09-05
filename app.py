import streamlit as st
import requests
import re
from datetime import date, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="무학여고 오늘의 급식",
    page_icon="🌸",
    layout="centered"
)

# 학교 정보 상수
OFFICE_CODE = "B10"        # 서울특별시교육청
SCHOOL_CODE = "7010079"    # 무학여자고등학교
SCHOOL_NAME = "무학여자고등학교"
MEAL_CODE = "2"            # 중식 고정 코드

# 2. 파스텔 감성 스타일 & 폰트
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dongle:wght@400;700&family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Gaegu', cursive, 'Noto Sans KR', sans-serif;
    }

    /* 상단 헤더 */
    .header-box {
        text-align: center;
        padding: 10px 0 6px 0;
    }
    .sub-badge {
        display: inline-block;
        background-color: #FFE5EC;
        color: #D63384;
        font-size: 1.15rem;
        font-weight: 700;
        padding: 3px 14px;
        border-radius: 20px;
        margin-bottom: 4px;
    }
    .main-title {
        font-family: 'Dongle', sans-serif;
        font-size: 3.4rem;
        font-weight: 700;
        color: #3D3A45;
        margin: 0;
        line-height: 1;
    }

    /* 현재 날짜 강조 뱃지 */
    .date-indicator-box {
        text-align: center;
        margin: 12px 0 16px 0;
    }
    .date-indicator {
        display: inline-block;
        background: #FFF8E7;
        color: #795548;
        font-size: 1.4rem;
        font-weight: 700;
        padding: 6px 20px;
        border-radius: 25px;
        border: 2px dashed #FFD54F;
        letter-spacing: 0.5px;
    }

    /* 날짜 변경 버튼 */
    div[data-testid="stButton"] > button {
        background-color: #FFF3B0 !important;
        color: #5C4D3C !important;
        border: 2px solid #FFE680 !important;
        border-radius: 18px !important;
        font-family: 'Gaegu', cursive !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        padding: 6px 10px !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.04) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #FFE680 !important;
        transform: translateY(-2px);
    }

    /* date_input 텍스트 필드 정돈 */
    div[data-testid="stDateInput"] input {
        font-family: 'Gaegu', cursive !important;
        font-size: 1.2rem !important;
        text-align: center !important;
        border-radius: 16px !important;
        border: 2px solid #E2ECE9 !important;
        background-color: #FAFCFC !important;
        color: #4A4E69 !important;
    }

    /* 메인 급식 카드 */
    .lunch-card {
        background: #FFFFFF;
        border: 2.5px solid #FDE2E4;
        border-radius: 24px;
        padding: 26px 20px;
        box-shadow: 0 8px 20px rgba(253, 226, 228, 0.45);
        margin-top: 10px;
        text-align: center;
    }
    .lunch-header {
        font-family: 'Dongle', sans-serif;
        font-size: 2.7rem;
        color: #FB6F92;
        margin-bottom: 4px;
        line-height: 1;
    }
    .menu-list {
        list-style: none;
        padding: 0;
        margin: 18px 0 14px 0;
    }
    .menu-item {
        font-size: 1.35rem;
        font-weight: 700;
        color: #4A4E69;
        line-height: 1.8;
    }
    .calories-pill {
        display: inline-block;
        background-color: #E8F0FE;
        color: #4361EE;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 5px 16px;
        border-radius: 20px;
        margin-top: 8px;
    }

    /* 급식 없는 날 카드 */
    .empty-card {
        background: #FDFBF7;
        border: 2px dashed #E5DFD3;
        border-radius: 22px;
        padding: 32px 18px;
        text-align: center;
        color: #8D877B;
        font-size: 1.3rem;
        margin-top: 12px;
    }

    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1.5px solid #EAE4E9 !important;
        background-color: #FCFBFD !important;
        font-family: 'Gaegu', cursive !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 날짜 상태 관리 (단일 키 완벽 연동 콜백)
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

def set_prev_day():
    st.session_state.selected_date -= timedelta(days=1)

def set_next_day():
    st.session_state.selected_date += timedelta(days=1)

# 4. 나이스 API 호출 (중식 고정)
@st.cache_data(ttl=3600)
def fetch_lunch(ymd_str):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    api_key = st.secrets.get("NEIS_API_KEY", "sample key")

    params = {
        "KEY": api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 5,
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MMEAL_SC_CODE": MEAL_CODE,
        "MLSV_YMD": ymd_str
    }

    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        if "mealServiceDietInfo" in data:
            rows = data["mealServiceDietInfo"][1]["row"]
            if rows:
                return rows[0]
        return None
    except Exception:
        return None

# 5. 헤더
st.markdown(f"""
    <div class="header-box">
        <span class="sub-badge">🏫 {SCHOOL_NAME}</span>
        <h1 class="main-title">오늘 뭐 먹지? 🍱</h1>
    </div>
""", unsafe_allow_html=True)

# 6. 날짜 이동 컨트롤러
col1, col2, col3 = st.columns([1, 2.3, 1], vertical_alignment="center")

with col1:
    st.button("◀ 어제", on_click=set_prev_day, use_container_width=True)

with col2:
    # key="selected_date"로 직접 연결하여 상태 변경 시 즉각 양방향 반영
    st.date_input(
        "날짜 선택",
        key="selected_date",
        label_visibility="collapsed"
    )

with col3:
    st.button("내일 ▶", on_click=set_next_day, use_container_width=True)

# 7. 현재 선택된 날짜 텍스트 (화살표/달력 변경 시 실시간 반영)
active_date = st.session_state.selected_date
weekday_korean = ["월", "화", "수", "목", "금", "토", "일"][active_date.weekday()]
formatted_display_date = active_date.strftime(f"%Y년 %m월 %d일 ({weekday_korean})")

st.markdown(f"""
    <div class="date-indicator-box">
        <span class="date-indicator">📅 {formatted_display_date}</span>
    </div>
""", unsafe_allow_html=True)

# 8. 급식 데이터 조회 및 렌더링
ymd = active_date.strftime("%Y%m%d")
lunch_data = fetch_lunch(ymd)

if lunch_data:
    raw_dish = lunch_data.get("DDISH_NM", "")
    cal_info = lunch_data.get("CAL_INFO", "칼로리 정보 없음")

    # 알레르기 번호 제거
    cleaned = re.sub(r'\([0-9\.\s]+\)', '', raw_dish)
    cleaned = re.sub(r'[0-9\.]+', '', cleaned)
    dishes = [d.strip() for d in cleaned.split("<br/>") if d.strip()]

    dish_html = "".join([f'<li class="menu-item">✨ {dish}</li>' for dish in dishes])
    st.markdown(f"""
        <div class="lunch-card">
            <div class="lunch-header">🍱 오늘의 점심 메뉴</div>
            <ul class="menu-list">
                {dish_html}
            </ul>
            <div class="calories-pill">⚡ {cal_info}</div>
        </div>
    """, unsafe_allow_html=True)

    st.write("")

    with st.expander("🔍 원산지 및 영양 정보"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**[원산지 정보]**")
            orplc = lunch_data.get("ORPLC_INFO", "정보 없음").replace("<br/>", "\n- ")
            st.markdown(f"- {orplc}" if orplc != "정보 없음" else "정보 없음")
        with col_b:
            st.markdown("**[영양성분]**")
            ntr = lunch_data.get("NTR_INFO", "정보 없음").replace("<br/>", "\n- ")
            st.markdown(f"- {ntr}" if ntr != "정보 없음" else "정보 없음")

else:
    st.markdown(f"""
        <div class="empty-card">
            <div style="font-size: 2.2rem; margin-bottom: 6px;">🍃</div>
            <b>{formatted_display_date}</b>에는 급식이 없어요!<br>
            <span style="font-size: 1.05rem; color: #A09A8E;">(주말, 공휴일 또는 방학)</span>
        </div>
    """, unsafe_allow_html=True)
