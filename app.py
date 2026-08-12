# 1. 설치 함수를 호출하는 부분을 삭제하거나 주석 처리하세요.
# install_playwright_browsers() 

# 2. 대신, 수집 실행 함수 내부에서 브라우저가 없으면 그때 설치하게 합니다.
async def scrape_meta_ad_images(target_url, max_items=24):
    # 크롤링 시점에 설치 확인 (앱 로딩과는 무관해짐)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True)
    # ... 아래 기존 로직 그대로 유지



import asyncio
import base64
import io
import json
import os
import subprocess
import sys
from datetime import datetime
import requests
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ------------------------------------------------------------------
# 1. Playwright 자동 설치 (브라우저 수집용)
# ------------------------------------------------------------------
@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception: pass

install_playwright_browsers()

# ------------------------------------------------------------------
# 2. 디자인 CSS (톤앤매너 유지)
# ------------------------------------------------------------------
st.set_page_config(page_title="경쟁사 광고 소재 분석", layout="wide", page_icon="◆")
st.markdown("""
<style>
.stApp { background-color: #FAF9F5 !important; }
.score-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }
.score-card { border: 1px solid #E2E1D9; border-radius: 8px; padding: 12px 14px; background-color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# [데이터 로드/저장/매핑 로직은 이전과 동일하게 유지됩니다]
# ... (중간 생략: 이전 코드와 동일) ...

# ------------------------------------------------------------------
# 3. 통합 AI 호출 엔진 (에러 방지용 동적 모델 탐색 로직)
# ------------------------------------------------------------------
def run_unified_ai_prompt(ai_provider, api_key, prompt_text, collage_bytes=None):
    if ai_provider == "Gemini (Google)":
        from google import genai
        from google.genai import types
        # 1. 클라이언트 초기화
        client = genai.Client(api_key=api_key)
        
        contents = [prompt_text]
        if collage_bytes:
            contents.append(types.Part.from_bytes(data=collage_bytes, mime_type="image/jpeg"))

        # 2. 정식 모델명 호출 (최신 SDK 방식)
        # 404를 피하기 위해 명시적 경로 없이 호출
        try:
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=contents)
            return resp.text
        except Exception:
            # 실패 시 안전한 1.5-flash로 즉시 폴백
            resp = client.models.generate_content(model="gemini-1.5-flash", contents=contents)
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
        resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": content_payload}])
        return resp.choices[0].message.content

    elif ai_provider == "Claude (Anthropic)":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        content_payload = []
        if collage_bytes:
            content_payload.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(collage_bytes).decode("utf-8")}
            })
        content_payload.append({"type": "text", "text": prompt_text})
        resp = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=2000, messages=[{"role": "user", "content": content_payload}])
        return resp.content[0].text

# 나머지 UI 로직은 이전 코드와 동일하게 전체 복사해서 쓰시면 됩니다.
