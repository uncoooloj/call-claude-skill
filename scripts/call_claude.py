#!/usr/bin/env python3
"""Call the authenticated Claude CLI in non-interactive print mode."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple


KNOWN_CLAUDE_CANDIDATES = (
    "/Applications/Conductor.app/Contents/Resources/bin/claude",
    "/Applications/cmux.app/Contents/Resources/bin/claude",
)


def read_prompt(args: argparse.Namespace) -> str:
    parts: List[str] = []
    if args.prompt:
        parts.append(args.prompt)
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as handle:
            parts.append(handle.read())
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
        if stdin_text.strip():
            parts.append(stdin_text)
    prompt = "\n\n".join(part.strip() for part in parts if part.strip())
    if not prompt:
        raise SystemExit("No prompt supplied. Use --prompt, --prompt-file, or pipe stdin.")
    return prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call Claude CLI via `claude -p`.")
    parser.add_argument("--prompt", help="Prompt text to send to Claude.")
    parser.add_argument("--prompt-file", help="Path to a UTF-8 text prompt/evidence file.")
    parser.add_argument("--system", help="System prompt or role instruction.")
    parser.add_argument("--model", help="Claude CLI model or alias.")
    parser.add_argument("--claude-bin", help="Path to a specific Claude CLI binary.")
    parser.add_argument("--diagnose", action="store_true", help="Only resolve and validate the Claude CLI, then print diagnostics.")
    parser.add_argument("--max-turns", type=int, default=1, help="Maximum Claude CLI turns in print mode.")
    parser.add_argument("--output-format", choices=["text", "json", "stream-json"], default="text", help="Claude print-mode output format.")
    parser.add_argument("--bare", action="store_true", help="Use Claude CLI bare mode.")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds.")
    parser.add_argument("--stdin-threshold", type=int, default=8000, help="Send prompts longer than this many characters over stdin.")
    return parser.parse_args()


def path_candidates(executable: str = "claude") -> List[str]:
    candidates: List[str] = []
    seen: Set[str] = set()

    def add(candidate: Optional[str]) -> None:
        if not candidate:
            return
        expanded = str(Path(candidate).expanduser())
        if expanded in seen:
            return
        seen.add(expanded)
        candidates.append(expanded)

    for key in ("CLAUDE_BIN", "CLAUDE_PATH", "CMUX_CUSTOM_CLAUDE_PATH"):
        add(os.environ.get(key))

    path = os.environ.get("PATH", "")
    for directory in path.split(os.pathsep):
        if directory:
            candidate = Path(directory) / executable
            if candidate.exists():
                add(str(candidate))

    if os.environ.get("CALL_CLAUDE_DISABLE_KNOWN_PATHS") != "1":
        for candidate in KNOWN_CLAUDE_CANDIDATES:
            if Path(candidate).expanduser().exists():
                add(candidate)

    return candidates


def validate_claude(candidate: str, timeout: int = 10) -> Tuple[bool, str]:
    path = Path(candidate).expanduser()
    if not path.exists():
        return False, "not found"
    if not os.access(path, os.X_OK):
        return False, "not executable"
    try:
        result = subprocess.run(
            [str(path), "--version"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "version check timed out"
    except OSError as exc:
        return False, f"cannot execute: {exc}"

    output = (result.stdout or result.stderr or "").strip()
    if result.returncode == 0:
        return True, output or "version check passed"
    detail = output or f"exited with {result.returncode}"
    return False, detail


def resolve_claude(args: argparse.Namespace) -> Tuple[Optional[str], List[Tuple[str, bool, str]]]:
    candidates: List[str] = []
    if args.claude_bin:
        candidates.append(str(Path(args.claude_bin).expanduser()))
    candidates.extend(path_candidates())

    diagnostics: List[Tuple[str, bool, str]] = []
    seen: Set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        ok, detail = validate_claude(candidate)
        diagnostics.append((candidate, ok, detail))
        if ok:
            return candidate, diagnostics
    return None, diagnostics


def print_diagnostics(diagnostics: List[Tuple[str, bool, str]]) -> None:
    if not diagnostics:
        sys.stderr.write("No Claude CLI candidates found.\n")
        return
    sys.stderr.write("Claude CLI candidates checked:\n")
    for candidate, ok, detail in diagnostics:
        marker = "OK" if ok else "NO"
        sys.stderr.write(f"- {marker} {candidate}: {detail}\n")


def add_failure_hint(message: str) -> str:
    hints: List[str] = []
    if "not found in PATH" in message:
        hints.append("The first `claude` on PATH appears to be a wrapper that cannot find a real Claude binary.")
    if "native binary not installed" in message or "Could not find native binary package" in message:
        hints.append("Claude Code's npm optional native package is missing or incomplete; reinstall Claude Code without --ignore-scripts or --omit=optional.")
    if "EPERM" in message and ("/Users/" in message or "~/.claude" in message or ".claude" in message):
        hints.append("Claude tried to write to the user home config directory. In Codex sandboxed runs, rerun with escalation so the authenticated CLI can access ~/.claude and ~/.claude.json.")
    if hints:
        return message.rstrip() + "\n\n" + "\n".join(f"Hint: {hint}" for hint in hints) + "\n"
    return message


def output_text(value: object) -> str:
    if not value:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def main() -> int:
    args = parse_args()
    claude, diagnostics = resolve_claude(args)
    if not claude:
        print_diagnostics(diagnostics)
        sys.stderr.write("No usable Claude CLI was found.\n")
        return 127
    if args.diagnose:
        print_diagnostics(diagnostics)
        sys.stdout.write(f"{claude}\n")
        return 0

    prompt = read_prompt(args)
    use_stdin_prompt = len(prompt) > args.stdin_threshold

    cmd = [claude]
    if args.bare:
        cmd.append("--bare")
    if use_stdin_prompt:
        cmd.extend(["-p", "Use the complete prompt provided on stdin.", "--output-format", args.output_format, "--max-turns", str(args.max_turns)])
    else:
        cmd.extend(["-p", prompt, "--output-format", args.output_format, "--max-turns", str(args.max_turns)])
    if args.model:
        cmd.extend(["--model", args.model])
    if args.system:
        cmd.extend(["--append-system-prompt", args.system])

    try:
        result = subprocess.run(
            cmd,
            check=False,
            text=True,
            input=prompt if use_stdin_prompt else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = output_text(exc.stderr)
        stdout = output_text(exc.stdout)
        combined = "\n".join(part for part in (stderr, stdout) if part)
        if combined:
            sys.stderr.write(add_failure_hint(combined))
        sys.stderr.write(f"claude timed out after {args.timeout} seconds\n")
        return 124
    if result.returncode != 0:
        sys.stderr.write(add_failure_hint(result.stderr or f"claude exited with {result.returncode}\n"))
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
