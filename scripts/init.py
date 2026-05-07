#!/usr/bin/env python3
"""
Harness Init — 새 프로젝트 디렉토리에 하네스 프레임워크를 복사한다.

Usage:
    python3 scripts/init.py <project-name> [target-dir]

Arguments:
    project-name  새 프로젝트명
    target-dir    생성할 디렉토리 경로 (기본: ./<project-name>)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent

COPY_FILES = [
    ("templates/CLAUDE.md", "CLAUDE.md"),
    ("requirements.txt", "requirements.txt"),
    ("scripts/execute.py", "scripts/execute.py"),
    ("scripts/test_execute.py", "scripts/test_execute.py"),
    ("scripts/init.py", "scripts/init.py"),
    ("scripts/check.sh", "scripts/check.sh"),
    ("scripts/session_start.py", "scripts/session_start.py"),
]

COPY_DIRS = [
    "docs",
    ".claude",
]


def main():
    parser = argparse.ArgumentParser(description="Harness Init — 새 프로젝트 초기화")
    parser.add_argument("project_name", help="프로젝트명")
    parser.add_argument("target_dir", nargs="?", help="생성할 디렉토리 경로 (기본: ./<project-name>)")
    args = parser.parse_args()

    target = Path(args.target_dir).resolve() if args.target_dir else Path.cwd() / args.project_name

    if target.exists():
        print(f"ERROR: {target} 이미 존재합니다.")
        sys.exit(1)

    print(f"\n하네스 프레임워크 초기화: {args.project_name}")
    print(f"위치: {target}\n")

    target.mkdir(parents=True)
    (target / "scripts").mkdir()
    (target / "phases").mkdir()

    for src_rel, dst_rel in COPY_FILES:
        src = FRAMEWORK_ROOT / src_rel
        if not src.exists():
            print(f"  SKIP: {src_rel} (없음)")
            continue
        dst = target / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✓ {dst_rel}")

    for rel_dir in COPY_DIRS:
        src = FRAMEWORK_ROOT / rel_dir
        if not src.exists():
            print(f"  SKIP: {rel_dir}/ (없음)")
            continue
        shutil.copytree(src, target / rel_dir)
        print(f"  ✓ {rel_dir}/")

    check_sh = target / "scripts" / "check.sh"
    if check_sh.exists():
        check_sh.chmod(0o755)

    (target / "phases" / ".gitkeep").touch()

    (target / ".gitignore").write_text(
        "# Harness output\n"
        "phases/**/*-output.json\n"
        "\n# 프로젝트별 추가\n"
    )
    print(f"  ✓ .gitignore")

    r = subprocess.run(["git", "init"], cwd=target, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  ✓ git init")

    print(f"\n{'='*50}")
    print(f"  ✓ {args.project_name} 초기화 완료!")
    print(f"{'='*50}")
    print(f"\n다음 단계:")
    print(f"  cd {target}")
    print(f"  # 아래 파일들을 프로젝트에 맞게 채우세요:")
    print(f"  #   CLAUDE.md            — 기술 스택, 아키텍처 규칙, 명령어")
    print(f"  #   docs/PRD.md          — 제품 요구사항")
    print(f"  #   docs/ARCHITECTURE.md — 아키텍처 설계")
    print(f"  #   docs/ADR.md          — 기술 결정 기록")
    print(f"  #   docs/UI_GUIDE.md     — UI 디자인 가이드 (프론트엔드 프로젝트)")
    print(f"  # 채운 뒤: claude 실행 → /harness 입력")


if __name__ == "__main__":
    main()
