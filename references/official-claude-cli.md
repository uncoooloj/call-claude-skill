# Official Claude CLI Notes

Sources checked on 2026-06-02:

- Claude Code CLI reference: https://code.claude.com/docs/en/cli-usage
- Claude Code programmatic/headless usage: https://code.claude.com/docs/en/headless

## Non-Interactive Calls

The Claude Code CLI supports non-interactive calls with:

```bash
claude -p "query"
```

It can also process piped input:

```bash
cat file.txt | claude -p "summarize this"
```

Useful flags from the official CLI docs:

- `--print` / `-p`: print a response without interactive mode.
- `--output-format text|json|stream-json`: choose output format in print mode.
- `--model`: choose a model or alias.
- `--max-turns`: cap agentic turns in print mode.
- `--append-system-prompt`: add system prompt text.

Use normal print mode by default because this workflow assumes the local CLI is already installed and authenticated. Use `--bare` only when the caller explicitly wants reproducible scripted behavior that skips local hooks, skills, plugins, and MCP auto-discovery.

## Local Wrapper Notes

Some desktop environments put a wrapper named `claude` on PATH. For example, a cmux wrapper may inject hooks and then search PATH for the real Claude binary while skipping its own directory. If no real binary exists later on PATH, the wrapper can print `Error: claude not found in PATH` even though `which claude` succeeds.

Use the skill helper's resolver instead of trusting `which`:

```bash
python3 scripts/call_claude.py --diagnose
```

If the authenticated CLI needs to write to `~/.claude`, `~/.claude.json`, or other user-home config files, Codex sandboxed runs may need escalation for the real call.
