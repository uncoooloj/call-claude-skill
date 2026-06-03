# Call Claude

A Codex skill for calling an authenticated local Claude CLI as a bounded external reviewer, critic, or judge.

Codex remains responsible for evidence hygiene and the final decision. Claude is used as a second opinion: useful for alternate framing, missed risks, critique, taste, design judgment, writing quality, product nuance, or judge-of-judge workflows.

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

- Claude CLI installed and available as `claude`
- Claude CLI already authenticated locally
- Python 3 for `scripts/call_claude.py`

This workflow does not require Anthropic API keys in Codex.

## Files

- `SKILL.md` - the skill instructions and output contract
- `agents/openai.yaml` - Codex UI metadata
- `references/official-claude-cli.md` - CLI usage notes
- `scripts/call_claude.py` - wrapper for non-interactive `claude -p` calls

## License

No license has been selected yet.
