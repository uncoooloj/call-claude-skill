#!/usr/bin/env python3
"""Call the authenticated Claude CLI in non-interactive print mode."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def read_prompt(args: argparse.Namespace) -> str:
    parts: list[str] = []
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
    parser.add_argument("--max-turns", type=int, default=1, help="Maximum Claude CLI turns in print mode.")
    parser.add_argument("--output-format", choices=["text", "json", "stream-json"], default="text", help="Claude print-mode output format.")
    parser.add_argument("--bare", action="store_true", help="Use Claude CLI bare mode.")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds.")
    parser.add_argument("--stdin-threshold", type=int, default=8000, help="Send prompts longer than this many characters over stdin.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    claude = shutil.which("claude")
    if not claude:
        sys.stderr.write("Claude CLI not found on PATH.\n")
        return 127

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

    result = subprocess.run(
        cmd,
        check=False,
        text=True,
        input=prompt if use_stdin_prompt else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or f"claude exited with {result.returncode}\n")
        return result.returncode

    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
