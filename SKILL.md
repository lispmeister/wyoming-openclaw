---
name: wyoming-openclaw
description: Wyoming Protocol bridge for Home Assistant voice assistant integration with OpenClaw.
---

# Wyoming-OpenClaw

Bridge Home Assistant Assist voice commands to OpenClaw via Wyoming Protocol.

## What it does

- Receives voice commands from Home Assistant Assist
- Forwards them to OpenClaw via the OpenAI-compatible Gateway API
- Returns AI responses to be spoken by Home Assistant TTS

## Setup

1. Enable the OpenAI-compatible API in OpenClaw:
```bash
openclaw config set gateway.http.endpoints.chatCompletions.enabled true
openclaw gateway restart
```

2. Get your gateway token:
```bash
openclaw config get gateway.auth.token
```

3. Clone and run the server:
```bash
git clone https://github.com/lispmeister/wyoming-openclaw.git
cd wyoming-openclaw
docker compose up -d
```

Or manually:
```bash
python wyoming_openclaw.py --port 10600 \
  --gateway-url http://127.0.0.1:18789 \
  --token YOUR_TOKEN \
  --session-id voice-assistant
```

4. Add Wyoming integration in Home Assistant:
   - Settings → Devices & Services → Add Integration
   - Search "Wyoming Protocol"
   - Enter host:port (e.g., `192.168.1.100:10600`)

5. Configure Voice Assistant pipeline to use "openclaw" as Conversation Agent

## Requirements

- OpenClaw gateway running with OpenAI API enabled
- Home Assistant with Wyoming integration
- Docker (recommended) or Python 3.11+

## Environment Variables (Docker)

| Variable | Description | Default |
|----------|-------------|---------|
| `GATEWAY_URL` | OpenClaw Gateway URL | `http://127.0.0.1:18789` |
| `GATEWAY_TOKEN` | OpenClaw Gateway auth token | (required) |

## Links

- GitHub: https://github.com/lispmeister/wyoming-openclaw
- OpenClaw: https://github.com/openclaw/openclaw
