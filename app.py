import json
import os
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

# ------------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------------
st.set_page_config(page_title="Ad Signal — 경쟁사 광고 분석", layout="wide", page_icon="◆")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --ink: #191B29;
    --muted: #6B6E7D;
    --paper: #F7F7F5;
    --surface: #FFFFFF;
    --border: #E6E5E0;
    --primary: #2A2F6B;
    --primary-soft: #EEEFF7;
    --amber: #F5A623;
    --teal: #1F9D8C;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }

.appbar { display: flex; align-items: center; gap: 14px; padding: 18px 4px 22px 4px; border-bottom: 1px solid var(--border); margin-bottom: 28px; }
.appbar-mark { width: 34px; height: 34px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--teal)); flex-shrink: 0; }
.appbar-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 21px; line-height: 1.1; color: var(--ink); }
.appbar-sub { font-size: 13px; color: var(--muted); margin-top: 2px; }
.appbar-pill { margin-left: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--teal); background: #E9F7F5; border: 1px solid #CDEEE9; padding: 5px 10px; border-radius: 20px; white-space: nowrap; }

.eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.08em; color: var(--primary); background: var(--primary-soft); display: inline-block; padding: 3px 9px; border-radius: 4px; margin-bottom: 8px; }
.eyebrow.amber { color: #8A5A00; background: #FCEFD2; }
.section-title { font-size: 20px; font-weight: 700; margin: 0 0 4px 0; }
.section-desc { font-size: 13.5px; color: var(--muted); margin-bottom: 18px; }

[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
[data-testid="stSidebar"] .eyebrow { margin-top: 6px; }

.stButton > button { border-radius: 7px; font-weight: 600; border: 1px solid var(--border); }
.stButton > button[kind="primary"] { background: var(--primary); border: none; }
.stButton > button[kind="primary"]:hover { background: #21245A; }
.stDownloadButton > button { border-radius: 7px; font-weight: 600; }

.stTextInput input, .stTextArea textarea { border-radius: 7px !important; border-color: var(--border) !important; }

.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 13.5px; padding: 10px 14px; border-radius: 7px 7px 0 0; }
.stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom: 2px solid var(--primary) !important; }

[data-testid="stImage"] img { border-radius: 8px; border: 1px solid var(--border); }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 10px !important; border-color: var(--border) !important; background: var(--surface); }

[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 8px !important; background: var(--surface); }
[data-testid="stAlert"] { border-radius: 8px; }

.field-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.06em; color: var(--muted); margin: 6px 0 2px 0; text-transform: uppercase; }
.history-meta { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); }
</style>
""", unsafe_allow_html=True)


def section_header(step, title, desc="", amber=False):
    cls = "eyebrow amber" if amber else "eyebrow"
    st.markdown(f'<div class="{cls}">STEP {step}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if desc:
        st.markdown(f'<div class="section-desc">{desc}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------
# 로컬 저장 (히스토리 / 브랜드 정보)
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "ad_signal_history.json")
BRAND_FILE = os.path.join(BASE_DIR, "ad_signal_brand.json")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return default


def load_history():
    return load_json(HISTORY_FILE, [])


def save_history_entry(entry):
    history = load_history()
    history.insert(0, entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as fp:
        json.dump(history, fp, ensure_ascii=False, indent=2)


def load_brand():
    return load_json(BRAND_FILE, {})


def save_brand(data):
    with open(BRAND_FILE, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# 구조화된 카피 추출 (브랜드명 / 메인 메시지 / 썸네일 / CTA)
# ------------------------------------------------------------------
STRUCTURED_OCR_PROMPT = """이 광고 이미지를 보고 아래 4가지 항목을 정리해줘. 다른 설명 없이 정확히 아래 형식으로만 답해줘.
이미지에 해당 내용이 없으면 그 항목은 비워둬.

