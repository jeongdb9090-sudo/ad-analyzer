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
# 기본 설정 및 디자인 CSS (어두운 배경 컬러 #191B29 원천 차단 및 백색 고정)
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

/* [핵심 수정] 셀렉트박스, 인풋 필드, 팝오버, 드롭다운 전체에 걸쳐 어두운 배경(#191B29 등)을 백색으로 완전 교체 및 강제 */
div[data-baseweb="select"] > div,
div[data-baseweb="base-input"] > input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
div[data-baseweb="popover"],
div[data-testid="stPopoverBody"],
div[data-baseweb="menu"],
div[data-baseweb="tag"] {
    background-color: #FFFFFF !important;
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
    "웅진ส마트올 중학": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id=103396781600446",
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

def load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as fp: return json.load(fp)
    except Exception: return default

def save_json(path, data):
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


# ------------------------------------------------------------------
# Playwright 크롤링 함수 (프로필 아이콘 정밀 필터링 로직 포함)
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
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        contents = [prompt_text]
        if collage_bytes: contents.append(Image.open(io.BytesIO(collage_bytes)))
        return model.generate_content(contents).text
    elif ai_provider == "ChatGPT (OpenAI)":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        content_payload = [{"type": "text", "text": prompt_text}]
        if collage_bytes:
            content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(collage_bytes).decode('utf-8')}"}})
        return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": content_payload}]).choices[0].message.content
    elif ai_provider == "Claude (Anthropic)":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        content_payload = []
        if collage_bytes:
            content_payload.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(collage_bytes).decode('utf-8')}})
        content_payload.append({"type": "text", "text": prompt_text})
        return client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=2000, messages=[{"role": "user", "content": content_payload}]).content[0].text

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
                        st.error(f"오류 발생: {e}")


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
NAV_ITEMS = ["01 · 경쟁사 소재 분석", "02 · 경쟁사 프로필", "03 · 자사 소재 분석", "04 · 메시지 갭 분석", "05 · 스토리보드 아이디어", "06 · 히스토리"]

with st.sidebar:
    st.markdown('<div class="eyebrow">SEGMENT</div>', unsafe_allow_html=True)
    segment = st.radio("사업 구분", SEGMENTS, label_visibility="collapsed", key="segment_selector")
    st.divider()
    nav = st.radio("메뉴", NAV_ITEMS, label_visibility="collapsed", key="nav_selector")

if "work" not in st.session_state: st.session_state.work = {}
if segment not in st.session_state.work:
    st.session_state.work[segment] = {"own_analyses": None, "insight": "", "gap_analysis": "", "ideas": "", "last_comp_result": None, "last_competitor": ""}
W = st.session_state.work[segment]

# ------------------------------------------------------------------
# 01 · 경쟁사 소재 분석
# ------------------------------------------------------------------
if nav == "01 · 경쟁사 소재 분석":
    section_header("01", f"{segment} 경쟁사 광고 소재 분석", "경쟁사를 선택하면 해당 브랜드의 메타 광고 라이브러리 URL이 자동으로 세팅됩니다.")

    competitors = load_competitors()[segment]
    
    comp_col, add_col, del_col = st.columns([3.5, 1.2, 1.2])
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
    with del_col:
        st.markdown('<div class="align-bottom-btn"></div>', unsafe_allow_html=True)
        with st.popover("❌ 경쟁사 삭제", use_container_width=True):
            st.markdown("##### 삭제할 경쟁사 선택")
            target_to_del = st.selectbox("삭제 대상", competitors, key=f"{segment}_del_select")
            if st.button("선택 경쟁사 삭제", key=f"{segment}_del_btn", use_container_width=True):
                if target_to_del in DEFAULT_COMPETITORS.get(segment, []):
                    st.warning("기본 제공 경쟁사는 삭제할 수 없습니다.")
                else:
                    remove_competitor(segment, target_to_del)
                    st.success(f"'{target_to_del}' 삭제 완료!")
                    time.sleep(0.5)
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
# 02 · 경쟁사 프로필
# ------------------------------------------------------------------
elif nav == "02 · 경쟁사 프로필":
    section_header("02", f"{segment} 경쟁사 프로필", "01 탭에서 분석한 브랜드별 통합 크리에이티브 리포트가 누적됩니다.")
    profiles = load_all_profiles().get(segment, {})
    competitors = load_competitors()[segment]
    for comp in competitors:
        entries = profiles.get(comp, [])
        if not entries: continue
        latest = entries[0]
        rep = latest.get("report", {})
        st.markdown(f'<div class="comp-card"><div class="comp-name">{comp}</div><div class="comp-meta">누적 분석 {len(entries)}회 · 최근 수집 소재 {latest.get("count", 0)}건</div></div>', unsafe_allow_html=True)
        with st.expander(f"{comp} 리포트 세부보기"):
            render_integrated_scorecard(rep)

# ------------------------------------------------------------------
# 03 · 자사 소재 분석
# ------------------------------------------------------------------
elif nav == "03 · 자사 소재 분석":
    section_header("03", f"{segment} 자사 광고 소재 분석")
    render_material_section("own", f"자사({segment})", OWN_META_URL_MAP.get(segment, ""), lambda res: W.update({"own_analyses": res}))

# ------------------------------------------------------------------
# 04 · 메시지 갭 분석
# ------------------------------------------------------------------
elif nav == "04 · 메시지 갭 분석":
    section_header("04", f"{segment} 메시지 갭 분석 & 위닝 포인트")
    if st.button("메시지 갭 분석 실행", type="primary"):
        W["gap_analysis"] = "갭 분석 완료 결과 예시"
    if W["gap_analysis"]: st.markdown(W["gap_analysis"])

# ------------------------------------------------------------------
# 05 · 스토리보드 아이디어
# ------------------------------------------------------------------
elif nav == "05 · 스토리보드 아이디어":
    section_header("05", f"{segment} 맞춤형 스토리보드 아이디어")
    brand_name = st.text_input("브랜드명", key=f"{segment}_bn")
    if st.button("아이디어 생성", type="primary"):
        W["ideas"] = "스토리보드 결과 예시"
    if W["ideas"]: st.markdown(W["ideas"])

# ------------------------------------------------------------------
# 06 · 히스토리
# ------------------------------------------------------------------
elif nav == "06 · 히스토리":
    section_header("06", "히스토리")
    for entry in load_history():
        st.markdown(f"**{entry.get('brand_name')}**")
