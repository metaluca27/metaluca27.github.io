# build.py
import os
import re
import shutil
import markdown
import xml.etree.ElementTree as ET
from datetime import datetime
from config import CONFIG

# 폴더 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content", "posts")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
PUBLIC_DIR = os.path.join(BASE_DIR, "docs")
PUBLIC_POSTS_DIR = os.path.join(PUBLIC_DIR, "posts")

# 필요한 폴더 생성
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(PUBLIC_POSTS_DIR, exist_ok=True)

def parse_front_matter(content):
    """YAML Front Matter 파싱"""
    title = "제목 없음"
    date_str = datetime.now().strftime("%Y-%m-%d")
    description = ""
    category = "일반"
    
    # --- 로 둘러싸인 Front Matter 추출
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if match:
        front_matter = match.group(1)
        body = match.group(2)
        
        for line in front_matter.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if key == "title":
                    title = val
                elif key == "date":
                    date_str = val
                elif key == "description":
                    description = val
                elif key == "category":
                    category = val
        return title, date_str, description, category, body
    else:
        # Front Matter가 없는 경우
        return title, date_str, description, category, content

def get_adsense_codes():
    """애드센스 코드 생성"""
    client = CONFIG.get("adsense_client", "").strip()
    if not client:
        return {
            "head": "",
            "sidebar": "",
            "body": ""
        }
    
    head_code = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}" crossorigin="anonymous"></script>'
    
    sidebar_code = f'''
    <div class="widget">
        <h3 class="widget-title"><i class="fa-solid fa-rectangle-ad"></i> 광고</h3>
        <div class="adsense-slot">
            <!-- 사이드바 광고 영역 -->
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{client}"
                 data-ad-slot="sidebar"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({{}});
            </script>
        </div>
    </div>
    '''
    
    body_code = f'''
    <div class="adsense-slot">
        <!-- 본문 내 광고 영역 -->
        <ins class="adsbygoogle"
             style="display:block; text-align:center;"
             data-ad-layout="in-article"
             data-ad-format="fluid"
             data-ad-client="{client}"
             data-ad-slot="body"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({{}});
        </script>
    </div>
    '''
    
    return {
        "head": head_code,
        "sidebar": sidebar_code,
        "body": body_code
    }

def build_recent_posts_widget(posts_metadata):
    """사이드바 최근 글 위젯 빌드"""
    widget_html = '<div class="widget">\n'
    widget_html += '    <h3 class="widget-title"><i class="fa-solid fa-list"></i> 최근 포스팅</h3>\n'
    widget_html += '    <ul style="list-style: none; display: flex; flex-direction: column; gap: 12px;">\n'
    
    # 최근 5개 글 링크 생성
    for post in posts_metadata[:5]:
        widget_html += f'        <li><a href="/posts/{post["filename"]}.html" style="font-size: 0.95rem; line-height: 1.4; display: block;">{post["title"]}</a></li>\n'
        
    widget_html += '    </ul>\n'
    widget_html += '</div>\n'
    return widget_html