브랜드명: (이미지 안에 보이는 브랜드/제품명. 로고나 텍스트로 적힌 것만)
메인 메시지: (가장 크고 눈에 띄는 핵심 카피 문구. 실제 적힌 텍스트 그대로)
썸네일: (이미지의 비주얼을 아주 간단히, 한 줄로 요약. 자세한 묘사 말고 대략적인 느낌만 - 예: "운동하는 여성 이미지", "제품 클로즈업 사진")
CTA: (구매하기, 지금 다운로드 등 행동 유도 문구나 버튼 텍스트)"""

FIELD_LABELS = {"brand": "브랜드명", "message": "메인 메시지", "thumbnail": "썸네일", "cta": "CTA"}
FIELD_ORDER = ["brand", "message", "thumbnail", "cta"]
_LABEL_TO_KEY = {v: k for k, v in FIELD_LABELS.items()}


def parse_structured_copy(text):
    fields = {"brand": "", "message": "", "thumbnail": "", "cta": ""}
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched_key = None
        for label, key in _LABEL_TO_KEY.items():
            if line.startswith(label + ":") or line.startswith(label + " :"):
                fields[key] = line.split(":", 1)[1].strip() if ":" in line else ""
                current = key
                matched_key = key
                break
        if matched_key is None and current:
            fields[current] = (fields[current] + " " + line).strip()
    return fields


def structured_to_reference_text(fields):
    return "\n".join(f"{FIELD_LABELS[k]}: {fields.get(k, '') or '없음'}" for k in FIELD_ORDER)


ANALYSIS_PROMPT = """당신은 퍼포먼스 마케팅 및 광고 크리에이티브 전문가입니다.
첨부된 광고 소재 이미지와 구조화된 정보를 참고해서 분석해주세요. 아래 항목을 한국어로 간결하게 정리해주세요.

1. 후킹 포인트 (3초 시선 집중 요소)
2. 카피 스타일 및 톤앤매너
3. 비주얼 구성 (색감, 레이아웃, 인물/제품 배치)
4. 소구 심리 (가격, 사회적 증거, 공포/결핍, 자기효능감 등)
5. 예상 타겟층
6. CTA(행동유도) 방식

