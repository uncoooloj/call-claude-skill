# Call Claude

A Codex skill for calling an authenticated local Claude CLI as a bounded external-review helper.

This skill is the adapter layer. It gets a prompt or evidence bundle to Claude and returns Claude's output. The calling workflow remains responsible for evidence hygiene, verdict synthesis, and any judge-of-judge decision.

Use Claude especially for:

- UI/UX taste and design critique
- brand, naming, voice, tone, narrative, and copy
- product judgment where user perception matters
- creative direction and ambiguous human-preference decisions

For deep logic, algorithms, invariants, runtime behavior, and implementation correctness, verify with tools first; Claude can still critique, but should not replace evidence.

## Install

Copy this folder into your Codex skills directory:

```bash
cp -R call-claude ~/.codex/skills/call-claude
```

Then invoke it in Codex with:

```text
Use $call-claude to ask Claude for an independent review of this design, product judgment, or evidence bundle.
```

## Requirements

- Claude CLI installed and available through PATH, `CLAUDE_BIN`, `--claude-bin`, or a supported app bundle location
- Claude CLI already authenticated locally
- Python 3 for `scripts/call_claude.py`

This workflow does not require Anthropic API keys in Codex.

Check resolution before a real call:

```bash
python3 scripts/call_claude.py --diagnose
```

The helper validates candidate binaries with `--version` and skips broken wrappers before invoking Claude. This keeps wrapper-only setups, partial npm installs, and missing optional native packages from failing with a vague `claude not found`.

For large evidence bundles, pass a file with `--prompt-file` or pipe content into `scripts/call_claude.py`; the helper will switch large prompts to stdin to avoid command-line argument limits.

## Files

- `SKILL.md` - the skill instructions and output contract
- `agents/openai.yaml` - Codex UI metadata
- `references/official-claude-cli.md` - CLI usage notes
- `scripts/call_claude.py` - wrapper for non-interactive `claude -p` calls
- `scripts/test_call_claude.py` - resolver and invocation tests with fake Claude binaries

## License

No license has been selected yet.
