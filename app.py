import base64
import io
import json
import os
import re
import time
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# 필수 패키지 자동 설치 보장 함수 (맨 처음에 실행)
def ensure_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        try:
            subprocess.run(["pip", "install", package_name], check=True)
        except Exception:
            pass

ensure_package("requests")
ensure_package("Pillow", "PIL")
ensure_package("beautifulsoup4", "bs4")
ensure_package("google-generativeai", "google.generativeai")
ensure_package("openai")
ensure_package("anthropic")
ensure_package("playwright")
# --- [추가] 히스토리 영구 저장을 위한 구글시트 연동 패키지 (선택 사항, 미설정 시 자동 미사용) ---
ensure_package("gspread")
ensure_package("google-auth", "google.oauth2")

import requests
import streamlit as st
from PIL import Image
from bs4 import BeautifulSoup

# 스트림릿 클라우드 서버 환경에서 Playwright 브라우저 자동 설치 보장
@st.cache_resource
def install_playwright():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_playwright()

try:
    from playwright.sync_api import sync_playwright
except Exception:
    pass

# ------------------------------------------------------------------
# 기본 설정 및 디자인 CSS
# ------------------------------------------------------------------
try:
    st.set_page_config(page_title="경쟁사 광고 소재 분석", layout="wide", page_icon="◆")
except Exception:
    pass

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

.appbar { display: flex; align-items: center; gap: 14px; padding: 18px 4px 20px 4px; border-bottom: 1px solid var(--border); margin-bottom: 18px; }
.appbar-mark { width: 34px; height: 34px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--teal)); flex-shrink: 0; }
.appbar-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 21px; line-height: 1.1; color: var(--ink) !important; }

.eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.08em; color: var(--primary) !important; background: var(--primary-soft); display: inline-block; padding: 3px 9px; border-radius: 4px; margin-bottom: 8px; font-weight: 600; }
.section-title { font-size: 20px; font-weight: 700; margin: 0 0 4px 0; color: var(--ink) !important; }
.section-desc { font-size: 13.5px; color: var(--muted) !important; margin-bottom: 18px; }

