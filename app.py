import subprocess
import sys
import streamlit as st

# Streamlit Cloud 서버 구동 시 Playwright 크롬 브라우저 자동 다운로드
@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Playwright browser install log: {e}")

install_playwright_browsers()




import asyncio
import io
import json
import os
from datetime import datetime
import requests
from PIL import Image

import streamlit as st
from google import genai
from google.genai import types

# ------------------------------------------------------------------
# 기본 설정 및 톤앤매너 디자인 CSS (컨테이너/입력창 색상 완벽 통일)
# ------------------------------------------------------------------
st.set_page_config(page_title="경쟁사 광고 소재 분석", layout="wide", page_icon="◆")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --ink: #191B29;
    --muted: #555866;
    --paper: #FAF9F5;
    --surface: #FFFFFF;
    --border: #E2E1D9;
    --primary: #2A2F6B;
    --primary-soft: #EEEFF7;
    --amber: #D97706;
    --teal: #0D9488;
}

/* 기본 전체 배경 및 폰트 색상 */
html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'Inter', sans-serif;
    color: var(--ink) !important;
}

.stApp { background-color: #FAF9F5 !important; }

h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em;
    color: var(--ink) !important;
}

/* 상단 앱바 */
.appbar { display: flex; align-items: center; gap: 14px; padding: 18px 4px 20px 4px; border-bottom: 1px solid var(--border); margin-bottom: 18px; }
.appbar-mark { width: 34px; height: 34px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--teal)); flex-shrink: 0; }
.appbar-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 21px; line-height: 1.1; color: var(--ink) !important; }
.appbar-pill { margin-left: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--teal) !important; background: #E9F7F5; border: 1px solid #CDEEE9; padding: 5px 10px; border-radius: 20px; white-space: nowrap; }

.eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.08em; color: var(--primary) !important; background: var(--primary-soft); display: inline-block; padding: 3px 9px; border-radius: 4px; margin-bottom: 8px; font-weight: 600; }
.section-title { font-size: 20px; font-weight: 700; margin: 0 0 4px 0; color: var(--ink) !important; }
.section-desc { font-size: 13.5px; color: var(--muted) !important; margin-bottom: 18px; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: #F3F3EE !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }

/* 버튼 스타일 */
.stButton > button { border-radius: 7px; font-weight: 600; border: 1px solid var(--border); background-color: #FFFFFF !important; color: var(--ink) !important; }
.stButton > button[kind="primary"] { background-color: var(--primary) !important; color: #FFFFFF !important; border: none; }
.stButton > button[kind="primary"] * { color: #FFFFFF !important; }
.stButton > button[kind="primary"]:hover { background-color: #21245A !important; }

/* 텍스트 입력창, 셀렉트박스 및 드롭다운 배경 및 글자색 일치 (어두운 회색 제거) */
.stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
}

/* 파일 업로더 영역 이질감 없게 배경 정리 */
[data-testid="stFileUploader"], [data-testid="stFileUploader"] section {
    background-color: #FFFFFF !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] * {
    color: var(--ink) !important;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--border); flex-wrap: wrap; background-color: transparent !important; }
.stTabs [data-baseweb="tab"] { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 13px; padding: 9px 12px; border-radius: 7px 7px 0 0; color: var(--muted) !important; }
.stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom: 2px solid var(--primary) !important; font-weight: 700; }

/* 카드 및 컨테이너 */
[data-testid="stImage"] img { border-radius: 8px; border: 1px solid var(--border); }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 10px !important; border: 1px solid var(--border) !important; background-color: #FFFFFF !important; }

[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 8px !important; background-color: #FFFFFF !important; }
[data-testid="stExpander"] * { color: var(--ink) !important; }

.field-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.06em; color: var(--muted) !important; margin: 6px 0 2px 0; text-transform: uppercase; font-weight: 600; }

.score-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 10px 0; }
.score-card { border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; background-color: #F8F8F5 !important; }
.score-cat { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.05em; color: var(--muted) !important; text-transform: uppercase; font-weight: 600; }
.score-stars { color: var(--amber) !important; font-size: 15px; margin: 3px 0; }
.score-desc { font-size: 12.5px; color: var(--ink) !important; line-height: 1.4; }

.comp-card { border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; background-color: #FFFFFF !important; margin-bottom: 10px; }
.comp-name { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 15px; color: var(--ink) !important; }
.comp-meta { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted) !important; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


def section_header(step, title, desc=""):
    st.markdown(f'<div class="eyebrow">STEP {step}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if desc:
        st.markdown(f'<div class="section-desc">{desc}</div>', unsafe_allow_html=True)


def stars(score, max_score=5):
    try:
        n = max(0, min(max_score, round(float(score))))
    except (ValueError, TypeError):
        n = 0
    return "★" * n + "☆" * (max_score - n)


# ------------------------------------------------------------------
# 데이터 로드 / 저장
# ------------------------------------------------------------------
SEGMENTS = ["유아", "초등", "중등"]
DEFAULT_COMPETITORS = {
    "유아": ["윙크", "웅진스마트올", "밀크T아이", "리틀홈런"],
    "초등": ["밀크T", "아이스크림 홈런", "비상 온리원", "단꿈e", "기타"],
    "중등": ["밀크T중등", "웅진스마트올 중학", "비상 온리원 중등", "아이스크림 홈런 중등", "EBS"],
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "ad_signal_history.json")
BRAND_FILE = os.path.join(BASE_DIR, "ad_signal_brand.json")
COMPETITORS_FILE = os.path.join(BASE_DIR, "ad_signal_competitors.json")
PROFILES_FILE = os.path.join(BASE_DIR, "ad_signal_profiles.json")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def load_history(): return load_json(HISTORY_FILE, [])


def save_history_entry(entry):
    history = load_history()
    history.insert(0, entry)
    save_json(HISTORY_FILE, history)


def load_all_brands(): return load_json(BRAND_FILE, {})


def save_brand(segment, data):
    all_brands = load_all_brands()
    all_brands[segment] = data
    save_json(BRAND_FILE, all_brands)


def load_competitors():
    data = load_json(COMPETITORS_FILE, {})
    changed = False
    for seg in SEGMENTS:
        if seg not in data:
            data[seg] = list(DEFAULT_COMPETITORS[seg])
            changed = True
    if changed: save_json(COMPETITORS_FILE, data)
    return data


def add_competitor(segment, name):
    data = load_competitors()
    if name and name not in data[segment]:
        data[segment].append(name)
        save_json(COMPETITORS_FILE, data)


def load_all_profiles(): return load_json(PROFILES_FILE, {})


def save_profile_entry(segment, competitor, entry):
    data = load_all_profiles()
    data.setdefault(segment, {}).setdefault(competitor, []).insert(0, entry)
    save_json(PROFILES_FILE, data)


# ------------------------------------------------------------------
# Playwright 기반 메타 광고 수집기
# ------------------------------------------------------------------
async def scrape_meta_ad_images(target_url, max_items=5):
    captured_images = []
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            await page.route("**/*.{font,woff,woff2,css}", lambda route: route.abort())

            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            for _ in range(5):
                await page.mouse.wheel(0, 1500)
                await page.wait_for_timeout(600)

            captured_images = await page.evaluate('''() => {
                const images = [];
                const imgElements = document.querySelectorAll('img');
                imgElements.forEach(img => {
                    if (img.naturalWidth > 150 && img.naturalHeight > 150) {
                        const src = img.src;
                        if ((src.includes("scontent") || src.includes("fbcdn")) && !images.includes(src)) {
                            images.push(src);
                        }
                    }
                });
                return images;
            }''')
            await browser.close()
    except Exception as e:
        st.warning(f"메타 수집 중 참조: {e}")
        
    return captured_images[:max_items]


# ------------------------------------------------------------------
# 구조화된 카피 추출 (OCR) 및 스코어카드
# ------------------------------------------------------------------
STRUCTURED_OCR_PROMPT = """이 광고 이미지를 보고 아래 4가지 항목을 정리해줘. 다른 설명 없이 정확히 아래 형식으로만 답해줘.
이미지에 해당 내용이 없으면 그 항목은 비워둬.

브랜드명: (이미지 안에 보이는 브랜드/제품명. 로고나 텍스트로 적힌 것만)
메인 메시지: (가장 크고 눈에 띄는 핵심 카피 문구. 실제 적힌 텍스트 그대로)
썸네일: (이미지의 비주얼을 아주 간단히, 한 줄로 요약 - 예: "운동하는 여성 이미지", "제품 클로즈업 사진")
CTA: (구매하기, 지금 다운로드 등 행동 유도 문구)"""

FIELD_LABELS = {"brand": "브랜드명", "message": "메인 메시지", "thumbnail": "썸네일", "cta": "CTA"}
FIELD_ORDER = ["brand", "message", "thumbnail", "cta"]
_LABEL_TO_KEY = {v: k for k, v in FIELD_LABELS.items()}


def parse_labeled_text(text, label_to_key, empty_fields):
    fields = dict(empty_fields)
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line: continue
        matched_key = None
        for label, key in label_to_key.items():
            if line.startswith(label + ":") or line.startswith(label + " :"):
                fields[key] = line.split(":", 1)[1].strip() if ":" in line else ""
                current = key
                matched_key = key
                break
        if matched_key is None and current:
            fields[current] = (fields[current] + " " + line).strip()
    return fields


def parse_structured_copy(text):
    return parse_labeled_text(text, _LABEL_TO_KEY, {"brand": "", "message": "", "thumbnail": "", "cta": ""})


def structured_to_reference_text(fields):
    return "\n".join(f"{FIELD_LABELS[k]}: {fields.get(k, '') or '없음'}" for k in FIELD_ORDER)


ANALYSIS_PROMPT = """당신은 퍼포먼스 마케팅 및 광고 크리에이티브 전문가입니다.
첨부된 광고 소재 이미지와 구조화된 정보를 참고해서 분석해주세요.
다른 설명 없이, 정확히 아래 형식으로만 답해주세요. 평점은 1~5 사이 숫자만 적어주세요.

핵심메시지_설명: (이 소재가 전달하는 핵심 메시지/소구 포인트, 1~2문장)
핵심메시지_평점: (숫자만)
비주얼_설명: (색감, 레이아웃, 이미지 구성 특징, 1~2문장)
비주얼_평점: (숫자만)
타겟팅_설명: (예상 타겟 고객과 소구 방식, 1~2문장)
타겟팅_평점: (숫자만)
기타_설명: (후킹포인트, CTA, 톤앤매너 등 특이사항, 1~2문장)
종합_평점: (숫자만, 전체 완성도)

참고용 구조화 정보:
{copy_text}"""

_SCORE_LABEL_TO_KEY = {
    "핵심메시지_설명": "message_desc", "핵심메시지_평점": "message_score",
    "비주얼_설명": "visual_desc", "비주얼_평점": "visual_score",
    "타겟팅_설명": "target_desc", "타겟팅_평점": "target_score",
    "기타_설명": "other_desc", "종합_평점": "overall_score",
}
_SCORE_EMPTY = {k: "" for k in _SCORE_LABEL_TO_KEY.values()}


def parse_scorecard(text): return parse_labeled_text(text, _SCORE_LABEL_TO_KEY, _SCORE_EMPTY)


def render_scorecard(sc):
    cats = [
        ("핵심 메시지", sc.get("message_desc", ""), sc.get("message_score", 0)),
        ("비주얼", sc.get("visual_desc", ""), sc.get("visual_score", 0)),
        ("타겟팅", sc.get("target_desc", ""), sc.get("target_score", 0)),
        ("기타", sc.get("other_desc", ""), sc.get("overall_score", 0)),
    ]
    html = '<div class="score-grid">'
    for label, desc, score in cats:
        html += (
            f'<div class="score-card"><div class="score-cat">{label}</div>'
            f'<div class="score-stars">{stars(score)}</div>'
            f'<div class="score-desc">{desc}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def scorecard_to_text(sc, name):
    return (
        f"[{name}]\n"
        f"핵심 메시지({sc.get('message_score', '-')}점): {sc.get('message_desc', '')}\n"
        f"비주얼({sc.get('visual_score', '-')}점): {sc.get('visual_desc', '')}\n"
        f"타겟팅({sc.get('target_score', '-')}점): {sc.get('target_desc', '')}\n"
        f"기타(종합 {sc.get('overall_score', '-')}점): {sc.get('other_desc', '')}"
    )


def analyze_material(image_bytes, ref_text, file_name="image.png"):
    mime_type = "image/png" if file_name.lower().endswith("png") else "image/jpeg"
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    resp = client.models.generate_content(
        model=MODEL, contents=[image_part, ANALYSIS_PROMPT.format(copy_text=ref_text)]
    )
    return parse_scorecard(resp.text)


def run_structured_ocr(image_bytes, file_name="image.png"):
    mime_type = "image/png" if file_name.lower().endswith("png") else "image/jpeg"
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    resp = client.models.generate_content(model=MODEL, contents=[image_part, STRUCTURED_OCR_PROMPT])
    return parse_structured_copy(resp.text)


# ------------------------------------------------------------------
# [수집 + 업로드 통합 UI]
# ------------------------------------------------------------------
def render_material_section(prefix, on_complete):
    tab1, tab2 = st.tabs(["📁 파일 직접 업로드", "🔗 메타 광고 라이브러리 URL 자동 수집"])
    
    uploaded_items = []
    
    with tab1:
        uploaded_files = st.file_uploader(
            "광고 이미지 업로드 (다중 선택 가능 / PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"{prefix}_uploader",
        )
        if uploaded_files:
            for f in uploaded_files:
                f.seek(0)
                uploaded_items.append((f.name, f.read()))

    with tab2:
        meta_url = st.text_input(
            "메타 광고 라이브러리 페이지 URL 입력",
            placeholder="https://www.facebook.com/ads/library/?...",
            key=f"{prefix}_meta_url_input"
        )
        if st.button("🚀 메타 라이브러리 소재 자동 수집", key=f"{prefix}_crawl_btn", type="primary"):
            if not meta_url.strip():
                st.warning("메타 라이브러리 URL을 입력해주세요.")
            else:
                with st.spinner("Playwright 크롤러로 배너 이미지를 수집 중입니다..."):
                    img_urls = asyncio.run(scrape_meta_ad_images(meta_url.strip(), max_items=5))
                    
                    if not img_urls:
                        st.info("수집된 배너가 없습니다. URL을 재확인해주시거나 파일 직접 업로드를 이용해 주세요.")
                    else:
                        st.session_state[f"{prefix}_crawled_images"] = []
                        for idx, url in enumerate(img_urls, start=1):
                            try:
                                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                                fn = f"meta_crawled_{idx}.png"
                                st.session_state[f"{prefix}_crawled_images"].append((fn, resp.content))
                            except Exception:
                                pass
                        st.success(f"메타 라이브러리에서 광고 배너 {len(st.session_state[f'{prefix}_crawled_images'])}건 수집 완료!")

        if f"{prefix}_crawled_images" in st.session_state:
            uploaded_items.extend(st.session_state[f"{prefix}_crawled_images"])

    field_values_by_file = {}
    
    if uploaded_items:
        st.divider()
        st.markdown("**인식된 소재 정보 확인 · 수정**")
        st.caption("AI가 브랜드명 / 메인 메시지 / 썸네일 / CTA를 항목별로 자동 인식합니다. 틀린 부분은 직접 고쳐주세요.")

        for name, img_bytes in uploaded_items:
            file_key = f"{prefix}_{name}_{len(img_bytes)}"

            if client and file_key not in st.session_state.structured_copy:
                try:
                    with st.spinner(f"'{name}' AI OCR 읽는 중..."):
                        parsed = run_structured_ocr(img_bytes, file_name=name)
                except Exception:
                    parsed = {"brand": "", "message": "", "thumbnail": "", "cta": ""}
                st.session_state.structured_copy[file_key] = parsed

            with st.container(border=True):
                card_cols = st.columns([1, 2])
                with card_cols[0]:
                    st.image(img_bytes, use_container_width=True)
                with card_cols[1]:
                    saved = st.session_state.structured_copy.get(
                        file_key, {"brand": "", "message": "", "thumbnail": "", "cta": ""}
                    )
                    fv = {}
                    for fkey in FIELD_ORDER:
                        widget_key = f"{file_key}_{fkey}"
                        if widget_key not in st.session_state:
                            st.session_state[widget_key] = saved.get(fkey, "")
                        st.markdown(f'<div class="field-label">{FIELD_LABELS[fkey]}</div>', unsafe_allow_html=True)
                        if fkey in ("message", "thumbnail"):
                            fv[fkey] = st.text_area(FIELD_LABELS[fkey], key=widget_key, height=60, label_visibility="collapsed")
                        else:
                            fv[fkey] = st.text_input(FIELD_LABELS[fkey], key=widget_key, label_visibility="collapsed")
                    field_values_by_file[name] = fv

        if not client:
            st.info("Gemini API 키를 입력하면 정보가 자동으로 채워집니다.")

        st.divider()
        if st.button("소재 분석 실행", type="primary", key=f"{prefix}_analyze_btn"):
            if not client:
                st.error("Gemini API 키를 먼저 입력해주세요.")
            else:
                results = []
                progress = st.progress(0, text="소재 분석 진행 중...")
                for idx, (name, img_bytes) in enumerate(uploaded_items):
                    fv = field_values_by_file.get(name, {})
                    ref_text = structured_to_reference_text(fv)
                    try:
                        sc = analyze_material(img_bytes, ref_text, file_name=name)
                    except Exception as e:
                        sc = dict(_SCORE_EMPTY)
                        sc["other_desc"] = f"분석 오류: {e}"
                    results.append({"name": name, "structured": fv, "scorecard": sc})
                    progress.progress((idx + 1) / len(uploaded_items), text=f"[{name}] 분석 완료")
                progress.empty()
                on_complete(results)


# ------------------------------------------------------------------
# 상단 헤더 & API 키 입력 영역 (시인성 레이블 가공)
# ------------------------------------------------------------------
top_col1, top_col2 = st.columns([3, 1.3])
with top_col1:
    st.markdown("""
    <div class="appbar">
        <div class="appbar-mark"></div>
        <div>
            <div class="appbar-title">경쟁사 광고 소재 분석</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with top_col2:
    default_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            default_key = st.secrets["GEMINI_API_KEY"]
    except Exception: pass
    
    # API 키 명확한 텍스트 라벨 부여
    input_api_key = st.text_input(
        "Gemini API Key 입력",
        value=default_key,
        type="password",
        placeholder="API 키를 입력하세요 (AIzaSy...)",
        key="main_gemini_api_key_input"
    )
    st.markdown(
        '<div class="appbar-pill" style="margin-left:0;">FREE · GEMINI 2.0 FLASH</div>',
        unsafe_allow_html=True,
    )

client = genai.Client(api_key=input_api_key) if input_api_key else None
MODEL = "gemini-2.0-flash"

# ------------------------------------------------------------------
# 사이드바
# ------------------------------------------------------------------
NAV_ITEMS = [
    "01 · 경쟁사 소재 분석",
    "02 · 경쟁사 프로필",
    "03 · 자사 소재 분석",
    "04 · 메시지 갭 분석",
    "05 · 스토리보드 아이디어",
    "06 · 히스토리",
]

with st.sidebar:
    st.markdown('<div class="eyebrow">SEGMENT</div>', unsafe_allow_html=True)
    st.markdown("##### 사업 부문")
    segment = st.radio("사업 구분", SEGMENTS, label_visibility="collapsed", key="segment_selector")
    st.caption(f"현재 작업 중: **{segment}** 부문")

    st.divider()
    st.markdown('<div class="eyebrow">MENU</div>', unsafe_allow_html=True)
    nav = st.radio("메뉴", NAV_ITEMS, label_visibility="collapsed", key="nav_selector")

# 세션 관리
if "work" not in st.session_state: st.session_state.work = {}
if segment not in st.session_state.work:
    st.session_state.work[segment] = {
        "own_analyses": [], "insight": "", "gap_analysis": "", "ideas": "",
        "last_comp_results": [], "last_competitor": "",
    }
W = st.session_state.work[segment]
if "structured_copy" not in st.session_state: st.session_state.structured_copy = {}

# ------------------------------------------------------------------
# 01 · 경쟁사 소재 분석
# ------------------------------------------------------------------
if nav == "01 · 경쟁사 소재 분석":
    section_header("01", f"{segment} 경쟁사 광고 소재 분석", "분석할 경쟁사를 먼저 선택한 뒤, 파일 직접 업로드 또는 메타 라이브러리 URL로 자동 수집하세요.")

    competitors = load_competitors()[segment]
    comp_col, add_col = st.columns([2, 1])
    with comp_col:
        selected_competitor = st.selectbox("분석할 경쟁사", competitors, key=f"{segment}_comp_select")
    with add_col:
        with st.popover("+ 새 경쟁사 추가"):
            new_comp = st.text_input("경쟁사명", key=f"{segment}_new_comp_input")
            if st.button("추가", key=f"{segment}_new_comp_btn"):
                if new_comp.strip():
                    add_competitor(segment, new_comp.strip())
                    st.success(f"'{new_comp.strip()}' 추가되었습니다.")
                    st.rerun()

    def _on_comp_complete(results):
        W["last_comp_results"] = results
        W["last_competitor"] = selected_competitor
        for r in results:
            save_profile_entry(segment, selected_competitor, {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "name": r["name"],
                "structured": r["structured"],
                "scorecard": r["scorecard"],
            })
        st.success(f"'{selected_competitor}' 소재 {len(results)}건 분석 완료 → 02 탭 프로필에 저장되었습니다.")

    render_material_section("comp", _on_comp_complete)

    if W["last_comp_results"]:
        st.divider()
        st.markdown(f"**방금 분석한 '{W['last_competitor']}' 소재 결과**")
        for r in W["last_comp_results"]:
            with st.expander(r["name"]):
                render_scorecard(r["scorecard"])

# ------------------------------------------------------------------
# 02 · 경쟁사 프로필
# ------------------------------------------------------------------
elif nav == "02 · 경쟁사 프로필":
    section_header("02", f"{segment} 경쟁사 프로필", "01 탭에서 분석한 소재가 경쟁사별로 누적 저장됩니다.")

    profiles = load_all_profiles().get(segment, {})
    competitors = load_competitors()[segment]

    if not any(profiles.get(c) for c in competitors):
        st.info("아직 분석된 경쟁사 소재가 없어요. 01 탭에서 소재를 분석하면 여기에 자동으로 쌓입니다.")
    else:
        for comp in competitors:
            entries = profiles.get(comp, [])
            if not entries: continue

            def _avg(key):
                vals = []
                for e in entries:
                    try: vals.append(float(e["scorecard"].get(key, 0)))
                    except (ValueError, TypeError): pass
                return sum(vals) / len(vals) if vals else 0

            st.markdown(
                f'<div class="comp-card"><div class="comp-name">{comp}</div>'
                f'<div class="comp-meta">분석된 소재 {len(entries)}건 · '
                f'평균 메시지 {stars(round(_avg("message_score")))} · '
                f'평균 비주얼 {stars(round(_avg("visual_score")))} · '
                f'평균 타겟팅 {stars(round(_avg("target_score")))}</div></div>',
                unsafe_allow_html=True,
            )
            with st.expander(f"{comp} — 소재별 세부 내역 ({len(entries)}건)"):
                for e in entries:
                    st.markdown(f"**{e['name']}** · {e.get('timestamp', '')}")
                    render_scorecard(e["scorecard"])
                    st.divider()

# ------------------------------------------------------------------
# 03 · 자사 소재 분석
# ------------------------------------------------------------------
elif nav == "03 · 자사 소재 분석":
    section_header("03", f"{segment} 자사 광고 소재 분석", "지금 우리가 쓰고 있는 소재를 올려주세요.")

    def _on_own_complete(results):
        W["own_analyses"] = results
        st.success(f"자사 소재 {len(results)}건 분석 완료. 04 탭에서 경쟁사와 비교할 수 있어요.")

    render_material_section("own", _on_own_complete)

    if W["own_analyses"]:
        st.divider()
        st.markdown("**자사 소재 분석 결과**")
        for r in W["own_analyses"]:
            with st.expander(r["name"]):
                render_scorecard(r["scorecard"])

# ------------------------------------------------------------------
# 04 · 메시지 갭 분석
# ------------------------------------------------------------------
elif nav == "04 · 메시지 갭 분석":
    section_header("04", f"{segment} 메시지 갭 분석 & 위닝 포인트", "경쟁사 전체와 자사 소재를 비교해 부족한 메시지를 찾아냅니다.")

    profiles = load_all_profiles().get(segment, {})
    all_comp_entries = [(comp, e) for comp, es in profiles.items() for e in es]

    if not all_comp_entries:
        st.info("먼저 01 탭에서 경쟁사 소재 분석을 완료해주세요.")
    else:
        if st.button("경쟁사 위닝 포인트 도출", type="primary", key="insight_btn"):
            combined_analyses = "\n\n---\n\n".join(
                scorecard_to_text(e["scorecard"], f"{comp} · {e['name']}") for comp, e in all_comp_entries
            )
            INSIGHT_PROMPT = """당신은 수석 브랜드 전략가입니다. 아래 경쟁사 소재 분석 리포트들을 검토하고,
이 광고들이 공통으로 활용하고 있는 성공 패턴(위닝 포인트)을 3가지 핵심 키워드로 요약하고, 시장의 트렌드 인사이트를 도출해주세요.

[경쟁사 분석 모음]
{analyses}

작성 형식:
### 핵심 위닝 포인트 3가지
1. **[키워드]**: 설명...
2. **[키워드]**: 설명...
3. **[키워드]**: 설명...

### 종합 마케팅 인사이트
- 시장 내 공통적인 소구 트렌드 및 시사점
"""
            with st.spinner("인사이트 도출 중..."):
                try:
                    resp = client.models.generate_content(model=MODEL, contents=[INSIGHT_PROMPT.format(analyses=combined_analyses)])
                    W["insight"] = resp.text
                except Exception as e: st.error(f"오류 발생: {e}")

        if W["insight"]: st.markdown(W["insight"])

        st.divider()
        st.markdown("**우리 소재와 비교해서 부족한 메시지 찾기**")

        if not W["own_analyses"]:
            st.info("03 탭에서 자사 소재 분석을 완료하면, 경쟁사 대비 부족한 메시지를 비교해드려요.")
        else:
            if st.button("메시지 갭 분석 실행", type="primary", key="gap_btn"):
                comp_combined = "\n\n---\n\n".join(
                    scorecard_to_text(e["scorecard"], f"{comp} · {e['name']}") for comp, e in all_comp_entries
                )
                own_combined = "\n\n---\n\n".join(
                    scorecard_to_text(r["scorecard"], r["name"]) for r in W["own_analyses"]
                )
                GAP_PROMPT = """당신은 브랜드 전략 컨설턴트입니다. 아래는 여러 경쟁사 광고 소재 분석과, 우리 브랜드 자체 소재 분석입니다.
두 그룹을 비교해서 아래 내용을 정리해주세요.

[경쟁사 소재 분석 모음]
{competitor}

[자사 소재 분석]
{own}

작성 형식:
### 경쟁사는 다루지만 우리 소재에는 부족한 메시지
- ...

### 보강하면 좋을 메시지 (우선순위 순, 이유 포함)
1. ...
2. ...
3. ...

### 우리만 갖고 있는 강점 (계속 유지할 것)
- ...
"""
                with st.spinner("갭 분석 중..."):
                    try:
                        resp = client.models.generate_content(model=MODEL, contents=[GAP_PROMPT.format(competitor=comp_combined, own=own_combined)])
                        W["gap_analysis"] = resp.text
                    except Exception as e: st.error(f"오류 발생: {e}")

            if W["gap_analysis"]: st.markdown(W["gap_analysis"])

# ------------------------------------------------------------------
# 05 · 스토리보드 아이디어
# ------------------------------------------------------------------
elif nav == "05 · 스토리보드 아이디어":
    section_header("05", f"{segment} 맞춤형 스토리보드 아이디어", "브랜드 정보를 입력하고 기획안을 생성합니다.")

    with st.expander(f"{segment} 브랜드 정보 입력 / 수정", expanded=True):
        all_brands = load_all_brands()
        saved_brand = all_brands.get(segment, {})
        for fkey, default in [
            ("brand_name", ""), ("brand_product", ""), ("brand_usp", ""),
            ("target_audience", ""), ("brand_design_memory", ""),
        ]:
            skey = f"{segment}_{fkey}"
            if skey not in st.session_state:
                st.session_state[skey] = saved_brand.get(fkey, default)

        col_a, col_b = st.columns(2)
        with col_a:
            brand_name = st.text_input("브랜드/제품명", key=f"{segment}_brand_name", placeholder="예: 브랜드명 입력")
            brand_usp = st.text_area("핵심 셀링포인트 (USP)", key=f"{segment}_brand_usp", placeholder="예: 우리 제품만의 차별점")
        with col_b:
            brand_product = st.text_area("제품/서비스 설명", key=f"{segment}_brand_product", placeholder="예: 제공하는 제품/서비스 설명")
            target_audience = st.text_input("타겟 고객층", key=f"{segment}_target_audience", placeholder="예: 학부모 / 자녀 연령대 등")

        st.markdown("**디자인 톤앤매너 및 레퍼런스 메모리**")
        brand_design_memory = st.text_area(
            "디자인 메모리", key=f"{segment}_brand_design_memory",
            placeholder="예: 밝고 친근한 톤, 학습 효과를 강조, 과장된 비교 광고는 지양함.",
            height=100, label_visibility="collapsed",
        )

        save_col, status_col = st.columns([1, 3])
        with save_col:
            if st.button("저장", type="primary", key=f"{segment}_brand_save"):
                save_brand(segment, {
                    "brand_name": brand_name, "brand_product": brand_product, "brand_usp": brand_usp,
                    "target_audience": target_audience, "brand_design_memory": brand_design_memory,
                })
                st.session_state[f"{segment}_brand_saved"] = True
        with status_col:
            if st.session_state.get(f"{segment}_brand_saved"): st.caption("저장되었습니다.")

    st.divider()

    profiles = load_all_profiles().get(segment, {})
    all_comp_entries = [(comp, e) for comp, es in profiles.items() for e in es]

    if not brand_name or not brand_product:
        st.warning("위에서 '브랜드/제품명'과 '제품 설명'을 먼저 입력하고 저장해 주세요.")
    elif not all_comp_entries:
        st.info("먼저 01 탭에서 경쟁사 소재 분석을 완료해 주세요.")
    else:
        if st.button("위닝 스토리보드 아이디어 생성", type="primary"):
            combined_analyses = "\n\n---\n\n".join(
                scorecard_to_text(e["scorecard"], f"{comp} · {e['name']}") for comp, e in all_comp_entries
            )
            gap_context = W["gap_analysis"] or "없음 (아직 메시지 갭 분석을 실행하지 않음)"

            STORYBOARD_PROMPT = """당신은 크리에이티브 디렉터입니다. 아래 경쟁사 분석 결과, 메시지 갭 분석, 우리 브랜드 정보,
그리고 **자사 디자인 메모리(가이드)**를 완벽하게 반영하여 경쟁사의 장점을 흡수하고 메시지 갭을 보완하되,
우리 브랜드만의 정체성과 가이드를 철저히 지킨 **광고 크리에이티브 스토리보드 3개**를 제안해주세요.

[자사 브랜드 정보]
- 브랜드/제품명: {brand_name}
- 제품 설명: {brand_product}
- 핵심 USP: {brand_usp}
- 타겟 고객: {target_audience}
- [중요] 자사 디자인 메모리 및 가이드 (반드시 준수): {design_memory}

[메시지 갭 분석 - 우리에게 부족한 메시지]
{gap_context}

[경쟁사 분석 모음]
{analyses}

각 아이디어는 아래 구조의 **스토리보드 형식**으로 구체적으로 작성해주세요:
### [아이디어 N] 한줄 컨셉 타이틀
- **타겟구간 / 매체 소구 포인트**: 
- **훅킹 카피 (오프닝 3초)**: 
- **비주얼 구성안 (자사 디자인 메모리 반영 연출 기획)**: 
- **본문 설득 및 USP 소구 방식**: 
- **CTA (행동 유도 문구)**: 
- **경쟁사 대비 차별화 포인트**: 
- **보완한 메시지 갭**: 
"""
            with st.spinner("스토리보드 기획안 작성 중..."):
                try:
                    resp = client.models.generate_content(
                        model=MODEL,
                        contents=[STORYBOARD_PROMPT.format(
                            brand_name=brand_name, brand_product=brand_product, brand_usp=brand_usp,
                            target_audience=target_audience,
                            design_memory=brand_design_memory or "없음 (기본 톤앤매너 유지)",
                            gap_context=gap_context, analyses=combined_analyses,
                        )]
                    )
                    W["ideas"] = resp.text

                    save_history_entry({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "segment": segment,
                        "brand_name": brand_name,
                        "brand_product": brand_product,
                        "target_audience": target_audience,
                        "material_count": len(all_comp_entries),
                        "own_material_count": len(W["own_analyses"]),
                        "insight": W["insight"],
                        "gap_analysis": W["gap_analysis"],
                        "ideas": W["ideas"],
                    })
                except Exception as e: st.error(f"오류 발생: {e}")

        if W["ideas"]:
            st.markdown(W["ideas"])
            st.divider()
            st.download_button(
                "광고 기획안 다운로드 (.md)", data=W["ideas"],
                file_name=f"{segment}_ad_winning_storyboards.md", mime="text/markdown",
            )

# ------------------------------------------------------------------
# 06 · 히스토리
# ------------------------------------------------------------------
elif nav == "06 · 히스토리":
    section_header("06", "히스토리", "완료한 아이디어 추출 결과가 부문 구분과 함께 자동으로 쌓입니다.")

    history = load_history()
    show_all = st.checkbox("모든 부문 보기 (선택 해제 시 현재 부문만)", value=False)
    filtered = history if show_all else [h for h in history if h.get("segment", "") == segment]

    if not filtered:
        st.info("아직 완료된 결과가 없어요. 05 탭에서 아이디어를 생성하면 여기에 자동으로 기록됩니다.")
    else:
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1: st.caption(f"총 {len(filtered)}건의 기록")
        with col_h2:
            if st.button("전체 기록 삭제"):
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.rerun()

        for i, entry in enumerate(filtered):
            title = f"[{entry.get('segment', '-')}] {entry.get('brand_name', '(브랜드명 없음)')} · {entry.get('timestamp', '')}"
            with st.expander(title):
                st.markdown(
                    f'<div class="history-meta">경쟁사 소재 {entry.get("material_count", 0)}개 · '
                    f'자사 소재 {entry.get("own_material_count", 0)}개 · '
                    f'타겟: {entry.get("target_audience", "-")}</div>',
                    unsafe_allow_html=True,
                )
                st.divider()
                if entry.get("insight"):
                    st.markdown("**위닝 포인트 요약**")
                    st.markdown(entry["insight"])
                    st.divider()
                if entry.get("gap_analysis"):
                    st.markdown("**메시지 갭 분석**")
                    st.markdown(entry["gap_analysis"])
                    st.divider()
                st.markdown("**스토리보드 아이디어**")
                st.markdown(entry.get("ideas", ""))
                st.download_button(
                    "이 결과 다운로드 (.md)", data=entry.get("ideas", ""),
                    file_name=f"ad_ideas_{entry.get('timestamp', '').replace(':', '').replace(' ', '_')}.md",
                    mime="text/markdown", key=f"history_dl_{i}",
                )
