import os, re, time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content", "posts")
IMAGES_DIR = os.path.join(BASE_DIR, "docs", "images", "posts")
API_KEY = os.environ.get("GEMINI_API_KEY")

os.makedirs(IMAGES_DIR, exist_ok=True)

from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)

def generate_thumbnail(topic, filename_slug, overwrite=False):
    img_path = os.path.join(IMAGES_DIR, f"{filename_slug}.png")
    if os.path.exists(img_path) and not overwrite:
        print(f"  [SKIP] already exists")
        return True

    prompt = f"""Generate a clean, modern blog thumbnail illustration.
Topic: {topic}
Style: flat design, minimal, vibrant colors, tech-themed.
ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO CHARACTERS, NO WRITING of any kind in the image. Not in any language. No labels, no captions, no watermarks, no speech bubbles with text. Only pure visual illustration with icons, shapes, and graphics.
Aspect ratio: landscape (16:9).
The image should feel like a professional tech blog header."""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    with open(img_path, "wb") as f:
                        f.write(part.inline_data.data)
                    size_kb = len(part.inline_data.data) // 1024
                    print(f"  [OK] {size_kb}KB")
                    return True
            print(f"  [WARN] No image in response")
            return False
        except Exception as e:
            print(f"  [RETRY {attempt+1}/3] {e}")
            if attempt < 2:
                time.sleep(10 * (attempt + 1))
    return False


def insert_image_to_post(filepath, image_url):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if "![" in content.split("---", 3)[-1][:500]:
        return False

    match = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)", content, re.DOTALL)
    if match:
        front_matter = match.group(1)
        body = match.group(2)
        lines = body.split("\n", 3)
        insert_after = 0
        for i, line in enumerate(lines[:3]):
            if line.strip():
                insert_after = i + 1
                break
        image_md = f"\n![thumbnail]({image_url})\n"
        lines.insert(insert_after, image_md)
        new_content = front_matter + "\n".join(lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    if not API_KEY:
        print("[ERROR] GEMINI_API_KEY not set")
        return

    posts = sorted([f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')])
    total = len(posts)
    success = 0
    failed = []

    print(f"[START] {total}개 포스트 썸네일 생성 시작\n")

    for i, filename in enumerate(posts):
        filepath = os.path.join(CONTENT_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        title = None
        for line in content.split('\n')[:15]:
            if line.lower().startswith('title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                break

        if not title:
            print(f"[SKIP] {filename}")
            continue

        slug = os.path.splitext(filename)[0]
        print(f"[{i+1}/{total}] {title}")

        if generate_thumbnail(title, slug, overwrite=True):
            image_url = f"/images/posts/{slug}.png"
            insert_image_to_post(filepath, image_url)
            success += 1
        else:
            failed.append(filename)

        if i < total - 1:
            time.sleep(5)

    print(f"\n[DONE] 성공: {success}/{total}, 실패: {len(failed)}")
    if failed:
        print(f"[FAILED] {failed}")


if __name__ == "__main__":
    main()
