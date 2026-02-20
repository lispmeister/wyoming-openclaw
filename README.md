# Wyoming-OpenClaw

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Wyoming Protocol server that bridges [Home Assistant Assist](https://www.home-assistant.io/voice_control/) to [OpenClaw](https://github.com/openclaw/openclaw) — enabling voice control of your AI assistant.

## Features

- 🎤 Voice commands through Home Assistant Assist
- 🤖 Powered by OpenClaw AI (Claude, GPT, etc.)
- 🏠 Full Home Assistant integration
- 🌍 Multilingual support (English, Russian, German, French, and more)
- 💬 Persistent conversation context

## How It Works

```
Voice → Home Assistant → STT → Wyoming-OpenClaw → OpenClaw Gateway API → Response → TTS → Speaker
```

1. You speak to your Home Assistant voice satellite (ESPHome, etc.)
2. Speech-to-Text converts your voice to text
3. Wyoming-OpenClaw sends the text to OpenClaw via the OpenAI-compatible API
4. OpenClaw processes and returns a response
5. Text-to-Speech speaks the response

## Requirements

- [OpenClaw](https://github.com/openclaw/openclaw) gateway running with OpenAI API enabled
- Home Assistant with Wyoming integration
- Python 3.11+ (or Docker)

## Installation

### Docker Compose (recommended)

```bash
git clone https://github.com/lispmeister/wyoming-openclaw.git
cd wyoming-openclaw
docker-compose up -d
```

### Manual

```bash
# Clone the repository
git clone https://github.com/lispmeister/wyoming-openclaw.git
cd wyoming-openclaw

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## OpenClaw Gateway Configuration

Ensure your OpenClaw gateway has the OpenAI-compatible API enabled:

```json
{
  "gateway": {
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true }
      }
    }
  }
}
```

Get your gateway token:

```bash
openclaw config get gateway.auth.token
```

## Usage

### Basic

```bash
python wyoming_openclaw.py --port 10600 \
  --gateway-url http://127.0.0.1:18789 \
  --token YOUR_GATEWAY_TOKEN
```

### With persistent session (recommended)

```bash
python wyoming_openclaw.py --port 10600 \
  --gateway-url http://127.0.0.1:18789 \
  --token YOUR_GATEWAY_TOKEN \
  --session-id voice-assistant \
  --agent-id main
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Host to bind to | `0.0.0.0` |
| `--port` | Port to listen on | `10400` |
| `--gateway-url` | OpenClaw Gateway URL | `http://127.0.0.1:18789` |
| `--token` | OpenClaw Gateway auth token | (required) |
| `--agent-id` | OpenClaw agent ID | `main` |
| `--session-id` | Session ID for context persistence | none (stateless) |
| `--debug` | Enable debug logging | false |

## Systemd Service

Create `/etc/systemd/system/wyoming-openclaw.service`:

```ini
[Unit]
Description=Wyoming OpenClaw Bridge
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/wyoming-openclaw
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/path/to/wyoming-openclaw/venv/bin/python wyoming_openclaw.py \
  --port 10600 \
  --gateway-url http://127.0.0.1:18789 \
  --token YOUR_GATEWAY_TOKEN \
  --session-id voice-assistant
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable wyoming-openclaw
sudo systemctl start wyoming-openclaw
```

## Home Assistant Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Wyoming Protocol**
3. Enter the host and port (e.g., `192.168.1.100:10600`)
4. The "openclaw" conversation agent will appear
5. Configure your Voice Assistant pipeline to use "openclaw" as the Conversation Agent

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [OpenClaw](https://github.com/openclaw/openclaw) - AI assistant platform
- [Wyoming Protocol](https://github.com/rhasspy/wyoming) - Voice assistant protocol
- [Home Assistant](https://www.home-assistant.io/) - Home automation platform
