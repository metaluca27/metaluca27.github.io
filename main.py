# main.py
import os
import sys
import json
import re
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
import build
import publish
from config import CONFIG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content", "posts")

# 구글 검색 노출 및 애드센스에 매우 유리한 50개 고품질 IT/테크 주제 리스트
TOPIC_BANK = [
    # AI & 머신러닝
    "인공지능 RAG(검색 증강 생성) 아키텍처의 개념과 구현 원리",
    "개인용 컴퓨터에서 실행하는 Gemma 2 로컬 구동 및 프롬프트 제어 기법",
    "개발자를 위한 GitHub Copilot 200% 활용하는 페어 프로그래밍 꿀팁",
    "Stable Diffusion을 활용한 고품질 AI 이미지 생성 기초와 프롬프트 가이드",
    "대형 언어 모델(LLM) 파인튜닝(Fine-Tuning)과 RAG의 차이점 및 활용 가이드",
    "머신러닝 초보자를 위한 지도학습과 비지도학습의 핵심 개념 정리",
    
    # 개발 & 프로그래밍
    "파이썬 비동기 프로그래밍 Asyncio 기초 및 실무 적용 방안",
    "웹 성능 최적화: 브라우저 렌더링 과정을 이해하고 LCP 점수 개선하기",
    "Docker 컨테이너 기술의 핵심 개념과 초보자를 위한 Dockerfile 작성법",
    "RESTful API 설계 표준 규칙과 예외 처리(Error Handling) 베스트 프랙티스",
    "파이썬 pandas 라이브러리를 활용한 데이터 정제 및 분석법 기초",
    "Git Branch 전략의 표준: Git Flow와 GitHub Flow 완벽 비교 분석",
    "웹 애플리케이션 보안의 기본: OWASP Top 10 취약점과 방어 전략",
    "초보 개발자를 위한 데이터베이스 정규화(1NF, 2NF, 3NF)와 비정규화 이해하기",
    "FastAPI를 활용한 초고속 파이썬 웹 API 서버 개발 가이드",
    
    # 생산성 & IT 툴
    "맥북(Mac) 필수 유틸리티 앱 추천 및 생산성 향상 단축키 정리",
    "Slack과 다양한 외부 앱(GitHub, Notion) 연동을 통한 업무 자동화 비결",
    "시간 관리의 끝판왕: 뽀모도로 기법과 시간 기록 앱 활용 가이드",
    "마인드맵 도구 XMind와 옵시디언의 결합을 통한 구조적 기획서 작성법",
    "크롬 개발자 도구(Chrome DevTools) 실무에서 유용하게 쓰는 기능 5가지",
    "엑셀(Excel) VLOOKUP을 넘어선 XLOOKUP 및 동적 배열 수식 활용 팁",
    
    # SEO & 디지털 마케팅
    "구글 서치 콘솔(Search Console) 등록 및 색인 생성 오류 해결 가이드",
    "네이버 웹마스터도구를 활용한 네이버 검색 상위 노출 최적화 팁",
    "수익형 블로그를 위한 구글 애드센스 고단가 키워드 분석 및 매칭법",
    "구글 애널리틱스 4 (GA4) 설치 및 웹사이트 핵심 전환 지표 트래킹 기초",
    "모바일 페이지 로딩 속도를 높이는 Google AMP 기술의 명과 암",
    
    # 최신 IT 트렌드 & 인프라
    "서버리스(Serverless) 아키텍처의 장단점 및 AWS Lambda 도입 시 고려사항",
    "블록체인(Blockchain) 기술의 작동 원리와 스마트 계약(Smart Contract) 기초",
    "메타버스(Metaverse) 트렌드와 현실적인 비즈니스 모델 전망",
    "클라우드 보안 책임 공유 모델(Shared Responsibility Model)의 정의와 중요성",
    "쿠버네티스(Kubernetes) 컨테이너 오케스트레이션 개념과 핵심 아키텍처 정리",
    "에지 컴퓨팅(Edge Computing)의 개념과 클라우드 컴퓨팅과의 상호 보완성",
    
    # IT 하드웨어 & 실용 지식
    "최신 SSD 규격(SATA, NVMe PCIe 4.0/5.0) 비교 및 구매 가이드",
    "외장하드 및 NAS 구축을 통한 개인 데이터 3-2-1 백업 전략 가이드",
    "인터넷 속도를 개선하는 DNS 설정 변경법 (Cloudflare 1.1.1.1 vs Google 8.8.8.8)",
    "기계식 키보드 스위치(청축, 적축, 갈축, 저소음) 특성과 나에게 맞는 키보드 고르기",
    "컴퓨터 쿨링 시스템(공랭 vs 수랭) 장단점 비교 및 올바른 쿨러 선택 요령",
    
    # 고급 IT 기술
    "TypeScript를 도입해야 하는 이유와 JavaScript 코드 마이그레이션 가이드",
    "디자인 패턴의 기초: 싱글톤, 팩토리, 옵저버 패턴의 개념과 구현 예시",
    "클린 코드(Clean Code) 작성을 위한 변수 네이밍과 리팩토링의 황금 법칙",
    "네트워크 3-Way Handshake와 4-Way Handshake 작동 과정 완벽 이해",
    "HTTPS와 SSL/TLS 암호화 통신 메커니즘의 상세 작동 원리",
    "리눅스(Linux) 터미널 자주 쓰는 핵심 명령어 및 셸 스크립트 작성 기초",
    "가상 사설망(VPN)의 기술적 작동 원리와 보안 연결의 중요성",
    "데이터 프라이버시 법(GDPR)이 글로벌 IT 비즈니스에 미치는 영향 분석",
    "파이썬 웹 스크래핑 시 봇 차단(Anti-Bot)을 우회하는 고급 기법과 헤더 설정",
    "소프트웨어 테스트 자동화: CI/CD 파이프라인에 단위 테스트 통합하기",
    "그래프 데이터베이스(Graph DB)의 개념과 관계형 DB(RDB) 대비 강점 분석",
    "클라우드 비용 절감 전략: AWS Spot Instance와 Reserved Instance 활용 요령",
    "개발자 번아웃 증후군 증상 진단과 일과 삶의 균형(WLB) 회복 솔루션"
]

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
category: "테크"
---

