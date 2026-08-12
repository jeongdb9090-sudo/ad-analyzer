import base64
import io
import json
import os
import re
from datetime import datetime
import requests
import streamlit as st
from PIL import Image

# ------------------------------------------------------------------
# 설정: 구글 앱스크립트 배포 URL (여기에 본인의 배포 주소를 입력하세요)
# ------------------------------------------------------------------
GAS_WEB_APP_URL = "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"

# (기존 CSS 및 디자인 설정 코드는 동일하게 유지...)
# ... [중략: 기존 CSS, 헤더, star, load/save_json 등 모든 함수 포함] ...

# ------------------------------------------------------------------
# [통합] 메타 봇 방패를 뚫는 '초정밀 위장 파서' 수집기 (앱스크립트 연동형)
# ------------------------------------------------------------------
def scrape_meta_ad_images(target_url, max_items=24):
    captured_urls = []
    
    # 1. 앱스크립트 연동 시도 (시트 기반 데이터 수집)
    try:
        # target_url을 파라미터로 넘겨 시트 내 브랜드 매칭 데이터 호출
        resp = requests.get(f"{GAS_WEB_APP_URL}?brand={target_url}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                st.toast("구글 시트에서 데이터를 성공적으로 불러왔습니다.")
                return data[:max_items]
    except Exception as e:
        st.sidebar.warning("앱스크립트 연동 실패, 크롤러를 가동합니다.")

    # 2. 앱스크립트 데이터가 없을 경우 기존 크롤러 실행
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        session = requests.Session()
        resp = session.get(target_url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            html_content = resp.text
            # 정규표현식 파싱 로직
            pattern = r'https://[^\s<>"]+?\.(?:fbcdn\.net|scontent[^\s<>"]+?)\.(?:jpg|jpeg|png|webp)[^\s<>"]*?'
            found = re.findall(pattern, html_content)
            json_pattern = r'"url":"(https:[^"]+?\.(?:jpg|jpeg|png|webp)[^"]*?)"'
            found_json = re.findall(json_pattern, html_content)
            
            total_found = list(set(found + found_json))
            for u in total_found:
                try:
                    clean_u = u.encode().decode('unicode-escape').replace('\\', '')
                    base_u = clean_u.split('?')[0]
                    if not any(x in clean_u for x in ["profile", "avatar", "icon"]):
                        captured_urls.append(clean_u)
                except: continue
    except Exception as e:
        st.warning(f"메타 자동 수집 통신 참고: {e}")
        
    return captured_urls[:max_items]

# ------------------------------------------------------------------
# (이하 기존의 run_brand_integrated_analysis, render_material_section 등 동일하게 유지)
# ------------------------------------------------------------------

# 01번 탭 내부 render_material_section 실행 시 위 함수가 자동으로 호출됩니다.
# 버튼 클릭 시 위 scrape_meta_ad_images 함수가 GAS -> 크롤러 순서로 동작합니다.
