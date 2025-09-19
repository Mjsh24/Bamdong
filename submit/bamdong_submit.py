
import streamlit as st

st.set_page_config(
    page_title="대밤동 | 대구 야간관광 경로 추천",
    page_icon="🌃",
    layout="wide",                 # ← 와이드 모드
    initial_sidebar_state="expanded",  # 선택: 사이드바 기본 펼침
    
)

# 페이지 맨위에 앵커 심기 (맨 위로 가기)
st.markdown('<a id="page-top"></a>', unsafe_allow_html=True)

#from streamlit_folium import st_folium
import pandas as pd
from geopy.distance import geodesic
import itertools
import folium
import requests

from streamlit.components.v1 import html  # 파일 맨 위 import 구역에 추가해도 OK 

#import urllib.parse

from urllib.parse import quote
import io
import os
KAKAO_API_KEY = st.secrets.get("KAKAO_API_KEY") or os.getenv("KAKAO_API_KEY")


from pathlib import Path

try:
    from streamlit_sortables import sort_items
    _HAS_SORTABLES = True
except Exception:
    _HAS_SORTABLES = False


# --- 캐시: CSV 로더 ---
@st.cache_data(show_spinner=False)
def load_csv(relpath: str) -> pd.DataFrame:
    base = Path(__file__).resolve().parent  # 현재 파일 기준 상대경로
    return pd.read_csv(base / relpath)


# 딥링크/웹링크 유틸함수
def make_links(start, end):
    # 좌표/이름
    slat, slng = start['mapy'], start['mapx']
    dlat, dlng = end['mapy'], end['mapx']
    sname_q = quote(start['title'])
    dname_q = quote(end['title'])

    # 1) 네이버 앱(모바일) 딥링크
    naver_app = (
        f"nmap://route/car?slat={slat}&slng={slng}&sname={sname_q}"
        f"&dlat={dlat}&dlng={dlng}&dname={dname_q}&appname=com.streamlit.route"
    )

    # 2) 카카오 지도 '웹' 길찾기(PC에서도 확실)
    kakao_web = (
        f"https://map.kakao.com/?sName={sname_q}&sX={slng}&sY={slat}"
        f"&eName={dname_q}&eX={dlng}&eY={dlat}&service=dpath"
    )

    return naver_app, kakao_web

def estimate_walk_minutes_km(slat, slng, dlat, dlng, detour_factor=1.25, speed_kmh=4.5):
    """
    직선거리 → 우회보정(도심 1.2~1.35 권장) → 보행속도(기본 4.5km/h)
    반환: (추정거리_km, 추정시간_분)
    """
    straight_km = geodesic((slat, slng), (dlat, dlng)).km
    est_km = straight_km * detour_factor
    est_min = int(round(est_km / speed_kmh * 60))
    return est_km, est_min
# 포맷터 함수 
def fmt_min_kor(total_min: int) -> str:
    h = total_min // 60
    m = total_min % 60
    if h and m:
        return f"{h}시간 {m}분"
    elif h:
        return f"{h}시간"
    else:
        return f"{m}분"

# QR 도우미
@st.cache_data(show_spinner=False)
def make_qr_bytes(url: str, box_size: int = 6, border: int = 2) -> bytes:

    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    qr = qrcode.QRCode(
        version=None,                      # 자동 버전
        error_correction=ERROR_CORRECT_M,  # 중간 수준(스캔 안정성↑)
        box_size=box_size,                 # 모듈 픽셀 크기
        border=border                      # 외곽 모듈 여백
    )
    qr.add_data(url)
    qr.make(fit=True)
    pil = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return buf.getvalue()



# ---- 데이터 로딩 ----
# -> 파일 위치가 어디든 스크립트 기준 상대경로로 안정적으로 읽혀
df_day = load_csv('../02 야간 관광지 필터링/day_tourlist.csv')
df_night = load_csv('../02 야간 관광지 필터링/night_tourlist.csv')
df_food = load_csv('../02 야간 관광지 필터링/food_list.csv')
df_shop = load_csv('../02 야간 관광지 필터링/shopping_list.csv')
df_stay = load_csv('../02 야간 관광지 필터링/stay_list.csv')


# ---- 헤더 & 스타일 ----
st.markdown("""
    <div style='background-color:#E0F7FA; padding:30px; border-radius:18px; margin-bottom:24px;'>
        <h1 style='color:#0288D1; text-align:center;'>🚶🏻‍♀️‍➡️ 대밤동 🌃
</h1>
        <p style='color:#0288D1; text-align:center; font-size:1.2em;'>
            🧳 쉽고 빠른 나만의 여행동선! 🚗<br>
            대구의 아름다운 밤을 <br>거닐며 탐험하세요.
        </p>
    </div>
""", unsafe_allow_html=True)