본문에는 # 대신 ##, ### 등의 소제목 태그를 사용하여 문단을 보기 좋게 나눠주시고, 구체적인 사례나 팁을 포함하여 글자 수 1500자 이상의 알찬 분량으로 작성해 주세요.
인공지능이라는 답변 어투(예: "네, 작성해 드리겠습니다" 등)는 완전히 배제하고, 실제 전문 테크 블로거인 '루카(Luka)'가 쓴 글처럼 독립적인 본문 내용만 출력해야 합니다.
첫 단락에는 "안녕하세요, IT와 테크 지식을 공부하고 기록하는 루카(Luka)입니다."로 자연스러운 인사를 넣어주시고, 끝 문단에도 다정하고 전문적인 마무리 인사를 남겨주세요.
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
            
        # 방어적 코드: 복사 과정에서 혼입될 수 있는 앞뒤 공백 및 따옴표 제거
        api_key = api_key.strip().strip('"').strip("'").strip()
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[*] Gemini API 호출 시도 {attempt + 1}/{max_retries}...")
                with urllib.request.urlopen(req, timeout=90) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    # 제미니 응답 구조 파싱
                    text = res['candidates'][0]['content']['parts'][0]['text']
                    
                    # 제미니가 종종 마크다운 펜스(```markdown ... ```)로 본문을 감싸서 주는 경우가 있어 제거해 줌
                    if text.startswith("```markdown"):
                        text = text[11:].strip()
                    elif text.startswith("```"):
                        text = text[3:].strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
                        
                    return text.strip()
            except Exception as e:
                print(f"[WARNING] Gemini API 호출 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                # 구글 서버가 돌려준 자세한 에러 바디 파싱 시도 및 출력
                if hasattr(e, "read"):
                    try:
                        error_body = e.read().decode("utf-8")
                        print(f"[ERROR] Gemini API 응답 상세: {error_body}")
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    sleep_time = 15 * (attempt + 1)
                    print(f"[*] {sleep_time}초 후 재시도합니다...")
                    time.sleep(sleep_time)
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
    slug = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "-")
    today_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{today_str}-{slug}.md"
    filepath = os.path.join(CONTENT_DIR, filename)
    
    # Front Matter의 date가 다를 경우 강제 교정
    fm_match = re.match(r"^(---\s*\n)(.*?\n)(---\s*\n.*)$", content, re.DOTALL)
    if fm_match:
        header, front_matter, body = fm_match.groups()
        lines = front_matter.split("\n")
        date_found = False
        for i, line in enumerate(lines):
            if line.lower().startswith("date:"):
                lines[i] = f"date: {today_str}"
                date_found = True
                break
        if not date_found:
            lines.insert(0, f"date: {today_str}")
        content = header + "\n".join(lines) + body
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[OK] 새 포스팅 저장 완료: {filepath}")
    return filepath

