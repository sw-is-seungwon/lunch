import streamlit as st
import requests
import re
from datetime import date, timedelta

# 페이지 설정
st.set_page_config(
    page_title="무학여고 급식 알리미",
    page_icon="🍱",
    layout="centered"
)

# 학교 정보 상수
OFFICE_CODE = "B10"        # 서울특별시교육청
SCHOOL_CODE = "7010168"    # 무학여자고등학교 행정표준코드
SCHOOL_NAME = "무학여자고등학교"

# 커스텀 스타일 (부드러운 카드 UI)
st.markdown("""
    <style>
    .meal-card {
        background-color: #F8F9FA;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border-left: 5px solid #A0C4FF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .meal-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #2B2D42;
        margin-bottom: 10px;
    }
    .menu-item {
        font-size: 1.05rem;
        line-height: 1.7;
        color: #4A4E69;
    }
    .info-text {
        font-size: 0.85rem;
        color: #8D99AE;
        margin-top: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "target_date" not in st.session_state:
    st.session_state.target_date = date.today()

def change_date(days):
    st.session_state.target_date += timedelta(days=days)

# 나이스 API 호출 함수
@st.cache_data(ttl=3600)
def fetch_meal_data(ymd_str):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    # Streamlit secrets에 등록된 키가 있으면 사용, 없으면 sample key 사용
    api_key = st.secrets.get("NEIS_API_KEY", "sample key")
    
    params = {
        "KEY": api_key,
        "Type": "json",
        "pIndex": 1,
        "pSize": 10,
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MLSV_YMD": ymd_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "mealServiceDietInfo" in data:
            return data["mealServiceDietInfo"][1]["row"]
        return None
    except Exception:
        return None

# 상단 헤더
st.title("🍱 무학여자고등학교 급식")

# 날짜 제어 바
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if st.button("◀ 이전 날", use_container_width=True):
        change_date(-1)
        st.rerun()

with col2:
    selected_date = st.date_input(
        "날짜 선택",
        value=st.session_state.target_date,
        key="date_picker",
        label_visibility="collapsed"
    )
    if selected_date != st.session_state.target_date:
        st.session_state.target_date = selected_date
        st.rerun()

with col3:
    if st.button("다음 날 ▶", use_container_width=True):
        change_date(1)
        st.rerun()

current_ymd = st.session_state.target_date.strftime("%Y%m%d")
formatted_display_date = st.session_state.target_date.strftime("%Y년 %m월 %d일 (%a)")

st.subheader(formatted_display_date)

# 데이터 조회 및 렌더링
meals = fetch_meal_data(current_ymd)

if not meals:
    st.info("해당 날짜에는 등록된 급식 정보가 없습니다. (주말, 공휴일 또는 방학)")
else:
    for meal in meals:
        meal_name = meal.get("MMEAL_SC_NM", "급식")
        raw_dish = meal.get("DDISH_NM", "")
        cal_info = meal.get("CAL_INFO", "칼로리 정보 없음")
        
        # 1. 알레르기 번호 제거 (예: 1.2.5.6. -> 공백)
        # 2. HTML 줄바꿈 태그(<br/>)를 일반 줄바꿈으로 변환
        clean_dish = re.sub(r'[0-9\.]+', '', raw_dish)
        dish_items = [d.strip() for d in clean_dish.split("<br/>") if d.strip()]
        
        st.markdown(f"""
            <div class="meal-card">
                <div class="meal-title">🍴 {meal_name}</div>
                <div class="menu-item">
                    {"<br>".join(dish_items)}
                </div>
                <div class="info-text">⚡ 열량: {cal_info}</div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander(f"{meal_name} 상세 영양/원산지 정보 보기"):
            ntr_info = meal.get("NTR_INFO", "").replace("<br/>", "\n- ")
            orplc_info = meal.get("ORPLC_INFO", "").replace("<br/>", "\n- ")
            st.markdown("**[원산지]**\n- " + (orplc_info if orplc_info else "정보 없음"))
            st.markdown("**[영양성분]**\n- " + (ntr_info if ntr_info else "정보 없음"))
