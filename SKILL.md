---
name: wyoming-clawdbot
description: Manage Wyoming-Clawdbot bridge service for Home Assistant voice control integration.
homepage: https://github.com/vglafirov/wyoming-clawdbot
metadata: {"clawdbot":{"emoji":"🎤","requires":{"bins":["systemctl"]}}}
---

# Wyoming-Clawdbot

Wyoming Protocol bridge connecting Home Assistant Assist to Clawdbot for voice control.

## Architecture

```
Voice → Home Assistant → STT → Wyoming-Clawdbot → Clawdbot → TTS → Speaker
```

## Service Management

Check status:
```bash
systemctl status wyoming-clawdbot
```

Start/stop/restart:
```bash
sudo systemctl start wyoming-clawdbot
sudo systemctl stop wyoming-clawdbot
sudo systemctl restart wyoming-clawdbot
```

Enable on boot:
```bash
sudo systemctl enable wyoming-clawdbot
```

## Logs

View recent logs:
```bash
journalctl -u wyoming-clawdbot -n 50 --no-pager
```

Follow logs in real-time:
```bash
journalctl -u wyoming-clawdbot -f
```

## Docker (alternative)

If running via Docker:
```bash
docker-compose -f /path/to/wyoming-clawdbot/docker-compose.yml logs -f
docker-compose -f /path/to/wyoming-clawdbot/docker-compose.yml restart
```

## Configuration

Default port: `10400` (commonly changed to `10600`)

Options:
- `--host` — bind address (default: 0.0.0.0)
- `--port` — listening port
- `--session-id` — persistent session ID for conversation context
- `--agent` — Clawdbot agent ID
- `--debug` — verbose logging

## Home Assistant Setup

1. Settings → Devices & Services → Add Integration
2. Search "Wyoming Protocol"
3. Enter host:port (e.g., `192.168.1.100:10600`)
4. Set "clawdbot" as Conversation Agent in Voice Assistant pipeline

## Troubleshooting

**Service won't start:**
```bash
journalctl -u wyoming-clawdbot -n 100 --no-pager
```

**Connection refused in Home Assistant:**
- Check service is running: `systemctl is-active wyoming-clawdbot`
- Verify port is open: `ss -tlnp | grep 10600`
- Check firewall: `sudo ufw status`

**No response from Clawdbot:**
- Verify Clawdbot is running: `clawdbot status`
- Check session exists: `clawdbot sessions list`

## Links

- GitHub: https://github.com/vglafirov/wyoming-clawdbot
- Clawdbot: https://clawd.bot
- Wyoming Protocol: https://github.com/rhasspy/wyoming
