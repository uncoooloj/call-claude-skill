---
name: call-claude
description: Invoke the authenticated Claude CLI as an external reviewer, judge, critic, second-opinion model, or cross-model evaluator from Codex. Use when the user asks to call Claude in the terminal, ask Claude for an independent angle, use Claude as a judge, compare Codex and Claude opinions, run a judge-of-judge workflow, or obtain a Claude CLI review of code, algorithms, plans, documents, diffs, evidence bundles, or decisions.
---

# Call Claude

## Overview

Use this skill to call the local authenticated Claude CLI for a bounded external opinion while Codex remains responsible for evidence hygiene, tool verification, and the final decision. Prefer this when Claude's different model behavior may reveal an alternate framing, missed risk, stronger critique, or second-opinion judgment.

Read `references/official-claude-cli.md` when updating the invocation method or diagnosing Claude CLI behavior.

## Access Check

Before trying to call Claude, check that the CLI is available:

```bash
which claude
claude auth status --text
```

Do not ask for Anthropic API keys for this workflow. This skill assumes the CLI is installed and already authenticated. If `claude` is not on PATH, say that Claude CLI access is unavailable in the current terminal and continue only if the user accepts a simulated external-review pass.

## Calling Claude

Use `scripts/call_claude.py` from this skill directory. It wraps `claude -p` so prompts can come from an argument, a file, or stdin.

Examples:

```bash
python3 scripts/call_claude.py --prompt "Review this algorithm choice and return only risks, alternatives, and a verdict."
```

```bash
python3 scripts/call_claude.py --prompt-file /path/to/evidence.md --system "You are an external judge. Be skeptical, concrete, and concise." --max-turns 1
```

```bash
git diff main | python3 scripts/call_claude.py --system "You are a code reviewer. Focus on correctness and missed edge cases."
```

When running inside a sandbox, request escalation if the Claude CLI call fails due network, authentication, or terminal-boundary restrictions.

## Prompt Shape

Give Claude a compact evidence bundle, not the whole conversation by default.

Include:

- The exact question Claude should judge.
- The current path or decision.
- The strongest known arguments on each side.
- Relevant code, logs, tests, metrics, or constraints.
- The requested output format.

Do not include:

- Secrets, bearer tokens, private keys, or unnecessary credentials.
- Unbounded chat history.
- The desired answer disguised as context.

## Recommended Output Contract

Ask Claude to return:

```markdown
**Claude Verdict**
<keep / modify / replace / investigate>

**Why**
<short evidence-based reasoning>

**Strongest Missed Risk**
<risk or "none">

**Best Alternative**
<concrete alternative or "none">

**Confidence**
<low / medium / high, plus why>
```

## Codex Responsibilities

Treat Claude as an external reviewer, not the final authority. After Claude responds:

- Check whether Claude used the supplied evidence correctly.
- Separate new useful insight from generic critique.
- Verify testable claims with tools when feasible.
- Identify any assumption Claude imported that was not in evidence.
- Produce the final Codex decision or pass Claude's opinion into a judge-of-judge workflow.
