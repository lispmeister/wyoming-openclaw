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
- Docker and Docker Compose (recommended)

## Quick Start

### 1. Get your gateway token

```bash
openclaw config get gateway.auth.token
```

### 2. Create a .env file

```bash
cd wyoming-openclaw
echo "GATEWAY_TOKEN=your_token_here" > .env
```

### 3. Run the container

```bash
docker compose up -d --build
```

### 4. Configure Home Assistant

1. Settings → Devices & Services → Add Integration
2. Search "Wyoming Protocol"
3. Enter your server IP and port 10600 (e.g., `192.168.1.100:10600`)
4. Select "openclaw" as the conversation agent
5. Configure your voice assistant to use "openclaw"

## Docker Deployment

### Standalone

Run wyoming-openclaw as a separate container on the same Docker network as your gateway:

```bash
cd wyoming-openclaw
docker compose up -d
```

### With OpenClaw Gateway (Orchestration)

To run both services together, use the orchestration compose file:

```bash
cd wyoming-openclaw/openclaw-orchestration
docker compose up -d
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GATEWAY_URL` | OpenClaw Gateway URL | `http://openclaw-gateway:18789` |
| `GATEWAY_TOKEN` | OpenClaw Gateway auth token | (required) |
| `SESSION_ID` | Session ID for context persistence | `voice-assistant` |

## Docker Network Setup

wyoming-openclaw must be on the same Docker network as your OpenClaw gateway for DNS resolution.

### Step 1: Find the gateway's network

```bash
# List all Docker containers
docker ps | grep openclaw

# Find which network the gateway is on
docker inspect <gateway-container-name> | grep -A5 Networks
```

Example output:
```
"Networks": {
    "openclaw-fix_default": {
        "IPAMConfig": null,
        "Links": null,
        "Aliases": ["openclaw-fix-openclaw-gateway-1"],
```

### Step 2: Update docker-compose.yml

Edit `docker-compose.yml` to use the gateway's network:

```yaml
services:
  wyoming-openclaw:
    ...
    networks:
      - openclaw-fix_default  # Use the network name from Step 1

networks:
  openclaw-fix_default:
    external: true
```

### Step 3: Run the container

```bash
docker compose up -d --build
```

### Troubleshooting DNS

If you see `Name or service not known` errors:

1. Check both containers are on the same network:
   ```bash
   docker network inspect <network-name> --format '{{range .Containers}}Name: {{.Name}}{{println}}{{end}}'
   ```

2. Use the gateway's IP address instead of hostname:
   ```bash
   GATEWAY_URL=http://<gateway-ip>:18789 docker compose up -d
   ```

3. Or reconnect the container to the correct network:
   ```bash
   docker network connect <network-name> wyoming-openclaw
   ```

## Manual Installation

### Prerequisites

- Python 3.11+
- OpenClaw gateway running with OpenAI API enabled

### Setup

```bash
git clone https://github.com/lispmeister/wyoming-openclaw.git
cd wyoming-openclaw

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python wyoming_openclaw.py --port 10600 \
  --gateway-url http://127.0.0.1:18789 \
  --token YOUR_GATEWAY_TOKEN \
  --session-id voice-assistant
```

### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Host to bind to | `0.0.0.0` |
| `--port` | Port to listen on | `10400` |
| `--gateway-url` | OpenClaw Gateway URL | `http://127.0.0.1:18789` |
| `--token` | OpenClaw Gateway auth token | (required) |
| `--agent-id` | OpenClaw agent ID | `main` |
| `--session-id` | Session ID for context persistence | none (stateless) |
| `--debug` | Enable debug logging | false |

## OpenClaw Gateway Configuration

Enable the OpenAI-compatible API in your OpenClaw config:

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

## Troubleshooting

### DNS resolution fails

If you see `Name or service not known` when connecting to the gateway:

1. Ensure both containers are on the same Docker network
2. Use the gateway's container name or IP address in `GATEWAY_URL`
3. Check networks: `docker network inspect <network-name>`

### Port not accessible

If Home Assistant can't reach the service:

1. Verify port 10600 is open on the host firewall:
   ```bash
   sudo ufw allow proto tcp from 192.168.1.0/24 to any port 10600
   ```
2. Check the container is listening: `docker logs wyoming-openclaw`

### No response from gateway

Check the logs for errors:

```bash
docker logs wyoming-openclaw -f
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [OpenClaw](https://github.com/openclaw/openclaw) - AI assistant platform
- [Wyoming Protocol](https://github.com/rhasspy/wyoming) - Voice assistant protocol
- [Home Assistant](https://www.home-assistant.io/) - Home automation platform
