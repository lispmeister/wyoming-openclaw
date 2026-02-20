#!/usr/bin/env python3
"""Wyoming protocol server for OpenClaw + Home Assistant integration."""

import argparse
import asyncio
import json
import logging
import os
import re
from typing import Optional

import httpx
from wyoming.asr import Transcript
from wyoming.event import Event, async_read_event, async_write_event
from wyoming.info import Attribution, Describe, Info, HandleProgram, HandleModel
from wyoming.handle import Handled, NotHandled

_LOGGER = logging.getLogger(__name__)


class HomeAssistantClient:
    """Simple HA API client for device control."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def call_service(self, domain: str, service: str, entity_id: Optional[str] = None, data: Optional[dict] = None) -> str:
        """Call a Home Assistant service."""
        url = f"{self.url}/api/services/{domain}/{service}"
        payload = {}
        if entity_id:
            payload["entity_id"] = entity_id
        if data:
            payload.update(data)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10.0,
            )

        if response.status_code == 200:
            return f"Done! {service} executed on {entity_id or domain}"
        else:
            raise RuntimeError(f"HA API error: {response.status_code} - {response.text}")

    async def get_state(self, entity_id: str) -> str:
        """Get an entity state."""
        url = f"{self.url}/api/states/{entity_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                timeout=10.0,
            )

        if response.status_code == 200:
            data = response.json()
            state = data.get("state", "unknown")
            friendly_name = data.get("attributes", {}).get("friendly_name", entity_id)
            return f"{friendly_name}: {state}"
        else:
            raise RuntimeError(f"HA API error: {response.status_code}")

    async def get_states(self) -> str:
        """Get all states."""
        url = f"{self.url}/api/states"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                timeout=10.0,
            )

        if response.status_code == 200:
            states = response.json()
            # Return first 20 states as a summary
            lines = []
            for state in states[:20]:
                entity_id = state.get("entity_id", "unknown")
                state_val = state.get("state", "unknown")
                friendly_name = state.get("attributes", {}).get("friendly_name", "")
                if friendly_name and friendly_name != entity_id:
                    lines.append(f"{friendly_name}: {state_val}")
                else:
                    lines.append(f"{entity_id}: {state_val}")
            return "\n".join(lines)
        else:
            raise RuntimeError(f"HA API error: {response.status_code}")


class OpenClawHandler:
    """Handle Wyoming events for OpenClaw + HA."""

    # Patterns for device control commands
    LIGHT_ON_PATTERN = re.compile(r"(?:turn|switch)\s+on\s+(?:the\s+)?(.+?)(?:\s+light)?$", re.IGNORECASE)
    LIGHT_OFF_PATTERN = re.compile(r"(?:turn|switch)\s+off\s+(?:the\s+)?(.+?)(?:\s+light)?$", re.IGNORECASE)
    GET_STATE_PATTERN = re.compile(r"what(?:'s| is)?\s+(?:the\s+)?(?:state|status|of)\s+(?:the\s+)?(.+)", re.IGNORECASE)
    GET_STATES_PATTERN = re.compile(r"(?:what(?:'s| is)\s+(?:on|active|connected)|list|show)\s+(?:all\s+)?(?:states|devices|entities)", re.IGNORECASE)

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        gateway_url: str,
        token: str,
        agent_id: str,
        ha_url: Optional[str] = None,
        ha_token: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token
        self.agent_id = agent_id
        self.session_key = f"voice-{session_id}" if session_id else "voice-default"
        self.ha_client = None
        if ha_url and ha_token:
            self.ha_client = HomeAssistantClient(ha_url, ha_token)
            _LOGGER.info("HA client initialized for direct device control")

    def _extract_entity_id(self, name: str) -> str:
        """Convert a natural language entity name to an entity_id."""
        # Convert "living room light" to "light.living_room"
        # This is a simple implementation - can be enhanced
        name = name.lower().strip()
        name = re.sub(r"[^\w\s]", "", name)  # Remove special chars
        name = re.sub(r"\s+", "_", name)  # Spaces to underscores
        return f"light.{name}" if "light" not in name else f"light.{name.replace('light_', '').replace('light', '')}"

    async def _handle_device_command(self, text: str) -> Optional[str]:
        """Try to handle device control commands directly."""
        if not self.ha_client:
            return None

        text = text.lower().strip()

        # Turn on light - "turn on living room"
        match = self.LIGHT_ON_PATTERN.match(text)
        if match:
            entity = match.group(1).strip() if match.group(1) else ""
            if entity:
                entity_id = f"light.{entity.replace(' ', '_')}"
                try:
                    return await self.ha_client.call_service("light", "turn_on", entity_id)
                except Exception:
                    pass

        # Turn off light - "turn off living room"
        match = self.LIGHT_OFF_PATTERN.match(text)
        if match:
            entity = match.group(1).strip() if match.group(1) else ""
            if entity:
                entity_id = f"light.{entity.replace(' ', '_')}"
                try:
                    return await self.ha_client.call_service("light", "turn_off", entity_id)
                except Exception:
                    pass

        # Get specific entity state - "what's the state of living room"
        match = self.GET_STATE_PATTERN.match(text)
        if match:
            entity = match.group(1).strip() if match.group(1) else ""
            if entity:
                entity_id = entity.replace(" ", "_")
                try:
                    return await self.ha_client.get_state(entity_id)
                except Exception:
                    pass

        # Get all states
        if self.GET_STATES_PATTERN.search(text):
            try:
                return await self.ha_client.get_states()
            except Exception as e:
                return f"Error getting states: {e}"

        return None

    async def handle_event(self, event: Event) -> bool:
        """Handle incoming Wyoming event."""
        _LOGGER.debug("Received event type: %s", event.type)

        if Describe.is_type(event.type):
            info = Info(
                handle=[
                    HandleProgram(
                        name="openclaw",
                        description="OpenClaw AI Assistant + Home Assistant Control",
                        attribution=Attribution(
                            name="OpenClaw",
                            url="https://github.com/openclaw/openclaw",
                        ),
                        installed=True,
                        version="1.0.0",
                        models=[
                            HandleModel(
                                name="openclaw",
                                description="OpenClaw multilingual assistant",
                                attribution=Attribution(
                                    name="OpenClaw",
                                    url="https://github.com/openclaw/openclaw",
                                ),
                                installed=True,
                                version="1.0.0",
                                languages=["en", "ru", "de", "fr", "es", "it", "pt", "nl", "pl", "uk"],
                            )
                        ],
                    )
                ]
            )
            await async_write_event(info.event(), self.writer)
            _LOGGER.debug("Sent info response")
            return True

        if Transcript.is_type(event.type):
            transcript = Transcript.from_event(event)
            _LOGGER.info("Received transcript: %s", transcript.text)

            try:
                # First try direct device control via HA API
                device_response = await self._handle_device_command(transcript.text)
                if device_response:
                    _LOGGER.info("Direct HA response: %s", device_response)
                    handled = Handled(text=device_response)
                    await async_write_event(handled.event(), self.writer)
                    return True

                # Fall back to OpenClaw for general questions
                response_text = await self._call_openclaw(transcript.text)
                _LOGGER.info("OpenClaw response: %s", response_text[:200] if len(response_text) > 200 else response_text)

                handled = Handled(text=response_text)
                _LOGGER.debug("Sending Handled event with text: %s", response_text[:100])
                await async_write_event(handled.event(), self.writer)
                _LOGGER.debug("Sent Handled response to Wyoming client")

            except Exception as e:
                _LOGGER.error("Error: %s", e)
                not_handled = NotHandled(text=f"Error: {e}")
                await async_write_event(not_handled.event(), self.writer)

            return True

        _LOGGER.warning("Unexpected event type: %s", event.type)
        return True

    async def _call_openclaw(self, text: str) -> str:
        """Call OpenClaw via OpenResponses API."""
        url = f"{self.gateway_url}/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "x-openclaw-session-key": self.session_key,
        }

        payload = {
            "model": f"openclaw:{self.agent_id}",
            "input": [{"type": "message", "role": "user", "content": text}],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise RuntimeError(f"OpenClaw API error: {response.status_code} - {response.text}")

            result = response.json()

            if isinstance(result, dict):
                output = result.get("output", [])
                for item in reversed(output):
                    if item.get("type") == "message" and item.get("role") == "assistant":
                        content = item.get("content", [])
                        if isinstance(content, list):
                            for part in content:
                                if part.get("type") == "output_text":
                                    return part.get("text", "")
                                elif part.get("type") == "text":
                                    return part.get("text", "")
                        elif isinstance(content, str):
                            return content
                return str(result)
            return str(result)

    async def run(self) -> None:
        """Run the handler loop."""
        try:
            while True:
                event = await async_read_event(self.reader)
                if event is None:
                    break
                if not await self.handle_event(event):
                    break
        finally:
            self.writer.close()


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Wyoming server for OpenClaw + Home Assistant")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=10400, help="Port to listen on")
    parser.add_argument("--gateway-url", default=os.environ.get("GATEWAY_URL", "http://127.0.0.1:18789"), help="OpenClaw Gateway URL")
    parser.add_argument("--token", default=os.environ.get("GATEWAY_TOKEN"), required=os.environ.get("GATEWAY_TOKEN") is None, help="OpenClaw Gateway auth token")
    parser.add_argument("--agent-id", default="main", help="OpenClaw agent ID")
    parser.add_argument("--ha-url", default=os.environ.get("HA_URL"), help="Home Assistant URL (optional, for direct device control)")
    parser.add_argument("--ha-token", default=os.environ.get("HA_TOKEN"), help="Home Assistant long-lived access token (optional)")
    parser.add_argument("--session-id", default=os.environ.get("SESSION_ID"), help="Session ID for context persistence")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    _LOGGER.info("Starting Wyoming-OpenClaw server on %s:%d", args.host, args.port)
    _LOGGER.info("Gateway URL: %s", args.gateway_url)
    _LOGGER.info("Agent ID: %s", args.agent_id)
    _LOGGER.info("HA URL: %s", args.ha_url or "not configured")
    _LOGGER.info("Session ID: %s", args.session_id or "none")

    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        handler = OpenClawHandler(
            reader,
            writer,
            args.gateway_url,
            args.token,
            args.agent_id,
            args.ha_url,
            args.ha_token,
            args.session_id,
        )
        await handler.run()

    server = await asyncio.start_server(handle_client, args.host, args.port)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