# st.markdown("""
#     <div style='background:linear-gradient(90deg,#E3F2FD,#B3E5FC,#E1F5FE); 
#                 padding:32px 20px 18px 20px; border-radius:18px; margin-bottom:18px;
#                 border: 2px solid #4FC3F7;'>
#         <h1 style='color:#039BE5; text-align:center; font-size:2.5em; letter-spacing:-1px;'>🌃 대구 야간 관광<br>맞춤 코스 추천</h1>
#         <p style='color:#0277BD; text-align:center; font-size:1.25em; margin-top:20px;'>
#             하늘빛 감성으로 즐기는<br>
#             <span style='background-color:#B3E5FC; border-radius:8px; padding:3px 8px;'>나만의 여행 루트</span>를 만들어보세요!<br>
#             <span style='color:#01579B;'>필수/선택 코스, 자동 추천, 경로 지도까지 한 번에!</span>
#         </p>
#     </div>
# """, unsafe_allow_html=True)
st.markdown("---")

mode = st.radio(
    "경로 추천 방식을 선택하세요",
    ("자동 추천(카테고리 순서 고정)", "내가 직접 순서 지정(번호 입력)"),
    horizontal=True,
    help="자동 추천: 낮 관광지→음식점→야간 명소→쇼핑→숙박 순서, \n\n각 카테고리는 최적 동선. 직접 지정: 번호로 순서 결정"
)

final_titles, categories = [], []

# ---- 세션 상태 초기화 (자동 추천용) ----
for k in ("food_auto", "shop_auto", "stay_auto", "night_auto"):
    st.session_state.setdefault(k, None)


# --- STEP 1: 낮 관광지 ---
st.markdown("""
    <div style='background-color:#B3E5FC; border-radius:10px; padding:15px; margin-bottom:12px;'>
    <b>🚶‍♂️ STEP 1. 낮 관광지 선택 (필수, 최대 2개)</b>
    </div>
""", unsafe_allow_html=True)
selected_day = st.multiselect(
    "낮 관광지",
    df_day['title'].unique().tolist(),
    max_selections=2,
    label_visibility="collapsed",               # ← 라벨 숨김
    placeholder="낮 관광지를 선택하세요 (최대 2개)"  # ← 안내 문구만 노출
)

final_titles.extend(selected_day)
categories.extend(['day'] * len(selected_day))

# --- STEP 2: 야간 명소 (자동 추천/다시 추천 기능) ---
st.markdown("""
    <div style='background-color:#B3E5FC; border-radius:10px; padding:15px; margin-bottom:12px;'>
    <b>🌌 STEP 2. 야간 명소 선택 (직접 or 자동 추천)</b>
    </div>
""", unsafe_allow_html=True)
col1, col2 = st.columns([8, 2])  # col2를 2로 넓힘
with col1:
    selected_night = st.selectbox("야간 명소", ['(자동 추천)'] + df_night['title'].unique().tolist(), key='sel_night', label_visibility='collapsed')
with col2:
    if selected_night == '(자동 추천)':
        if st.button("야간명소 다시 추천", key='btn_night'):
            st.session_state.night_auto = df_night.sample(1)['title'].iloc[0]
    else:
        st.session_state.night_auto = selected_night

if selected_night == '(자동 추천)':
    if not st.session_state.get('night_auto'):
        st.session_state['night_auto'] = df_night.sample(1)['title'].iloc[0]
    final_titles.append(st.session_state['night_auto'])
    categories.append('night')
else:
    st.session_state['night_auto'] = selected_night
    final_titles.append(selected_night)
    categories.append('night')


# --- STEP 3: 음식점 (자동 추천/다시 추천 기능) ---
st.markdown("""
    <div style='background-color:#B3E5FC; border-radius:10px; padding:15px; margin-bottom:12px;'>
    <b>🍴 STEP 3. 음식점 선택 (직접 or 자동 추천)</b>
    </div>
""", unsafe_allow_html=True)
col1, col2 = st.columns([8, 2])
with col1:
    selected_food = st.selectbox("음식점", ['(자동 추천)'] + df_food['title'].unique().tolist(), key='sel_food', label_visibility='collapsed')
with col2:
    if selected_food == '(자동 추천)':
        if st.button("맛집 다시 추천", key='btn_food'):
            st.session_state.food_auto = df_food.sample(1)['title'].iloc[0]
    else:
        st.session_state.food_auto = selected_food

if selected_food == '(자동 추천)':
    if not st.session_state.get('food_auto'):
        st.session_state['food_auto'] = df_food.sample(1)['title'].iloc[0]
    final_titles.append(st.session_state['food_auto'])
    categories.append('food')
else:
    st.session_state['food_auto'] = selected_food
    final_titles.append(selected_food)
    categories.append('food')


