#!/usr/bin/env python3
"""
Harness Step Executor — phase 내 step을 순차 또는 병렬 실행하고 자가 교정한다.

Usage:
    python3 scripts/execute.py <phase-dir> [--push] [--pr] [--parallel]
"""

import argparse
import concurrent.futures
import contextlib
import json
import os
import subprocess
import sys
import threading
import time
import types
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent


@contextlib.contextmanager
def progress_indicator(label: str):
    """터미널 진행 표시기. with 문으로 사용하며 .elapsed 로 경과 시간을 읽는다."""
    frames = "◐◓◑◒"
    stop = threading.Event()
    t0 = time.monotonic()

    def _animate():
        idx = 0
        while not stop.wait(0.12):
            sec = int(time.monotonic() - t0)
            sys.stderr.write(f"\r{frames[idx % len(frames)]} {label} [{sec}s]")
            sys.stderr.flush()
            idx += 1
        sys.stderr.write("\r" + " " * (len(label) + 20) + "\r")
        sys.stderr.flush()

    th = threading.Thread(target=_animate, daemon=True)
    th.start()
    info = types.SimpleNamespace(elapsed=0.0)
    try:
        yield info
    finally:
        stop.set()
        th.join()
        info.elapsed = time.monotonic() - t0


class StepExecutor:
    """Phase 디렉토리 안의 step들을 순차 또는 병렬 실행하는 하네스."""

    MAX_RETRIES = 3
    FEAT_MSG = "feat({phase}): step {num} — {name}"
    CHORE_MSG = "chore({phase}): step {num} output"
    TZ = timezone(timedelta(hours=9))

    def __init__(self, phase_dir_name: str, *, auto_push: bool = False,
                 auto_pr: bool = False, parallel: bool = False):
        self._root = str(ROOT)
        self._phases_dir = ROOT / "phases"
        self._phase_dir = self._phases_dir / phase_dir_name
        self._phase_dir_name = phase_dir_name
        self._top_index_file = self._phases_dir / "index.json"
        self._auto_push = auto_push
        self._auto_pr = auto_pr
        self._parallel = parallel

        if not self._phase_dir.is_dir():
            print(f"ERROR: {self._phase_dir} not found")
            sys.exit(1)

        self._index_file = self._phase_dir / "index.json"
        if not self._index_file.exists():
            print(f"ERROR: {self._index_file} not found")
            sys.exit(1)

        idx = self._read_json(self._index_file)
        self._project = idx.get("project", "project")
        self._phase_name = idx.get("phase", phase_dir_name)
        self._total = len(idx["steps"])

    def run(self):
        self._print_header()
        self._check_blockers()
        self._checkout_branch()
        guardrails = self._load_guardrails()
        self._ensure_created_at()
        self._execute_all_steps(guardrails)
        self._finalize()

    # --- timestamps ---

    def _stamp(self) -> str:
        return datetime.now(self.TZ).strftime("%Y-%m-%dT%H:%M:%S%z")

    # --- JSON I/O ---

    @staticmethod
    def _read_json(p: Path) -> dict:
        return json.loads(p.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(p: Path, data: dict):
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- git ---

    def _run_git(self, *args) -> subprocess.CompletedProcess:
        cmd = ["git"] + list(args)
        return subprocess.run(cmd, cwd=self._root, capture_output=True, text=True)

    def _checkout_branch(self):
        branch = f"feat-{self._phase_name}"

        r = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if r.returncode != 0:
            print(f"  ERROR: git을 사용할 수 없거나 git repo가 아닙니다.")
            print(f"  {r.stderr.strip()}")
            sys.exit(1)

        if r.stdout.strip() == branch:
            return

        r = self._run_git("rev-parse", "--verify", branch)
        r = self._run_git("checkout", branch) if r.returncode == 0 else self._run_git("checkout", "-b", branch)

        if r.returncode != 0:
            print(f"  ERROR: 브랜치 '{branch}' checkout 실패.")
            print(f"  {r.stderr.strip()}")
            print(f"  Hint: 변경사항을 stash하거나 commit한 후 다시 시도하세요.")
            sys.exit(1)

        print(f"  Branch: {branch}")

    def _commit_step(self, step_num: int, step_name: str):
        output_rel = f"phases/{self._phase_dir_name}/step{step_num}-output.json"
        status_rel = f"phases/{self._phase_dir_name}/step{step_num}-status.json"
        index_rel = f"phases/{self._phase_dir_name}/index.json"

        self._run_git("add", "-A")
        self._run_git("reset", "HEAD", "--", output_rel)
        self._run_git("reset", "HEAD", "--", status_rel)
        self._run_git("reset", "HEAD", "--", index_rel)

        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            msg = self.FEAT_MSG.format(phase=self._phase_name, num=step_num, name=step_name)
            r = self._run_git("commit", "-m", msg)
            if r.returncode == 0:
                print(f"  Commit: {msg}")
            else:
                print(f"  WARN: 코드 커밋 실패: {r.stderr.strip()}")

        self._run_git("add", "-A")
        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            msg = self.CHORE_MSG.format(phase=self._phase_name, num=step_num)
            r = self._run_git("commit", "-m", msg)
            if r.returncode != 0:
                print(f"  WARN: housekeeping 커밋 실패: {r.stderr.strip()}")

    # --- top-level index ---

    def _update_top_index(self, status: str):
        if not self._top_index_file.exists():
            return
        top = self._read_json(self._top_index_file)
        ts = self._stamp()
        for phase in top.get("phases", []):
            if phase.get("dir") == self._phase_dir_name:
                phase["status"] = status
                ts_key = {"completed": "completed_at", "error": "failed_at", "blocked": "blocked_at"}.get(status)
                if ts_key:
                    phase[ts_key] = ts
                break
        self._write_json(self._top_index_file, top)

    # --- guardrails & context ---

    def _load_guardrails(self) -> str:
        sections = []
        claude_md = ROOT / "CLAUDE.md"
        if claude_md.exists():
            sections.append(f"## 프로젝트 규칙 (CLAUDE.md)\n\n{claude_md.read_text()}")
        docs_dir = ROOT / "docs"
        if docs_dir.is_dir():
            for doc in sorted(docs_dir.glob("*.md")):
                sections.append(f"## {doc.stem}\n\n{doc.read_text()}")
        return "\n\n---\n\n".join(sections) if sections else ""

    @staticmethod
    def _build_step_context(index: dict) -> str:
        lines = [
            f"- Step {s['step']} ({s['name']}): {s['summary']}"
            for s in index["steps"]
            if s["status"] == "completed" and s.get("summary")
        ]
        if not lines:
            return ""
        return "## 이전 Step 산출물\n\n" + "\n".join(lines) + "\n\n"

    def _build_preamble(self, guardrails: str, step_context: str,
                        prev_error: Optional[str] = None) -> str:
        commit_example = self.FEAT_MSG.format(
            phase=self._phase_name, num="N", name="<step-name>"
        )
        retry_section = ""
        if prev_error:
            retry_section = (
                f"\n## ⚠ 이전 시도 실패 — 4단계 디버깅 프로세스를 따라라\n\n"
                f"**이전 에러:**\n{prev_error}\n\n"
                f"- Phase 1 (근본 원인 조사): 증상이 아닌 원인을 찾아라. 에러 메시지를 끝까지 읽어라.\n"
                f"- Phase 2 (패턴 분석): 코드베이스에서 유사하게 작동하는 코드와의 차이를 식별하라.\n"
                f"- Phase 3 (가설 테스트): 한 번에 하나의 변수만 변경하라. 추측성 수정 금지.\n"
                f"- Phase 4 (구현): 근본 원인에 대한 최소 변경만 적용하라.\n\n---\n\n"
            )
        return (
            f"당신은 {self._project} 프로젝트의 개발자입니다. 아래 step을 수행하세요.\n\n"
            f"{guardrails}\n\n---\n\n"
            f"{step_context}{retry_section}"
            f"## 작업 규칙\n\n"
            f"1. 이전 step에서 작성된 코드를 확인하고 일관성을 유지하라.\n"
            f"2. 이 step에 명시된 작업만 수행하라. 추가 기능이나 파일을 만들지 마라.\n"
            f"3. 기존 테스트를 깨뜨리지 마라.\n"
            f"4. AC(Acceptance Criteria) 검증을 직접 실행하라.\n"
            f"5. /phases/{self._phase_dir_name}/index.json의 해당 step status를 업데이트하라:\n"
            f"   - AC 통과 → \"completed\" + \"summary\" 필드에 이 step의 산출물을 한 줄로 요약\n"
            f"   - {self.MAX_RETRIES}회 수정 시도 후에도 실패 → \"error\" + \"error_message\" 기록\n"
            f"   - 사용자 개입이 필요한 경우 (API 키, 인증, 수동 설정 등) → \"blocked\" + \"blocked_reason\" 기록 후 즉시 중단\n"
            f"6. 모든 변경사항을 커밋하라:\n"
            f"   {commit_example}\n"
            f"7. AC 커맨드를 실제로 실행하고 exit 0을 확인한 뒤에만 `completed`로 변경하라.\n"
            f"   'should', 'probably', 'seems to' 표현은 증거가 아니다. 실행 결과만 증거다.\n\n---\n\n"
        )

    # --- Claude 호출 ---

    def _invoke_claude(self, step: dict, preamble: str) -> dict:
        step_num, step_name = step["step"], step["name"]
        step_file = self._phase_dir / f"step{step_num}.md"

        if not step_file.exists():
            print(f"  ERROR: {step_file} not found")
            sys.exit(1)

        prompt = preamble + step_file.read_text()
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", "--output-format", "json", prompt],
            cwd=self._root, capture_output=True, text=True, timeout=1800,
        )

        if result.returncode != 0:
            print(f"\n  WARN: Claude가 비정상 종료됨 (code {result.returncode})")
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}")

        output = {
            "step": step_num, "name": step_name,
            "exitCode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr,
        }
        out_path = self._phase_dir / f"step{step_num}-output.json"
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    # --- 헤더 & 검증 ---

    def _print_header(self):
        print(f"\n{'='*60}")
        print(f"  Harness Step Executor")
        print(f"  Phase: {self._phase_name} | Steps: {self._total}")
        flags = []
        if self._auto_push:
            flags.append("push")
        if self._auto_pr:
            flags.append("PR")
        if self._parallel:
            flags.append("parallel")
        if flags:
            print(f"  Options: {', '.join(flags)}")
        print(f"{'='*60}")

    def _check_blockers(self):
        index = self._read_json(self._index_file)
        for s in reversed(index["steps"]):
            if s["status"] == "error":
                print(f"\n  ✗ Step {s['step']} ({s['name']}) failed.")
                print(f"  Error: {s.get('error_message', 'unknown')}")
                print(f"  Fix and reset status to 'pending' to retry.")
                sys.exit(1)
            if s["status"] == "blocked":
                print(f"\n  ⏸ Step {s['step']} ({s['name']}) blocked.")
                print(f"  Reason: {s.get('blocked_reason', 'unknown')}")
                print(f"  Resolve and reset status to 'pending' to retry.")
                sys.exit(2)
            if s["status"] != "pending":
                break

    def _ensure_created_at(self):
        index = self._read_json(self._index_file)
        if "created_at" not in index:
            index["created_at"] = self._stamp()
            self._write_json(self._index_file, index)

    # --- 순차 실행 ---

    def _execute_single_step(self, step: dict, guardrails: str) -> bool:
        """단일 step 실행 (재시도 포함). 완료되면 True, 실패/차단이면 False."""
        step_num, step_name = step["step"], step["name"]
        done = sum(1 for s in self._read_json(self._index_file)["steps"] if s["status"] == "completed")
        prev_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            index = self._read_json(self._index_file)
            step_context = self._build_step_context(index)
            preamble = self._build_preamble(guardrails, step_context, prev_error)

            tag = f"Step {step_num}/{self._total - 1} ({done} done): {step_name}"
            if attempt > 1:
                tag += f" [retry {attempt}/{self.MAX_RETRIES}]"

            with progress_indicator(tag) as pi:
                self._invoke_claude(step, preamble)
                elapsed = int(pi.elapsed)

            index = self._read_json(self._index_file)
            status = next((s.get("status", "pending") for s in index["steps"] if s["step"] == step_num), "pending")
            ts = self._stamp()

            if status == "completed":
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["completed_at"] = ts
                self._write_json(self._index_file, index)
                self._commit_step(step_num, step_name)
                print(f"  ✓ Step {step_num}: {step_name} [{elapsed}s]")
                return True

            if status == "blocked":
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["blocked_at"] = ts
                self._write_json(self._index_file, index)
                reason = next((s.get("blocked_reason", "") for s in index["steps"] if s["step"] == step_num), "")
                print(f"  ⏸ Step {step_num}: {step_name} blocked [{elapsed}s]")
                print(f"    Reason: {reason}")
                self._update_top_index("blocked")
                sys.exit(2)

            err_msg = next(
                (s.get("error_message", "Step did not update status") for s in index["steps"] if s["step"] == step_num),
                "Step did not update status",
            )

            if attempt < self.MAX_RETRIES:
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["status"] = "pending"
                        s.pop("error_message", None)
                self._write_json(self._index_file, index)
                prev_error = err_msg
                print(f"  ↻ Step {step_num}: retry {attempt}/{self.MAX_RETRIES} — {err_msg}")
            else:
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["status"] = "error"
                        s["error_message"] = f"[{self.MAX_RETRIES}회 시도 후 실패] {err_msg}"
                        s["failed_at"] = ts
                self._write_json(self._index_file, index)
                self._commit_step(step_num, step_name)
                print(f"  ✗ Step {step_num}: {step_name} failed after {self.MAX_RETRIES} attempts [{elapsed}s]")
                print(f"    Error: {err_msg}")
                self._update_top_index("error")
                sys.exit(1)

        return False  # unreachable

    def _execute_all_steps(self, guardrails: str):
        if self._parallel:
            self._execute_all_steps_parallel(guardrails)
        else:
            self._execute_all_steps_sequential(guardrails)

    def _execute_all_steps_sequential(self, guardrails: str):
        while True:
            index = self._read_json(self._index_file)
            pending = next((s for s in index["steps"] if s["status"] == "pending"), None)
            if pending is None:
                print("\n  All steps completed!")
                return

            step_num = pending["step"]
            for s in index["steps"]:
                if s["step"] == step_num and "started_at" not in s:
                    s["started_at"] = self._stamp()
                    self._write_json(self._index_file, index)
                    break

            self._execute_single_step(pending, guardrails)

    # --- 병렬 실행 ---

    def _execute_all_steps_parallel(self, guardrails: str):
        """모든 pending step을 동시에 실행한다."""
        index = self._read_json(self._index_file)
        pending_steps = [s for s in index["steps"] if s["status"] == "pending"]

        if not pending_steps:
            print("\n  All steps completed!")
            return

        print(f"\n  병렬 실행: {len(pending_steps)}개 step 동시 시작")

        ts = self._stamp()
        for step in pending_steps:
            for s in index["steps"]:
                if s["step"] == step["step"] and "started_at" not in s:
                    s["started_at"] = ts
        self._write_json(self._index_file, index)

        self._execute_parallel_group(pending_steps, guardrails)

    def _execute_parallel_group(self, steps: list, guardrails: str):
        """step 목록을 동시에 실행하고 결과를 순서대로 처리한다."""
        lock = threading.Lock()
        results: dict = {}

        def run_one(step):
            step_num = step["step"]
            with lock:
                index = self._read_json(self._index_file)
                step_context = self._build_step_context(index)

            preamble = self._build_preamble(guardrails, step_context)
            parallel_note = (
                f"\n## 병렬 실행 모드\n\n"
                f"이 step은 다른 step들과 동시에 실행됩니다.\n"
                f"- `phases/{self._phase_dir_name}/index.json` 수정 금지\n"
                f"- `git add` / `git commit` 실행 금지\n"
                f"- 작업 완료 후 `phases/{self._phase_dir_name}/step{step_num}-status.json`에 결과를 저장하라:\n"
                f"  - 성공: {{\"status\": \"completed\", \"summary\": \"산출물 한 줄 요약\"}}\n"
                f"  - 실패: {{\"status\": \"error\", \"error_message\": \"구체적 에러\"}}\n"
                f"  - 차단: {{\"status\": \"blocked\", \"blocked_reason\": \"구체적 사유\"}}\n\n---\n\n"
            )

            tag = f"Step {step_num} ({step['name']}) [parallel]"
            with progress_indicator(tag) as pi:
                self._invoke_claude(step, preamble + parallel_note)
            results[step_num] = (step, int(pi.elapsed))

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(steps)) as executor:
            futures = [executor.submit(run_one, s) for s in steps]
            for f in concurrent.futures.as_completed(futures):
                f.result()

        for step_num in sorted(results.keys()):
            step, elapsed = results[step_num]
            self._apply_parallel_result(step, elapsed)

    def _apply_parallel_result(self, step: dict, elapsed: int):
        """병렬 실행 결과를 index.json에 반영하고 커밋한다."""
        step_num = step["step"]
        step_name = step["name"]

        status_file = self._phase_dir / f"step{step_num}-status.json"
        if status_file.exists():
            try:
                result = self._read_json(status_file)
                status = result.get("status", "error")
            except Exception:
                status = "error"
                result = {"status": "error", "error_message": "status.json 파싱 실패"}
        else:
            status = "error"
            result = {"status": "error", "error_message": "status.json 미생성 — Claude가 상태를 기록하지 않음"}

        ts_key = {"completed": "completed_at", "error": "failed_at", "blocked": "blocked_at"}.get(status, "failed_at")
        ts = self._stamp()

        index = self._read_json(self._index_file)
        for s in index["steps"]:
            if s["step"] == step_num:
                s["status"] = status
                s[ts_key] = ts
                if status == "completed":
                    s["summary"] = result.get("summary", "")
                elif status == "error":
                    s["error_message"] = result.get("error_message", "알 수 없는 에러")
                elif status == "blocked":
                    s["blocked_reason"] = result.get("blocked_reason", "알 수 없는 차단 사유")
        self._write_json(self._index_file, index)

        icon = {"completed": "✓", "error": "✗", "blocked": "⏸"}.get(status, "?")
        print(f"  {icon} Step {step_num}: {step_name} [{elapsed}s] — {status}")

        if status == "completed":
            self._commit_step(step_num, step_name)
        elif status in ("error", "blocked"):
            self._update_top_index(status)

    # --- PR 생성 ---

    def _create_pr(self):
        """완료된 phase에 대한 GitHub PR을 생성한다."""
        branch = f"feat-{self._phase_name}"
        index = self._read_json(self._index_file)

        summaries = "\n".join(
            f"- Step {s['step']} ({s['name']}): {s.get('summary', '(요약 없음)')}"
            for s in index["steps"]
            if s.get("status") == "completed"
        )
        body = (
            f"## Phase: {self._phase_name}\n\n"
            f"## 완료된 Steps\n\n{summaries}\n\n"
            f"🤖 Generated with Claude Code Harness"
        )

        r = subprocess.run(
            ["gh", "pr", "create",
             "--title", f"feat({self._phase_name}): {self._phase_name}",
             "--body", body,
             "--head", branch],
            cwd=self._root, capture_output=True, text=True,
        )
        if r.returncode == 0:
            print(f"  ✓ PR 생성: {r.stdout.strip()}")
        else:
            print(f"  WARN: PR 생성 실패: {r.stderr.strip()}")
            if "not found" in r.stderr.lower():
                print(f"  Hint: GitHub CLI 설치: https://cli.github.com")

    # --- 완료 ---

    def _finalize(self):
        index = self._read_json(self._index_file)
        index["completed_at"] = self._stamp()
        self._write_json(self._index_file, index)
        self._update_top_index("completed")

        self._run_git("add", "-A")
        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            msg = f"chore({self._phase_name}): mark phase completed"
            r = self._run_git("commit", "-m", msg)
            if r.returncode == 0:
                print(f"  ✓ {msg}")

        if self._auto_push or self._auto_pr:
            branch = f"feat-{self._phase_name}"
            r = self._run_git("push", "-u", "origin", branch)
            if r.returncode != 0:
                print(f"\n  ERROR: git push 실패: {r.stderr.strip()}")
                sys.exit(1)
            print(f"  ✓ Pushed to origin/{branch}")

        if self._auto_pr:
            self._create_pr()

        print(f"\n{'='*60}")
        print(f"  Phase '{self._phase_name}' completed!")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Harness Step Executor")
    parser.add_argument("phase_dir", help="Phase directory name (e.g. 0-mvp)")
    parser.add_argument("--push", action="store_true", help="Push branch after completion")
    parser.add_argument("--pr", action="store_true", help="Push and create GitHub PR after completion")
    parser.add_argument("--parallel", action="store_true", help="Run all pending steps in parallel")
    args = parser.parse_args()

    StepExecutor(args.phase_dir, auto_push=args.push, auto_pr=args.pr, parallel=args.parallel).run()


if __name__ == "__main__":
    main()
