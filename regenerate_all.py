import os, re, time, json, urllib.request, urllib.error
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content", "posts")
API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_post(topic, api_key):
    prompt = f"""
다음 주제에 대해 한국어로 블로그 포스팅 글을 작성해 주세요:
주제: {topic}

[페르소나]
당신은 IT에 관심 많은 비개발자 테크 블로거 '루카(Luka)'입니다.
코딩은 못 하지만 궁금한 건 못 참아서 직접 파보고 기록하는 사람입니다.
전문가 행세가 아니라, 비개발자 시선에서 "이게 뭔데? 직접 알아봤다"는 솔직한 탐구 기록을 씁니다.

[작성 지침 - 가장 중요: 독창성과 구체성]
이 글은 "검색하면 어디에나 나오는 일반론"이어서는 안 됩니다. 아래 요소를 반드시 포함하세요:
1. **비개발자의 솔직한 시선**으로 서술하세요. "제가 개발자는 아닌데, 이게 뭔지 너무 궁금해서 파봤습니다" 같은 톤으로, 모르는 건 모른다고 쓰고 알아가는 과정을 보여주세요.
2. **구체적인 수치와 조사 결과**를 포함하세요. (예: "찾아보니 빌드 시간이 42초에서 11초로 줄어든다고 합니다", "공식 문서 기준 메모리 1.2GB") 추상적 표현("크게 향상", "훨씬 빠름")은 금지합니다.
3. **따라할 수 있는 코드/명령어/설정값**을 코드 블록으로 최소 2개 이상 넣으세요. "이걸 터미널에 치면 된다고 해서 해봤더니" 같은 맥락으로 자연스럽게 포함하세요.
4. **비개발자가 처음 접하면 헷갈리는 부분 2~3가지**와 그 해결법을 별도 섹션(## 비개발자가 헷갈리기 쉬운 부분)으로 다루세요.
5. **비교 표(마크다운 테이블)를 1개 이상** 포함하세요. (선택지 비교, 장단점, 버전 차이 등)
6. 글 마지막에 **핵심 요약 3줄**과 **FAQ 2~3개**(### 질문 형식)를 넣으세요.

[형식 지침]
1. 마크다운(Markdown) 포맷을 사용하고, # 대신 ##, ### 소제목으로 문단을 나누세요.
2. 글 제목은 독자의 호기심을 유발하되 과장("충격", "경악")은 피하고, 검색 의도에 맞는 구체적 제목으로 지으세요. 제목에 "개발자"라는 단어를 넣지 마세요.
3. 분량은 공백 포함 3000자 이상으로 알차게 작성하세요. 단, 분량을 채우기 위한 동어 반복이나 뻔한 배경 설명은 넣지 마세요.
4. 반드시 본문의 가장 처음에 YAML Front Matter 형식을 아래 예시처럼 채워서 넣어주세요. (구분선 --- 포함)

예시:
---
title: "포스팅 글의 최종 제목"
date: {datetime.now().strftime("%Y-%m-%d")}
description: "검색 스니펫에 노출될 이 글에 대한 흥미로운 1~2문장 요약 설명"
category: "테크"
---

[어투 지침]
인공지능이라는 답변 어투(예: "네, 작성해 드리겠습니다" 등)는 완전히 배제하고, 독립적인 본문 내용만 출력해야 합니다.
첫 단락에는 "안녕하세요, 코딩은 못 하지만 IT가 너무 궁금한 비개발자 루카(Luka)입니다."로 자연스러운 인사를 넣되, 바로 이어서 이 주제가 왜 궁금했는지 한두 문장으로 덧붙이세요. 끝 문단에는 "저처럼 비개발자도 충분히 이해할 수 있다"는 다정한 마무리 인사를 남겨주세요.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                text = re.sub(r"^```(?:markdown)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)
                return text.strip()
        except Exception as e:
            print(f"  [RETRY {attempt+1}/3] {e}")
            if attempt < 2:
                time.sleep(10 * (attempt + 1))
    return None


def main():
    if not API_KEY:
        print("[ERROR] GEMINI_API_KEY not set")
        return

    posts = sorted([f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')])
    total = len(posts)
    success = 0
    failed = []

    print(f"[START] {total}개 포스트 재생성 시작\n")

    for i, filename in enumerate(posts):
        filepath = os.path.join(CONTENT_DIR, filename)

        date_match = re.match(r'(\d{4}-\d{2}-\d{2})-', filename)
        if not date_match:
            print(f"[SKIP] 날짜 패턴 없음: {filename}")
            continue
        original_date = date_match.group(1)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        title = None
        category = "테크"
        for line in content.split('\n')[:15]:
            if line.lower().startswith('title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
            if line.lower().startswith('category:'):
                category = line.split(':', 1)[1].strip().strip('"').strip("'")

        if not title:
            print(f"[SKIP] 제목 없음: {filename}")
            continue

        print(f"[{i+1}/{total}] {title}")

        new_content = generate_post(title, API_KEY)
        if not new_content:
            print(f"  [FAIL] 생성 실패!")
            failed.append(filename)
            continue

        fm_match = re.match(r"^(---\s*\n)(.*?\n)(---\s*\n.*)$", new_content, re.DOTALL)
        if fm_match:
            header, front_matter, body = fm_match.groups()
            lines = front_matter.split("\n")
            for j, line in enumerate(lines):
                if line.lower().startswith("date:"):
                    lines[j] = f"date: {original_date}"
                    break
            new_content = header + "\n".join(lines) + body

        new_title = title
        for line in new_content.split('\n')[:15]:
            if line.lower().startswith('title:'):
                new_title = line.split(':', 1)[1].strip().strip('"').strip("'")
                break

        os.remove(filepath)

        slug = re.sub(r'[^\w\s-]', '', new_title).strip().replace(" ", "-")
        new_filename = f"{original_date}-{slug}.md"
        new_filepath = os.path.join(CONTENT_DIR, new_filename)

        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        success += 1
        print(f"  [OK] -> {new_filename}")

        if i < total - 1:
            time.sleep(4)

    print(f"\n[DONE] 성공: {success}/{total}, 실패: {len(failed)}")
    if failed:
        print(f"[FAILED] {failed}")


if __name__ == "__main__":
    main()