def get_next_auto_topic():
    """기존 작성된 마크다운 포스트 개수를 세어 다음 주제 자동 선정"""
    if not os.path.exists(CONTENT_DIR):
        return TOPIC_BANK[0]
        
    # .md 파일 목록 수집
    md_files = [f for f in os.listdir(CONTENT_DIR) if f.endswith(".md")]
    post_count = len(md_files)
    
    # 50개 주제를 순차적으로 돌아가며 선택 (초과 시 첫 주제부터 다시 순환)
    topic_index = post_count % len(TOPIC_BANK)
    selected_topic = TOPIC_BANK[topic_index]
    
    print(f"[INFO] 현재까지 작성된 포스트 수: {post_count}개")
    print(f"[INFO] 오늘의 자동 선정 주제 (인덱스 {topic_index}): '{selected_topic}'")
    return selected_topic

def main():
    parser = argparse.ArgumentParser(description="NABE - Nova Autonomous Blog Engine")
    parser.add_argument("--write", type=str, help="AI를 통해 글을 작성할 주제 지정")
    parser.add_argument("--auto", action="store_true", help="주제 은행에서 기존 포스트 수 기준으로 자동 주제 선정하여 발행")
    parser.add_argument("--model", type=str, default="ollama", choices=["ollama", "gemini"], help="AI 모델 타입 (ollama 또는 gemini)")
    parser.add_argument("--model-name", type=str, help="사용할 상세 모델명 (기본값: llama3.1:latest 또는 gemini-2.5-flash)")
    parser.add_argument("--api-key", type=str, help="Gemini API 키 (환경 변수 GEMINI_API_KEY 로도 가능)")
    parser.add_argument("--build-only", action="store_true", help="배포 없이 사이트 빌드만 수행")
    
    args = parser.parse_args()
    
    # 모델명 기본값 처리
    model_name = args.model_name
    if not model_name:
        model_name = "llama3.1:latest" if args.model == "ollama" else "gemini-2.5-flash"
        
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")

    
    # 1단계: AI 글쓰기 수행 (지정한 주제 또는 자동 주제가 있을 경우)
    target_topic = None
    if args.write:
        target_topic = args.write
    elif args.auto:
        target_topic = get_next_auto_topic()
        
    if target_topic:
        post_content = generate_seo_post(target_topic, args.model, model_name, api_key)
        if post_content:
            create_post_file(post_content)
        else:
            print("[ERROR] 글 생성에 실패하여 다음 단계를 진행하지 않습니다.")
            sys.exit(1)

    # 2단계: 블로그 사이트 빌드 (Markdown -> HTML)
    build.main()
    
    # 3단계: 깃허브 배포 (build-only가 아닐 경우)
    if not args.build_only:
        publish.main()

if __name__ == "__main__":
    main()