# --- STEP 4: 쇼핑 (옵션, 자동 추천/다시 추천 기능) ---
st.markdown("""
    <div style='background-color:#B3E5FC; border-radius:10px; padding:15px; margin-bottom:12px;'>
    <b>🛍️ STEP 4. 쇼핑 (원하면 추가, 자동 추천 가능)</b>
    </div>
""", unsafe_allow_html=True)
use_shop = st.checkbox("쇼핑 코스 포함", value=False)
if use_shop:
    col1, col2 = st.columns([8, 2])
    with col1:
        selected_shop = st.selectbox("쇼핑 장소", ['(자동 추천)'] + df_shop['title'].unique().tolist(), key='sel_shop', label_visibility='collapsed')
    with col2:
        if selected_shop == '(자동 추천)':
            if st.button("쇼핑 다시 추천", key='btn_shop'):
                st.session_state.shop_auto = df_shop.sample(1)['title'].iloc[0]
        else:
            st.session_state.shop_auto = selected_shop
    if selected_shop == '(자동 추천)':
        if not st.session_state.get('shop_auto'):
            st.session_state['shop_auto'] = df_shop.sample(1)['title'].iloc[0]
        final_titles.append(st.session_state['shop_auto'])
        categories.append('shop')
    else:
        st.session_state['shop_auto'] = selected_shop
        final_titles.append(selected_shop)
        categories.append('shop')

# --- STEP 5: 숙박 (옵션, 자동 추천/다시 추천 기능) ---
st.markdown("""
    <div style='background-color:#B3E5FC; border-radius:10px; padding:15px; margin-bottom:12px;'>
    <b>🏨 STEP 5. 숙박 (원하면 추가, 자동 추천 가능)</b>
    </div>
""", unsafe_allow_html=True)
use_stay = st.checkbox("숙박 코스 포함", value=False)
if use_stay:
    col1, col2 = st.columns([8, 2])
    with col1:
        selected_stay = st.selectbox("숙소", ['(자동 추천)'] + df_stay['title'].unique().tolist(), key='sel_stay', label_visibility='collapsed')
    with col2:
        if selected_stay == '(자동 추천)':
            if st.button("숙소 다시 추천", key='btn_stay'):
                st.session_state.stay_auto = df_stay.sample(1)['title'].iloc[0]
        else:
            st.session_state.stay_auto = selected_stay
    if selected_stay == '(자동 추천)':
        if not st.session_state.get('stay_auto'):
            st.session_state['stay_auto'] = df_stay.sample(1)['title'].iloc[0]
        final_titles.append(st.session_state['stay_auto'])
        categories.append('stay')
    else:
        st.session_state['stay_auto'] = selected_stay
        final_titles.append(selected_stay)
        categories.append('stay')

# --- [모두 새로 추천] 버튼 (STEP 5 바로 아래, df_all 만들기 전) ---

# 자동추천용 세션 상태 기본값(혹시 없으면 생성)
for k in ("food_auto", "shop_auto", "stay_auto", "night_auto"):
    st.session_state.setdefault(k, None)

# 선택값 정리(옵션인 쇼핑/숙박은 체크박스가 꺼져 있으면 None로)
selected_shop_val = selected_shop if use_shop else None
selected_stay_val = selected_stay if use_stay else None

# ⬇️ STEP 5(숙박) 블록 '끝난 직후' (df_all 만들기 전에!)
show_global_refresh = (
    (selected_night == '(자동 추천)') or
    (selected_food == '(자동 추천)') or
    (use_shop and selected_shop == '(자동 추천)') or
    (use_stay and selected_stay == '(자동 추천)')
)

if show_global_refresh:
    

    # 왼쪽 정렬: 버튼을 첫 번째 작은 컬럼에 배치
    col_btn, _ = st.columns([4, 5])
    with col_btn:
        clicked = st.button("🔁 자동 추천 장소 전체 다시 뽑기", key="btn_global_refresh")
        # 한 번만 보여주고 싶으면 다음 줄 추가
        # st.session_state['show_caption'] = False

    # 버튼 설명은 항상 표시
    st.caption("※ 자동 추천으로 설정한 항목(야간명소·맛집·쇼핑·숙소)을 전부 랜덤으로 다시 뽑습니다. 직접 고른 항목은 그대로 유지돼요.")
    # 위의 캡션과 '🗺️ 추천 코스 순서' 사이 여백 줄이기

    if clicked:
        for k in ['food_auto', 'shop_auto', 'stay_auto', 'night_auto']:
            st.session_state[k] = None
        st.rerun()



# --- 장소 정보 합치기 ---
df_all = pd.concat([
    df_day.assign(category='day'),
    df_night.assign(category='night'),
    df_food.assign(category='food'),
    df_shop.assign(category='shop'),
    df_stay.assign(category='stay')
])

final_places = []
for title, cat in zip(final_titles, categories):
    row = df_all[df_all['title'] == title].iloc[0]
    final_places.append({
        'title': title,
        'category': cat,
        'mapx': row['mapx'],
        'mapy': row['mapy'],
        'addr': row['addr'] if 'addr' in row else ''
    })

# --- (필수) TSP용 직선거리 계산 함수: 화면 표시는 안 함 ---
def total_distance(order):
    return sum(
        geodesic(
            (order[i]['mapy'], order[i]['mapx']),
            (order[i+1]['mapy'], order[i+1]['mapx'])
        ).km
        for i in range(len(order)-1)
    )

ordered_course = []

