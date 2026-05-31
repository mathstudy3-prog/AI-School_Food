# =============================================================================
# 학교 급식 저탄소 AI 밸런서 - 영양교사용 데모 웹사이트 (v2 - 매트릭스 반영)
# =============================================================================
#
# [필요한 라이브러리 설치 명령어]
#   pip install streamlit pandas plotly
#
# [실행 방법]
#   streamlit run app.py
#
# [필요한 데이터 파일] (app.py와 같은 폴더에 있어야 합니다)
#   - final_data.csv
#   - dish_recipe.csv
#
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import Counter

# =============================================================================
# 페이지 기본 설정
# =============================================================================
st.set_page_config(
    page_title="학교 급식 저탄소 AI 밸런서",
    page_icon="🌿",
    layout="wide",
)

# =============================================================================
# 전체 CSS 스타일
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #2d6a4f 0%, #40916c 50%, #52b788 100%);
        padding: 2rem 2.5rem; border-radius: 16px; margin-bottom: 1.5rem;
        color: white; box-shadow: 0 4px 20px rgba(45, 106, 79, 0.3);
    }
    .main-header h1 { font-size: 2rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
    .main-header p  { font-size: 0.95rem; margin: 0.4rem 0 0 0; opacity: 0.88; }

    .info-card    { background:#f8fdf9; border:1.5px solid #b7e4c7; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
    .alert-card   { background:#fff5f5; border:2px solid #fc8181;   border-radius:12px; padding:1.2rem 1.5rem; margin:1rem 0; }
    .safe-card    { background:#f0fff4; border:2px solid #68d391;   border-radius:12px; padding:1.2rem 1.5rem; margin:1rem 0; }
    .normal-card  { background:#fffff0; border:2px solid #f6e05e;   border-radius:12px; padding:1.2rem 1.5rem; margin:1rem 0; }

    .matrix-badge {
        display:inline-block; background:#ebf8ff; border:1px solid #90cdf4;
        border-radius:20px; padding:3px 10px; font-size:0.76rem; color:#2c5282; margin:2px;
    }
    .pop-card {
        background: linear-gradient(145deg, #e8f5e9 0%, #f1f8e9 100%);
        border: 2px solid #81c784; border-radius: 20px; padding: 2rem 2.5rem;
        margin: 1.5rem 0; box-shadow: 0 6px 24px rgba(0,0,0,0.08); text-align: center;
    }
    .pop-card h2 { color: #2d6a4f; font-size: 1.6rem; font-weight: 700; margin-bottom: 0.5rem; }
    .pop-card .pop-subtitle { color: #40916c; font-size: 1rem; margin-bottom: 1.2rem; }
    .pop-card .pop-story {
        background: white; border-radius: 12px; padding: 1rem 1.5rem;
        color: #333; font-size: 0.95rem; line-height: 1.8;
        margin-top: 1rem; border-left: 4px solid #52b788; text-align: left;
    }
    .pop-nutrition { display:flex; justify-content:center; gap:1rem; margin:1.2rem 0; flex-wrap:wrap; }
    .pop-nutrition-item {
        background:white; border-radius:10px; padding:0.6rem 1.2rem;
        text-align:center; min-width:80px; border:1px solid #b7e4c7;
    }
    .pop-nutrition-item .label { font-size:0.72rem; color:#666; }
    .pop-nutrition-item .value { font-size:1.1rem; font-weight:700; color:#2d6a4f; }

    .recommend-card { background:#ebf8ff; border:1.5px solid #90cdf4; border-radius:12px; padding:1rem 1.5rem; margin-top:0.7rem; }
    .guide-box {
        background: linear-gradient(135deg, #e6fffa 0%, #ebf8ff 100%);
        border:1.5px solid #81e6d9; border-radius:12px; padding:1.2rem 1.5rem; margin-top:1rem; line-height:1.8;
    }
    .stTabs [data-baseweb="tab"] { font-weight:500; font-size:0.95rem; }
    .stSelectbox label { font-weight:500; color:#2d6a4f; }
    .stButton > button {
        background: linear-gradient(135deg, #2d6a4f, #40916c);
        color:white; border:none; border-radius:8px; font-weight:600;
        padding:0.5rem 2rem; font-family:'Noto Sans KR',sans-serif; transition:all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1b4332, #2d6a4f);
        box-shadow: 0 4px 12px rgba(45,106,79,0.3);
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# ★ 핵심 업그레이드: [핵심식재료 × 조리법] 1:1 매칭 매트릭스 (하드코딩)
# =============================================================================
#
# 이미지 "4단계 정밀 융합 매트릭스" 에서 읽은 실제 값을 모두 내장합니다.
#   키  : (핵심식재료, 조리법) 튜플
#   값  : 해당 조합의 평균 잔반량 (단위: kg, 1인당)
#
# 빈 셀(회색)은 데이터 없음을 의미하며 딕셔너리에 포함하지 않습니다.
# 매트릭스에 없는 조합은 None 반환 → 폴백 로직이 자동 실행됩니다.
# 나중에 값을 수정하고 싶다면 아래 숫자만 바꾸면 됩니다.
# =============================================================================

WASTE_MATRIX = {
    # ─────────── 구이 (Y축 첫 번째 행) ───────────────────────────────────────
    ("닭고기", "구이"): 0.333,
    # 무 × 구이: 빈 셀
    ("김치",   "구이"): 0.238,
    ("감자",   "구이"): 0.328,
    ("두부",   "구이"): 0.334,
    ("떡",     "구이"): 0.293,
    ("돼지고기","구이"): 0.341,
    # 콩나물 × 구이: 빈 셀
    ("계란",   "구이"): 0.313,
    ("야채",   "구이"): 0.350,
    # 어묵 × 구이: 빈 셀
    ("치즈",   "구이"): 0.319,
    ("삼치",   "구이"): 0.324,
    ("고등어", "구이"): 0.316,
    # 갈치, 동태, 주꾸미, 낙지, 오징어 × 구이: 빈 셀

    # ─────────── 볶음 (Y축 두 번째 행) ───────────────────────────────────────
    ("닭고기", "볶음"): 0.379,
    ("무",     "볶음"): 0.318,
    ("김치",   "볶음"): 0.329,
    ("감자",   "볶음"): 0.342,
    ("두부",   "볶음"): 0.322,
    ("떡",     "볶음"): 0.339,
    ("돼지고기","볶음"): 0.305,
    ("콩나물", "볶음"): 0.331,
    ("계란",   "볶음"): 0.338,
    # 야채 × 볶음: 빈 셀
    ("어묵",   "볶음"): 0.334,
    # 치즈, 삼치, 고등어, 갈치 × 볶음: 빈 셀
    ("동태",   "볶음"): 0.331,
    # 주꾸미, 낙지, 오징어 × 볶음: 빈 셀

    # ─────────── 무침 (Y축 세 번째 행) ───────────────────────────────────────
    # 닭고기 × 무침: 빈 셀
    ("무",     "무침"): 0.335,
    # 김치 × 무침: 빈 셀
    # 감자 × 무침: 빈 셀
    ("두부",   "무침"): 0.334,
    # 떡 × 무침: 빈 셀
    ("콩나물", "무침"): 0.342,
    # 계란 × 무침: 빈 셀
    ("야채",   "무침"): 0.343,
    # 나머지 × 무침: 빈 셀

    # ─────────── 찜 (Y축 네 번째 행 - "예미 사전에 정의" 로 표시된 행) ───────
    ("닭고기", "찜"): 0.338,
    ("무",     "찜"): 0.315,
    ("감자",   "찜"): 0.308,
    ("두부",   "찜"): 0.277,
    ("떡",     "찜"): 0.347,
    ("돼지고기","찜"): 0.346,
    ("콩나물", "찜"): 0.341,
    ("계란",   "찜"): 0.262,   # 전체 매트릭스에서 가장 낮은 값
    ("야채",   "찜"): 0.299,
    ("어묵",   "찜"): 0.332,
    ("치즈",   "찜"): 0.316,
    # 삼치, 고등어, 갈치 × 찜: 빈 셀
    ("주꾸미", "찜"): 0.357,
    ("낙지",   "찜"): 0.321,
    # 오징어 × 찜: 빈 셀

    # ─────────── 국물 (Y축 다섯 번째 행 - "볶음 사전에 정의" 로 표시) ─────────
    # 닭고기 × 국물: 빈 셀
    ("무",     "국물"): 0.379,
    # 김치 × 국물: 빈 셀
    ("두부",   "국물"): 0.334,
    ("떡",     "국물"): 0.356,
    ("돼지고기","국물"): 0.346,
    # 콩나물 × 국물: 빈 셀
    ("계란",   "국물"): 0.360,
    # 야채 × 국물: 빈 셀
    ("갈치",   "국물"): 0.379,
    # 나머지 × 국물: 빈 셀

    # ─────────── 조림 (Y축 여섯 번째 행) ─────────────────────────────────────
    ("닭고기", "조림"): 0.337,
    # 무 × 조림: 빈 셀
    ("김치",   "조림"): 0.367,
    # 감자, 두부, 떡 × 조림: 빈 셀
    ("돼지고기","조림"): 0.370,
    ("콩나물", "조림"): 0.291,
    ("계란",   "조림"): 0.386,
    ("야채",   "조림"): 0.396,   # 전체 매트릭스에서 가장 높은 값
    # 나머지 × 조림: 빈 셀

    # ─────────── 끓임/삶음 (Y축 일곱 번째 행) ────────────────────────────────
    ("닭고기", "끓임"): 0.317,
    # 무 × 끓임: 빈 셀
    ("감자",   "끓임"): 0.289,
    ("두부",   "끓임"): 0.310,
    ("떡",     "끓임"): 0.314,
    ("돼지고기","끓임"): 0.318,
    # 콩나물 × 끓임: 빈 셀
    ("야채",   "끓임"): 0.319,
    # 어묵 × 끓임: 빈 셀
    ("치즈",   "끓임"): 0.349,
    # 나머지 × 끓임: 빈 셀
}

# ── 잔반 그룹 판정 기준값 (kg 단위) ──
# 매트릭스 전체 값 범위: 0.238 ~ 0.396
# LOW    < 0.310
# NORMAL : 0.310 이상 0.345 미만
# HIGH   >= 0.345
MATRIX_LOW_THRESHOLD  = 0.310
MATRIX_HIGH_THRESHOLD = 0.345


# =============================================================================
# 식재료 동의어 매핑 테이블
# =============================================================================
# dish_recipe.csv의 핵심식재료 또는 요리명에서 식재료를 추출할 때
# 다양한 표현을 매트릭스 X축 키로 통일합니다.
# 새로운 동의어가 필요하면 이 딕셔너리에 줄을 추가하면 됩니다.
INGREDIENT_ALIAS = {
    # 닭고기 계열
    "닭고기": "닭고기", "닭": "닭고기", "치킨": "닭고기", "닭가슴살": "닭고기",
    # 돼지고기 계열
    "돼지고기": "돼지고기", "돼지": "돼지고기", "삼겹살": "돼지고기",
    "제육": "돼지고기", "돈육": "돼지고기",
    # 소고기는 매트릭스에 없으므로 돼지고기로 근사 처리
    "소고기": "돼지고기", "불고기": "돼지고기", "쇠고기": "돼지고기",
    # 계란
    "계란": "계란", "달걀": "계란",
    # 두부
    "두부": "두부",
    # 콩나물
    "콩나물": "콩나물",
    # 야채/채소 계열 (매트릭스에 "야채"로 통일)
    "야채": "야채", "채소": "야채", "시금치": "야채", "상추": "야채",
    "호박": "야채", "당근": "야채", "브로콜리": "야채", "도라지": "야채",
    "나물": "야채",
    # 김치
    "김치": "김치",
    # 무
    "무": "무",
    # 감자
    "감자": "감자",
    # 떡
    "떡": "떡",
    # 어묵
    "어묵": "어묵",
    # 치즈
    "치즈": "치즈",
    # 생선류
    "삼치": "삼치",
    "고등어": "고등어",
    "갈치": "갈치",
    "동태": "동태", "명태": "동태", "대구": "동태",
    # 해산물
    "주꾸미": "주꾸미",
    "낙지":   "낙지",
    "오징어": "오징어",
}

# dish_recipe.csv 조리법 → 매트릭스 Y축 조리법 정규화
# 튀김은 매트릭스에 별도 행이 없으므로 기름 조리계열인 "볶음"으로 근사합니다.
METHOD_ALIAS = {
    "튀김":   "볶음",   # 기름 요리 계열 근사
    "볶음":   "볶음",
    "구이":   "구이",
    "조림":   "조림",
    "찜":     "찜",
    "무침":   "무침",
    "국물":   "국물",
    "끓임":   "끓임",
    "해당없음": None,   # 매트릭스 조회 불가 → None 반환
}


# =============================================================================
# 데이터 로딩 함수 (캐시 적용)
# =============================================================================
@st.cache_data
def load_data():
    """
    CSV 파일을 불러옵니다.
    파일이 없으면 샘플 데이터를 자동 생성하여 데모가 항상 작동합니다.
    """
    # ── dish_recipe.csv ──
    try:
        recipe_df = pd.read_csv("dish_recipe.csv", encoding="utf-8-sig")
    except FileNotFoundError:
        st.warning("⚠️ dish_recipe.csv 파일이 없어 샘플 데이터를 사용합니다.")
        recipe_df = pd.DataFrame({
            "요리명": [
                "쌀밥", "잡곡밥", "볶음밥", "비빔밥",
                "된장찌개", "김치찌개", "미역국", "육개장", "콩나물국",
                "돈까스", "치킨까스", "불고기", "제육볶음", "갈치조림",
                "시금치나물", "콩나물무침", "도라지무침", "호박나물",
                "배추김치", "깍두기", "열무김치", "오이소박이",
                "계란찜", "두부조림", "어묵볶음", "감자조림",
                "삼겹살구이", "고등어구이", "닭강정", "떡볶이",
            ],
            "조리법": [
                "해당없음", "해당없음", "볶음", "해당없음",
                "국물", "국물", "국물", "국물", "국물",
                "튀김", "튀김", "볶음", "볶음", "조림",
                "무침", "무침", "무침", "무침",
                "해당없음", "해당없음", "해당없음", "해당없음",
                "찜", "조림", "볶음", "조림",
                "구이", "구이", "튀김", "볶음",
            ],
            "매칭근거": [
                "밥류", "밥류", "밥류", "밥류",
                "국/찌개류", "국/찌개류", "국/찌개류", "국/찌개류", "국/찌개류",
                "단백질주요리", "단백질주요리", "단백질주요리", "단백질주요리", "생선주요리",
                "채소보조식", "채소보조식", "채소보조식", "채소보조식",
                "김치류", "김치류", "김치류", "김치류",
                "계란보조식", "두부보조식", "채소보조식", "감자보조식",
                "육류주요리", "생선주요리", "닭고기주요리", "분식주요리",
            ],
            # 핵심식재료: 매트릭스 조회에 사용되는 주 재료
            # (실제 dish_recipe.csv에 이 컬럼이 없으면 INGREDIENT_ALIAS로 요리명에서 추론)
            "핵심식재료": [
                "쌀", "잡곡", "야채", "야채",
                "두부", "김치", "야채", "소고기", "콩나물",
                "돼지고기", "닭고기", "소고기", "돼지고기", "갈치",
                "야채", "콩나물", "야채", "야채",
                "김치", "무", "야채", "야채",
                "계란", "두부", "어묵", "감자",
                "돼지고기", "고등어", "닭고기", "떡",
            ],
            # F열 식단내분류: 밥/국/주/보조/김치
            "식단내분류": [
                "밥", "밥", "밥", "밥",
                "국", "국", "국", "국", "국",
                "주", "주", "주", "주", "주",
                "보조", "보조", "보조", "보조",
                "김치", "김치", "김치", "김치",
                "보조", "보조", "보조", "보조",
                "주", "주", "주", "주",
            ],
        })

    # ── final_data.csv ──
    try:
        final_df = pd.read_csv("final_data.csv", encoding="utf-8-sig")
    except FileNotFoundError:
        st.warning("⚠️ final_data.csv 파일이 없어 샘플 데이터를 사용합니다.")
        final_df = pd.DataFrame({
            "요리명_양념소스, 음료 제외__basket": [
                "쌀밥,된장찌개,돈까스,시금치나물,배추김치",
                "잡곡밥,미역국,불고기,콩나물무침,깍두기",
                "쌀밥,김치찌개,제육볶음,도라지무침,배추김치",
                "쌀밥,육개장,치킨까스,호박나물,열무김치",
                "볶음밥,된장찌개,갈치조림,시금치나물,깍두기",
                "잡곡밥,콩나물국,삼겹살구이,두부조림,배추김치",
                "쌀밥,김치찌개,닭강정,콩나물무침,열무김치",
                "비빔밥,미역국,고등어구이,도라지무침,깍두기",
            ],
            "최종_잔반그룹": ["LOW", "LOW", "NORMAL", "HIGH", "NORMAL", "LOW", "HIGH", "LOW"],
            "1인당 쓰레기양": [45.2, 38.7, 72.1, 115.4, 68.3, 41.0, 108.9, 36.5],
            "핵심식재료_basket": [
                "돼지고기,야채", "소고기,콩나물", "돼지고기,야채",
                "닭고기,야채", "갈치,야채", "돼지고기,두부",
                "닭고기,콩나물", "고등어,야채",
            ],
            "칼로리_평균": [720, 680, 750, 820, 710, 660, 810, 640],
            "탄_평균":    [110, 105, 108, 125, 112,  98, 118,  95],
            "단_평균":    [ 28,  32,  30,  25,  27,  35,  26,  38],
            "지_평균":    [ 18,  15,  22,  28,  20,  14,  26,  12],
        })

    return recipe_df, final_df


# =============================================================================
# 요리 분류 함수 (F열 '식단내분류' 기반)
# =============================================================================
def classify_dishes(recipe_df):
    """
    dish_recipe.csv의 F열 '식단내분류' 값을 기준으로
    요리들을 5개 카테고리로 분류합니다.

    F열 값 → 탭1 카테고리 매핑:
        '밥'  → 밥류
        '국'  → 국/찌개류
        '주'  → 주요리
        '보조' → 보조요리
        '김치' → 김치류

    '식단내분류' 컬럼이 없거나 값이 비어있는 요리는
    기존 매칭근거/조리법 기반 폴백 로직으로 분류합니다.
    """
    if recipe_df is None or recipe_df.empty:
        return {k: ["(데이터 없음)"] for k in ["밥류","국/찌개류","주요리","보조요리","김치류"]}

    if "요리명" not in recipe_df.columns:
        st.error("dish_recipe.csv에 '요리명' 컬럼이 없습니다.")
        return {k: ["(오류)"] for k in ["밥류","국/찌개류","주요리","보조요리","김치류"]}

    # F열 식단내분류 값 → 내부 카테고리 키 매핑 테이블
    # 키: F열에 실제 들어오는 문자열 (strip 후 비교)
    # 값: cats 딕셔너리의 키
    FOOD_CLASS_MAP = {
        "밥":  "밥류",
        "국":  "국/찌개류",
        "주":  "주요리",
        "보조": "보조요리",
        "김치": "김치류",
    }

    # 폴백용: 조리법/매칭근거 기반 분류 (F열 값이 없을 때)
    MAIN_METHODS  = {"튀김", "구이", "볶음", "조림", "찜"}
    HAS_CLASS_COL = "식단내분류" in recipe_df.columns

    cats = {"밥류": [], "국/찌개류": [], "주요리": [], "보조요리": [], "김치류": []}

    for _, row in recipe_df.iterrows():
        name = str(row.get("요리명", "")).strip()
        if not name:
            continue

        placed = False  # 이미 분류됐으면 True

        # ── 1순위: F열 '식단내분류' 값으로 분류 ──────────────────────────
        if HAS_CLASS_COL:
            raw_class = str(row.get("식단내분류", "")).strip()
            # nan, NaN, 빈 문자열 등은 무시
            if raw_class and raw_class.lower() != "nan":
                target_cat = FOOD_CLASS_MAP.get(raw_class)
                if target_cat:
                    cats[target_cat].append(name)
                    placed = True

        # ── 2순위(폴백): F열 없거나 값 비어있을 때 기존 로직 사용 ─────────
        if not placed:
            method = str(row.get("조리법",   "")).strip()
            basis  = str(row.get("매칭근거", "")).strip()
            if basis == "밥류":
                cats["밥류"].append(name)
            elif any(k in basis for k in ["국","찌개","탕"]):
                cats["국/찌개류"].append(name)
            elif basis == "김치류":
                cats["김치류"].append(name)
            elif method in MAIN_METHODS:
                cats["주요리"].append(name)
            elif method == "무침" or "보조" in basis:
                cats["보조요리"].append(name)
            # 위 어디에도 해당 안 되면 건너뜀 (보조식/디저트 등)

    # 카테고리가 비어있으면 기본값 추가 (selectbox 오류 방지)
    for key in cats:
        if not cats[key]:
            cats[key] = ["(해당 없음)"]

    return cats


# =============================================================================
# ★ 핵심 함수: 매트릭스 1건 조회
# =============================================================================
def get_matrix_score(ingredient_raw: str, method_raw: str):
    """
    식재료명과 조리법명을 받아 WASTE_MATRIX 에서 잔반량 점수를 반환합니다.

    동작:
    1. INGREDIENT_ALIAS 로 식재료명 정규화  (예: "닭" -> "닭고기")
    2. METHOD_ALIAS 로 조리법명 정규화      (예: "튀김" -> "볶음")
    3. WASTE_MATRIX[(식재료, 조리법)] 조회
    4. 키가 없거나 정규화 실패 시 None 반환 -> 폴백 로직 작동

    Parameters
    ----------
    ingredient_raw : str  예) "닭고기", "소고기", "야채"
    method_raw     : str  예) "볶음", "튀김", "찜"

    Returns
    -------
    float 또는 None
    """
    ingredient = INGREDIENT_ALIAS.get(str(ingredient_raw).strip(), None)
    if ingredient is None:
        return None

    method = METHOD_ALIAS.get(str(method_raw).strip(), None)
    if method is None:
        return None

    return WASTE_MATRIX.get((ingredient, method), None)


# =============================================================================
# ★ 핵심 업그레이드: 매트릭스 반영 잔반량 예측 함수
# =============================================================================
def predict_food_waste(selected_dishes, final_df, recipe_df):
    """
    선택한 요리들의 잔반량을 3단계 우선순위로 계산합니다.

    [1순위] final_data.csv 과거 데이터: 3개 이상 겹치는 식단 탐색
    [2순위] ★신규★ 매트릭스 기반: 각 요리의 (식재료 x 조리법) 점수 평균
    [3순위] 폴백: 조리법 점수만으로 단순 계산 (매트릭스 조회 실패 시)

    Returns
    -------
    tuple: (그룹str, 1인당쓰레기양g_float, 영양정보dict, 계산방식설명str, 매트릭스상세list)
    """
    SKIP = {"(해당 없음)", "(오류)", "(데이터 없음)"}

    # ── 1순위: 과거 데이터 매칭 ──────────────────────────────────────────────
    matched_rows = []
    if final_df is not None and not final_df.empty:
        basket_col = "요리명_양념소스, 음료 제외__basket"
        if basket_col in final_df.columns:
            for _, row in final_df.iterrows():
                past = [d.strip() for d in str(row.get(basket_col,"")).split(",") if d.strip()]
                if len(set(selected_dishes) & set(past)) >= 3:
                    matched_rows.append(row)

    if matched_rows:
        mdf       = pd.DataFrame(matched_rows)
        avg_waste = mdf["1인당 쓰레기양"].mean()
        group     = mdf["최종_잔반그룹"].value_counts().idxmax()
        nutrition = {}
        for col, lbl in [("칼로리_평균","칼로리"),("탄_평균","탄수화물"),
                          ("단_평균","단백질"),("지_평균","지방")]:
            if col in mdf.columns:
                nutrition[lbl] = round(mdf[col].mean(), 1)
        return group, round(avg_waste, 1), nutrition, "과거 데이터 기반", []

    # ── 2순위: 매트릭스 기반 계산 ────────────────────────────────────────────
    matrix_scores  = []   # {"요리명", "식재료", "조리법", "점수"} 리스트

    for dish in selected_dishes:
        if not dish or dish in SKIP:
            continue

        m = recipe_df[recipe_df["요리명"] == dish]
        if m.empty:
            continue

        method_raw     = str(m.iloc[0].get("조리법",        "")).strip()
        ingredient_raw = str(m.iloc[0].get("핵심식재료",     "")).strip()

        # 핵심식재료 컬럼이 비어있으면 요리명 자체를 식재료 후보로 시도
        if not ingredient_raw:
            ingredient_raw = dish

        score = get_matrix_score(ingredient_raw, method_raw)

        if score is not None:
            matrix_scores.append({
                "요리명": dish,
                "식재료": INGREDIENT_ALIAS.get(ingredient_raw, ingredient_raw),
                "조리법": method_raw,
                "점수":   score,
            })

    if matrix_scores:
        avg_score   = sum(d["점수"] for d in matrix_scores) / len(matrix_scores)
        avg_waste_g = round(avg_score * 1000, 1)   # kg -> g 변환

        if avg_score >= MATRIX_HIGH_THRESHOLD:
            group = "HIGH"
        elif avg_score >= MATRIX_LOW_THRESHOLD:
            group = "NORMAL"
        else:
            group = "LOW"

        nutrition    = {"칼로리": 720, "탄수화물": 108, "단백질": 28, "지방": 20}
        method_label = f"매트릭스 기반 ({len(matrix_scores)}개 요리 조회 성공)"
        return group, avg_waste_g, nutrition, method_label, matrix_scores

    # ── 3순위: 폴백 (조리법 점수 합산) ──────────────────────────────────────
    fb_weights = {"튀김":3,"볶음":2,"조림":1,"구이":1,
                  "찜":0,"무침":-1,"국물":-1,"해당없음":0}
    total_score = 0
    for dish in selected_dishes:
        if dish and dish not in SKIP:
            m = recipe_df[recipe_df["요리명"] == dish]
            if not m.empty:
                total_score += fb_weights.get(str(m.iloc[0]["조리법"]).strip(), 0)

    if total_score >= 5:
        group, avg_waste_g = "HIGH",  110.0
    elif total_score >= 2:
        group, avg_waste_g = "NORMAL", 70.0
    else:
        group, avg_waste_g = "LOW",    40.0

    nutrition    = {"칼로리": 720, "탄수화물": 108, "단백질": 28, "지방": 20}
    method_label = "조리법 점수 기반 폴백 (매트릭스 조회 불가)"
    return group, avg_waste_g, nutrition, method_label, []


# =============================================================================
# =============================================================================
# ① 대체 요리 추천 함수 (기존 유지 + 핵심식재료 컬럼명 자동 감지)
# =============================================================================
def recommend_alternative(selected_main_dish, recipe_df):
    """
    HIGH 잔반 위험 시, 주요리를 아예 다른 요리로 교체할 때 추천합니다.
    매트릭스 점수가 현재보다 낮은 조리법의 요리를 최대 3개 반환합니다.

    반환값 예시:
        [{"요리명": "안동찜닭", "조리법": "찜", "점수": 0.338,
          "식재료": "닭고기", "절감량": 0.041}, ...]
    """
    # 핵심 식재료 컬럼명 자동 감지 (공백 있는 버전 / 없는 버전 모두 대응)
    ING_COL = "핵심 식재료" if "핵심 식재료" in recipe_df.columns else "핵심식재료"

    m = recipe_df[recipe_df["요리명"] == selected_main_dish]
    if m.empty:
        return []

    current_method = str(m.iloc[0].get("조리법",  "")).strip()
    current_ing    = str(m.iloc[0].get(ING_COL,   "")).strip()
    # 복수 식재료면 첫 번째만 매트릭스 조회 키로 사용
    current_ing_first = current_ing.split(",")[0].strip()
    current_score     = get_matrix_score(current_ing_first, current_method)

    # 매트릭스에서 현재 식재료 기준 더 낮은 점수의 조리법 목록 추출
    better_methods = []
    norm_ing = INGREDIENT_ALIAS.get(current_ing_first, None)
    if norm_ing and current_score is not None:
        norm_curr_mth = METHOD_ALIAS.get(current_method)
        for (ing, mth), score in WASTE_MATRIX.items():
            if ing == norm_ing and mth != norm_curr_mth and score < current_score:
                better_methods.append((mth, score))
        better_methods.sort(key=lambda x: x[1])

    # 조리법 우선순위: 매트릭스 추천 → 기본 저위험 순
    low_waste_order = [mth for mth, _ in better_methods] + ["찜","구이","무침","조림"]
    seen = set()
    low_waste_order = [x for x in low_waste_order if not (x in seen or seen.add(x))]

    alternatives = []
    for method in low_waste_order:
        if method == current_method:
            continue
        for _, crow in recipe_df[recipe_df["조리법"] == method].iterrows():
            cname = str(crow.get("요리명","")).strip()
            if not cname or cname == selected_main_dish:
                continue
            if cname in [a["요리명"] for a in alternatives]:
                continue
            alt_ing   = str(crow.get(ING_COL,"")).split(",")[0].strip()
            alt_score = get_matrix_score(alt_ing, method)
            절감량    = round(current_score - alt_score, 3) if (current_score and alt_score) else None
            alternatives.append({
                "요리명": cname,
                "조리법": method,
                "점수":   alt_score,
                "식재료": alt_ing,
                "절감량": 절감량,
            })
        if len(alternatives) >= 3:
            break

    alternatives.sort(key=lambda x: (x["점수"] is None, x["점수"] or 9))
    return alternatives[:3]


# =============================================================================
# ② 신규: 동일 식재료 + 대체 조리법 추천 함수
# =============================================================================
def recommend_cooking_method(selected_main_dish, recipe_df):
    """
    HIGH 잔반 위험 시, 요리를 바꾸지 않고 '같은 핵심 식재료'를 사용하면서
    조리법만 달리한 대체 요리를 dish_recipe.csv에서 탐색하여 추천합니다.

    로직:
    1. 현재 주요리의 핵심 식재료(들) 파악
    2. 해당 식재료를 포함한 모든 요리 중 현재 조리법과 다른 것 탐색
    3. 매트릭스 점수 기준으로 현재보다 낮은 것 우선, 없으면 저위험 조리법 순
    4. 최대 3개 반환

    반환값 예시:
        [{"요리명": "닭날개오븐구이", "조리법": "구이", "공통식재료": "닭고기",
          "점수": 0.333, "현재점수": 0.379, "절감량": 0.046}, ...]
    """
    ING_COL = "핵심 식재료" if "핵심 식재료" in recipe_df.columns else "핵심식재료"

    m = recipe_df[recipe_df["요리명"] == selected_main_dish]
    if m.empty:
        return []

    current_method = str(m.iloc[0].get("조리법", "")).strip()
    current_ing_raw = str(m.iloc[0].get(ING_COL, "")).strip()

    # 현재 요리의 식재료 목록 (복수 식재료 모두 수집)
    current_ings = [i.strip() for i in current_ing_raw.split(",") if i.strip()]
    if not current_ings:
        return []

    # 현재 주요리의 매트릭스 점수 (첫 번째 식재료 기준)
    current_score = get_matrix_score(current_ings[0], current_method)

    # 저위험 조리법 우선순위 (잔반 적은 순)
    LOW_RISK_ORDER = ["찜", "구이", "조림", "볶음", "무침", "국물"]

    # 식재료 매칭: 현재 요리의 식재료 중 하나라도 포함된 요리 탐색
    candidates = []
    for _, crow in recipe_df.iterrows():
        cname       = str(crow.get("요리명",  "")).strip()
        cmethod     = str(crow.get("조리법",  "")).strip()
        cing_raw    = str(crow.get(ING_COL,   "")).strip()

        # 자기 자신, 조리법 같은 것, 주요리가 아닌 것 제외
        if not cname or cname == selected_main_dish:
            continue
        if cmethod == current_method:
            continue
        # 보조식/밥류/김치류는 주요리 대체로 부적절하므로 제외
        if cmethod in {"보조식", "밥류", "김치류"}:
            continue

        # 공통 식재료가 있는지 확인
        cings = [i.strip() for i in cing_raw.split(",") if i.strip()]
        common = [ing for ing in current_ings if ing in cings]
        if not common:
            continue

        # 매트릭스 점수 조회 (첫 번째 공통 식재료 기준)
        alt_score = get_matrix_score(common[0], cmethod)
        절감량    = round(current_score - alt_score, 3) \
                   if (current_score is not None and alt_score is not None) else None

        candidates.append({
            "요리명":    cname,
            "조리법":    cmethod,
            "공통식재료": ", ".join(common),
            "점수":      alt_score,
            "현재점수":  current_score,
            "절감량":    절감량,
        })

    if not candidates:
        return []

    # 정렬 우선순위:
    # 1) 현재 점수보다 낮은 것 먼저 (절감량 높은 순)
    # 2) 매트릭스 점수 없는 것은 저위험 조리법 순서로
    def sort_key(c):
        # 절감량이 있고 양수인 것: 절감량 높은 순 (음수로 변환)
        if c["절감량"] is not None and c["절감량"] > 0:
            return (0, -c["절감량"])
        # 매트릭스 점수 있지만 개선 없음
        if c["점수"] is not None:
            return (1, c["점수"])
        # 매트릭스 점수 없음: 저위험 조리법 순서
        try:
            order = LOW_RISK_ORDER.index(c["조리법"])
        except ValueError:
            order = 99
        return (2, order)

    candidates.sort(key=sort_key)
    return candidates[:3]


# =============================================================================
# 식단 POP 컨셉명 생성 함수 (규칙 기반 템플릿)
# =============================================================================
def generate_pop_concept(selected_dishes, recipe_df):
    templates = {
        "튀김": {
            "prefix": "바삭바삭",
            "theme":  "튀김 페스티벌",
            "story":  "오늘은 셰프의 솜씨가 빛나는 바삭한 튀김 특선입니다! 🍳\n기름기가 적고 영양은 가득한 당신을 위한 한 끼.\n🌿 잔반 ZERO에 도전해서 지구도 함께 지켜요!",
        },
        "볶음": {
            "prefix": "불맛 가득",
            "theme":  "웍 요리의 날",
            "story":  "뜨겁게 달군 팬에서 만들어진 불맛 요리가 여러분을 기다립니다! 🔥\n골고루 먹으면 오후 수업도 더 집중할 수 있어요!\n🌿 잔반을 줄이면 탄소발자국도 줄어들어요!",
        },
        "찜": {
            "prefix": "촉촉한",
            "theme":  "스팀 건강식 Day",
            "story":  "기름 없이 영양을 쏙 담은 건강한 찜 요리 특선입니다! 🥦\n탄소 배출도 적은 친환경 메뉴예요.\n🌿 지구를 위해, 오늘 잔반 없이 먹어요!",
        },
        "구이": {
            "prefix": "고소한",
            "theme":  "그릴 특선의 날",
            "story":  "직화로 구워낸 고소함이 가득한 구이 요리 특선! 🥩\n단백질이 풍부해 성장기 여러분에게 딱 맞는 메뉴입니다!\n🌿 오늘도 잔반 제로, 지구가 고마워해요!",
        },
        "무침": {
            "prefix": "상큼한",
            "theme":  "비건 나물 Day",
            "story":  "신선한 채소를 가볍게 무쳐 만든 건강 식단이에요! 🥗\n탄소 배출이 가장 적은 친환경 조리법으로 만들었습니다.\n🌿 채소 한 입이 지구를 살리는 한 걸음!",
        },
        "국물": {
            "prefix": "따뜻한",
            "theme":  "국물 힐링 Day",
            "story":  "몸과 마음을 따뜻하게 해주는 국물 요리 특선! 🍲\n정성껏 끓인 국물에는 영양과 사랑이 담겨 있어요.\n🌿 국물까지 비우면 잔반 ZERO 챌린지 성공!",
        },
    }
    methods_used = []
    for dish in selected_dishes:
        if dish and dish not in ["(해당 없음)", "(오류)"]:
            row = recipe_df[recipe_df["요리명"] == dish]
            if not row.empty:
                mth = str(row.iloc[0]["조리법"]).strip()
                if mth != "해당없음":
                    methods_used.append(mth)

    dominant = Counter(methods_used).most_common(1)[0][0] if methods_used else "국물"
    tpl = templates.get(dominant, templates["국물"])
    return f"{tpl['prefix']} {tpl['theme']}", tpl["story"], dominant


# =============================================================================
# 메인 UI 구성
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>🌿 학교 급식 저탄소 AI 밸런서</h1>
    <p>영양교사를 위한 잔반 예측 · 식단 POP 제작 · 식단 분석 통합 관리 시스템</p>
</div>
""", unsafe_allow_html=True)

recipe_df, final_df = load_data()
categories = classify_dishes(recipe_df)

for key, default in [("selected_dishes", {}), ("prediction_result", None), ("nutrition_info", {})]:
    if key not in st.session_state:
        st.session_state[key] = default

tab1, tab2, tab3 = st.tabs(["🔮 잔반량 예측 모드", "📋 식단 POP 제작 모드", "📊 식단 분석 모드"])


# =============================================================================
# 탭 1: 잔반량 예측 모드
# =============================================================================
with tab1:
    st.subheader("🔮 오늘의 식단 잔반량 예측")
    st.markdown("""
    <div class="info-card">
        오늘 급식 메뉴를 선택하면 <strong>[핵심식재료 × 조리법] 매트릭스</strong>와
        과거 데이터를 결합하여 <strong>예상 잔반 그룹</strong>과
        <strong>1인당 예상 쓰레기양</strong>을 계산합니다.<br>
        <small style="color:#40916c">※ 매트릭스 조회가 가능한 요리는 상세 점수가 표시됩니다.</small>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        selected_rice   = st.selectbox("🍚 밥류",      categories.get("밥류",     ["(해당 없음)"]))
        selected_soup   = st.selectbox("🍲 국/찌개류", categories.get("국/찌개류", ["(해당 없음)"]))
        selected_main   = st.selectbox("🍖 주요리",    categories.get("주요리",    ["(해당 없음)"]))
    with col2:
        selected_side   = st.selectbox("🥗 보조요리",  categories.get("보조요리",  ["(해당 없음)"]))
        selected_kimchi = st.selectbox("🥬 김치류",    categories.get("김치류",    ["(해당 없음)"]))

    selected_dishes = [selected_rice, selected_soup, selected_main, selected_side, selected_kimchi]
    st.session_state["selected_dishes"] = {
        "밥류": selected_rice, "국/찌개류": selected_soup, "주요리": selected_main,
        "보조요리": selected_side, "김치류": selected_kimchi,
    }

    st.markdown("---")
    st.markdown("**📌 선택된 오늘의 식단:**")
    st.markdown(" &nbsp;|&nbsp; ".join(
        f"**{v}**" for v in selected_dishes if v and v not in ["(해당 없음)", "(오류)"]
    ))

    if st.button("🔍 잔반량 예측하기", key="predict_btn"):
        with st.spinner("매트릭스 데이터를 분석 중입니다..."):
            group, waste_g, nutrition, method_label, matrix_detail = predict_food_waste(
                selected_dishes, final_df, recipe_df
            )

        st.session_state["prediction_result"] = {
            "group": group, "waste_amount": waste_g, "method_label": method_label
        }
        st.session_state["nutrition_info"] = nutrition

        # 계산 방식 안내
        st.markdown(
            f"<small>📌 계산 방식: <strong>{method_label}</strong></small>",
            unsafe_allow_html=True
        )

        # ── 매트릭스 상세 조회 결과 표시 ──────────────────────────────────
        if matrix_detail:
            with st.expander("🔬 매트릭스 조회 상세 내역 보기 (클릭하여 펼치기)"):
                st.markdown(
                    "각 요리의 **[핵심식재료 × 조리법]** 조합으로 조회한 실제 매트릭스 잔반량 점수입니다."
                )
                dcols = st.columns(len(matrix_detail))
                for i, d in enumerate(matrix_detail):
                    with dcols[i]:
                        if d["점수"] >= MATRIX_HIGH_THRESHOLD:
                            score_color = "#c53030"   # 빨강 (HIGH)
                        elif d["점수"] >= MATRIX_LOW_THRESHOLD:
                            score_color = "#744210"   # 노랑 (NORMAL)
                        else:
                            score_color = "#276749"   # 초록 (LOW)

                        st.markdown(
                            f"<div style='text-align:center; background:#f8fdf9; border-radius:10px;"
                            f"padding:0.8rem; border:1px solid #b7e4c7;'>"
                            f"<div style='font-size:0.78rem; color:#555; margin-bottom:4px'>{d['요리명']}</div>"
                            f"<div class='matrix-badge'>{d['식재료']} × {d['조리법']}</div><br>"
                            f"<div style='font-size:1.4rem; font-weight:700; color:{score_color}; margin-top:4px'>"
                            f"{d['점수']:.3f} kg</div>"
                            f"<div style='font-size:0.72rem; color:#888'>= {d['점수']*1000:.0f}g</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                avg_shown = sum(d["점수"] for d in matrix_detail) / len(matrix_detail)
                st.markdown(
                    f"<div style='text-align:right; font-size:0.84rem; color:#555; margin-top:0.6rem'>"
                    f"매트릭스 평균: <strong>{avg_shown:.3f} kg</strong> &nbsp;|&nbsp;"
                    f" LOW &lt; {MATRIX_LOW_THRESHOLD} &nbsp;|&nbsp;"
                    f" HIGH ≥ {MATRIX_HIGH_THRESHOLD}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        # ── 결과 카드 출력 ─────────────────────────────────────────────────
        if group == "HIGH":
            st.error("🚨 예상 잔반량 위험군 진입!")
            st.markdown(f"""
            <div class="alert-card">
                <h3 style="color:#e53e3e; margin:0">⚠️ 잔반 그룹: HIGH (위험)</h3>
                <p style="margin:0.5rem 0 0 0; color:#c53030">
                    예상 1인당 쓰레기양: <strong>{waste_g}g</strong><br>
                    선택하신 식단의 [식재료×조리법] 조합 평균이
                    위험 기준({MATRIX_HIGH_THRESHOLD} kg)을 초과합니다.<br>
                    아래 두 가지 방법으로 잔반을 줄일 수 있습니다.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # ── 두 추천을 2열로 나란히 표시 ──────────────────────────────
            rec_col_left, rec_col_right = st.columns(2)

            # ── 왼쪽: 대체 요리 추천 ─────────────────────────────────────
            with rec_col_left:
                st.markdown(
                    "<div style='background:#fff5f5; border:1.5px solid #fc8181; "
                    "border-radius:12px; padding:0.9rem 1.1rem; margin-bottom:0.5rem'>"
                    "<h4 style='color:#c53030; margin:0 0 0.3rem 0'>🔄 방법 1: 주요리 교체 추천</h4>"
                    "<small style='color:#888'>지금 선택한 요리 대신 이 요리로 바꿔보세요</small>"
                    "</div>",
                    unsafe_allow_html=True
                )
                alts = recommend_alternative(selected_main, recipe_df)
                if alts:
                    for i, alt in enumerate(alts):
                        score_txt  = f"{alt['점수']:.3f}kg" if alt["점수"] is not None else "—"
                        saving_txt = (
                            f"<span style='color:#276749; font-weight:700'>"
                            f"▼ {alt['절감량']*1000:.0f}g 절감 예상</span>"
                            if alt.get("절감량") and alt["절감량"] > 0
                            else ""
                        )
                        rank_icon = ["🥇","🥈","🥉"][i]
                        st.markdown(
                            f"<div style='background:white; border:1px solid #fed7d7; "
                            f"border-radius:10px; padding:0.75rem 1rem; margin-bottom:0.5rem'>"
                            f"<div style='display:flex; justify-content:space-between; align-items:center'>"
                            f"<span>{rank_icon} <strong>{alt['요리명']}</strong></span>"
                            f"<span style='background:#bee3f8; padding:2px 8px; border-radius:12px;"
                            f"font-size:0.78rem; color:#2c5282'>{alt['조리법']}</span>"
                            f"</div>"
                            f"<div style='font-size:0.8rem; color:#666; margin-top:4px'>"
                            f"매트릭스 점수: {score_txt} &nbsp; {saving_txt}"
                            f"</div></div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info("현재 데이터에서 적합한 대체 요리를 찾지 못했습니다.")

            # ── 오른쪽: 동일 식재료 + 대체 조리법 추천 ──────────────────
            with rec_col_right:
                st.markdown(
                    "<div style='background:#ebf8ff; border:1.5px solid #90cdf4; "
                    "border-radius:12px; padding:0.9rem 1.1rem; margin-bottom:0.5rem'>"
                    "<h4 style='color:#2b6cb0; margin:0 0 0.3rem 0'>🍳 방법 2: 조리법만 바꾸기</h4>"
                    "<small style='color:#888'>같은 식재료, 조리법만 달리하면 잔반을 줄일 수 있어요</small>"
                    "</div>",
                    unsafe_allow_html=True
                )
                method_recs = recommend_cooking_method(selected_main, recipe_df)
                if method_recs:
                    for i, rec in enumerate(method_recs):
                        score_txt  = f"{rec['점수']:.3f}kg" if rec["점수"] is not None else "—"
                        saving_txt = (
                            f"<span style='color:#276749; font-weight:700'>"
                            f"▼ {rec['절감량']*1000:.0f}g 절감 예상</span>"
                            if rec.get("절감량") and rec["절감량"] > 0
                            else ""
                        )
                        rank_icon = ["🥇","🥈","🥉"][i]
                        st.markdown(
                            f"<div style='background:white; border:1px solid #bee3f8; "
                            f"border-radius:10px; padding:0.75rem 1rem; margin-bottom:0.5rem'>"
                            f"<div style='display:flex; justify-content:space-between; align-items:center'>"
                            f"<span>{rank_icon} <strong>{rec['요리명']}</strong></span>"
                            f"<span style='background:#c6f6d5; padding:2px 8px; border-radius:12px;"
                            f"font-size:0.78rem; color:#276749'>{rec['조리법']}</span>"
                            f"</div>"
                            f"<div style='font-size:0.8rem; color:#555; margin-top:4px'>"
                            f"<span style='background:#ebf8ff; border-radius:8px; padding:1px 7px;"
                            f"font-size:0.75rem; color:#2c5282'>공통 식재료: {rec['공통식재료']}</span>"
                            f"&nbsp; 매트릭스 점수: {score_txt} &nbsp; {saving_txt}"
                            f"</div></div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info("같은 식재료로 만든 다른 조리법 요리를 찾지 못했습니다.")

            # ── 두 추천 방법 요약 안내 ────────────────────────────────────
            st.markdown(
                "<div style='background:#f0fff4; border:1px solid #9ae6b4; border-radius:10px;"
                "padding:0.6rem 1.1rem; margin-top:0.3rem; font-size:0.85rem; color:#276749'>"
                "💡 <strong>방법 1</strong>은 메뉴 자체를 바꾸는 방식, "
                "<strong>방법 2</strong>는 같은 식재료를 활용해 조리법만 변경하는 방식입니다. "
                "두 방법 중 하나를 선택하거나 조합하면 잔반을 효과적으로 줄일 수 있습니다."
                "</div>",
                unsafe_allow_html=True
            )

        elif group == "NORMAL":
            st.markdown(f"""
            <div class="normal-card">
                <h3 style="color:#b7791f; margin:0">📊 잔반 그룹: NORMAL (보통)</h3>
                <p style="margin:0.5rem 0 0 0; color:#744210">
                    예상 1인당 쓰레기양: <strong>{waste_g}g</strong><br>
                    평균 수준의 잔반이 예상됩니다. 무침·찜 비중을 높이면 LOW로 개선할 수 있어요.
                </p>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.success("✅ 훌륭한 식단입니다! 잔반 최소화 예상!")
            st.markdown(f"""
            <div class="safe-card">
                <h3 style="color:#276749; margin:0">🌿 잔반 그룹: LOW (최소)</h3>
                <p style="margin:0.5rem 0 0 0; color:#22543d">
                    예상 1인당 쓰레기양: <strong>{waste_g}g</strong><br>
                    잔반이 적게 발생하는 훌륭한 저탄소 식단입니다! 🎉
                </p>
            </div>
            """, unsafe_allow_html=True)

        if nutrition:
            st.markdown("**🥗 예상 영양정보 (1인 기준):**")
            nc1, nc2, nc3, nc4 = st.columns(4)
            nc1.metric("🔥 칼로리",   f"{nutrition.get('칼로리','-')} kcal")
            nc2.metric("🌾 탄수화물", f"{nutrition.get('탄수화물','-')} g")
            nc3.metric("🥩 단백질",   f"{nutrition.get('단백질','-')} g")
            nc4.metric("🧈 지방",     f"{nutrition.get('지방','-')} g")


# =============================================================================
# 탭 2: 식단 POP 제작 모드
# =============================================================================
with tab2:
    st.subheader("📋 식단 POP 제작 모드")
    st.markdown("""
    <div class="info-card">
        탭 1에서 선택한 식단을 기반으로 학생들이 흥미를 가질 만한
        <strong>급식 POP 카드</strong>를 자동으로 생성합니다.
    </div>
    """, unsafe_allow_html=True)

    dishes_dict    = st.session_state.get("selected_dishes", {})
    nutrition_info = st.session_state.get("nutrition_info", {})
    pred_result    = st.session_state.get("prediction_result", None)

    if dishes_dict:
        st.markdown("**📌 현재 선택된 식단 (탭 1 기준):**")
        pcols = st.columns(len(dishes_dict))
        for i, (cat, dish) in enumerate(dishes_dict.items()):
            with pcols[i]:
                st.markdown(
                    f"<div style='text-align:center; background:#f0fff4; border-radius:8px;"
                    f"padding:0.5rem; border:1px solid #b7e4c7;'>"
                    f"<small style='color:#666'>{cat}</small><br>"
                    f"<strong style='color:#2d6a4f'>{dish}</strong></div>",
                    unsafe_allow_html=True
                )
    else:
        st.info("💡 먼저 **탭 1(잔반량 예측 모드)**에서 식단을 선택해 주세요.")

    st.markdown("")

    if st.button("🎨 식단 POP 생성하기", key="pop_btn"):
        if not dishes_dict:
            st.warning("탭 1에서 식단을 먼저 선택해 주세요.")
        else:
            dish_list = list(dishes_dict.values())
            concept_name, story_text, dominant_method = generate_pop_concept(dish_list, recipe_df)

            g = (pred_result or {}).get("group", "")
            group_badge = {"LOW":"🟢 잔반 예상 LOW","NORMAL":"🟡 잔반 예상 NORMAL","HIGH":"🔴 잔반 예상 HIGH"}.get(g,"")

            nutrition_html = ""
            if nutrition_info:
                nutrition_html = '<div class="pop-nutrition">'
                for lbl, val, unit in [
                    ("🔥 칼로리",   nutrition_info.get("칼로리","-"),   "kcal"),
                    ("🌾 탄수화물", nutrition_info.get("탄수화물","-"), "g"),
                    ("🥩 단백질",   nutrition_info.get("단백질","-"),   "g"),
                    ("🧈 지방",     nutrition_info.get("지방","-"),     "g"),
                ]:
                    nutrition_html += (
                        f'<div class="pop-nutrition-item">'
                        f'<div class="label">{lbl}</div>'
                        f'<div class="value">{val}{unit}</div></div>'
                    )
                nutrition_html += "</div>"

            menu_html = " · ".join(
                f"<span style='font-weight:600; color:#2d6a4f'>{d}</span>"
                for d in dish_list if d not in ["(해당 없음)","(오류)"]
            )

            badge_html = (
                f'<div style="display:inline-block; background:#e6fffa; border:1px solid #81e6d9;'
                f'border-radius:20px; padding:3px 14px; font-size:0.82rem; color:#234e52;'
                f'margin-bottom:0.8rem">{group_badge}</div>'
            ) if group_badge else ""

            st.markdown(f"""
            <div class="pop-card">
                <div style="font-size:0.85rem; color:#40916c; letter-spacing:2px; margin-bottom:0.3rem">
                    오늘의 급식 메뉴 · 저탄소 식단
                </div>
                <h2>🌿 {concept_name}</h2>
                <div class="pop-subtitle">{menu_html}</div>
                {badge_html}
                {nutrition_html}
                <div class="pop-story">{story_text.replace(chr(10), "<br>")}</div>
                <div style="margin-top:1.2rem; font-size:0.78rem; color:#68a085">
                    🌍 우리 학교 급식은 탄소 배출을 줄이기 위해 노력합니다. | 잔반 제로 챌린지 참여해주세요!
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.success("✅ 식단 POP가 생성되었습니다! 위 내용을 출력하거나 디스플레이에 활용하세요.")


# =============================================================================
# 탭 3: 식단 분석 모드
# =============================================================================
with tab3:
    st.subheader("📊 한 달 식단 분석 모드")
    st.markdown("""
    <div class="info-card">
        한 달 치 식단 요리명을 입력하면 <strong>핵심 식재료 분포</strong>와
        <strong>조리법 비율</strong>을 나란히 시각화하고
        <strong>매트릭스 기반 저탄소 가이드</strong>를 제공합니다.<br>
        <small style="color:#40916c">
            ※ 핵심 식재료 통계는 밥류·김치류 요리를 제외하며,
            요리 하나에 여러 식재료가 있으면 모두 개별 집계합니다.
        </small>
    </div>
    """, unsafe_allow_html=True)

    default_menu_text = """잡곡밥, 들깨미역국, 돼지갈비찜(육), 숙주나물무침, 깍두기, 두부티라미수
찹쌀밥, 순대국밥, 표고야채만두, 부추겉절이, 깍두기, 쑥꿀떡
보리밥, 감자고추장찌개, 세발나물양파무침, 대패삼겹살볶음(전), 보쌈김치, 사과(한조각)
기장밥(전), 북어국(육), 김자반, 고구마닭갈비, 모짜렐라치즈볼, 총각김치
두부무침/달래양념장, 현미밥, 사골떡국, 제육볶음(육), 배추김치
흑미밥, 육개장, 감자채볶음, 닭날개오븐구이, 배추김치, 파인애플(40g)
참치야채비빔밥, 유부된장국, 맛밤송송함박, 나박김치
잡곡밥, 얼큰순두부국, 마늘쫑&어묵볶음(육), 슈프림치킨, 무생채, 바나나
귀리밥, 오색어묵국, 삶은계란, 밀떡볶이, 야채치즈크로켓, 배추김치
수수밥, 미니해물짬뽕, 참나물&오이무침(육), 유린기, 배추김치
현미밥, 김치수제비(육), 돈육메추리알조림, 고등어구이, 양념깻잎지
플레로티치킨마요덮밥, 팽이버섯장국, 배추김치, 사과주스, 고구마츄러스맛탕
흑미밥, 순살감자탕, 미트볼조림, 쑥갓두부무침, 깍두기, 망고요거트
수수밥, 부대찌개&라면사리, 청포묵김무침, 닭살바베큐오븐구이, 무생채
차조밥, 우렁살된장찌개, (우유)야채계란찜, 돈육김치찜, 깍두기, 사과(한조각)
잡곡밥, 얼큰콩나물국, 분모자간장찜닭, 진미채쪽파무침, 배추김치, 크루키, 자율밥
베트남쌀국수(육), 새우야채짜조롤, 총각김치, 자두주스, (방울)토마토샐러드
보리밥, 닭곰탕大(육), 시금치나물무침, 돈육간장불고기, 배추김치, 오렌지
귀리밥, 두부김치국, 흑돼지숯불바베큐, 콩나물김가루무침, 무쌈, 배추겉절이
양배추샐러드, 카레라이스, 반각오븐구이, 배추김치
귀리밥, 근대된장국, 오이부추무침, 바베큐폭찹스테이크, 배추김치, 유기농초코쌀뻥
홍국쌀밥, 딸기에끌레어, 조랭이꽃떡국, 참나물두부무침, 활짝핀떡갈비, 총각김치
잡곡밥, 감자수제비국, 마라로제찜닭, 달달한토마토, 찹쌀콩멸치볶음, 깍두기, 베이컨&김치볶음밥
맑은콩나물국, 고구마치즈돈가스, 무생채, 우리밀 행운목 케익
짜장밥, 나가사끼짬뽕국(육), 찹쌀꿔바로우, 배추김치"""

    menu_text = st.text_area(
        "📝 한 달 식단 입력 (한 줄 = 하루, 요리명은 쉼표로 구분)",
        value=default_menu_text,
        height=280,
        help="예: 쌀밥, 된장찌개, 돈까스, 시금치나물, 배추김치"
    )

    if st.button("📊 식단 분석하기", key="analyze_btn"):
        if not menu_text.strip():
            st.warning("식단을 입력해 주세요.")
        else:
            with st.spinner("분석 중..."):

                # ── 입력 텍스트에서 요리명 목록 추출 ──────────────────────────
                all_dishes_flat = []
                for line in menu_text.strip().split("\n"):
                    line = line.strip()
                    if line:
                        all_dishes_flat.extend([d.strip() for d in line.split(",") if d.strip()])

                # ── 핵심 식재료 컬럼명 결정 ──────────────────────────────────
                # dish_recipe.csv 실제 파일: "핵심 식재료" (공백 있음)
                # 샘플 데이터(파일 없을 때): "핵심식재료" (공백 없음)
                # 두 경우 모두 대응
                ING_COL = "핵심 식재료" if "핵심 식재료" in recipe_df.columns else "핵심식재료"

                # 밥류·김치류 제외 대상 조리법 집합
                EXCLUDE_METHODS = {"밥류", "김치류"}

                method_counts       = Counter()   # 조리법 집계
                ingredient_counts   = Counter()   # 핵심 식재료 집계 (밥류·김치류 제외)
                unmatched           = []           # 매칭 안 된 요리
                matrix_scores_month = []           # 매트릭스 점수 누적

                for dish in all_dishes_flat:
                    row = recipe_df[recipe_df["요리명"] == dish]

                    if row.empty:
                        # recipe_df에 없는 요리 → 미분류 처리
                        unmatched.append(dish)
                        method_counts["미분류"] += 1
                        continue

                    mth = str(row.iloc[0]["조리법"]).strip()

                    # ── 조리법 집계 (모든 요리 포함) ─────────────────────────
                    method_counts[mth] += 1

                    # ── 핵심 식재료 집계 (밥류·김치류 제외) ──────────────────
                    if mth not in EXCLUDE_METHODS:
                        ing_raw = str(row.iloc[0].get(ING_COL, "")).strip()
                        if ing_raw and ing_raw != "nan":
                            # 쉼표로 구분된 여러 식재료를 모두 개별 집계
                            for ing in ing_raw.split(","):
                                ing = ing.strip()
                                if ing:
                                    ingredient_counts[ing] += 1

                    # ── 매트릭스 점수 수집 ────────────────────────────────────
                    ing_for_matrix = str(row.iloc[0].get(ING_COL, "")).strip()
                    # 여러 식재료 중 첫 번째만 매트릭스 키로 사용
                    first_ing = ing_for_matrix.split(",")[0].strip() if ing_for_matrix else ""
                    score = get_matrix_score(first_ing, mth)
                    if score is not None:
                        matrix_scores_month.append(score)

                total_method = sum(method_counts.values())

                if total_method == 0:
                    st.error("매칭된 요리가 없습니다. 입력 데이터를 확인해 주세요.")
                else:
                    method_pct = {k: round(v / total_method * 100, 1)
                                  for k, v in method_counts.items()}

                    # ── 요약 지표 4개 ─────────────────────────────────────────
                    total_days = len([l for l in menu_text.strip().split("\n") if l.strip()])
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("📅 분석 일수",   f"{total_days}일")
                    col_b.metric("🍽️ 총 요리 수",  f"{total_method}가지")

                    if matrix_scores_month:
                        avg_m   = sum(matrix_scores_month) / len(matrix_scores_month)
                        m_group = ("HIGH"   if avg_m >= MATRIX_HIGH_THRESHOLD else
                                   "NORMAL" if avg_m >= MATRIX_LOW_THRESHOLD  else "LOW")
                        col_c.metric("📐 매트릭스 평균",    f"{avg_m:.3f} kg")
                        col_d.metric("🏷️ 이번달 잔반 등급", m_group)
                    elif unmatched:
                        col_c.metric("❓ 미매칭 요리", f"{len(set(unmatched))}가지")

                    # ── 미매칭 요리 목록 ──────────────────────────────────────
                    if unmatched:
                        with st.expander("❓ dish_recipe.csv에서 찾지 못한 요리 목록"):
                            st.write(sorted(set(unmatched)))

                    st.markdown("---")

                    # ==========================================================
                    # ★ 핵심 신규: 두 차트를 좌우 2열로 나란히 배치
                    # 왼쪽: 핵심 식재료 Top 10 가로 막대 차트
                    # 오른쪽: 조리법 비율 도넛 차트
                    # ==========================================================
                    chart_col_left, chart_col_right = st.columns(2)

                    # ── 왼쪽: 핵심 식재료 Top 10 가로 막대 차트 ─────────────
                    with chart_col_left:
                        st.markdown(
                            "<h4 style='color:#2d6a4f; margin-bottom:0.3rem'>"
                            "🥕 핵심 식재료 사용 빈도 Top 10</h4>"
                            "<small style='color:#888'>밥류·김치류 요리 제외 / 복수 식재료 개별 집계</small>",
                            unsafe_allow_html=True
                        )

                        if ingredient_counts:
                            # 상위 10개 추출 (빈도 높은 순)
                            top10_ing = ingredient_counts.most_common(10)
                            # Plotly 가로 막대 그래프용 데이터 (낮은 빈도가 위로 오도록 역순)
                            ing_names  = [item[0] for item in reversed(top10_ing)]
                            ing_values = [item[1] for item in reversed(top10_ing)]

                            # 빈도에 따른 그라데이션 색상 (진초록 → 연초록)
                            max_v = max(ing_values) if ing_values else 1
                            bar_colors = [
                                f"rgba(45,106,79,{0.4 + 0.6 * (v / max_v):.2f})"
                                for v in ing_values
                            ]

                            fig_ing = go.Figure(data=[go.Bar(
                                x=ing_values,
                                y=ing_names,
                                orientation="h",           # 가로 막대
                                marker_color=bar_colors,
                                text=ing_values,           # 막대 끝에 숫자 표시
                                textposition="outside",
                                hovertemplate="<b>%{y}</b><br>%{x}회 사용<extra></extra>",
                            )])
                            fig_ing.update_layout(
                                margin=dict(t=10, b=10, l=10, r=40),
                                height=380,
                                xaxis=dict(
                                    title="사용 횟수",
                                    title_font=dict(size=12),
                                    gridcolor="#e8f5e9",
                                ),
                                yaxis=dict(
                                    tickfont=dict(size=12),
                                    automargin=True,
                                ),
                                plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                            )
                            st.plotly_chart(fig_ing, use_container_width=True)

                            # 식재료 통계 요약 텍스트
                            top1_ing, top1_cnt = top10_ing[0]
                            total_ing_types = len(ingredient_counts)
                            st.markdown(
                                f"<div style='background:#f0fff4; border-radius:8px; "
                                f"padding:0.6rem 1rem; font-size:0.85rem; color:#2d6a4f; "
                                f"border:1px solid #b7e4c7; margin-top:0.3rem'>"
                                f"🥇 가장 많이 쓴 식재료: <strong>{top1_ing}</strong> ({top1_cnt}회) &nbsp;|&nbsp; "
                                f"총 식재료 종류: <strong>{total_ing_types}종</strong>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            st.info("식재료 데이터를 집계할 수 없습니다. "
                                    "dish_recipe.csv의 '핵심 식재료' 컬럼을 확인해 주세요.")

                    # ── 오른쪽: 조리법 비율 도넛 차트 ───────────────────────
                    with chart_col_right:
                        st.markdown(
                            "<h4 style='color:#2d6a4f; margin-bottom:0.3rem'>"
                            "🍳 조리법 비율 분석</h4>"
                            "<small style='color:#888'>전체 요리 대상 조리법 분포</small>",
                            unsafe_allow_html=True
                        )

                        method_color_map = {
                            "튀김": "#fc8181",   # 빨강 계열 (잔반 위험)
                            "볶음": "#f6ad55",   # 주황 계열
                            "조림": "#f6e05e",   # 노랑 계열
                            "구이": "#68d391",   # 초록 계열
                            "찜":   "#4fd1c5",   # 청록 계열
                            "무침": "#63b3ed",   # 파랑 계열
                            "국물": "#b794f4",   # 보라 계열
                            "보조식":"#a0c4a0",  # 회녹색
                            "밥류": "#d4a76a",   # 갈색 계열
                            "김치류":"#f9a8d4",  # 분홍 계열
                            "미분류":"#e2e8f0",  # 연회색
                        }
                        m_labels = list(method_counts.keys())
                        m_values = list(method_counts.values())
                        m_colors = [method_color_map.get(l, "#cbd5e0") for l in m_labels]

                        fig_method = go.Figure(data=[go.Pie(
                            labels=m_labels,
                            values=m_values,
                            hole=0.45,
                            marker_colors=m_colors,
                            textinfo="label+percent",
                            textfont_size=12,
                            hovertemplate="<b>%{label}</b><br>%{value}회 (%{percent})<extra></extra>",
                        )])
                        fig_method.update_layout(
                            margin=dict(t=10, b=10, l=10, r=10),
                            height=380,
                            legend=dict(
                                orientation="v",
                                x=1.02, y=0.5,
                                font=dict(size=11),
                            ),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig_method, use_container_width=True)

                        # 조리법 통계 요약 텍스트
                        high_risk_pct = sum(method_pct.get(m, 0) for m in ["튀김", "볶음"])
                        low_risk_pct  = sum(method_pct.get(m, 0) for m in ["찜", "무침", "구이"])
                        risk_color = "#c53030" if high_risk_pct >= 40 else (
                                     "#744210" if high_risk_pct >= 25 else "#276749")
                        st.markdown(
                            f"<div style='background:#f0fff4; border-radius:8px; "
                            f"padding:0.6rem 1rem; font-size:0.85rem; color:{risk_color}; "
                            f"border:1px solid #b7e4c7; margin-top:0.3rem'>"
                            f"⚡ 고위험(튀김·볶음): <strong>{high_risk_pct:.1f}%</strong> &nbsp;|&nbsp; "
                            f"🌿 저탄소(찜·무침·구이): <strong>{low_risk_pct:.1f}%</strong>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    st.markdown("---")

                    # ── 저탄소 종합 가이드 ────────────────────────────────────
                    guide_lines = []

                    if high_risk_pct >= 40:
                        guide_lines.append(
                            f"⚠️ 이번 달은 <strong>튀김·볶음 조리법 비중({high_risk_pct:.1f}%)</strong>이 "
                            "높으므로 잔반량이 다소 늘어날 수 있습니다."
                        )
                        guide_lines.append(
                            "➡️ <strong>무침이나 찜 요리 비중을 10% 이상 늘리는 것</strong>을 권장합니다."
                        )
                    elif high_risk_pct >= 25:
                        guide_lines.append(
                            f"📌 튀김·볶음 비중({high_risk_pct:.1f}%)이 다소 높습니다. "
                            "5~10% 줄이면 잔반 감소와 탄소 절감에 효과적입니다."
                        )
                    else:
                        guide_lines.append(f"✅ 튀김·볶음 비중({high_risk_pct:.1f}%)이 적절한 수준입니다.")

                    if low_risk_pct >= 35:
                        guide_lines.append(f"🌿 저탄소 조리법 비중({low_risk_pct:.1f}%)이 우수합니다!")
                    elif low_risk_pct < 20:
                        guide_lines.append(
                            f"💡 찜·무침·구이 등 저탄소 조리법 비중({low_risk_pct:.1f}%)을 늘려보세요."
                        )

                    # 핵심 식재료 편중 여부 진단
                    if ingredient_counts:
                        top3_ings = ingredient_counts.most_common(3)
                        top3_total = sum(v for _, v in top3_ings)
                        all_ing_total = sum(ingredient_counts.values())
                        top3_ratio = top3_total / all_ing_total * 100 if all_ing_total else 0
                        top3_names = "·".join(n for n, _ in top3_ings)
                        if top3_ratio >= 50:
                            guide_lines.append(
                                f"🥕 상위 3개 식재료(<strong>{top3_names}</strong>)가 전체의 "
                                f"<strong>{top3_ratio:.0f}%</strong>를 차지합니다. "
                                "식재료 다양성을 높이면 영양 균형과 저탄소 식단에 도움이 됩니다."
                            )
                        else:
                            guide_lines.append(
                                f"🥕 식재료 다양성이 양호합니다. "
                                f"상위 3개 식재료({top3_names}) 비중: {top3_ratio:.0f}%"
                            )

                    if matrix_scores_month:
                        avg_m = sum(matrix_scores_month) / len(matrix_scores_month)
                        guide_lines.append(
                            f"📐 <strong>매트릭스 기반 이번 달 평균 잔반량: {avg_m:.3f}kg</strong> "
                            f"(LOW 기준 &lt;{MATRIX_LOW_THRESHOLD} / HIGH 기준 ≥{MATRIX_HIGH_THRESHOLD})"
                        )

                    if high_risk_pct < 20 and low_risk_pct >= 30:
                        overall, guide_color = "🏆 이번 달 식단은 저탄소 우수 식단입니다! 계속 유지해 주세요.", "#276749"
                    elif high_risk_pct >= 40:
                        overall, guide_color = "🚨 이번 달 식단은 잔반·탄소 배출 위험 수준입니다. 조리법 개선이 필요합니다.", "#c53030"
                    else:
                        overall, guide_color = "📊 이번 달 식단은 보통 수준입니다. 조금만 개선하면 저탄소 우수 식단이 됩니다!", "#744210"

                    st.markdown(f"""
                    <div class="guide-box">
                        <h4 style="color:{guide_color}; margin:0 0 0.7rem 0">📋 종합 저탄소 가이드</h4>
                        <p style="color:{guide_color}; font-weight:600; margin-bottom:0.7rem">{overall}</p>
                        <p style="color:#333; line-height:1.9">{"<br>".join(guide_lines)}</p>
                        <hr style="border:none; border-top:1px solid #81e6d9; margin:0.8rem 0">
                        <p style="font-size:0.85rem; color:#4a5568; margin:0">
                            💚 <strong>저탄소 식단 TIP</strong>:
                            채소 위주의 무침·찜 요리는 육류 볶음 요리 대비 탄소 배출량이 최대
                            <strong>60% 적습니다.</strong> 지속적인 저탄소 식단으로 건강과 환경을 함께 지켜요!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

# =============================================================================
# 푸터
# =============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#888; font-size:0.82rem; padding:0.5rem'>"
    "🌿 학교 급식 저탄소 AI 밸런서 | 영양교사 데모 시스템 | Powered by Streamlit"
    "</div>",
    unsafe_allow_html=True
)
