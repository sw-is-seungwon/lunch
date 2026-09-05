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
SCHOOL_CODE = "7010168"    # 무학여자고등학교
SCHOOL_NAME = "무학여자고등학교"
MEAL_CODE = "2"            # 중식 고정 코드 (1: 조식, 2: 중식, 3: 석식)

# 2. 귀여운 파스텔톤 스타일 및 웹폰트 (Google Fonts)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dongle:wght@400;700&family=Gaegu:wght@400;700&family=Noto+Sans+KR:wght@400;600&display=swap');

    /* 전체 폰트 및 배경 기본 톤 */
    html, body, [class*="css"] {
        font-family: 'Gaegu', cursive, 'Noto Sans KR', sans-serif;
    }

    /* 최상단 타이틀 영역 */
    .header-box {
        text-align: center;
        padding: 18px 10px 8px 10px;
    }
    .sub-badge {
        display: inline-block;
        background-color: #FFE5EC;
        color: #D63384;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 20px;
        margin-bottom: 6px;
    }
    .main-title {
        font-family: 'Dongle', sans-serif;
        font-size: 3.2rem;
        font-weight: 700;
        color: #3D3A45;
        margin: 0;
        line-height: 1.1;
    }

    /* 날짜 네비게이션 버튼 스타일 */
    div[data-testid="stButton"] > button {
        background-color: #FFF2B2 !important;
        color: #6C584C !important;
        border: 2px solid #FFE680 !important;
        border-radius: 18px !important;
        font-family: 'Gaegu', cursive !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        padding: 6px 12px !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #FFE680 !important;
        transform: translateY(-2px);
    }

    /* date_input 컨테이너 정돈 */
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
        padding: 26px 22px;
        box-shadow: 0 8px 20px rgba(253, 226, 228, 0.45);
        margin-top: 14px;
        text-align: center;
    }
    .lunch-header {
        font-family: 'Dongle', sans-serif;
        font-size: 2.6rem;
        color: #FB6F92;
        margin-bottom: 6px;
        line-height: 1;
    }
    .menu-list {
        list-style: none;
        padding: 0;
        margin: 18px 0 12px 0;
    }
    .menu-item {
        font-size: 1.35rem;
        font-weight: 700;
        color: #4A4E69;
        line-height: 1.8;
        letter-spacing: 0.3px;
    }
    .calories-pill {
        display: inline-block;
        background-color: #E8F0FE;
        color: #4361EE;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 5px 16px;
        border-radius: 20px;
        margin-top: 10px;
    }

    /* 비어있는 날 (주말/방학) 알림 카드 */
    .empty-card {
        background: #FDFBF7;
        border: 2px dashed #E5DFD3;
        border-radius: 22px;
        padding: 34px 20px;
        text-align: center;
        color: #8D877B;
        font-size: 1.3rem;
        margin-top: 14px;
    }

    /* Streamlit 기본 Expander 둥글게 */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1.5px solid #EAE4E9 !important;
        background-color: #FCFBFD !important;
        font-family: 'Gaegu', cursive !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 날짜 상태 관리 (화살표 & 달력 선택 완벽 동기화)
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

def prev_day():
    st.session_state.current_date -= timedelta(days=1)

def next_day():
    st.session_state.current_date += timedelta(days=1)

def update_from_picker():
    st.session_state.current_date = st.session_state.date_picker_value

# 4. 나이스 API 호출 (중식 MMEAL_SC_CODE=2 고정)
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
        "MMEAL_SC_CODE": MEAL_CODE,  # 2: 중식만 요청
        "MLSV_YMD": ymd_str
    }

    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        if "mealServiceDietInfo" in data:
            rows = data["mealServiceDietInfo"][1]["row"]
            if rows:
                return rows[0]  # 중식 단일 데이터 반환
        return None
    except Exception:
        return None

# 5. 상단 헤더 렌더링
st.markdown(f"""
    <div class="header-box">
        <span class="sub-badge">🏫 {SCHOOL_NAME}</span>
        <h1 class="main-title">오늘 뭐 먹지? 🍱</h1>
    </div>
""", unsafe_allow_html=True)

# 6. 날짜 이동 컨트롤러
col1, col2, col3 = st.columns([1, 2.4, 1], vertical_alignment="center")

with col1:
    st.button("◀ 어제", on_click=prev_day, use_container_width=True)

with col2:
    st.date_input(
        "날짜 선택",
        value=st.session_state.current_date,
        key="date_picker_value",
        on_change=update_from_picker,
        label_visibility="collapsed"
    )

with col3:
    st.button("내일 ▶", on_click=next_day, use_container_width=True)

# 요일 매핑
weekday_korean = ["월", "화", "수", "목", "금", "토", "일"][st.session_state.current_date.weekday()]
formatted_display_date = st.session_state.current_date.strftime(f"%Y년 %m월 %d일 ({weekday_korean})")

# 7. 급식 정보 불러오기
ymd = st.session_state.current_date.strftime("%Y%m%d")
lunch_data = fetch_lunch(ymd)

# 8. 화면 출력
if lunch_data:
    raw_dish = lunch_data.get("DDISH_NM", "")
    cal_info = lunch_data.get("CAL_INFO", "칼로리 정보 없음")

    # 알레르기 유발 번호, 특수기호 제거
    cleaned = re.sub(r'\([0-9\.\s]+\)', '', raw_dish)  # (1.2.5) 형태 제거
    cleaned = re.sub(r'[0-9\.]+', '', cleaned)          # 단독 번호 제거
    dishes = [d.strip() for d in cleaned.split("<br/>") if d.strip()]

    # 카드 본문
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

    st.write("")  # 간격 조절

    # 상세 정보 아코디언
    with st.expander("🔍 원산지 및 영양 정보 확인하기"):
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
