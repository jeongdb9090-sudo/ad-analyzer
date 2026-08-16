import base64
import io
import json
import os
import re
import time
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import requests
import streamlit as str_lit
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
from playwright.sync_api import sync_playwright

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

/* 셀렉트박스 / 텍스트 인풋 / 텍스트에어리어 가독성 강제 (다크 테마에서도 항상 밝은 배경 + 어두운 글씨) */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] span,
[data-testid="stSelectbox"] div[data-baseweb="select"] div {
    color: var(--ink) !important;
}

/* 셀렉트박스를 클릭했을 때 뜨는 드롭다운 옵션 목록 */
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
    "유아": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=1600636653593633",
    "초등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=113924893334247",
    "중등": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=104085702734737"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "ad_signal_history.json")
BRAND_FILE = os.path.join(BASE_DIR, "ad_signal_brand.json")
COMPETITORS_FILE = os.path.join(BASE_DIR, "ad_signal_competitors.json")
PROFILES_FILE = os.path.join(BASE_DIR, "ad_signal_profiles.json")
SELECTORS_FILE = os.path.join(BASE_DIR, "ad_signal_selectors.json")

# ------------------------------------------------------------------
# [중요] 메타 광고 라이브러리 크롤링용 CSS 선택자 설정
# ------------------------------------------------------------------
# 메타가 페이지의 클래스명(예: _7j6g)을 자주 바꾸기 때문에, 이 부분이
# 크롤링 코드에서 "가장 먼저 깨지는" 지점입니다. 그래서 코드 로직과
# 분리해서 JSON 파일(ad_signal_selectors.json)로 따로 관리합니다.
#
# ▶ 실제 크롤링이 0건이 나오기 시작하면:
#   1) 앱 사이드바 하단 "⚙️ 크롤링 선택자 설정" 패널을 열고
#   2) 크롬 개발자도구(F12)로 광고 카드 div의 새 class를 확인한 뒤
#   3) 후보 목록 맨 위에 새 선택자를 추가하고 저장하면 끝.
#   코드를 다시 배포할 필요 없이 즉시 반영됩니다.
DEFAULT_SELECTORS = {
    # 광고 카드(하나의 광고 단위)를 감싸는 컨테이너 후보들.
    # 위에서부터 순서대로 시도하고, 실제로 요소가 1개 이상 잡히는
    # 첫 번째 선택자를 사용합니다. 새 구조를 발견하면 맨 앞에 추가하세요.
    "ad_card_candidates": [
        'div[class*="_7jyg"]',
        'div[class*="_7j6g"]',
        'div[role="article"]',
        'div[data-testid="ad_library_card"]',
    ],
    # 이미지 URL이 이 키워드 중 하나를 포함해야 "광고 소재 이미지"로 인정
    # (프로필 아이콘, UI 스프라이트 등 잡음 제거용). 메타 CDN이 바뀌면 여기에 추가.
    "image_domain_keywords": ["scontent", "fbcdn"],
    # 이보다 작은 이미지는 아이콘/썸네일로 보고 제외 (px)
    "image_min_width": 100,
    # 스크롤 반복 최대 횟수 / 1회당 대기 시간(ms)
    "max_scroll_count": 8,
    "scroll_wait_ms": 2000,
    # 최초 카드 로딩 대기 타임아웃(ms)
    "initial_wait_timeout_ms": 15000,
}


def load_selectors():
    """선택자 설정을 파일에서 불러오되, 없으면 기본값으로 생성."""
    data = load_json(SELECTORS_FILE, None)
    if data is None:
        data = json.loads(json.dumps(DEFAULT_SELECTORS))  # deep copy
        save_json(SELECTORS_FILE, data)
        return data
    # 과거 버전 파일에 새 필드가 없을 수 있으니 기본값으로 보강
    merged = dict(DEFAULT_SELECTORS)
    merged.update(data)
    return merged


def save_selectors(data):
    save_json(SELECTORS_FILE, data)


