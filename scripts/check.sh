#!/bin/bash
# 프로젝트 타입을 감지하여 적절한 품질 검증을 실행한다.
# Claude Code Stop 훅에서 자동 호출된다.

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if [ -f "package.json" ]; then
    echo "→ Node.js 프로젝트"
    npm run lint && npm run build && npm run test
elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    echo "→ Python 프로젝트"
    python3 -m pytest scripts/ -q
else
    echo "→ 테스트 러너 미설정 — package.json 또는 requirements.txt를 추가하세요." >&2
fi