if len(final_places) >= 2:
    if mode.startswith("자동 추천"):
        # 카테고리별로 분리
        places_by_cat = {'day': [], 'food': [], 'night': [], 'shop': [], 'stay': []}
        for place in final_places:
            places_by_cat[place['category']].append(place)

        # day끼리 TSP
        day_order = []
        if len(places_by_cat['day']) > 1:
            day_order = list(min(itertools.permutations(places_by_cat['day']), key=total_distance))
        else:
            day_order = places_by_cat['day']

        # 나머지 카테고리는 순서 그대로
        food_order = places_by_cat['food']
        night_order = places_by_cat['night']
        shop_order = places_by_cat['shop']
        stay_order = places_by_cat['stay']

        # 전체 코스 (논리적 스토리 순서)
        ordered_course = day_order + food_order + night_order + shop_order + stay_order

    elif mode.startswith("내가 직접"):
        st.info("""
        **방문 순서 입력 안내** 
        - 아래에서 **드래그** 또는 **숫자 입력** 방식으로 순서를 정하세요.
        - **1번부터 연속된 번호**로 입력해야 하며, **중복**이 있으면 경고가 뜹니다.
        """)

        # ✅ 드래그로 순서 지정(가능하면 권장)
        use_drag = _HAS_SORTABLES and st.toggle(
            "드래그로 순서 지정(베타)", value=False, help="카드를 끌어서 순서를 바꿔요"
        )

        cat_emo = {"day":"🚶‍♂️","food":"🍴","night":"🌌","shop":"🛍️","stay":"🏨"}
        cat_kor = {"day":"낮 관광지","food":"맛집","night":"야간 명소","shop":"쇼핑","stay":"숙박"}

        ordered_course = []

        if use_drag:
            # 드래그 UI (표는 렌더하지 않음)
            items = [
                f"{idx:02d} | {cat_emo[p['category']]} {p['title']} ({cat_kor[p['category']]})"
                for idx, p in enumerate(final_places)
            ]
            st.caption("아래 항목을 드래그해서 순서를 바꾸세요.")
            new_order = sort_items(items, direction="vertical", key="drag_sort_order")
            ordered_course = [final_places[int(s.split('|', 1)[0])] for s in new_order]

            # 카드 미리보기
            st.markdown("""
                <div id="route-order"
                    style='background-color:#B3E5FC; border-radius:12px; padding:12px; margin:8px 0 8px 0;'>
                    <b>🗺️ 추천 코스 순서</b>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='display:flex;flex-direction:column;gap:6px;'>", unsafe_allow_html=True)
            for i, p in enumerate(ordered_course, 1):
                st.markdown(
                    f"<div style='border:1px solid #E0F2FE; border-radius:10px; padding:8px 10px; background:#F8FBFF;'>"
                    f"<b>{i}. {cat_emo[p['category']]} {p['title']}</b>"
                    f"<div style='opacity:.8; font-size:.9em;'>{p.get('addr','')}</div>"
                    f"</div>", unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # 숫자 입력 방식 (여기에서만 표 렌더)
            df_order = pd.DataFrame({
                '장소': [f"{p['title']} ({p['category']})" for p in final_places],
                '순서': list(range(1, len(final_places) + 1)),
                '주소': [p['addr'] for p in final_places]
            })
            df_edit = st.data_editor(df_order, num_rows="fixed", use_container_width=True)

            seq_list = list(df_edit['순서'])
            has_duplicate = len(seq_list) != len(set(seq_list))
            has_miss = sorted(seq_list) != list(range(1, len(seq_list) + 1))

            if has_duplicate:
                st.error("🚨 **동일한 순서 번호가 있습니다. 각 장소마다 고유한 순서를 부여해주세요.**")
            elif has_miss:
                st.error("🚨 **순서 번호는 1번부터 연속되게 입력해야 합니다. (예: 1,2,3,4...)**")
            else:
                df_edit = df_edit.sort_values('순서')
                for name in df_edit['장소']:
                    for p in final_places:
                        if f"{p['title']} ({p['category']})" == name:
                            ordered_course.append(p)
                            break

                # 카드 미리보기
                st.markdown("""
                    <div id="route-order"
                        style='background-color:#B3E5FC; border-radius:12px; padding:12px; margin:8px 0 8px 0;'>
                        <b>🗺️ 추천 코스 순서</b>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='display:flex;flex-direction:column;gap:6px;'>", unsafe_allow_html=True)
                for i, p in enumerate(ordered_course, 1):
                    st.markdown(
                        f"<div style='border:1px solid #E0F2FE; border-radius:10px; padding:8px 10px; background:#F8FBFF;'>"
                        f"<b>{i}. {cat_emo[p['category']]} {p['title']}</b>"
                        f"<div style='opacity:.8; font-size:.9em;'>{p.get('addr','')}</div>"
                        f"</div>", unsafe_allow_html=True
                    )
                st.markdown("</div>", unsafe_allow_html=True)


# --- 추천 순서, 지도, 합계 ---
if ordered_course:
    if show_global_refresh:
            st.markdown('<div style="height:0;margin-bottom:-12px;"></div>', unsafe_allow_html=True)

    # 2) 자동 추천이면 읽기 전용 표로 미리보기 (호환 안전 버전)
    if mode.startswith("자동 추천"):
        # 🔹 자동 추천도 ‘직접 지정’과 같은 카드 UI 사용
        st.markdown("""
            <div id="route-order"
                style='background-color:#B3E5FC; border-radius:12px; padding:12px; margin:8px 0 8px 0;'>
                <b>🗺️ 추천 코스 순서</b>
            </div>
        """, unsafe_allow_html=True)

        cat_emo = {"day":"🚶‍♂️","food":"🍴","night":"🌌","shop":"🛍️","stay":"🏨"}  # 이미 있다면 재사용
        st.markdown("<div style='display:flex;flex-direction:column;gap:6px;'>", unsafe_allow_html=True)
        for i, p in enumerate(ordered_course, 1):
            st.markdown(
                f"<div style='border:1px solid #E0F2FE; border-radius:10px; padding:8px 10px; background:#F8FBFF;'>"
                f"<b>{i}. {cat_emo[p['category']]} {p['title']}</b>"
                f"<div style='opacity:.8; font-size:.9em;'>{p.get('addr','')}</div>"
                f"</div>", unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # 3) 지도 + 구간별 라디오 + 합계 (두 모드 공통)
    if len(ordered_course) > 1:
        totals_placeholder = st.empty()

        # 지도 생성
        m = folium.Map(location=[35.8714, 128.6014], zoom_start=12)
        color_dict = {'day': 'blue', 'night': 'orange', 'food': 'green', 'shop': 'purple', 'stay': 'red'}
        icon_dict  = {'day': 'info-sign', 'night': 'star', 'food': 'cloud', 'shop': 'shopping-cart', 'stay': 'home'}

        for idx, place in enumerate(ordered_course):
            folium.Marker(
                location=[place['mapy'], place['mapx']],
                popup=f"{idx+1}. {place['title']}",
                tooltip=place['title'],
                icon=folium.Icon(color=color_dict.get(place['category'],'gray'),
                                 icon=icon_dict.get(place['category'],'ok-sign'))
            ).add_to(m)

        folium.PolyLine([(p['mapy'], p['mapx']) for p in ordered_course],
                        color='#FF00FF', weight=3, dash_array='5, 10').add_to(m)

        # 중심/줌 맞춤
        latlngs = [(p['mapy'], p['mapx']) for p in ordered_course]
        if len(latlngs) == 1:
            m.location = latlngs[0]; m.zoom_start = 14
        else:
            m.fit_bounds(latlngs, padding=(20, 20))

        # 렌더
        map_html = m.get_root().render()
        html(map_html, height=520, scrolling=False)

        # ✅ 지도 범례 (아이콘/색상/경로 의미)
        st.markdown("""
        <style>
        .lgd { font-size:.85rem; color:#333; margin:6px 2px 8px 2px; 
            background:#F5FBFF; border:1px solid #E0F2FE; border-radius:8px; padding:6px 10px; 
            display:inline-block; }
        .lgd-row { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
        .lgd-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; }
        .lgd-item { white-space:nowrap; }
        .lgd-line { width:26px; height:0; border-top:2px dashed #FF00FF; display:inline-block; margin-right:6px; vertical-align:middle; }
        </style>
        <div class="lgd">
        <div><b>🗂️ 지도 범례</b></div>
        <div class="lgd-row">
            <span class="lgd-item"><span class="lgd-dot" style="background:blue"></span>낮 관광지 (info-sign)</span>
            <span class="lgd-item"><span class="lgd-dot" style="background:orange"></span>야간 명소 (star)</span>
            <span class="lgd-item"><span class="lgd-dot" style="background:green"></span>맛집 (cloud)</span>
            <span class="lgd-item"><span class="lgd-dot" style="background:purple"></span>쇼핑 (shopping-cart)</span>
            <span class="lgd-item"><span class="lgd-dot" style="background:red"></span>숙박 (home)</span>
            <span class="lgd-item"><span class="lgd-line"></span>이동 경로(분홍 점선)</span>
        </div>
        </div>
        """, unsafe_allow_html=True)

        # 여백 최적화
        st.markdown("""
        <style>
        div[data-testid="stElementContainer"] iframe { margin-bottom:0 !important; }
        div[data-testid="stVerticalBlock"] > div { margin-top:.25rem !important; margin-bottom:.25rem !important; }
        div[data-testid="stMarkdownContainer"] p { margin:0 0 .35rem 0 !important; }
        div[data-testid="stElementContainer"]:has(iframe) { margin-bottom:0 !important; padding-bottom:0 !important; }
        </style>
        """, unsafe_allow_html=True)
        
        # 각 구간별 길찾기 앵커
        st.markdown('<a id="route-detail"></a>', unsafe_allow_html=True)
        st.markdown("<b>🛣️ 각 구간별 길찾기 및 지도 확인</b>", unsafe_allow_html=True)

        # 합계 초기화
        total_car_km = total_car_min = 0
        total_walk_km = total_walk_min = 0
        used_car = used_walk = used_transit = False

        # 구간별 컨트롤
        for i in range(len(ordered_course)-1):
            start = ordered_course[i]
            end   = ordered_course[i+1]
            start_lat, start_lng = start['mapy'], start['mapx']
            end_lat,   end_lng   = end['mapy'],   end['mapx']

            route = None  # 매 구간 초기화
            naver_app_url, kakao_web_url = make_links(start, end)

            st.markdown(
                f"<div class='route-box'><b>{i+1}. {start['title']} → {i+2}. {end['title']}</b></div>",
                unsafe_allow_html=True
            )

            transport_mode = st.radio(
                "이동수단 선택",
                options=['자동차', '도보', '대중교통'],
                horizontal=True,
                key=f"mode_{i}_new"
            )

            if transport_mode == '자동차':
                if not KAKAO_API_KEY:
                    st.info("카카오 자동차 안내: API 키가 없어 대략치/웹/앱 안내만 제공합니다.")
                else:
                    url = "https://apis-navi.kakaomobility.com/v1/directions"
                    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
                    params = {
                        "origin": f"{start_lng},{start_lat}",
                        "destination": f"{end_lng},{end_lat}",
                        "priority": "TIME"
                    }
                    try:
                        response = requests.get(url, headers=headers, params=params, timeout=5)
                        response.raise_for_status()
                        result = response.json()
                        routes = result.get('routes') or []
                        if routes:
                            route = routes[0]
                            summary = route.get('summary', {})
                            used_car = True
                            total_car_km  += summary.get('distance', 0) / 1000
                            total_car_min += summary.get('duration', 0) // 60
                            car_min = int(summary.get('duration', 0) // 60)
                            car_min_str = fmt_min_kor(car_min)
                            st.markdown(f"""
                            <div style='background:#F8BBD0; border-radius:10px; padding:14px; margin:6px 0 4px 0;'>
                                🚗 <b>총 거리:</b> {summary.get('distance',0)/1000:.2f} km
                                &nbsp;&nbsp;⏱️ <b>소요 시간:</b> {car_min_str}
                                &nbsp;&nbsp;💰 <b>예상 택시 요금:</b> {summary.get('fare',{}).get('taxi',0):,} 원
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.warning("카카오 자동차 안내: 경로가 없습니다.")
                    except requests.Timeout:
                        st.warning("카카오 자동차 안내: 시간 초과")
                    except Exception as e:
                        st.warning(f"카카오 자동차 안내 실패: {e}")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <a href="{naver_app_url}">
                    <button style="padding:7px 14px; font-size:1em; border-radius:8px; background:#4FC3F7; color:#fff; border:none;">
                        🗺️ 네이버 지도 앱 열기(모바일)
                    </button>
                    </a>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <a href="{kakao_web_url}" target="_blank" rel="noopener">
                    <button style="padding:7px 14px; font-size:1em; border-radius:8px; background:#0288D1; color:#fff; border:none;">
                        🌐 카카오 맵 열기(PC)
                    </button>
                    </a>""", unsafe_allow_html=True)


            elif transport_mode == '도보':
                est_km, est_min = estimate_walk_minutes_km(start_lat, start_lng, end_lat, end_lng,
                                                           detour_factor=1.25, speed_kmh=4.5)
                used_walk = True
                total_walk_km  += est_km
                total_walk_min += est_min
                st.markdown(f"""
                <div style='background:#F8BBD0; border-radius:10px; padding:14px; margin:6px 0 4px 0;'>
                    🚶 <b>총 거리(추정):</b> {est_km:.2f} km
                    &nbsp;&nbsp;⏱️ <b>소요 시간(추정):</b> {fmt_min_kor(est_min)}
                </div>""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <a href="{naver_app_url}">
                    <button style="padding:7px 14px; font-size:1em; border-radius:8px; background:#4FC3F7; color:#fff; border:none;">
                        🗺️ 네이버 지도 앱 열기
                    </button>
                    </a>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <a href="{kakao_web_url}" target="_blank" rel="noopener">
                    <button style="padding:7px 14px; font-size:1em; border-radius:8px; background:#0288D1; color:#fff; border:none;">
                        🌐 웹에서 길찾기 (PC)
                    </button>
                    </a>""", unsafe_allow_html=True)

            else:  # 대중교통
                used_transit = True
                st.markdown("""
                <div style='background:#F8BBD0; border-radius:10px; padding:14px; margin:6px 0 4px 0;'>
                    🚇 <b>대중교통 경로 안내는 지도 앱/웹에서 확인해주세요</b><br>
                    (아래 버튼을 눌러 앱/웹을 여신 뒤, 대중교통 탭으로 전환하세요)
                </div>""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <a href="{naver_app_url}">
                    <button style="padding:7px 14px; font-size:1em; border-radius:8px; background:#4FC3F7; color:#fff; border:none;">
                        🗺️ 네이버 지도 앱 열기(모바일)
                    </button>
                    </a>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <a href="{kakao_web_url}" target="_blank" rel="noopener">
                    <button style="padding:7px 14px; font-size:1em; border-radius:8px; background:#0288D1; color:#fff; border:none;">
                        🌐 카카오 맵 열기(PC)
                    </button>
                    </a>""", unsafe_allow_html=True)
            # QR 익스팬더  추가
            # ✅ QR: 기본 숨김 → 토글 켜면 펼쳐짐
            if st.toggle("다른 기기로 보내기(QR)", value=False, key=f"qr_tg_{i}",
                        help="만든 경로를 스마트폰으로 넘길 때 사용합니다"):
                with st.expander("📱 QR로 내 폰에서 열기 (카카오 맵 길찾기)", expanded=True):
                    qr_png = make_qr_bytes(kakao_web_url, box_size=6, border=2)
                    st.image(qr_png, width=160, caption="카메라로 스캔하세요")
                    st.download_button(
                        "QR 이미지 저장(PNG)",
                        data=qr_png,
                        file_name=f"route_{i+1}_to_{i+2}.png",
                        mime="image/png",
                        key=f"dl_qr_{i}"
                    )
                    st.caption("※ 버튼은 현재 기기에서 열리고, QR은 다른 기기(주로 스마트폰)로 넘길 때 사용해요.")
                    st.caption("같이 갈 친구·가족에게 QR을 보내면, 각자 폰에서 바로 경로를 열 수 있어요.")


            
            # 경로 상세 안내 (자동차/도보만)
            guide_title = "경로 상세 안내 (카카오 " + ("자동차" if transport_mode=="자동차" else "도보") + " 안내문)"
            if transport_mode in ('자동차', '도보') and route and route.get('sections'):
                with st.expander(guide_title):
                    for guide in route['sections'][0].get('guides', []):
                        st.write(guide.get('guidance'))

            st.markdown("</div>", unsafe_allow_html=True)  # 하늘색 박스 닫기

        # 4) 합계 요약
        sum_km  = total_car_km + total_walk_km
        sum_min = total_car_min + total_walk_min
        if (used_car or used_walk) and (sum_km > 0 or sum_min > 0):
            modes = []
            if used_car:  modes.append("자동차")
            if used_walk: modes.append("도보(추정)")
            label = " · ".join(modes) + " 합계 (대중교통 제외)"
            totals_placeholder.markdown(
                f"<div style='color:#0288D1; font-size:1.15em; margin-top:8px;'>"
                f"<b>예상 총 이동거리:{sum_km:.1f} km·총 소요시간: {fmt_min_kor(sum_min)}</b><br>"
                f"<span style='font-size:.95em; opacity:.85;'>{label}</span>"
                f"</div>", unsafe_allow_html=True
            )
            with st.expander("▼ 선택한 이동수단 소요시간 보기 ▼", expanded=False):
                st.write(f"🚗 자동차: {total_car_km:.1f} km · {fmt_min_kor(total_car_min)}")
                st.write(f"🚶 도보(추정): {total_walk_km:.1f} km · {fmt_min_kor(total_walk_min)}")
                if used_transit:
                    st.write("🚇 대중교통: 현재 총합 제외 (추후 지원 예정)")
        else:
            totals_placeholder.markdown(
                "<div style='color:#0288D1; font-size:1.0em; margin-top:8px;'>"
                "<b>이동수단을 선택하면 자동차/도보 합계가 표시됩니다. (대중교통은 현재 제외)</b>"
                "</div>", unsafe_allow_html=True
            )
    else:
        st.warning("2곳 이상(관광지+야경 등) 포함해야 경로 추천이 가능합니다!")
else:
    st.warning("순서 오류로 추천 경로를 생성할 수 없습니다.")



# ordered_course가 있을 때만 코스 관련 점프 버튼도 보여주고,
# 없으면 "맨 위로"만 보여주고 싶다면 if/else로 감싸도 됩니다.
st.markdown("""
<style>
html { scroll-behavior: smooth; }

/* 버튼 묶음(왼쪽 아래 고정) */
.fab {
  position: fixed;
  left: 16px;
  bottom: 16px;
  z-index: 9999;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;   /* 폭 좁으면 자동 줄바꿈 */
}

.fab a {
  background: #64bdff;
  color: #fff;
  text-decoration: none;
  padding: 10px 12px;
  border-radius: 999px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0,0,0,.15);
  white-space: nowrap;
}

.fab a:hover { background: #0277BD; opacity:.51;}

/* 작은 폰에서 살짝 축소 */
@media (max-width: 420px) {
  .fab { left: 12px; bottom: 12px; gap: 6px; }
  .fab a { font-size: .95rem; padding: 8px 10px; }
}
</style>

<div class="fab">
  <a href="#page-top">⬆ 맨 위로</a>
  <a href="#route-order">🗺️ 추천 코스 순서</a>
  <a href="#route-detail">📍구간별 길찾기</a>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* === 초압축 레이아웃(이 블록 하나만 유지) === */

/* 전체 앱 컨테이너 패딩 축소 */
section.main [data-testid="stAppViewBlockContainer"]{
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}

/* 세로 블록(섹션) 간격/패딩 최소화 */
div[data-testid="stVerticalBlock"] > div{
  margin-top: 2px !important;
  margin-bottom: 2px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

/* 가로(columns) 내부 여백 축소 */
div[data-testid="stHorizontalBlock"] > div{
  margin: 2px !important;
}
div[data-testid="column"]{
  padding-left: 6px !important;
  padding-right: 6px !important;
}

/* 모든 요소 컨테이너(위젯 래퍼) 간격 최소화 */
div[data-testid="stElementContainer"]{
  margin-top: 2px !important;
  margin-bottom: 2px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

/* 마크다운 단락/리스트 & 제목 간격 */
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] ul,
div[data-testid="stMarkdownContainer"] ol{
  margin: 2px 0 !important;
  line-height: 1.4 !important;
}
h1, h2, h3, h4, h5, h6{
  margin: .25rem 0 .5rem 0 !important;
}

/* 라디오/라벨/버튼/테이블/익스팬더 간격 */
label[data-testid="stWidgetLabel"]{ margin-bottom: 2px !important; }
div[role="radiogroup"], div[role="group"]{ margin: 2px 0 !important; }
div.row-widget.stButton{ margin: 2px 0 !important; }
div[data-testid="stDataFrame"], div[data-testid="stDataFrameResizable"]{ margin: 4px 0 !important; }
details[role="group"]{ margin: 4px 0 !important; }

/* folium 지도 iframe 아래 여백 제거 */
div[data-testid="stElementContainer"] iframe{ margin-bottom: 0 !important; }

            
/* 캡션 바로 다음 마크다운 붙이기 */
div[data-testid="stCaptionContainer"] p{ margin-bottom: 0 !important; }
div[data-testid="stCaptionContainer"] + div[data-testid="stMarkdownContainer"]{ margin-top: .1rem !important; }

/* ▼▼▼ [추가] '다시 뽑기' 버튼과 그 다음 캡션 사이 간격 압축 ▼▼▼ */
div[data-testid="stHorizontalBlock"]:has(.stButton){ margin-bottom: 0 !important; padding-bottom: 0 !important; }
div[data-testid="stHorizontalBlock"]:has(.stButton) + div[data-testid="stElementContainer"]{ margin-top: 2px !important; }
div[data-testid="stHorizontalBlock"]:has(.stButton) + div[data-testid="stElementContainer"] div[data-testid="stCaptionContainer"] p{ margin: 0 !important; }        

/* ▼▼▼ [추가] '다시 뽑기' 버튼과 그 다음 캡션 사이 간격 압축(대체 셀렉터) ▼▼▼ */
div[data-testid="stElementContainer"]:has(.stButton) + div[data-testid="stElementContainer"]{ margin-top: 0 !important; }
div[data-testid="stElementContainer"]:has(.stButton) + div[data-testid="stElementContainer"] div[data-testid="stCaptionContainer"] p{ margin: 0 !important; }
/* ▲▲▲ [추가 끝] ▲▲▲ */
            
/*모바일 폰트 자동확대 방지 1줄(썬택*/            
html { text-size-adjust: 100%; -webkit-text-size-adjust: 100%; }


/* === Streamlit help= 툴팁: 가로 더 넓게 + 세로 스크롤 제거 + 자연스러운 줄바꿈 === */

/* 바깥 컨테이너 */
div[role="tooltip"]{
  max-height: none !important;
  /* 너무 넓어지지 않도록 반응형 폭: 최소 320px, 보통 화면의 48vw, 최대 560px */
  width: fit-content !important;
  max-width: clamp(320px, 48vw, 560px) !important;
  overflow-y: visible !important;
  padding: 8px 12px !important;
  line-height: 1.45 !important;
  z-index: 9999 !important;
}

/* 안쪽 실제 콘텐츠 박스까지 폭 제한 해제(스트림릿 내부 div 대응) */
div[role="tooltip"] > div,
div[role="tooltip"] [data-baseweb="tooltip"],
div[role="tooltip"] [data-testid="stTooltipContent"],
div[role="tooltip"] [class*="tooltip"]{
  width: fit-content !important;
  max-width: clamp(320px, 48vw, 560px) !important;
}

/* 줄바꿈 규칙: 한글은 단어 단위로 자연스럽게 줄바꿈, 길~은 토큰(URL 등)은 필요시 어디서든 줄바꿈 */
div[role="tooltip"] *{
  white-space: normal !important;
  word-break: keep-all !important;     /* 한글 자연 줄바꿈 */
  overflow-wrap: anywhere !important;  /* 긴 URL·해시 등 강제 줄바꿈 */
  font-size: 0.86rem !important;       /* 살짝 작게 */
  line-height: 1.45 !important;
}
            
/* ▼ 익스팬더 다음 요소(=다음 익스팬더 포함)와의 간격을 거의 0으로 */
div[data-testid="stElementContainer"]:has(> details[role="group"]) { 
  margin-bottom: 4px !important;   /* 기본 10~16px → 4px */
}
/* ▼ 익스팬더 바로 다음에 오는 요소의 위쪽 간격도 축소 */
div[data-testid="stElementContainer"]:has(> details[role="group"]) + div[data-testid="stElementContainer"]{
  margin-top: 0px !important;      /* 기본 10~16px → 4px */
}
            
.route-box{
  margin: 4px 0 !important;
  padding: 20px 15px 10px 15px;
  background: #E3F2FD;
  border-radius: 14px;
}            
</style>
""", unsafe_allow_html=True)


# pip install streamlit-sortable → streamlit 드래그