참고용 구조화 정보:
{copy_text}"""


def render_material_section(prefix, session_key, tone_note):
    """소재 업로드 -> 구조화 카피 자동추출 -> 분석 실행 UI. 반환값 없이 session_state에 결과 저장."""
    uploaded_files = st.file_uploader(
        "광고 이미지 업로드 (다중 선택 가능 / PNG, JPG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"{prefix}_uploader",
    )

    copy_refs = {}
    if uploaded_files:
        st.divider()
        st.markdown("**인식된 소재 정보 확인 · 수정**")
        st.caption("AI가 브랜드명 / 메인 메시지 / 썸네일 / CTA를 항목별로 자동 인식합니다. 틀린 부분은 직접 고쳐주세요.")

        for f in uploaded_files:
            file_key = f"{prefix}_{f.name}_{f.size}"

            if client and file_key not in st.session_state.structured_copy:
                f.seek(0)
                image_bytes = f.read()
                mime_type = "image/png" if f.name.lower().endswith("png") else "image/jpeg"
                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                try:
                    with st.spinner(f"'{f.name}' 인식 중..."):
                        ocr_resp = client.models.generate_content(
                            model=MODEL, contents=[image_part, STRUCTURED_OCR_PROMPT]
                        )
                    parsed = parse_structured_copy(ocr_resp.text)
                except Exception:
                    parsed = {"brand": "", "message": "", "thumbnail": "", "cta": ""}
                st.session_state.structured_copy[file_key] = parsed

            with st.container(border=True):
                card_cols = st.columns([1, 2])
                with card_cols[0]:
                    st.image(f, use_container_width=True)
                with card_cols[1]:
                    saved = st.session_state.structured_copy.get(
                        file_key, {"brand": "", "message": "", "thumbnail": "", "cta": ""}
                    )
                    field_values = {}
                    for fkey in FIELD_ORDER:
                        widget_key = f"{file_key}_{fkey}"
                        if widget_key not in st.session_state:
                            st.session_state[widget_key] = saved.get(fkey, "")
                        st.markdown(f'<div class="field-label">{FIELD_LABELS[fkey]}</div>', unsafe_allow_html=True)
                        if fkey in ("message", "thumbnail"):
                            field_values[fkey] = st.text_area(
                                FIELD_LABELS[fkey], key=widget_key, height=60, label_visibility="collapsed"
                            )
                        else:
                            field_values[fkey] = st.text_input(
                                FIELD_LABELS[fkey], key=widget_key, label_visibility="collapsed"
                            )
                    copy_refs[f.name] = structured_to_reference_text(field_values)

        if not client:
            st.info("Gemini API 키를 입력하면 정보가 자동으로 채워집니다.")

        st.divider()
        if st.button("소재 분석 실행", type="primary", key=f"{prefix}_analyze_btn"):
            if not client:
                st.error("Gemini API 키를 먼저 입력해주세요.")
            else:
                st.session_state[session_key] = []
                progress = st.progress(0, text="소재 분석 진행 중...")

                for idx, f in enumerate(uploaded_files):
                    f.seek(0)
                    image_bytes = f.read()
                    mime_type = "image/png" if f.name.lower().endswith("png") else "image/jpeg"
                    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                    ref_text = copy_refs.get(f.name, "")

                    try:
                        resp = client.models.generate_content(
                            model=MODEL,
                            contents=[image_part, ANALYSIS_PROMPT.format(copy_text=ref_text)],
                        )
                        analysis_text = resp.text
                    except Exception as e:
                        analysis_text = f"분석 오류: {e}"

                    st.session_state[session_key].append({
                        "name": f.name,
                        "copy_text": ref_text,
                        "analysis": analysis_text,
                    })
                    progress.progress((idx + 1) / len(uploaded_files), text=f"[{f.name}] 분석 완료")

                progress.empty()
                st.success(f"{tone_note} 분석이 완료되었습니다.")

    if st.session_state.get(session_key):
        st.divider()
        st.markdown("**개별 소재 분석 결과**")
        for item in st.session_state[session_key]:
            with st.expander(f"{item['name']}"):
                st.markdown(item["analysis"])


# ------------------------------------------------------------------
# 상단 앱바
# ------------------------------------------------------------------
st.markdown("""
<div class="appbar">
    <div class="appbar-mark"></div>
    <div>
        <div class="appbar-title">Ad Signal</div>
        <div class="appbar-sub">경쟁사 광고 소재 분석 · 위닝 아이디어 추출</div>
    </div>
    <div class="appbar-pill">FREE · GEMINI 3.1 FLASH-LITE</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 사이드바: API 연결
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="eyebrow">SETTINGS</div>', unsafe_allow_html=True)
    st.markdown("##### API 연결")

    default_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            default_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    input_api_key = st.text_input("Gemini API 키", value=default_key, type="password")
    st.caption("aistudio.google.com/apikey 에서 무료 발급 (입력 후 세션 유지)")

client = genai.Client(api_key=input_api_key) if input_api_key else None
MODEL = "gemini-3.1-flash-lite"

# ------------------------------------------------------------------
# 세션 상태 초기화
# ------------------------------------------------------------------
for _k, _v in [
    ("analyses", []), ("own_analyses", []), ("insight", ""), ("gap_analysis", ""),
    ("ideas", ""), ("structured_copy", {}),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ------------------------------------------------------------------
# 탭 구조
# ------------------------------------------------------------------
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "00 · 브랜드 설정",
    "01 · 경쟁사 소재 분석",
    "02 · 자사 소재 분석",
    "03 · 메시지 갭 분석",
    "04 · 스토리보드 아이디어",
    "05 · 히스토리",
])

