# publish.py
import subprocess
import os
from datetime import datetime
from config import CONFIG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_git_command(args, cwd=BASE_DIR):
    """Git 명령어 실행 헬퍼"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def is_git_repo():
    """현재 폴더가 깃 레포지토리인지 확인"""
    success, _ = run_git_command(["rev-parse", "--is-inside-work-tree"])
    return success

def main():
    print("[*] GitHub 배포 시작...")
    
    # 1. Git 초기화 확인
    if not is_git_repo():
        print("[*] Git 저장소 초기화 중...")
        success, out = run_git_command(["init"])
        if not success:
            print(f"[ERROR] Git 초기화 실패: {out}")
            return
            
    # 2. 파일 추가 (git add)
    print("[*] 변경된 파일 추가 중...")
    success, out = run_git_command(["add", "."])
    if not success:
        print(f"[ERROR] Git Add 실패: {out}")
        return
        
    # 3. 변경 사항 확인 및 커밋
    # 먼저 커밋할 변경사항이 있는지 확인
    success, status = run_git_command(["status", "--porcelain"])
    if not success:
        print(f"❌ Git Status 확인 실패: {status}")
        return
        
    if not status.strip():
        print("[INFO] 변경사항이 없어 배포를 건너뜁니다.")
        return
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"NABE Auto-Publish: {now_str}"
    
    print(f"[*] 커밋 생성 중: '{commit_msg}'")
    
    # 임시 유저 정보 설정 (전역 설정이 없을 경우를 대비해 로컬 설정)
    run_git_command(["config", "user.name", CONFIG.get("author", "Luka")])
    run_git_command(["config", "user.email", f"{CONFIG['github_username']}@users.noreply.github.com"])
    
    success, out = run_git_command(["commit", "-m", commit_msg])
    if not success:
        print(f"[ERROR] Git Commit 실패: {out}")
        return

    # 브랜치 이름을 main으로 통일
    run_git_command(["branch", "-M", "main"])

    # 4. 원격 저장소 설정 확인
    if "origin" not in remotes:
        repo_url = f"https://github.com/{CONFIG['github_username']}/{CONFIG['github_username']}.github.io.git"
        print(f"[OK] 원격 저장소(origin) 연결 설정 중: {repo_url}")
        success, out = run_git_command(["remote", "add", "origin", repo_url])
        if not success:
            # 혹시 이미 추가되어 있다면 URL만 업데이트
            run_git_command(["remote", "set-url", "origin", repo_url])

    # 5. 원격 푸시 (git push)
    print("[*] GitHub로 푸시 중...")
    print("[INFO] 처음 푸시할 경우 윈도우 로그인 인증 창이 뜰 수 있습니다. 확인 후 승인해 주세요.")
    
    success, out = run_git_command(["push", "-u", "origin", "main"])
    if success:
        print("[OK] GitHub Pages 배포 성공!")
        print(f"[OK] 블로그 도메인: http://{CONFIG['domain']}")
        print(f"[OK] 깃허브 주소: https://github.com/{CONFIG['github_username']}/{CONFIG['github_username']}.github.io")
    else:
        print("[ERROR] 푸시 실패!")
        print(f"상세 에러 내용:\n{out}")
        print("\n[해결 방법]")
        print(f"1. 깃허브 사이트에 로그인하셔서 '{CONFIG['github_username']}.github.io' 라는 이름의 빈 리포지토리(Repository)를 만드셨는지 확인해 주세요.")
        print("2. 윈도우 깃 자격증명(인증) 문제일 수 있으니 터미널에서 수동으로 'git push -u origin main'을 한 번 더 실행해 주시기 바랍니다.")

if __name__ == "__main__":
    main()
