---
name: call-claude
description: Invoke the authenticated Claude CLI as a low-level external-review adapter from Codex. Use when the user asks to call Claude, send an evidence bundle to Claude, ask Claude for an independent angle, or obtain a Claude CLI review of plans, documents, diffs, evidence bundles, or decisions. For full verdict synthesis or judge-of-judge workflows, use this only as the terminal invocation helper and let the calling workflow make the final decision.
---

# Call Claude

## Overview

Use this skill to call the local authenticated Claude CLI for a bounded external opinion. This is a transport/helper skill: it gets a prompt or evidence bundle to Claude and returns Claude's output. The calling workflow remains responsible for evidence hygiene, tool verification, verdict synthesis, and any judge-of-judge decision.

Claude is especially useful when the question has taste, design, narrative, tone, user empathy, or product judgment at its center. Use Claude for the human-readability and aesthetic side of a decision; use direct tool evidence and Codex's own verification for executable truth.

Read `references/official-claude-cli.md` when updating the invocation method or diagnosing Claude CLI behavior.

## Boundary

Use `call-claude` for terminal invocation only. Do not let it compete with broader decision workflows such as `judge-decision`.

This skill should not decide whether Claude is correct. After it returns Claude's response, the caller should decide what changed, what was unsupported, and what still needs tool verification.

## When To Use Claude

Prefer Claude for:

- UI/UX taste, visual hierarchy, layout polish, interaction feel, and design critique.
- Brand, naming, voice, tone, narrative, messaging, and copy quality.
- Product judgment where the tradeoff is user perception, clarity, motivation, or emotional fit.
- Creative direction, concept selection, pitch polish, story structure, and "does this feel right?" reviews.
- Ambiguous documents, strategy notes, PRDs, and communication where nuance matters.
- A second opinion on code or architecture when the desired value is framing, missed risks, or critique, not deterministic proof.

Do not use Claude as a substitute for direct verification. For deep logic, algorithms, invariants, proof-like reasoning, runtime behavior, or implementation correctness, gather tool evidence first and use Claude only as an external critique layer if it adds value.

## Access Check

Before trying to call Claude, check that the CLI is available:

```bash
which claude
claude --version
```

Do not ask for Anthropic API keys for this workflow. This skill assumes the CLI is installed and already authenticated. If `claude` is not on PATH, say that Claude CLI access is unavailable in the current terminal. Do not simulate Claude's response.

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

For large evidence bundles, prefer `--prompt-file` or piped stdin. The helper can send large prompts to Claude through stdin to avoid brittle command-line argument limits.

## Prompt Shape

Give Claude a compact evidence bundle, not the whole conversation by default.

Include:

- The exact question Claude should judge.
- The current path or decision.
- The strongest known arguments on each side.
- Relevant code, logs, tests, metrics, or constraints.
- For design/taste work: screenshots, target audience, brand constraints, product goal, competing options, and what "good" means.
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
