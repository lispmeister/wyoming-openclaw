# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wyoming-OpenClaw is a Wyoming Protocol server that bridges Home Assistant Assist voice pipeline to OpenClaw. Voice commands flow through: HA STT → Wyoming-OpenClaw (port 10600) → OpenClaw Gateway `/v1/responses` API → TTS.

Single-file Python project: `wyoming_openclaw.py` (~360 lines).

## Development Commands

```bash
# Run locally
python wyoming_openclaw.py --port 10600 \
  --gateway-url http://127.0.0.1:18789 \
  --token $GATEWAY_TOKEN \
  --session-id voice-assistant \
  --debug

# Docker (standalone, joins existing OpenClaw network)
docker compose up -d --build

# Docker (full stack with OpenClaw gateway)
cd openclaw-orchestration && docker compose up -d

# Check logs
docker logs wyoming-openclaw -f
```

No test suite exists. No linter configured. Dependencies: `wyoming>=1.5.0`, `httpx>=0.25.0`.

## Architecture

**`HomeAssistantClient`** — REST client for HA API. Handles `call_service`, `get_state`, `get_states`.

**`OpenClawHandler`** — Wyoming event handler with two response paths:
1. **Direct HA control**: regex-matched commands (light on/off, state queries) go straight to HA REST API, bypassing OpenClaw entirely.
2. **OpenClaw fallback**: everything else goes to the gateway's OpenAI-compatible `/v1/responses` endpoint with persistent session via `x-openclaw-session-key` header.

The server uses raw `asyncio.start_server` (not the Wyoming base server classes) — each client connection gets its own `OpenClawHandler` instance.

## Deployment

Two Docker compose setups:
- `docker-compose.yml` — standalone, attaches to existing `openclaw-fix_default` network
- `openclaw-orchestration/docker-compose.yml` — full stack (gateway + wyoming + cli)

Config via env vars: `GATEWAY_URL`, `GATEWAY_TOKEN`, `SESSION_ID`, `HA_URL`, `HA_TOKEN`.

## Editing Files

**NEVER edit a file you haven't read with `hashline read` in this conversation.**
For all code edits, use the hashline CLI via Bash instead of the built-in Edit tool.
For creating new files, use the Write tool. For deleting files, use `rm`.

### Reading

```bash
hashline read src/main.rs
```

Returns:
```
1:a3|use std::io;
2:05|
3:7f|fn main() {
4:01|    println!("hello");
5:0e|}
```

Each line has a `LINE:HASH` anchor. Use these anchors — not line numbers alone — in edits.

**Partial read** (after editing, verify just the changed region):
```bash
hashline read --start-line 10 --lines 20 src/main.rs
```

### Editing

Always use a heredoc to pipe JSON. Batch all changes to a file into one `edits` array — edits are atomic (all succeed or none apply):

```bash
cat << 'EOF' | hashline apply
{
  "path": "src/main.rs",
  "edits": [
    {"set_line": {"anchor": "4:01", "new_text": "    println!(\"goodbye\");"}},
    {"insert_after": {"anchor": "5:0e", "text": "fn helper() {\n    todo!()\n}"}}
  ]
}
EOF
```

### Operations

**`set_line`** — replace one line:
```json
{"set_line": {"anchor": "4:01", "new_text": "    println!(\"goodbye\");"}}
```

**`replace_lines`** — replace a range (use `"new_text": ""` to delete):
```json
{"replace_lines": {"start_anchor": "3:7f", "end_anchor": "5:0e", "new_text": "fn main() {}"}}
```

**`insert_after`** — insert lines after an anchor:
```json
{"insert_after": {"anchor": "2:05", "text": "use std::fs;"}}
```

**`replace`** — exact substring replacement, no anchor needed (use when anchor ops are awkward, e.g. replacing a unique multi-line block). Runs after all anchor edits. Errors if text is not found or matches multiple locations:
```json
{"replace": {"old_text": "old string", "new_text": "new string"}}
```

Use `\n` in strings for multi-line content.

### Exit Codes

- **0** — success
- **1** — hash mismatch (file changed since last read); stderr has updated anchors — copy them and retry
- **2** — other error (bad JSON, file not found, etc.); do not retry without fixing the input

### Error Recovery

On hash mismatch, stderr shows the current file state with `>>>` marking changed lines:

```
1 line has changed since last read. Use the updated LINE:HASH references shown below (>>> marks changed lines).

    3:7f|fn main() {
>>> 4:c9|    println!("changed");
    5:0e|}
```

Copy the updated anchor (`4:c9`) into your edit and retry. Do not re-read the whole file — just update the anchor.

### Rules

- Re-read a file before editing it again (hashes change after every apply)
- Batch all edits to one file into a single apply call
- Prefer anchor ops (`set_line`, `replace_lines`, `insert_after`) over `replace` — they are safer and more precise
- Never guess a hash — always read first