def main():
    print("[*] 블로그 빌드 시작...")
    
    # 템플릿 파일 로드
    template_path = os.path.join(TEMPLATE_DIR, "base.html")
    if not os.path.exists(template_path):
        print(f"[ERROR] 에러: {template_path} 템플릿 파일이 없습니다.")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # 1. 포스팅 정보 스캔 및 파싱
    posts_metadata = []
    
    for file in os.listdir(CONTENT_DIR):
        if file.endswith(".md"):
            filepath = os.path.join(CONTENT_DIR, file)
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()
                
            title, date_str, description, category, body = parse_front_matter(raw_content)
            filename = os.path.splitext(file)[0]
            
            posts_metadata.append({
                "filename": filename,
                "title": title,
                "date": date_str,
                "description": description,
                "category": category,
                "body_markdown": body
            })
            
    # 날짜 최신순으로 정렬
    posts_metadata.sort(key=lambda x: x["date"], reverse=True)
    
    # 애드센스 코드 획득
    ads_codes = get_adsense_codes()
    
    # 최근 글 위젯 빌드
    recent_posts_widget = build_recent_posts_widget(posts_metadata)

    # 2. 개별 포스팅 HTML 생성
    for post in posts_metadata:
        print(f"[*] 포스팅 변환 중: {post['title']}")
        post_html_content = markdown.markdown(post["body_markdown"], extensions=['fenced_code', 'codehilite', 'tables'])
        
        # 본문 상단에 날짜 및 카테고리 메타정보 추가
        meta_html = f'''
        <div class="post-meta">
            <span><i class="fa-regular fa-calendar"></i> {post["date"]}</span>
            <span><i class="fa-regular fa-folder"></i> {post["category"]}</span>
            <span><i class="fa-regular fa-user"></i> {CONFIG["author"]}</span>
        </div>
        '''
        
        full_content = f'''
        <article class="post-detail">
            <h1>{post["title"]}</h1>
            {meta_html}
            {ads_codes["body"]}
            <div class="post-content">
                {post_html_content}
            </div>
            {ads_codes["body"]}
        </article>
        '''
        
        # 템플릿 플레이스홀더 치환
        rendered = template_content
        rendered = rendered.replace("{{ page_title }}", post["title"])
        rendered = rendered.replace("{{ page_description }}", post["description"] or CONFIG["blog_subtitle"])
        rendered = rendered.replace("{{ blog_title }}", CONFIG["blog_title"])
        rendered = rendered.replace("{{ blog_subtitle }}", CONFIG["blog_subtitle"])
        rendered = rendered.replace("{{ github_username }}", CONFIG["github_username"])
        rendered = rendered.replace("{{ author }}", CONFIG["author"])
        rendered = rendered.replace("{{ hero_section }}", "")
        rendered = rendered.replace("{{ content }}", full_content)
        rendered = rendered.replace("{{ recent_posts_widget }}", recent_posts_widget)
        rendered = rendered.replace("{{ adsense_head_code }}", ads_codes["head"])
        rendered = rendered.replace("{{ adsense_sidebar_code }}", ads_codes["sidebar"])
        
        output_file_path = os.path.join(PUBLIC_POSTS_DIR, f"{post['filename']}.html")
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(rendered)

    # 3. 홈 메인 화면(index.html) 생성
    print("[*] 메인 페이지 생성 중...")
    cards_html = '<div class="post-list">\n'
    
    if not posts_metadata:
        cards_html += '    <div class="post-card" style="text-align:center; padding: 50px 20px;">포스팅이 아직 존재하지 않습니다. 첫 포스팅을 작성해 주세요!</div>\n'
    else:
        for post in posts_metadata:
            cards_html += f'''
            <article class="post-card">
                <div class="post-meta">
                    <span><i class="fa-regular fa-calendar"></i> {post["date"]}</span>
                    <span><i class="fa-regular fa-folder"></i> {post["category"]}</span>
                </div>
                <h2 class="post-title"><a href="/posts/{post["filename"]}.html">{post["title"]}</a></h2>
                <p class="post-excerpt">{post["description"] or "작성된 요약 정보가 없습니다."}</p>
                <a href="/posts/{post["filename"]}.html" class="read-more">더 읽어보기 <i class="fa-solid fa-arrow-right"></i></a>
            </article>
            '''
    cards_html += '</div>\n'
    
    hero_section_html = f'''
    <section class="hero">
        <div class="container">
            <h1>{CONFIG["blog_title"]}</h1>
            <p>{CONFIG["blog_subtitle"]}</p>
        </div>
    </section>
    '''
    
    rendered_index = template_content
    rendered_index = rendered_index.replace("{{ page_title }}", "홈")
    rendered_index = rendered_index.replace("{{ page_description }}", CONFIG["blog_subtitle"])
    rendered_index = rendered_index.replace("{{ blog_title }}", CONFIG["blog_title"])
    rendered_index = rendered_index.replace("{{ blog_subtitle }}", CONFIG["blog_subtitle"])
    rendered_index = rendered_index.replace("{{ github_username }}", CONFIG["github_username"])
    rendered_index = rendered_index.replace("{{ author }}", CONFIG["author"])
    rendered_index = rendered_index.replace("{{ hero_section }}", hero_section_html)
    rendered_index = rendered_index.replace("{{ content }}", cards_html)
    rendered_index = rendered_index.replace("{{ recent_posts_widget }}", recent_posts_widget)
    rendered_index = rendered_index.replace("{{ adsense_head_code }}", ads_codes["head"])
    rendered_index = rendered_index.replace("{{ adsense_sidebar_code }}", ads_codes["sidebar"])
    
    index_output_path = os.path.join(PUBLIC_DIR, "index.html")
    with open(index_output_path, "w", encoding="utf-8") as f:
        f.write(rendered_index)

    # 4. CNAME 파일 생성
    cname_path = os.path.join(PUBLIC_DIR, "CNAME")
    with open(cname_path, "w", encoding="utf-8") as f:
        f.write(CONFIG["domain"])
    print(f"[OK] CNAME 생성 완료 ({CONFIG['domain']})")

    # 5. ads.txt 파일 생성
    ads_txt_path = os.path.join(PUBLIC_DIR, "ads.txt")
    with open(ads_txt_path, "w", encoding="utf-8") as f:
        client = CONFIG.get("adsense_client", "").strip()
        if client:
            pub_id = client.replace("ca-", "")
            f.write(f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n")
        else:
            # 기본 빈 파일 또는 예시 형식
            f.write("# Google AdSense ads.txt 파일\n# 승인 후 ca-pub 번호가 입력되면 자동으로 활성화됩니다.\n")
    print("[OK] ads.txt 생성 완료")

    # 6. sitemap.xml 파일 생성
    print("[*] sitemap.xml 생성 중...")
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    
    # XML 네임스페이스 등록
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # 6-1. 홈 sitemap 등록
    url_node = ET.SubElement(urlset, "url")
    ET.SubElement(url_node, "loc").text = f"https://{CONFIG['domain']}/"
    ET.SubElement(url_node, "lastmod").text = now_str
    ET.SubElement(url_node, "changefreq").text = "daily"
    ET.SubElement(url_node, "priority").text = "1.0"
    
    # 6-2. 포스팅 sitemap 등록
    for post in posts_metadata:
        url_node = ET.SubElement(urlset, "url")
        ET.SubElement(url_node, "loc").text = f"https://{CONFIG['domain']}/posts/{post['filename']}.html"
        ET.SubElement(url_node, "lastmod").text = f"{post['date']}T00:00:00+09:00"
        ET.SubElement(url_node, "changefreq").text = "weekly"
        ET.SubElement(url_node, "priority").text = "0.8"
        
    tree = ET.ElementTree(urlset)
    sitemap_path = os.path.join(PUBLIC_DIR, "sitemap.xml")
    
    # 예쁘게 들여쓰기 처리 후 파일 쓰기
    ET.indent(tree, space="    ", level=0)
    with open(sitemap_path, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", xml_declaration=False)
        
    print("[OK] 블로그 빌드 완료!")

if __name__ == "__main__":
    main()