# ------------------------------------------------------------------
# TAB 0: 자사 브랜드 & 디자인 메모리
# ------------------------------------------------------------------
with tab0:
    section_header(
        "00", "자사 브랜드 & 디자인 메모리",
        "여기 입력한 정보는 04 탭에서 스토리보드 아이디어를 만들 때 반영됩니다. '저장'을 누르면 이 컴퓨터에 보관되어, 앱을 다시 켜도 값이 남아있어요."
    )

    saved_brand = load_brand()
    for _key, _default in [
        ("brand_name", ""), ("brand_product", ""), ("brand_usp", ""),
        ("target_audience", ""), ("brand_design_memory", ""),
    ]:
        if _key not in st.session_state:
            st.session_state[_key] = saved_brand.get(_key, _default)

    col_a, col_b = st.columns(2)
    with col_a:
        brand_name = st.text_input("브랜드/제품명", key="brand_name", placeholder="예: 브랜드명 입력")
        brand_usp = st.text_area("핵심 셀링포인트 (USP)", key="brand_usp", placeholder="예: 우리 제품만의 차별점, 기능적 장점")
    with col_b:
        brand_product = st.text_area("제품/서비스 설명", key="brand_product", placeholder="예: 제공하는 제품이나 서비스 설명")
        target_audience = st.text_input("타겟 고객층", key="target_audience", placeholder="예: 25-35세 직장인 / 다이어터 등")

    st.divider()
    st.markdown("**디자인 톤앤매너 및 레퍼런스 메모리**")
    st.caption("AI가 기억할 디자인 가이드, 선호하는 카피 톤, 피해야 할 요소 등을 적어두세요.")
    brand_design_memory = st.text_area(
        "디자인 메모리", key="brand_design_memory",
        placeholder="예: 우리 브랜드는 핑크/화이트톤 중심의 깔끔하고 친근한 어투를 선호함. 너무 과격하거나 자극적인 공포 마케팅은 지양함.",
        height=120, label_visibility="collapsed",
    )

    save_col, status_col = st.columns([1, 3])
    with save_col:
        if st.button("저장", type="primary"):
            save_brand({
                "brand_name": brand_name, "brand_product": brand_product, "brand_usp": brand_usp,
                "target_audience": target_audience, "brand_design_memory": brand_design_memory,
            })
            st.session_state["_brand_saved"] = True
    with status_col:
        if st.session_state.get("_brand_saved"):
            st.caption("저장되었습니다. 다음에 앱을 다시 켜도 이 값이 그대로 불러와져요.")

# ------------------------------------------------------------------
# TAB 1: 경쟁사 소재 분석
# ------------------------------------------------------------------
with tab1:
    section_header(
        "01", "경쟁사 광고 소재 업로드 및 자동 분석",
        "메타 광고 라이브러리 등에서 캡처한 경쟁사 광고 이미지를 올려주세요."
    )
    render_material_section("comp", "analyses", "경쟁사 소재")

# ------------------------------------------------------------------
# TAB 2: 자사 소재 분석 (신규)
# ------------------------------------------------------------------
with tab2:
    section_header(
        "02", "자사 광고 소재 업로드 및 자동 분석",
        "지금 우리가 실제로 쓰고 있는 광고 소재를 올려주세요. 경쟁사 소재와 같은 방식으로 분석한 뒤, 03 탭에서 서로 비교합니다."
    )
    render_material_section("own", "own_analyses", "자사 소재")