def reset_selectors():
    data = json.loads(json.dumps(DEFAULT_SELECTORS))
    save_json(SELECTORS_FILE, data)
    return data


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
# [핵심] Playwright 봇 우회 + 선택자 설정(config) 기반 크롤링 함수
# ------------------------------------------------------------------
# 이미지/카드 추출 로직은 브라우저 안에서 JS(page.evaluate)로 한 번에 처리합니다.
# 이렇게 하면 (1) DOM을 한 번만 순회해서 빠르고, (2) 카드 선택자가
# 전부 실패하더라도 "이미지 CDN 도메인 키워드" 기준으로 body 전체를
# 스캔하는 최후의 fallback이 자동으로 동작합니다.
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
        } catch (e) { /* 잘못된 선택자는 건너뜀 */ }
    }

    // 후보 선택자가 전부 실패하면 문서 전체를 하나의 "카드"로 취급 (fallback)
    const scope = cards.length ? cards : [document.body];
    if (!cards.length) usedSelector = 'FALLBACK: document.body (카드 선택자 전부 불일치)';

    const seen = new Set();
    const items = [];

    scope.forEach((card) => {
        const imgs = card.querySelectorAll('img');
        imgs.forEach((img) => {
            const src = img.currentSrc || img.src || '';
            if (!src || seen.has(src)) return;

            // 메타는 이미지를 지연 로딩(lazy load)하기 때문에, 아직 로드되지 않은
            // 이미지는 naturalWidth가 0으로 나올 수 있음. 이 경우 "크기 미상"으로
            // 보고 걸러내지 않는다 (0을 작은 이미지로 오판하지 않도록 방지).
            let renderedWidth = img.naturalWidth || 0;
            if (!renderedWidth) {
                try { renderedWidth = Math.round(img.getBoundingClientRect().width) || 0; } catch (e) {}
            }
            if (!renderedWidth) renderedWidth = img.width || 0;
            if (renderedWidth > 0 && renderedWidth < image_min_width) return;

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
    """
    메타 CDN 이미지 URL에 포함된 리사이즈 파라미터(예: s600x600)를
    한 단계 더 큰 값으로 바꿔서 조금 더 선명한 이미지를 받아온다.
    파라미터가 없으면 원본 URL을 그대로 반환.
    """
    if not url:
        return url
    try:
        # stp=dst-jpg_s600x600_tt6 형태의 sWIDTHxHEIGHT 부분을 찾아 소폭(약 1.6배) 확대
        def _bump(match):
            w, h = int(match.group(1)), int(match.group(2))
            new_w = min(int(w * 1.6), 1080)
            new_h = min(int(h * 1.6), 1080)
            return f"s{new_w}x{new_h}"

        upgraded = re.sub(r"s(\d{2,4})x(\d{2,4})", _bump, url)
        return upgraded
    except Exception:
        return url


def _scrape_once(library_url, max_items, cfg):
    """한 번의 Playwright 세션으로 스크래핑을 시도. 실패 시 예외를 그대로 던짐."""
    results = []
    debug_info = {"used_selector": None, "card_count": 0}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--no-zygote",
            ]
        )

        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="ko-KR"
            )

            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            # 메모리 절약: 광고 소재 이미지 외에 폰트/동영상 등 무거운 리소스는 차단
            # (크래시로 인한 'Target page ... has been closed' 오류를 줄이기 위함)
            def _block_heavy_resources(route):
                if route.request.resource_type in ("media", "font"):
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", _block_heavy_resources)

            try:
                page.goto(library_url, timeout=45000, wait_until="domcontentloaded")
            except Exception as e:
                raise RuntimeError(f"페이지 접속 실패 (goto): {e}")

            # 봇 탐지 회피를 위한 안전 딜레이
            time.sleep(5)

            if page.is_closed():
                raise RuntimeError("페이지 로딩 중 브라우저가 예기치 않게 종료되었습니다.")

            # 카드 후보 선택자 중 아무거나 하나라도 뜰 때까지 대기 (전부 실패해도 계속 진행)
            try:
                combined_selector = ", ".join(cfg["ad_card_candidates"])
                page.wait_for_selector(combined_selector, timeout=cfg.get("initial_wait_timeout_ms", 15000))
            except Exception:
                pass

            # 스크롤하며 동적 로딩 유도 — 높이가 더 이상 늘어나지 않으면 조기 종료
            last_height = 0
            for _ in range(cfg.get("max_scroll_count", 8)):
                if page.is_closed():
                    raise RuntimeError("스크롤 중 브라우저가 예기치 않게 종료되었습니다. (메모리 부족 가능성)")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(cfg.get("scroll_wait_ms", 2000) / 1000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            if page.is_closed():
                raise RuntimeError("소재 추출 직전 브라우저가 예기치 않게 종료되었습니다. (메모리 부족 가능성)")

            # 스크롤 직후 지연 로딩된 이미지들이 실제로 로드될 시간을 살짝 더 준다
            time.sleep(1.5)

            extracted = page.evaluate(_EXTRACT_ADS_JS, cfg)
            debug_info["used_selector"] = extracted.get("usedSelector")
            debug_info["card_count"] = extracted.get("cardCount", 0)

            for idx, item in enumerate(extracted.get("items", [])[:max_items], start=1):
                img_url = item.get("src")
                body_text = item.get("bodyText", "")
                img_bytes = None
                if img_url:
                    hi_res_url = _upgrade_image_resolution(img_url)
                    for candidate_url in [hi_res_url, img_url]:
                        try:
                            img_resp = requests.get(candidate_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                            if img_resp.status_code == 200:
                                img_bytes = img_resp.content
                                break
                        except Exception:
                            continue

                results.append({
                    "id": f"pw_{idx}_{time.time()}",
                    "fn": f"ad_{idx}.png",
                    "bytes": img_bytes,
                    "body": body_text,
                    "snapshot_url": library_url,
                })
        finally:
            try:
                browser.close()
            except Exception:
                pass

    return results, debug_info


def scrape_meta_ads_with_playwright(library_url, max_items=12, selectors=None, _retry=True):
    """
    메타 광고 라이브러리에서 이미지 소재를 자동 수집합니다.

    Returns:
        results: [{id, fn, bytes, body, snapshot_url}, ...]
        debug_info: {"used_selector": str, "card_count": int} — 선택자가
            깨졌는지 판단할 때 UI에서 보여주는 정보
        error: 에러 메시지 (없으면 None)
    """
    cfg = selectors or load_selectors()

    try:
        results, debug_info = _scrape_once(library_url, max_items, cfg)
        return results, debug_info, None
    except Exception as e:
        err_text = str(e)
        is_crash = (
            "has been closed" in err_text
            or "Target closed" in err_text
            or "Browser closed" in err_text
            or "예기치 않게 종료" in err_text
        )
        # 브라우저 크래시로 추정되는 경우 1회만 자동 재시도 (일시적 리소스 이슈일 수 있음)
        if is_crash and _retry:
            time.sleep(2)
            return scrape_meta_ads_with_playwright(library_url, max_items, cfg, _retry=False)

        if is_crash:
            friendly = (
                "스크레이핑 중 브라우저가 예기치 않게 종료되었습니다 (재시도도 실패). "
                "주로 (1) 배포 환경에 Playwright 시스템 라이브러리(packages.txt)가 없거나, "
                "(2) 메모리 부족일 때 발생합니다. 원본 오류: " + err_text
            )
            return [], {"used_selector": None, "card_count": 0}, friendly

        return [], {"used_selector": None, "card_count": 0}, f"스크레이핑 중 오류 발생: {err_text}"


def create_image_grid_collage(images_bytes_list, cols=4, thumb_size=(180, 180)):
    try:
        pil_images = []
        for b in images_bytes_list[:12]:
            if not b:
                continue
            try:
                img = Image.open(io.BytesIO(b)).convert("RGB")
                img.thumbnail(thumb_size)
                pil_images.append(img)
            except Exception:
                pass

        if not pil_images:
            return None

        num_imgs = len(pil_images)
        rows = (num_imgs + cols - 1) // cols
        grid_w = cols * thumb_size[0]
        grid_h = rows * thumb_size[1]

        collage = Image.new("RGB", (grid_w, grid_h), (255, 255, 255))

        for idx, img in enumerate(pil_images):
            r = idx // cols
            c = idx % cols
            collage.paste(img, (c * thumb_size[0], r * thumb_size[1]))

        buf = io.BytesIO()
        collage.save(buf, format="JPEG", quality=65)
        return buf.getvalue()
    except Exception:
        return None


BRAND_INTEGRATED_ANALYSIS_PROMPT = """당신은 수석 퍼포먼스 마케팅 크리에이티브 분석가입니다.
제시된 브랜드 '{brand_name}'이 메타 라이브러리에서 현재 동시 운영 중인 전체 광고 소재 그리드 이미지를 통째로 조망하고 객관적인 브랜드 통합 분석을 진행해 주세요.

아래 작성 형식에 맞춰 한국어로 정확히 분석 리포트를 작성해 주세요. 평점은 1~5 사이 숫자만 적어주세요.

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


def parse_integrated_report(text):
    return parse_labeled_text(text, _SCORE_LABEL_TO_KEY, _SCORE_EMPTY)


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
        html += (
            f'<div class="score-card"><div class="score-cat">{label}</div>'
            f'<div class="score-stars">{stars(score)}</div>'
            f'<div class="score-desc">{desc}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def run_unified_ai_prompt(ai_provider, api_key, prompt_text, collage_bytes=None):
    if ai_provider == "Gemini (Google)":
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        contents = [prompt_text]
        if collage_bytes:
            img = Image.open(io.BytesIO(collage_bytes))
            contents.append(img)
            
        resp = model.generate_content(contents)
        return resp.text

    elif ai_provider == "ChatGPT (OpenAI)":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        content_payload = [{"type": "text", "text": prompt_text}]
        if collage_bytes:
            b64_img = base64.b64encode(collage_bytes).decode("utf-8")
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content_payload}]
        )
        return resp.choices[0].message.content

    elif ai_provider == "Claude (Anthropic)":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        content_payload = []
        if collage_bytes:
            b64_img = base64.b64encode(collage_bytes).decode("utf-8")
            content_payload.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64_img
                }
            })
        content_payload.append({"type": "text", "text": prompt_text})
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": content_payload}]
        )
        return resp.content[0].text


def run_brand_integrated_analysis(ai_provider, api_key, brand_name, images_bytes_list):
    collage_bytes = create_image_grid_collage(images_bytes_list)
    prompt = BRAND_INTEGRATED_ANALYSIS_PROMPT.format(brand_name=brand_name)
    raw_text = run_unified_ai_prompt(ai_provider, api_key, prompt, collage_bytes)
    return parse_integrated_report(raw_text)


# ------------------------------------------------------------------
# [소재 수집 UI]
# ------------------------------------------------------------------
def render_material_section(prefix, selected_comp, default_url, on_complete):
    tab1, tab2 = st.tabs(["🚀 자동 크롤링 수집", "📁 예비 업로드"])
    
    sess_key = f"{prefix}_items_{selected_comp}"
    if sess_key not in st.session_state:
        st.session_state[sess_key] = []

    with tab1:
        meta_url = st.text_input(
            "메타 광고 라이브러리 페이지 URL",
            value=default_url,
            key=f"{prefix}_meta_url_input_{selected_comp}"
        )

        if st.button("🚀 전체 라이브 소재 자동 수집 실행", key=f"{prefix}_crawl_btn", type="primary"):
            if not meta_url.strip():
                st.warning("메타 라이브러리 URL을 입력해주세요.")
            else:
                with st.spinner(""):
                    ads, debug_info, err = scrape_meta_ads_with_playwright(
                        meta_url.strip(), max_items=12, selectors=load_selectors()
                    )

                    if err:
                        st.error(err)

                    used_selector = (debug_info or {}).get("used_selector") or "-"
                    card_count = (debug_info or {}).get("card_count", 0)
                    is_fallback = isinstance(used_selector, str) and used_selector.startswith("FALLBACK")

                    if not ads:
                        st.info(f"⚠️ [{selected_comp}] 활성 광고를 수집하지 못했습니다. [예비 업로드] 탭을 활용해 주세요.")
                        st.session_state[sess_key] = []
                    else:
                        st.session_state[sess_key] = ads
                        with_image = [it for it in ads if it["bytes"]]
                        st.success(f"[{selected_comp}] 총 {len(ads)}건 수집 완료 (이미지 확보 {len(with_image)}건)")

                    # 디버그 정보(사용된 선택자, 인식 카드 수)는 화면에 바로 노출하지 않고
                    # 필요할 때만 펼쳐볼 수 있도록 접힌 expander 안에 넣어둔다.
                    if not err:
                        with st.expander("🔍 수집 세부 정보 (문제 발생 시에만 확인)", expanded=False):
                            if is_fallback or card_count == 0:
                                st.caption(
                                    f"광고 카드 선택자가 매칭되지 않아 전체 페이지 스캔으로 수집했습니다 "
                                    f"(사용된 선택자: `{used_selector}`). 결과가 부정확하면 사이드바의 "
                                    "'⚙️ 크롤링 선택자 설정'에서 새 선택자를 추가해 보세요."
                                )
                            else:
                                st.caption(f"사용된 카드 선택자: `{used_selector}` · 인식된 카드 수: {card_count}개")

    with tab2:
        uploaded_files = st.file_uploader(
            "광고 이미지 업로드 (자동 수집 보완용)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"{prefix}_uploader_{selected_comp}",
        )
        if uploaded_files:
            new_items = []
            for idx, f in enumerate(uploaded_files, start=1):
                f.seek(0)
                b = f.read()
                new_items.append({
                    "id": f"upload_{idx}_{len(b)}",
                    "fn": f.name,
                    "bytes": b
                })
            st.session_state[sess_key] = new_items

    items = st.session_state[sess_key]
    
    if items:
        st.divider()
        st.markdown(f"**수집된 소재 ({len(items)}건) — 타겟 연령대가 다른 소재는 ❌ 삭제하세요**")

        cols_per_row = 6
        items_to_remove = []
        
        for i in range(0, len(items), cols_per_row):
            row_items = items[i:i + cols_per_row]
            grid_cols = st.columns(cols_per_row)
            
            for idx, item in enumerate(row_items):
                with grid_cols[idx]:
                    if item.get("bytes"):
                        st.image(item["bytes"], width=110)
                    else:
                        st.caption("🖼️ 실패")
                        if item.get("body"):
                            st.caption(item["body"][:40])
                    del_col1, del_col2 = st.columns([3, 1])
                    with del_col1:
                        st.caption(f"#{i+idx+1}")
                    with del_col2:
                        if st.button("❌", key=f"del_{item['id']}_{selected_comp}"):
                            items_to_remove.append(item['id'])

        if items_to_remove:
            st.session_state[sess_key] = [it for it in st.session_state[sess_key] if it['id'] not in items_to_remove]
            st.rerun()

        st.divider()
        if st.button(f"'{selected_comp}' 전체 브랜드 통합 분석 실행", type="primary", key=f"{prefix}_analyze_btn_{selected_comp}"):
            if not st.session_state.get("current_api_key"):
                st.error("상단에서 AI API Key를 입력해 주세요.")
            else:
                current_items = st.session_state[sess_key]
                if not current_items:
                    st.warning("분석할 소재가 없습니다. 먼저 수집해 주세요.")
                else:
                    with st.spinner(f"[{st.session_state['current_ai_provider']}] '{selected_comp}' 브랜드 소재 통째 캡처 통합 분석 중..."):
                        raw_bytes_list = [it["bytes"] for it in current_items if it.get("bytes")]

                        if not raw_bytes_list:
                            st.warning("분석 가능한 이미지가 없습니다. [예비 업로드] 탭에서 이미지를 추가해주세요.")
                        else:
                            try:
                                report = run_brand_integrated_analysis(
                                    st.session_state['current_ai_provider'],
                                    st.session_state['current_api_key'],
                                    selected_comp,
                                    raw_bytes_list
                                )
                                on_complete({
                                    "brand_name": selected_comp,
                                    "count": len(current_items),
                                    "report": report
                                })
                            except Exception as e:
                                st.error(f"통합 분석 중 오류 발생: {e}")


# ------------------------------------------------------------------
# 상단 헤더 & 멀티 AI 엔진 선택 영역
# ------------------------------------------------------------------
top_col1, top_col2, top_col3 = st.columns([2.5, 1.2, 1.5])
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
    ai_provider = st.selectbox(
        "AI 엔진 선택",
        ["Gemini (Google)", "ChatGPT (OpenAI)", "Claude (Anthropic)"],
        key="selected_ai_provider"
    )
    st.session_state["current_ai_provider"] = ai_provider

with top_col3:
    default_key = ""
    try:
        if ai_provider == "Gemini (Google)" and "GEMINI_API_KEY" in st.secrets:
            default_key = st.secrets["GEMINI_API_KEY"]
        elif ai_provider == "ChatGPT (OpenAI)" and "OPENAI_API_KEY" in st.secrets:
            default_key = st.secrets["OPENAI_API_KEY"]
        elif ai_provider == "Claude (Anthropic)" and "ANTHROPIC_API_KEY" in st.secrets:
            default_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

    placeholder_text = {
        "Gemini (Google)": "Gemini API 키 (AIzaSy...)",
        "ChatGPT (OpenAI)": "OpenAI API 키 (sk-proj-...)",
        "Claude (Anthropic)": "Claude API 키 (sk-ant-...)"
    }[ai_provider]

    input_api_key = st.text_input(
        f"{ai_provider} API Key",
        value=default_key,
        type="password",
        placeholder=placeholder_text,
        key="main_ai_api_key_input"
    )
    st.session_state["current_api_key"] = input_api_key

st.divider()

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

    st.divider()
    with st.expander("⚙️ 크롤링 선택자 설정 (고급)"):
        st.caption(
            "메타가 페이지 구조를 바꿔서 소재 수집이 0건이 되면, "
            "코드를 고치지 않고 여기서 선택자만 추가/수정하면 됩니다."
        )
        cur = load_selectors()

        cards_text = st.text_area(
            "광고 카드 선택자 후보 (한 줄에 하나씩, 위에서부터 순서대로 시도)",
            value="\n".join(cur["ad_card_candidates"]),
            height=110,
            key="sel_cards_text",
            help="예: div[class*=\"_7jyg\"]  ← F12로 카드를 감싸는 div의 class를 확인해 추가하세요.",
        )
        domain_text = st.text_input(
            "이미지 CDN 도메인 키워드 (쉼표로 구분)",
            value=", ".join(cur["image_domain_keywords"]),
            key="sel_domain_text",
        )
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            min_width = st.number_input(
                "최소 이미지 너비(px)", min_value=0, max_value=2000,
                value=int(cur.get("image_min_width", 100)), step=10, key="sel_min_width",
            )
            scroll_count = st.number_input(
                "최대 스크롤 횟수", min_value=1, max_value=30,
                value=int(cur.get("max_scroll_count", 8)), step=1, key="sel_scroll_count",
            )
        with col_s2:
            scroll_wait = st.number_input(
                "스크롤 대기(ms)", min_value=200, max_value=10000,
                value=int(cur.get("scroll_wait_ms", 2000)), step=100, key="sel_scroll_wait",
            )
            init_wait = st.number_input(
                "최초 로딩 대기(ms)", min_value=1000, max_value=60000,
                value=int(cur.get("initial_wait_timeout_ms", 15000)), step=1000, key="sel_init_wait",
            )

        btn_save, btn_reset = st.columns(2)
        with btn_save:
            if st.button("저장", key="sel_save_btn", use_container_width=True):
                new_cfg = {
                    "ad_card_candidates": [s.strip() for s in cards_text.splitlines() if s.strip()],
                    "image_domain_keywords": [s.strip() for s in domain_text.split(",") if s.strip()],
                    "image_min_width": int(min_width),
                    "max_scroll_count": int(scroll_count),
                    "scroll_wait_ms": int(scroll_wait),
                    "initial_wait_timeout_ms": int(init_wait),
                }
                save_selectors(new_cfg)
                st.success("선택자 설정이 저장되었습니다. 다음 수집부터 바로 적용됩니다.")
        with btn_reset:
            if st.button("기본값 복원", key="sel_reset_btn", use_container_width=True):
                reset_selectors()
                st.success("기본 선택자로 복원되었습니다.")
                st.rerun()

if "work" not in st.session_state: st.session_state.work = {}
if segment not in st.session_state.work:
    st.session_state.work[segment] = {
        "own_analyses": None, "insight": "", "gap_analysis": "", "ideas": "",
        "last_comp_result": None, "last_competitor": "",
    }
W = st.session_state.work[segment]

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
            new_comp = st.text_input("경쟁사명", key=f"{segment}_new_comp_input")
            if st.button("추가", key=f"{segment}_new_comp_btn", use_container_width=True):
                if new_comp.strip():
                    add_competitor(segment, new_comp.strip())
                    st.success(f"'{new_comp.strip()}' 추가되었습니다.")
                    st.rerun()

    auto_url = META_URL_MAP.get(selected_competitor, "")

    def _on_comp_complete(res):
        W["last_comp_result"] = res
        W["last_competitor"] = selected_competitor
        save_profile_entry(segment, selected_competitor, {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "count": res["count"],
            "report": res["report"],
        })
        st.success(f"'{selected_competitor}' 전체 브랜드 통합 분석 완료 ➔ 02 탭 프로필에 저장되었습니다!")

    render_material_section("comp", selected_competitor, auto_url, _on_comp_complete)

    if W["last_comp_result"] and W["last_competitor"] == selected_competitor:
        st.divider()
        st.markdown(f"### '{W['last_competitor']}' 브랜드 전체 크리에이티브 통합 분석 리포트")
        render_integrated_scorecard(W["last_comp_result"]["report"])

# ------------------------------------------------------------------
# 02 · 경쟁사 프로필
# ------------------------------------------------------------------
elif nav == "02 · 경쟁사 프로필":
    section_header("02", f"{segment} 경쟁사 프로필", "01 탭에서 분석한 브랜드별 통합 크리에이티브 리포트가 누적됩니다.")

    profiles = load_all_profiles().get(segment, {})
    competitors = load_competitors()[segment]

    if not any(profiles.get(c) for c in competitors):
        st.info("아직 분석된 경쟁사 리포트가 없어요. 01 탭에서 브랜드 분석을 실행해 주세요.")
    else:
        for comp in competitors:
            entries = profiles.get(comp, [])
            if not entries: continue

            latest = entries[0]
            rep = latest.get("report", {})
            st.markdown(
                f'<div class="comp-card"><div class="comp-name">{comp}</div>'
                f'<div class="comp-meta">누적 분석 {len(entries)}회 · 최근 수집 소재 {latest.get("count", 0)}건 · '
                f'메시지 {stars(rep.get("msg_score", 0))} · '
                f'비주얼 {stars(rep.get("vis_score", 0))} · '
                f'종합 {stars(rep.get("overall_score", 0))}</div></div>',
                unsafe_allow_html=True,
            )
            with st.expander(f"{comp} — 최신 통합 분석 리포트 세부보기 ({latest.get('timestamp', '')})"):
                render_integrated_scorecard(rep)
                st.divider()

# ------------------------------------------------------------------
# 03 · 자사 소재 분석
# ------------------------------------------------------------------
elif nav == "03 · 자사 소재 분석":
    section_header("03", f"{segment} 자사 광고 소재 분석", f"{segment} 자사 브랜드의 메타 광고 라이브러리 URL이 자동 세팅됩니다.")

    own_auto_url = OWN_META_URL_MAP.get(segment, "")

    def _on_own_complete(res):
        W["own_analyses"] = res
        st.success("자사 브랜드 통합 소재 분석 완료! 04 탭에서 경쟁사와 비교할 수 있습니다.")

    render_material_section("own", f"자사({segment})", own_auto_url, _on_own_complete)

    if W["own_analyses"]:
        st.divider()
        st.markdown(f"**자사({segment}) 브랜드 통합 분석 리포트**")
        render_integrated_scorecard(W["own_analyses"]["report"])

# ------------------------------------------------------------------
# 04 · 메시지 갭 분석 & 위닝 포인트
# ------------------------------------------------------------------
elif nav == "04 · 메시지 갭 분석":
    section_header("04", f"{segment} 메시지 갭 분석 & 위닝 포인트", "경쟁사 누적 프로필과 자사 브랜드 리포트를 비교해 부족한 메시지를 도출합니다.")

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
                with st.spinner(f"[{st.session_state['current_ai_provider']}] 인사이트 도출 중..."):
                    try:
                        resp_text = run_unified_ai_prompt(
                            st.session_state["current_ai_provider"],
                            st.session_state["current_api_key"],
                            INSIGHT_PROMPT.format(comp_summary=comp_summary)
                        )
                        W["insight"] = resp_text
                    except Exception as e: st.error(f"오류 발생: {e}")

        if W["insight"]: st.markdown(W["insight"])

        st.divider()
        st.markdown("**우리 소재와 비교해서 부족한 메시지 찾기**")

        if not W["own_analyses"]:
            st.info("03 탭에서 자사 소재 분석을 완료하면, 경쟁사 대비 부족한 메시지를 비교해드려요.")
        else:
            if st.button("메시지 갭 분석 실행", type="primary", key="gap_btn"):
                if not st.session_state.get("current_api_key"):
                    st.error("상단에서 API Key를 입력해 주세요.")
                else:
                    comp_summary = ""
                    for comp, e in all_comp_entries:
                        rep = e.get("report", {})
                        comp_summary += f"[{comp}] {rep.get('msg_good','')}\n"
                    
                    own_rep = W["own_analyses"].get("report", {})
                    own_summary = f"[자사] 메시지장점: {own_rep.get('msg_good','')}\n아쉬운점: {own_rep.get('msg_bad','')}"

                    GAP_PROMPT = """당신은 브랜드 전략 컨설턴트입니다. 아래는 경쟁사 그룹과 자사 브랜드 분석 정보입니다.
두 그룹을 비교해서 아래 내용을 정리해주세요.

[경쟁사 그룹 요약]
{comp_summary}

[자사 브랜드 요약]
{own_summary}

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
                    with st.spinner(f"[{st.session_state['current_ai_provider']}] 갭 분석 중..."):
                        try:
                            resp_text = run_unified_ai_prompt(
                                st.session_state["current_ai_provider"],
                                st.session_state["current_api_key"],
                                GAP_PROMPT.format(comp_summary=comp_summary, own_summary=own_summary)
                            )
                            W["gap_analysis"] = resp_text
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
                with st.spinner(f"[{st.session_state['current_ai_provider']}] 스토리보드 기획안 작성 중..."):
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

# 06 · 히스토리
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
                    f'<div class="history-meta">분석 경쟁사 {entry.get("material_count", 0)}개 · '
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
