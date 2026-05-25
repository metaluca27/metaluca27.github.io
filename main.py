# main.py
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
import build
import publish
from config import CONFIG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content", "posts")

def generate_seo_post(topic, model_type="ollama", model_name="llama3.1:latest", api_key=None):
    """Ollama 또는 Gemini API를 호출하여 SEO 최적화 포스팅 생성"""
    print(f"[*] AI 글쓰기 시작 (모델: {model_name}, 타겟 주제: '{topic}')...")
    
    prompt = f"""
다음 주제에 대해 한국어로 블로그 포스팅 글을 작성해 주세요:
주제: {topic}

[작성 지침]
1. 구글 검색엔진(SEO)에 노출되기 유리하도록 구조적이고 깊이 있는 정보성 글로 작성해 주세요.
2. 마크다운(Markdown) 포맷을 사용하세요.
3. 글 제목은 독자의 호기심을 유발하는 매력적인 형태로 지어주세요.
4. 반드시 본문의 가장 처음에 YAML Front Matter 형식을 아래 예시처럼 채워서 넣어주세요. (구분선 --- 포함)

예시:
---
title: "포스팅 글의 최종 제목"
date: {datetime.now().strftime("%Y-%m-%d")}
description: "검색 스니펫에 노출될 이 글에 대한 흥미로운 1~2문장 요약 설명"
category: "IT"
---

본문에는 # 대신 ##, ### 등의 소제목 태그를 사용하여 문단을 보기 좋게 나눠주시고, 구체적인 사례나 팁을 포함하여 글자 수 1500자 이상의 알찬 분량으로 작성해 주세요.
인공지능이라는 답변 어투(예: "네, 작성해 드리겠습니다" 등)는 완전히 배제하고, 실제 전문 테크 블로거가 쓴 글처럼 독립적인 본문 내용만 출력해야 합니다.
"""

    if model_type == "ollama":
        # 로컬 Ollama API 호출
        url = "http://127.0.0.1:11434/api/generate"
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res.get("response", "").strip()
        except Exception as e:
            print(f"[ERROR] Ollama 호출 실패: {e}")
            print("[INFO] Ollama가 켜져 있는지, 그리고 선택한 모델이 다운로드되어 있는지 확인해 주세요.")
            return None
            
    elif model_type == "gemini":
        if not api_key:
            print("[ERROR] 에러: Gemini API 키가 제공되지 않았습니다.")
            return None
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                res = json.loads(response.read().decode("utf-8"))
                # 제미니 응답 구조 파싱
                text = res['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
        except Exception as e:
            print(f"[ERROR] Gemini API 호출 실패: {e}")
            return None

def create_post_file(content):
    """생성된 글을 마크다운 파일로 저장"""
    # Front Matter에서 제목 추출해 파일명으로 삼기
    title = "temp-post"
    for line in content.split("\n")[:8]:
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip().strip('"').strip("'")
            break
            
    # 특수문자 제거 및 영문/한글 슬러그화
    slug = re_sub = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "-")
    filename = f"{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    filepath = os.path.join(CONTENT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[OK] 새 포스팅 저장 완료: {filepath}")
    return filepath

import re  # 정규식 임포트 확인

def main():
    parser = argparse.ArgumentParser(description="NABE - Nova Autonomous Blog Engine")
    parser.add_argument("--write", type=str, help="AI를 통해 글을 작성할 주제 지정")
    parser.add_argument("--model", type=str, default="ollama", choices=["ollama", "gemini"], help="AI 모델 타입 (ollama 또는 gemini)")
    parser.add_argument("--model-name", type=str, help="사용할 상세 모델명 (기본값: llama3.1:latest 또는 gemini-1.5-flash)")
    parser.add_argument("--api-key", type=str, help="Gemini API 키 (환경 변수 GEMINI_API_KEY 로도 가능)")
    parser.add_argument("--build-only", action="store_true", help="배포 없이 사이트 빌드만 수행")
    
    args = parser.parse_args()
    
    # 모델명 기본값 처리
    model_name = args.model_name
    if not model_name:
        model_name = "llama3.1:latest" if args.model == "ollama" else "gemini-1.5-flash"
        
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    
    # 1단계: AI 글쓰기 수행 (지정한 주제가 있을 경우)
    if args.write:
        post_content = generate_seo_post(args.write, args.model, model_name, api_key)
        if post_content:
            create_post_file(post_content)
        else:
            print("[ERROR] 글 생성에 실패하여 다음 단계를 진행하지 않습니다.")
            return

    # 2단계: 블로그 사이트 빌드 (Markdown -> HTML)
    build.main()
    
    # 3단계: 깃허브 배포 (build-only가 아닐 경우)
    if not args.build_only:
        publish.main()

if __name__ == "__main__":
    main()
