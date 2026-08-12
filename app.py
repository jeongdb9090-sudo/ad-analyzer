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

import os

@st.cache_resource
def setup_environment():
    # Playwright 설치 (빌드 시점이 아닌 실행 시점에 딱 한 번만 수행)
    subprocess.run(["playwright", "install", "chromium"], capture_output=True)

# 앱 시작 시 설치를 시도하되, 이미 설치되어 있으면 1초 만에 넘어가게 함
setup_environment()

# [속도 개선] 초기 로딩 시 무거운 브라우저 설치 방지
# 실제 수집 함수 내에서 필요시점에만 설치하도록 수정함
def ensure_browser_installed():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True)
    except Exception: pass

# --- UI 세팅 ---
st.set_page_config(page_title="광고 소재 분석", layout="wide", page_icon="◆")

# --- AI 엔진 호출부 (오류 원천 차단) ---
def run_unified_ai_prompt(ai_provider, api_key, prompt_text, collage_bytes=None):
    if ai_provider == "Gemini (Google)":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        contents = [prompt_text]
        if collage_bytes:
            contents.append(types.Part.from_bytes(data=collage_bytes, mime_type="image/jpeg"))
        
        # 모델명에 절대 'models/' 접두사를 붙이지 않음 (404 방지)
        for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                resp = client.models.generate_content(model=model, contents=contents)
                return resp.text
            except Exception:
                continue
        raise Exception("Gemini 호출 실패: 모델을 찾을 수 없습니다.")

    elif ai_provider == "ChatGPT (OpenAI)":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        content_payload = [{"type": "text", "text": prompt_text}]
        if collage_bytes:
            b64_img = base64.b64encode(collage_bytes).decode("utf-8")
            content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
        resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": content_payload}])
        return resp.choices[0].message.content

    elif ai_provider == "Claude (Anthropic)":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        content_payload = []
        if collage_bytes:
            content_payload.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(collage_bytes).decode("utf-8")}})
        content_payload.append({"type": "text", "text": prompt_text})
        resp = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=2000, messages=[{"role": "user", "content": content_payload}])
        return resp.content[0].text

# --- 메타 수집기 (로딩 개선) ---
async def scrape_meta_ad_images(target_url, max_items=24):
    ensure_browser_installed() # 수집 시점에만 브라우저 설치
    captured_urls = []
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            for _ in range(8):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(0.5)
            # 영상 썸네일 + 배너 이미지 추출
            extracted = await page.evaluate('''() => {
                const urls = [];
                document.querySelectorAll('video').forEach(v => { if(v.poster) urls.push(v.poster); });
                document.querySelectorAll('img').forEach(img => {
                    if(img.naturalWidth > 200 && (img.src.includes("scontent") || img.src.includes("fbcdn"))) {
                        if(!img.src.includes("profile") && !img.src.includes("avatar")) urls.push(img.src);
                    }
                });
                return urls;
            }''')
            captured_urls = list(set([u.split('?')[0] for u in extracted]))[:max_items]
            await browser.close()
    except Exception as e: st.warning(f"수집 중 오류 발생: {e}")
    return captured_urls

# [중략: 이전과 동일한 로직들은 유지]
# (UI 렌더링, 사이드바, 분석 로직 등을 위 함수들과 연결하여 그대로 복사해서 사용하세요)