[data-testid="stSidebar"] {
    background-color: #F3F3EE !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }

.stButton > button { border-radius: 8px; font-weight: 600; border: 1px solid var(--border); background-color: #FFFFFF !important; color: var(--ink) !important; }
.stButton > button[kind="primary"] { background-color: var(--primary) !important; color: #FFFFFF !important; border: none; }
.stButton > button[kind="primary"] * { color: #FFFFFF !important; }
.stButton > button[kind="primary"]:hover { background-color: #21245A !important; }

.score-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }
.score-card { border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background-color: #FFFFFF !important; }
.score-cat { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.05em; color: var(--muted) !important; text-transform: uppercase; font-weight: 600; }
.score-stars { color: var(--amber) !important; font-size: 16px; margin: 4px 0; }
.score-desc { font-size: 13px; color: var(--ink) !important; line-height: 1.5; white-space: pre-line; }

.comp-card { border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; background-color: #FFFFFF !important; margin-bottom: 10px; }
.comp-name { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 15px; color: var(--ink) !important; }
.comp-meta { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted) !important; margin-top: 2px; }

div[data-baseweb="select"] > div,
div[data-baseweb="base-input"] > input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
div[data-baseweb="popover"],
div[data-testid="stPopoverBody"],
div[data-baseweb="menu"],
div[data-baseweb="tag"],
div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border-color: var(--border) !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div,
[data-baseweb="select"] * {
    background-color: transparent !important;
    color: var(--ink) !important;
}

div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
div[role="listbox"],
li[role="option"] {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
}
li[role="option"]:hover,
li[aria-selected="true"] {
    background-color: var(--primary-soft) !important;
    color: var(--ink) !important;
}

.align-bottom-btn { margin-top: 28px; }

/* ------------------------------------------------------------------
   [추가 CSS - 2번] 다크모드에서 새는 요소 추가 보강
   config.toml에서 라이트 테마를 강제하지만, 팝업/파일업로더 등
   일부 컴포넌트는 브라우저 렌더링 타이밍에 따라 새는 경우가 있어 이중 방어.
------------------------------------------------------------------ */
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"] section,
div[data-baseweb="popover"] * ,
ul[role="listbox"] li,
div[data-baseweb="calendar"],
div[data-baseweb="datepicker"] {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
}
svg { fill: currentColor; }
input, textarea { caret-color: var(--ink) !important; }

/* ------------------------------------------------------------------
   [추가 CSS - 4번] 세그먼트 / 좌측 메뉴를 알약형·현대적 네비게이션으로
------------------------------------------------------------------ */
/* 세그먼트 선택 - 가로 알약(pill) 탭 */
div[data-testid="stSidebar"] div[data-testid="stRadio"]:has(div[role="radiogroup"]) {
    margin-bottom: 4px;
}
div[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 6px;
}
div[data-testid="stSidebar"] div[role="radiogroup"] > label {
    border: 1px solid var(--border) !important;
    background: #FFFFFF !important;
    border-radius: 999px;
    padding: 7px 14px !important;
    margin: 0 !important;
    transition: all 0.15s ease;
}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
    color: #FFFFFF !important;
    font-weight: 700;
}
div[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important; /* 기본 라디오 원형 아이콘 숨김 */
}

/* 좌측 05단계 메뉴 - 세로 카드형 내비게이션 */
.nav-block div[role="radiogroup"] {
    flex-direction: column;
    gap: 4px;
}
.nav-block div[role="radiogroup"] > label {
    width: 100%;
    border-radius: 8px;
    padding: 10px 12px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
}
.nav-block div[role="radiogroup"] > label:has(input:checked) {
    background: var(--primary-soft) !important;
    border-color: var(--primary) !important;
}
.nav-block div[role="radiogroup"] > label:has(input:checked) p {
    color: var(--primary) !important;
    font-weight: 700;
}
.nav-block div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
.sidebar-caption {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 0.08em;
    color: var(--muted) !important;
    margin: 4px 0 6px 2px;
    text-transform: uppercase;
    font-weight: 700;
}
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
# 세그먼트 & 메타 URL 사전
# ------------------------------------------------------------------
SEGMENTS = ["유아", "초등", "중등"]
DEFAULT_COMPETITORS = {
    "유아": ["윙크", "웅진스마트올", "밀크T아이", "리틀홈런"],
    "초등": ["밀크T", "아이스크림 홈런", "비상 온리원", "단꿈e", "기타"],
    "중등": ["밀크T중등", "웅진스마트올 중학", "비상 온리원 중등", "아이스크림 홈런 중등", "EBS"],
}

META_URL_MAP = {
    "윙크": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&q=%EC%9C%99%ED%81%AC%ED%95%99%EC%8A%B5&search_type=keyword_unordered&sort_data[direction]=desc&sort_data[mode]=total_impressions",
    "웅진스마트올": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=100188454740792",
    "밀크T아이": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=113781314278271",
    "리틀홈런": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&q=%EB%A6%AC%ED%8B%80%ED%99%88%EB%9F%B0&search_type=keyword_unordered&sort_data[direction]=desc&sort_data[mode]=total_impressions",
    "밀크T": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=699675066795625",
    "아이스크림 홈런": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=562669550571671",
    "비상 온리원": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=552773944780211",
    "단꿈e": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=350531981486027",
    "밀크T중등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=101376489315136",
    "웅진스마트올 중학": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=103396781600446",
    "비상 온리원 중등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=989750591106584",
    "아이스크림 홈런 중등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&q=%ED%99%88%EB%9F%B0%20%EC%A4%91%EB%93%B1&search_type=keyword_unordered&sort_data[direction]=desc&sort_data[mode]=total_impressions"
}

OWN_META_URL_MAP = {
    "유아": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=104085702734737",
    "초등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=113924893334247",
    "중등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=1600636653593633"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "ad_signal_history.json")
BRAND_FILE = os.path.join(BASE_DIR, "ad_signal_brand.json")
COMPETITORS_FILE = os.path.join(BASE_DIR, "ad_signal_competitors.json")
PROFILES_FILE = os.path.join(BASE_DIR, "ad_signal_profiles.json")
SELECTORS_FILE = os.path.join(BASE_DIR, "ad_signal_selectors.json")
# --- [추가 - 5,6번] 자사 소재 분석 & 인사이트/갭분석을 세션이 아닌 파일(=구글시트)에 영구 저장 ---
OWN_FILE = os.path.join(BASE_DIR, "ad_signal_own.json")
WORK_STATE_FILE = os.path.join(BASE_DIR, "ad_signal_work_state.json")

DEFAULT_SELECTORS = {
    "ad_card_candidates": [
        'div[class*="_7jyg"]',
        'div[class*="_7j6g"]',
        'div[role="article"]',
        'div[data-testid="ad_library_card"]',
    ],
    "image_domain_keywords": ["scontent", "fbcdn"],
    "image_min_width": 150,
    "max_scroll_count": 8,
    "scroll_wait_ms": 2000,
    "initial_wait_timeout_ms": 15000,
}

def load_selectors():
    data = load_json(SELECTORS_FILE, None)
    if data is None:
        data = json.loads(json.dumps(DEFAULT_SELECTORS))
        save_json(SELECTORS_FILE, data)
        return data
    merged = dict(DEFAULT_SELECTORS)
    merged.update(data)
    return merged

def save_selectors(data): save_json(SELECTORS_FILE, data)
def reset_selectors():
    data = json.loads(json.dumps(DEFAULT_SELECTORS))
    save_json(SELECTORS_FILE, data)
    return data


# ------------------------------------------------------------------
# [추가 - 6번] 구글시트 기반 영구 저장소
# Streamlit Cloud의 로컬 파일시스템은 컨테이너가 재시작되면 초기화될 수 있어
# 히스토리가 계속 리셋되는 문제가 있었습니다. secrets.toml에
# GSHEET_ID / gcp_service_account 가 설정되어 있으면 자동으로 구글시트에
# 저장하고, 설정이 없으면 예전처럼 로컬 파일을 그대로 사용합니다(무설정 시 동작 100% 동일).
# 설정 방법은 채팅 답변 참고.
# ------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _get_gsheet_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        if "gcp_service_account" not in st.secrets:
            return None
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
        return gspread.authorize(creds)
    except Exception:
        return None

def _get_worksheet(sheet_name):
    client = _get_gsheet_client()
    if client is None:
        return None
    try:
        sheet_id = st.secrets.get("GSHEET_ID")
        if not sheet_id:
            return None
        sh = client.open_by_key(sheet_id)
        try:
            ws = sh.worksheet(sheet_name)
        except Exception:
            ws = sh.add_worksheet(title=sheet_name, rows=500, cols=1)
        return ws
    except Exception:
        return None

def load_json(path, default):
    """구글시트가 설정되어 있으면 시트에서, 아니면 로컬 파일에서 읽기"""
    sheet_name = os.path.splitext(os.path.basename(path))[0]
    ws = _get_worksheet(sheet_name)
    if ws is not None:
        try:
            col = ws.col_values(1)
            chunks = col[1:] if len(col) > 1 else []
            if chunks:
                return json.loads("".join(chunks))
            return default
        except Exception:
            return default
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as fp: return json.load(fp)
    except Exception: return default

def save_json(path, data):
    """구글시트가 설정되어 있으면 시트에, 아니면 로컬 파일에 쓰기
    (구글시트 셀당 50,000자 제한이 있어 4만자 단위로 청크 분할 저장)"""
    sheet_name = os.path.splitext(os.path.basename(path))[0]
    ws = _get_worksheet(sheet_name)
    if ws is not None:
        try:
            text = json.dumps(data, ensure_ascii=False)
            chunk_size = 40000
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
            ws.clear()
            ws.update("A1", [["chunk"]] + [[c] for c in chunks])
            return
        except Exception:
            pass  # 실패 시 로컬 파일로 폴백
    with open(path, "w", encoding="utf-8") as fp: json.dump(data, fp, ensure_ascii=False, indent=2)


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

def remove_competitor(segment, name):
    data = load_competitors()
    if name in data[segment]:
        data[segment].remove(name)
        save_json(COMPETITORS_FILE, data)

def load_all_profiles(): return load_json(PROFILES_FILE, {})
def save_profile_entry(segment, competitor, entry):
    data = load_all_profiles()
    data.setdefault(segment, {}).setdefault(competitor, []).insert(0, entry)
    save_json(PROFILES_FILE, data)

# --- [추가 - 5,6번] 자사 소재 분석 결과 영구 저장 (기존엔 세션에만 있어서 새로고침하면 사라짐) ---
def load_own_analysis(segment):
    return load_json(OWN_FILE, {}).get(segment)

def save_own_analysis(segment, data):
    all_own = load_json(OWN_FILE, {})
    all_own[segment] = data
    save_json(OWN_FILE, all_own)

# --- [추가 - 5,6번] 세그먼트별 작업 상태(인사이트/갭분석/스토리보드) 영구 저장 ---
def load_work_state(segment):
    default = {"insight": "", "gap_analysis": "", "ideas": ""}
    default.update(load_json(WORK_STATE_FILE, {}).get(segment, {}))
    return default

def save_work_state(segment, data):
    all_state = load_json(WORK_STATE_FILE, {})
    all_state[segment] = data
    save_json(WORK_STATE_FILE, all_state)


# ------------------------------------------------------------------
# Playwright 크롤링 함수
# ------------------------------------------------------------------
_EXTRACT_ADS_JS = """
(config) => {
    const { ad_card_candidates, image_domain_keywords, image_min_width } = config;
    let cards = [];
    let usedSelector = null;
    for (const sel of ad_card_candidates) {
        try {
            const found = document.querySelectorAll(sel);
            if (found.length > 0) {
                cards = Array.from(found);
                usedSelector = sel;
                break;
            }
        } catch (e) {}
    }
    const scope = cards.length ? cards : [document.body];
    if (!cards.length) usedSelector = 'FALLBACK: document.body';

    const seen = new Set();
    const items = [];
    scope.forEach((card) => {
        const imgs = card.querySelectorAll('img');
        imgs.forEach((img) => {
            const src = img.currentSrc || img.src || '';
            if (!src || seen.has(src)) return;

            let renderedWidth = img.naturalWidth || 0;
            let renderedHeight = img.naturalHeight || 0;
            if (!renderedWidth) {
                try { 
                    const rect = img.getBoundingClientRect();
                    renderedWidth = Math.round(rect.width) || 0;
                    renderedHeight = Math.round(rect.height) || 0;
                } catch (e) {}
            }
            if (!renderedWidth) renderedWidth = img.width || 0;
            if (!renderedHeight) renderedHeight = img.height || 0;

            if (renderedWidth > 0 && renderedWidth < image_min_width) return;
            if (renderedHeight > 0 && renderedHeight < image_min_width) return;
            
            if (renderedWidth > 0 && renderedHeight > 0) {
                const ratio = renderedWidth / renderedHeight;
                if (ratio > 0.8 && ratio < 1.2 && renderedWidth < 180) return;
            }

            const matchesDomain = image_domain_keywords.some((k) => src.includes(k));
            if (!matchesDomain) return;

            seen.add(src);
            let bodyText = '';
            try { bodyText = (card.innerText || '').slice(0, 300); } catch (e) {}
            items.push({ src, bodyText });
        });
    });
    return { usedSelector, cardCount: cards.length, items };
}
"""

def _upgrade_image_resolution(url):
    if not url: return url
    try:
        def _bump(match):
            w, h = int(match.group(1)), int(match.group(2))
            return f"s{min(int(w * 1.6), 1080)}x{min(int(h * 1.6), 1080)}"
        return re.sub(r"s(\d{2,4})x(\d{2,4})", _bump, url)
    except Exception:
        return url

def _scrape_once(library_url, max_items, cfg, status_callback=None):
    results = []
    debug_info = {"used_selector": None, "card_count": 0}
    
    if status_callback: status_callback("브라우저 엔진을 구동하고 있습니다...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-extensions", "--no-zygote"]
        )
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="ko-KR"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            page.route("**/*", lambda route: route.abort() if route.request.resource_type in ("media", "font") else route.continue_())
            
            if status_callback: status_callback("메타 광고 라이브러리 페이지에 접속 중입니다...")
            page.goto(library_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if page.is_closed(): raise RuntimeError("브라우저 종료됨")
            try:
                page.wait_for_selector(", ".join(cfg["ad_card_candidates"]), timeout=cfg.get("initial_wait_timeout_ms", 15000))
            except Exception:
                pass
            
            if status_callback: status_callback("활성 광고 데이터를 스크롤하여 불러오는 중...")
            last_height = 0
            for i in range(cfg.get("max_scroll_count", 8)):
                if page.is_closed(): break
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(cfg.get("scroll_wait_ms", 2000) / 1000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height
            
            time.sleep(1.5)
            if status_callback: status_callback("광고 소재 이미지 및 텍스트를 추출하고 있습니다...")
            extracted = page.evaluate(_EXTRACT_ADS_JS, cfg)
            debug_info["used_selector"] = extracted.get("usedSelector")
            debug_info["card_count"] = extracted.get("cardCount", 0)
            
            total_items = extracted.get("items", [])[:max_items]
            for idx, item in enumerate(total_items, start=1):
                if status_callback: status_callback(f"고화질 광고 소재 이미지 다운로드 중 ({idx}/{len(total_items)}건)...")
                img_url = item.get("src")
                body_text = item.get("bodyText", "")
                img_bytes = None
                if img_url:
                    hi_res = _upgrade_image_resolution(img_url)
                    for cand in [hi_res, img_url]:
                        try:
                            resp = requests.get(cand, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                            if resp.status_code == 200:
                                img_bytes = resp.content
                                break
                        except Exception:
                            continue
                results.append({"id": f"pw_{idx}_{time.time()}", "fn": f"ad_{idx}.png", "bytes": img_bytes, "body": body_text, "snapshot_url": library_url})
        finally:
            try: browser.close()
            except Exception: pass
    return results, debug_info

def scrape_meta_ads_with_playwright(library_url, max_items=12, selectors=None, status_callback=None, _retry=True):
    cfg = selectors or load_selectors()
    try:
        results, debug_info = _scrape_once(library_url, max_items, cfg, status_callback)
        return results, debug_info, None
    except Exception as e:
        err_text = str(e)
        if ("closed" in err_text or "종료" in err_text) and _retry:
            time.sleep(2)
            return scrape_meta_ads_with_playwright(library_url, max_items, cfg, status_callback, _retry=False)
        return [], {"used_selector": None, "card_count": 0}, f"오류 발생: {err_text}"

def create_image_grid_collage(images_bytes_list, cols=4, thumb_size=(180, 180)):
    try:
        pil_images = []
        for b in images_bytes_list[:12]:
            if not b: continue
            try:
                img = Image.open(io.BytesIO(b)).convert("RGB")
                img.thumbnail(thumb_size)
                pil_images.append(img)
            except Exception: pass
        if not pil_images: return None
        num_imgs = len(pil_images)
        rows = (num_imgs + cols - 1) // cols
        collage = Image.new("RGB", (cols * thumb_size[0], rows * thumb_size[1]), (255, 255, 255))
        for idx, img in enumerate(pil_images):
            collage.paste(img, ((idx % cols) * thumb_size[0], (idx // cols) * thumb_size[1]))
        buf = io.BytesIO()
        collage.save(buf, format="JPEG", quality=65)
        return buf.getvalue()
    except Exception: return None

BRAND_INTEGRATED_ANALYSIS_PROMPT = """당신은 수석 퍼포먼스 마케팅 크리에이티브 분석가입니다.
제시된 브랜드 '{brand_name}'이 메타 라이브러리에서 현재 동시 운영 중인 전체 광고 소재 그리드 이미지를 통째로 조망하고 객관적인 브랜드 통합 분석을 진행해 주세요.
메시지_좋은점: (이 브랜드 소재들에서 강조되는 핵심 메인 메시지 및 소구 포인트 전략 강점 2문장)
메시지_아쉬운점: (메시지 측면에서 진부하거나 보완이 필요한 점 1~2문장)
메시지_평점: (숫자만 1~5)
비주얼_좋은점: (전체적인 키 비주얼, 색감, 톤앤매너, 레이아웃 차별성 및 강점 2문장)
비주얼_아쉬운점: (시각적 피로도나 디자인 요소 측면에서 아쉬운 점 1~2문장)
비주얼_평점: (숫자만 1~5)
종합_총평: (전체 광고 소재가 예상 타겟층에게 전달되는 판독성 및 브랜드 타겟팅 종합 한줄 총평)
종합_평점: (숫자만 1~5)
"""

_SCORE_LABEL_TO_KEY = {
    "메시지_좋은점": "msg_good", "메시지_아쉬운점": "msg_bad", "메시지_평점": "msg_score",
    "비주얼_좋은점": "vis_good", "비주얼_아쉬운점": "vis_bad", "비주얼_평점": "vis_score",
    "종합_총평": "overall_desc", "종합_평점": "overall_score",
}
_SCORE_EMPTY = {k: "" for k in _SCORE_LABEL_TO_KEY.values()}

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

def parse_integrated_report(text): return parse_labeled_text(text, _SCORE_LABEL_TO_KEY, _SCORE_EMPTY)

def render_integrated_scorecard(report):
    msg_desc = f"👍 **장점**: {report.get('msg_good', '')}\n👎 **아쉬운점**: {report.get('msg_bad', '')}"
    vis_desc = f"👍 **장점**: {report.get('vis_good', '')}\n👎 **아쉬운점**: {report.get('vis_bad', '')}"
    overall_desc = report.get('overall_desc', '')
    cats = [
        ("메시지 전략", msg_desc, report.get("msg_score", 0)),
        ("비주얼 / 디자인", vis_desc, report.get("vis_score", 0)),
        ("종합 타겟 전달력 평가", overall_desc, report.get("overall_score", 0)),
    ]
    html = '<div class="score-grid">'
    for label, desc, score in cats:
        html += f'<div class="score-card"><div class="score-cat">{label}</div><div class="score-stars">{stars(score)}</div><div class="score-desc">{desc}</div></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def run_unified_ai_prompt(ai_provider, api_key, prompt_text, collage_bytes=None):
    if ai_provider == "Gemini (Google)":
        try:
            import google.generativeai as genai
        except ImportError:
            subprocess.run(["pip", "install", "google-generativeai"], check=True)
            import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        # [수정 - 3번] gemini-1.5-pro는 완전히 서비스 종료(404)됨.
        # -latest 별칭을 사용하면 구글이 모델을 교체해도 자동으로 최신 모델을 가리켜서
        # 앞으로 이런 단종 문제가 재발할 확률이 낮습니다.
        model = genai.GenerativeModel("gemini-flash-latest")
        contents = [prompt_text]
        if collage_bytes: contents.append(Image.open(io.BytesIO(collage_bytes)))
        return model.generate_content(contents).text

    elif ai_provider == "ChatGPT (OpenAI)":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        content_payload = [{"type": "text", "text": prompt_text}]
        if collage_bytes:
            content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(collage_bytes).decode('utf-8')}"}})
        # [수정 - 3번] gpt-4o -> gpt-5.1 (최신 플래그십, 비전 지원)
        return client.chat.completions.create(model="gpt-5.1", messages=[{"role": "user", "content": content_payload}]).choices[0].message.content

    elif ai_provider == "Claude (Anthropic)":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        content_payload = []
        if collage_bytes:
            content_payload.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(collage_bytes).decode('utf-8')}})
        content_payload.append({"type": "text", "text": prompt_text})
        # [수정 - 3번] claude-3-5-sonnet-20241022 -> claude-sonnet-5 (최신 모델)
        return client.messages.create(model="claude-sonnet-5", max_tokens=2000, messages=[{"role": "user", "content": content_payload}]).content[0].text

def run_brand_integrated_analysis(ai_provider, api_key, brand_name, images_bytes_list):
    return parse_integrated_report(run_unified_ai_prompt(ai_provider, api_key, BRAND_INTEGRATED_ANALYSIS_PROMPT.format(brand_name=brand_name), create_image_grid_collage(images_bytes_list)))


# ------------------------------------------------------------------
# [소재 수집 UI]
# ------------------------------------------------------------------
def render_material_section(prefix, selected_comp, default_url, on_complete):
    tab1, tab2 = st.tabs(["🚀 자동 크롤링 수집", "📁 예비 업로드"])
    sess_key = f"{prefix}_items_{selected_comp}"
    if sess_key not in st.session_state: st.session_state[sess_key] = []

    with tab1:
        meta_url = st.text_input("메타 광고 라이브러리 페이지 URL", value=default_url, key=f"{prefix}_meta_url_input_{selected_comp}")
        if st.button("🚀 전체 라이브 소재 자동 수집 실행", key=f"{prefix}_crawl_btn", type="primary"):
            if not meta_url.strip():
                st.warning("메타 라이브러리 URL을 입력해주세요.")
            else:
                with st.status(f"'{selected_comp}' 광고 라이브러리 수집 진행 중...", expanded=True) as status_box:
                    def update_status(msg):
                        status_box.update(label=msg, state="running")

                    ads, debug_info, err = scrape_meta_ads_with_playwright(
                        meta_url.strip(), max_items=12, selectors=load_selectors(), status_callback=update_status
                    )

                    if err:
                        status_box.update(label="수집 중 오류 발생", state="error")
                        st.error(err)
                    elif not ads:
                        status_box.update(label="수집된 활성 광고가 없습니다.", state="complete")
                        st.info(f"⚠️ [{selected_comp}] 활성 광고를 수집하지 못했습니다. [예비 업로드] 탭을 활용해 주세요.")
                        st.session_state[sess_key] = []
                    else:
                        status_box.update(label=f"'{selected_comp}' 총 {len(ads)}건 수집 완료!", state="complete")
                        st.session_state[sess_key] = ads
                        st.success(f"[{selected_comp}] 총 {len(ads)}건 수집 완료")

    with tab2:
        uploaded_files = st.file_uploader("광고 이미지 업로드", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"{prefix}_uploader_{selected_comp}")
        if uploaded_files:
            st.session_state[sess_key] = [{"id": f"upload_{i}_{len(f.read())}", "fn": f.name, "bytes": f.getvalue()} for i, f in enumerate(uploaded_files, start=1)]

    items = st.session_state[sess_key]
    if items:
        st.divider()
        st.markdown(f"**수집된 소재 ({len(items)}건) — 타겟 연령대가 다른 소재는 ❌ 삭제하세요**")
        items_to_remove = []
        for i in range(0, len(items), 6):
            row_items = items[i:i + 6]
            grid_cols = st.columns(6)
            for idx, item in enumerate(row_items):
                with grid_cols[idx]:
                    if item.get("bytes"): st.image(item["bytes"], width=110)
                    if st.button("❌", key=f"del_{item['id']}_{selected_comp}"): items_to_remove.append(item['id'])
        if items_to_remove:
            st.session_state[sess_key] = [it for it in st.session_state[sess_key] if it['id'] not in items_to_remove]
            st.rerun()

        st.divider()
        if st.button(f"'{selected_comp}' 전체 브랜드 통합 분석 실행", type="primary", key=f"{prefix}_analyze_btn_{selected_comp}"):
            if not st.session_state.get("current_api_key"):
                st.error("상단에서 AI API Key를 입력해 주세요.")
            else:
                raw_bytes_list = [it["bytes"] for it in st.session_state[sess_key] if it.get("bytes")]
                if not raw_bytes_list:
                    st.warning("분석 가능한 이미지가 없습니다.")
                else:
                    try:
                        report = run_brand_integrated_analysis(st.session_state['current_ai_provider'], st.session_state['current_api_key'], selected_comp, raw_bytes_list)
                        on_complete({"brand_name": selected_comp, "count": len(st.session_state[sess_key]), "report": report})
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")


# ------------------------------------------------------------------
# 상단 헤더 & 멀티 AI 엔진 선택 영역
# ------------------------------------------------------------------
top_col1, top_col2, top_col3 = st.columns([2.5, 1.2, 1.5])
with top_col1:
    st.markdown('<div class="appbar"><div class="appbar-mark"></div><div><div class="appbar-title">경쟁사 광고 소재 분석</div></div></div>', unsafe_allow_html=True)

with top_col2:
    ai_provider = st.selectbox("AI 엔진 선택", ["Gemini (Google)", "ChatGPT (OpenAI)", "Claude (Anthropic)"], key="selected_ai_provider")
    st.session_state["current_ai_provider"] = ai_provider

with top_col3:
    default_key = ""
    try:
        if ai_provider == "Gemini (Google)" and "GEMINI_API_KEY" in st.secrets: default_key = st.secrets["GEMINI_API_KEY"]
        elif ai_provider == "ChatGPT (OpenAI)" and "OPENAI_API_KEY" in st.secrets: default_key = st.secrets["OPENAI_API_KEY"]
        elif ai_provider == "Claude (Anthropic)" and "ANTHROPIC_API_KEY" in st.secrets: default_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception: pass

    input_api_key = st.text_input(f"{ai_provider} API Key", value=default_key, type="password", key="main_ai_api_key_input")
    st.session_state["current_api_key"] = input_api_key

st.divider()

# ------------------------------------------------------------------
# 사이드바
# ------------------------------------------------------------------
NAV_ITEMS = ["🏆 01 · 경쟁사 소재 분석", "🏠 02 · 자사 소재 분석", "🔍 03 · 메시지 갭 분석", "🎬 04 · 스토리보드 아이디어", "🗂️ 05 · 히스토리"]

with st.sidebar:
    st.markdown('<div class="sidebar-caption">SEGMENT</div>', unsafe_allow_html=True)
    segment = st.radio("사업 구분", SEGMENTS, label_visibility="collapsed", key="segment_selector", horizontal=True)
    st.divider()
    st.markdown('<div class="sidebar-caption">MENU</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-block">', unsafe_allow_html=True)
    nav_full = st.radio("메뉴", NAV_ITEMS, label_visibility="collapsed", key="nav_selector")
    st.markdown('</div>', unsafe_allow_html=True)
    nav = nav_full.split(" · ", 1)[1] if " · " in nav_full else nav_full
    nav = "0" + nav if False else nav  # (내부 로직 호환을 위해 아래에서 원래 라벨과 매칭)

# 기존 코드의 "01 · ..." 형태 라벨과 매칭되도록 변환
_NAV_MAP = {item: item.split(" ", 1)[1] for item in NAV_ITEMS}
nav = _NAV_MAP[nav_full]

if "work" not in st.session_state: st.session_state.work = {}
if segment not in st.session_state.work:
    _persisted = load_work_state(segment)
    st.session_state.work[segment] = {
        "own_analyses": load_own_analysis(segment),
        "insight": _persisted.get("insight", ""),
        "gap_analysis": _persisted.get("gap_analysis", ""),
        "ideas": _persisted.get("ideas", ""),
        "last_comp_result": None,
        "last_competitor": "",
    }
W = st.session_state.work[segment]

def _persist_work_state():
    """인사이트 / 갭분석 / 스토리보드는 새로고침·재접속해도 남도록 즉시 저장"""
    save_work_state(segment, {
        "insight": W.get("insight", ""),
        "gap_analysis": W.get("gap_analysis", ""),
        "ideas": W.get("ideas", ""),
    })

# ------------------------------------------------------------------
# 01 · 경쟁사 소재 분석
# ------------------------------------------------------------------
if nav == "01 · 경쟁사 소재 분석":
    section_header("01", f"{segment} 경쟁사 광고 소재 분석", "경쟁사를 선택하면 해당 브랜드의 메타 광고 라이브러리 URL이 자동으로 세팅됩니다.")

    competitors = load_competitors()[segment]
    
    comp_col, add_col = st.columns([4, 1.2])
    with comp_col:
        selected_competitor = st.selectbox("분석할 경쟁사", competitors, key=f"{segment}_comp_select")
    with add_col:
        st.markdown('<div class="align-bottom-btn"></div>', unsafe_allow_html=True)
        with st.popover("+ 새 경쟁사 추가", use_container_width=True):
            st.markdown("##### 새 경쟁사 추가")
            new_comp = st.text_input("경쟁사명 입력", key=f"{segment}_new_comp_input")
            if st.button("추가 완료", key=f"{segment}_new_comp_btn", type="primary", use_container_width=True):
                if new_comp.strip():
                    add_competitor(segment, new_comp.strip())
                    st.success(f"'{new_comp.strip()}' 추가 완료!")
                    time.sleep(0.5)
                    st.rerun()

    default_list = DEFAULT_COMPETITORS.get(segment, [])
    custom_added = [c for c in competitors if c not in default_list]
    if custom_added:
        st.markdown("<div style='font-size: 12px; color: #555866; margin-top: 6px; margin-bottom: 8px;'>📌 내가 추가한 경쟁사 (❌를 누르면 바로 삭제됩니다)</div>", unsafe_allow_html=True)
        del_cols = st.columns(min(len(custom_added), 4))
        for c_idx, c_name in enumerate(custom_added):
            with del_cols[c_idx % len(del_cols)]:
                if st.button(f"{c_name} ❌", key=f"quick_del_{segment}_{c_name}", use_container_width=True):
                    remove_competitor(segment, c_name)
                    st.success(f"'{c_name}' 삭제 완료!")
                    time.sleep(0.3)
                    st.rerun()

    auto_url = META_URL_MAP.get(selected_competitor, "")

    def _on_comp_complete(res):
        W["last_comp_result"] = res
        W["last_competitor"] = selected_competitor
        save_profile_entry(segment, selected_competitor, {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "count": res["count"], "report": res["report"]})
        st.success(f"'{selected_competitor}' 전체 브랜드 통합 분석 완료!")

    render_material_section("comp", selected_competitor, auto_url, _on_comp_complete)

    if W["last_comp_result"] and W["last_competitor"] == selected_competitor:
        st.divider()
        st.markdown(f"### '{W['last_competitor']}' 브랜드 전체 크리에이티브 통합 분석 리포트")
        render_integrated_scorecard(W["last_comp_result"]["report"])

# ------------------------------------------------------------------
# 02 · 자사 소재 분석
# ------------------------------------------------------------------
elif nav == "02 · 자사 소재 분석":
    section_header("02", f"{segment} 자사 광고 소재 분석")

    def _on_own_complete(res):
        W["own_analyses"] = res
        save_own_analysis(segment, res)  # [수정 - 5,6번] 세션이 아닌 파일에 영구 저장
        st.success("자사 소재 분석 완료! (03 탭 메시지 갭 분석에서 계속 사용됩니다)")

    render_material_section("own", f"자사({segment})", OWN_META_URL_MAP.get(segment, ""), _on_own_complete)

    if W["own_analyses"]:
        st.divider()
        st.markdown("### 저장된 자사 브랜드 통합 분석 리포트")
        render_integrated_scorecard(W["own_analyses"].get("report", {}))

# ------------------------------------------------------------------
# 03 · 메시지 갭 분석
# ------------------------------------------------------------------
elif nav == "03 · 메시지 갭 분석":
    section_header("03", f"{segment} 메시지 갭 분석 & 위닝 포인트")
    
    profiles = load_all_profiles().get(segment, {})
    all_comp_entries = [(comp, e) for comp, es in profiles.items() for e in es]

    if not all_comp_entries:
        st.info("먼저 01 탭에서 경쟁사 소재 분석을 완료해주세요.")
    else:
        if st.button("경쟁사 위닝 포인트 도출", type="primary", key="insight_btn"):
            if not st.session_state.get("current_api_key"):
                st.error("상단에서 API Key를 입력해 주세요.")
            else:
                comp_summary = ""
                for comp, e in all_comp_entries:
                    rep = e.get("report", {})
                    comp_summary += f"[{comp}]\n메시지장점: {rep.get('msg_good','')}\n아쉬운점: {rep.get('msg_bad','')}\n\n"

                INSIGHT_PROMPT = """당신은 수석 브랜드 전략가입니다. 아래 경쟁사들의 최신 광고 분석 리포트를 검토하고,
경쟁사들이 공통으로 활용하고 있는 성공 패턴(위닝 포인트)을 3가지 핵심 키워드로 요약하고, 시장의 트렌드 인사이트를 도출해주세요.

[경쟁사 분석 모음]
{comp_summary}

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
                        resp_text = run_unified_ai_prompt(
                            st.session_state["current_ai_provider"],
                            st.session_state["current_api_key"],
                            INSIGHT_PROMPT.format(comp_summary=comp_summary)
                        )
                        W["insight"] = resp_text
                        _persist_work_state()  # [수정 - 5,6번]
                    except Exception as e: st.error(f"오류 발생: {e}")

        if W["insight"]: st.markdown(W["insight"])

        st.divider()
        st.markdown("**우리 소재와 비교해서 부족한 메시지 찾기**")

        if not W["own_analyses"]:
            st.info("02 탭(자사 소재 분석)에서 자사 소재 분석을 완료하면, 경쟁사 대비 부족한 메시지를 비교해드려요.")
        else:
            if st.button("메시지 갭 분석 실행", type="primary", key="gap_btn"):
                if not st.session_state.get("current_api_key"):
                    st.error("상단에서 API Key를 입력해 주세요.")
                else:
                    comp_summary = ""
                    for comp, e in all_comp_entries:
                        rep = e.get("report", {})
                        comp_summary += f"[{comp}] 메시지: {rep.get('msg_good','')} / 비주얼: {rep.get('vis_good','')}\n"
                    
                    own_rep = W["own_analyses"].get("report", {})
                    # [수정 - 5번] 메시지뿐 아니라 비주얼 강약점까지 포함해서 비교 정확도를 높임
                    own_summary = (
                        f"[자사] 메시지 장점: {own_rep.get('msg_good','')}\n"
                        f"메시지 아쉬운점: {own_rep.get('msg_bad','')}\n"
                        f"비주얼 장점: {own_rep.get('vis_good','')}\n"
                        f"비주얼 아쉬운점: {own_rep.get('vis_bad','')}"
                    )

                    GAP_PROMPT = """당신은 브랜드 전략 컨설턴트입니다. 아래는 경쟁사 그룹과 자사 브랜드 분석 정보입니다.
두 그룹을 비교해서 아래 내용을 정리해주세요.

[경쟁사 그룹 요약 (메시지/비주얼)]
{comp_summary}

[자사 브랜드 요약 (메시지/비주얼)]
{own_summary}

작성 형식:
### 경쟁사는 다루지만 우리 소재에는 부족한 메시지
- ...

### 보강하면 좋을 메시지 (우선순위 순, 이유 포함)
1. ...
2. ...
3. ...

### 비주얼/톤앤매너 측면에서 참고할 점
- ...

### 우리만 갖고 있는 강점 (계속 유지할 것)
- ...
"""
                    with st.spinner("갭 분석 중..."):
                        try:
                            resp_text = run_unified_ai_prompt(
                                st.session_state["current_ai_provider"],
                                st.session_state["current_api_key"],
                                GAP_PROMPT.format(comp_summary=comp_summary, own_summary=own_summary)
                            )
                            W["gap_analysis"] = resp_text
                            _persist_work_state()  # [수정 - 5,6번]
                        except Exception as e: st.error(f"오류 발생: {e}")

            if W["gap_analysis"]: st.markdown(W["gap_analysis"])

# ------------------------------------------------------------------
# 04 · 스토리보드 아이디어
# ------------------------------------------------------------------
elif nav == "04 · 스토리보드 아이디어":
    section_header("04", f"{segment} 맞춤형 스토리보드 아이디어", "브랜드 정보를 입력하고 기획안을 생성합니다.")

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
            if not st.session_state.get("current_api_key"):
                st.error("상단에서 API Key를 입력해 주세요.")
            else:
                gap_context = W["gap_analysis"] or "없음 (아직 메시지 갭 분석을 실행하지 않음)"

                STORYBOARD_PROMPT = """당신은 크리에이티브 디렉터입니다. 아래 경쟁사 분석 결과, 메시지 갭 분석, 우리 브랜드 정보,
그리고 자사 디자인 메모리를 반영하여 차별화된 **광고 크리에이티브 스토리보드 3개**를 제안해주세요.

[자사 브랜드 정보]
- 브랜드/제품명: {brand_name}
- 제품 설명: {brand_product}
- 핵심 USP: {brand_usp}
- 타겟 고객: {target_audience}
- 자사 디자인 가이드: {design_memory}

[메시지 갭 분석]
{gap_context}

각 아이디어는 아래 구조의 스토리보드 형식으로 작성해주세요:
### [아이디어 N] 한줄 컨셉 타이틀
- **타겟구간 / 매체 소구 포인트**: 
- **훅킹 카피 (오프닝 3초)**: 
- **비주얼 구성안 (연출 기획)**: 
- **본문 설득 및 USP 소구 방식**: 
- **CTA (행동 유도 문구)**: 
- **차별화 포인트**: 
"""
                with st.spinner("스토리보드 기획안 작성 중..."):
                    try:
                        resp_text = run_unified_ai_prompt(
                            st.session_state["current_ai_provider"],
                            st.session_state["current_api_key"],
                            STORYBOARD_PROMPT.format(
                                brand_name=brand_name, brand_product=brand_product, brand_usp=brand_usp,
                                target_audience=target_audience,
                                design_memory=brand_design_memory or "기본 톤앤매너",
                                gap_context=gap_context
                            )
                        )
                        W["ideas"] = resp_text
                        _persist_work_state()  # [수정 - 5,6번]

                        save_history_entry({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "segment": segment,
                            "brand_name": brand_name,
                            "brand_product": brand_product,
                            "target_audience": target_audience,
                            "material_count": len(all_comp_entries),
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
# 05 · 히스토리
# ------------------------------------------------------------------
elif nav == "05 · 히스토리":
    section_header("05", "히스토리", "완료한 아이디어 추출 결과가 부문 구분과 함께 자동으로 쌓입니다.")

    history = load_history()
    show_all = st.checkbox("모든 부문 보기 (선택 해제 시 현재 부문만)", value=False)
    filtered = history if show_all else [h for h in history if h.get("segment", "") == segment]

    if not filtered:
        st.info("아직 완료된 결과가 없어요. 04 탭에서 아이디어를 생성하면 여기에 자동으로 기록됩니다.")
    else:
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1: st.caption(f"총 {len(filtered)}건의 기록")
        with col_h2:
            if st.button("전체 기록 삭제"):
                save_json(HISTORY_FILE, [])
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.rerun()

        for i, entry in enumerate(filtered):
            title = f"[{entry.get('segment', '-')}] {entry.get('brand_name', '(브랜드명 없음)')} · {entry.get('timestamp', '')}"
            with st.expander(title):
                st.markdown(f'<div class="history-meta">분석 경쟁사 {entry.get("material_count", 0)}개 · 타겟: {entry.get("target_audience", "-")}</div>', unsafe_allow_html=True)
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