# ------------------------------------------------------------------
# TAB 3: 메시지 갭 분석 & 위닝 포인트
# ------------------------------------------------------------------
with tab3:
    section_header(
        "03", "메시지 갭 분석 & 위닝 포인트",
        "경쟁사 소재의 공통 성공 패턴을 파악하고, 우리 소재와 비교해 부족한 메시지를 찾아냅니다."
    )

    if not st.session_state.analyses:
        st.info("먼저 01 탭에서 경쟁사 소재 분석을 완료해주세요.")
    else:
        if st.button("경쟁사 위닝 포인트 도출", type="primary", key="insight_btn"):
            combined_analyses = "\n\n---\n\n".join(
                f"[{a['name']}]\n{a['copy_text']}\n분석:\n{a['analysis']}" for a in st.session_state.analyses
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
                    resp = client.models.generate_content(
                        model=MODEL, contents=[INSIGHT_PROMPT.format(analyses=combined_analyses)]
                    )
                    st.session_state.insight = resp.text
                except Exception as e:
                    st.error(f"오류 발생: {e}")

        if st.session_state.insight:
            st.markdown(st.session_state.insight)

        st.divider()
        st.markdown("**우리 소재와 비교해서 부족한 메시지 찾기**")

        if not st.session_state.own_analyses:
            st.info("02 탭에서 자사 소재 분석을 완료하면, 경쟁사 대비 부족한 메시지를 비교해드려요.")
        else:
            if st.button("메시지 갭 분석 실행", type="primary", key="gap_btn"):
                comp_combined = "\n\n---\n\n".join(
                    f"[{a['name']}]\n{a['copy_text']}\n분석:\n{a['analysis']}" for a in st.session_state.analyses
                )
                own_combined = "\n\n---\n\n".join(
                    f"[{a['name']}]\n{a['copy_text']}\n분석:\n{a['analysis']}" for a in st.session_state.own_analyses
                )
                GAP_PROMPT = """당신은 브랜드 전략 컨설턴트입니다. 아래는 경쟁사 광고 소재 분석과, 우리 브랜드 자체 소재 분석입니다.
두 그룹을 비교해서 아래 내용을 정리해주세요.

[경쟁사 소재 분석]
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
                        resp = client.models.generate_content(
                            model=MODEL,
                            contents=[GAP_PROMPT.format(competitor=comp_combined, own=own_combined)],
                        )
                        st.session_state.gap_analysis = resp.text
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

            if st.session_state.gap_analysis:
                st.markdown(st.session_state.gap_analysis)

# ------------------------------------------------------------------
# TAB 4: 스토리보드 아이디어
# ------------------------------------------------------------------
with tab4:
    section_header(
        "04", "자사 맞춤형 스토리보드 아이디어",
        "00 탭의 브랜드 정보와 03 탭의 갭 분석을 바탕으로, 경쟁사 위닝 포인트를 우리 브랜드에 맞게 녹여낸 기획안을 제안합니다."
    )

    if not brand_name or not brand_product:
        st.warning("00 탭에서 '자사 브랜드명'과 '제품 설명'을 먼저 입력해 주세요.")
    elif not st.session_state.analyses:
        st.info("먼저 01 탭에서 경쟁사 소재 분석을 완료해 주세요.")
    else:
        if st.button("위닝 스토리보드 아이디어 생성", type="primary"):
            combined_analyses = "\n\n---\n\n".join(
                f"[{a['name']}]\n{a['analysis']}" for a in st.session_state.analyses
            )
            gap_context = st.session_state.gap_analysis or "없음 (아직 메시지 갭 분석을 실행하지 않음)"

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

각 아이디어는 아래 구조의 **스토리보드 형식**으로 구체적으로 작성해주세요. 가능하면 메시지 갭에서 지적된 부족한 부분을 최소 1개 이상 보완하는 방향으로 작성해주세요:
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
                    st.session_state.ideas = resp.text

                    save_history_entry({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "brand_name": brand_name,
                        "brand_product": brand_product,
                        "target_audience": target_audience,
                        "material_count": len(st.session_state.analyses),
                        "own_material_count": len(st.session_state.own_analyses),
                        "insight": st.session_state.insight,
                        "gap_analysis": st.session_state.gap_analysis,
                        "ideas": st.session_state.ideas,
                    })
                except Exception as e:
                    st.error(f"오류 발생: {e}")

        if st.session_state.ideas:
            st.markdown(st.session_state.ideas)
            st.divider()
            st.download_button(
                "광고 기획안 다운로드 (.md)",
                data=st.session_state.ideas,
                file_name="ad_winning_storyboards.md",
                mime="text/markdown",
            )

# ------------------------------------------------------------------
# TAB 5: 히스토리
# ------------------------------------------------------------------
with tab5:
    section_header(
        "05", "히스토리",
        "지금까지 완료한 아이디어 추출 결과가 자동으로 쌓입니다. 이 컴퓨터에 파일로 저장되어, 앱을 껐다 켜도 남아있습니다."
    )

    history = load_history()

    if not history:
        st.info("아직 완료된 결과가 없어요. 04 탭에서 아이디어를 생성하면 여기에 자동으로 기록됩니다.")
    else:
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.caption(f"총 {len(history)}건의 기록")
        with col_h2:
            if st.button("전체 기록 삭제"):
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                st.rerun()

        for i, entry in enumerate(history):
            title = f"{entry.get('brand_name', '(브랜드명 없음)')} · {entry.get('timestamp', '')}"
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
                    "이 결과 다운로드 (.md)",
                    data=entry.get("ideas", ""),
                    file_name=f"ad_ideas_{entry.get('timestamp', '').replace(':', '').replace(' ', '_')}.md",
                    mime="text/markdown",
                    key=f"history_dl_{i}",
                )
