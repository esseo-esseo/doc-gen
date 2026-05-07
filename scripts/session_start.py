#!/usr/bin/env python3
"""SessionStart 훅 — 세션 시작 시 현재 Harness phases 상태를 출력한다."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
top_index = ROOT / "phases" / "index.json"

if not top_index.exists():
    sys.exit(0)

try:
    data = json.loads(top_index.read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)

phases = data.get("phases", [])
active = [p for p in phases if p.get("status") != "completed"]
completed = [p for p in phases if p.get("status") == "completed"]

if not active and not completed:
    sys.exit(0)

print("\n" + "=" * 54)
print("  [Harness] 프로젝트 현황")
print("=" * 54)

if active:
    print(f"\n  진행 중 ({len(active)}개):")
    for p in active:
        icon = {"pending": "⏳", "error": "✗", "blocked": "⏸"}.get(p.get("status", ""), "?")
        print(f"    {icon}  {p['dir']} — {p.get('status', '?')}")

        phase_index = ROOT / "phases" / p["dir"] / "index.json"
        if phase_index.exists():
            try:
                pidx = json.loads(phase_index.read_text(encoding="utf-8"))
                steps = pidx.get("steps", [])
                done = sum(1 for s in steps if s.get("status") == "completed")
                total = len(steps)
                current = next(
                    (s for s in steps if s.get("status") in ("pending", "error", "blocked")),
                    None,
                )
                step_info = f"{done}/{total} steps 완료"
                if current:
                    step_info += f"  →  Step {current['step']} ({current['name']}) [{current['status']}]"
                print(f"         {step_info}")
            except Exception:
                pass

if completed:
    dirs = ", ".join(p["dir"] for p in completed)
    print(f"\n  완료: {dirs}")

print(f"\n  실행: python3 scripts/execute.py <phase-dir> [--push] [--pr] [--parallel]")
print("=" * 54 + "\n")
