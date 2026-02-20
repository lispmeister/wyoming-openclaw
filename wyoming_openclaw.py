#!/usr/bin/env python3
"""Wyoming protocol server for OpenClaw integration."""

import argparse
import asyncio
import json
import logging
import os
from typing import Optional

import httpx
from wyoming.asr import Transcript
from wyoming.event import Event, async_read_event, async_write_event
from wyoming.info import Attribution, Describe, Info, HandleProgram, HandleModel
from wyoming.handle import Handled, NotHandled

_LOGGER = logging.getLogger(__name__)


class OpenClawHandler:
    """Handle Wyoming events for OpenClaw."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        gateway_url: str,
        token: str,
        agent_id: str,
        session_id: Optional[str] = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token
        self.agent_id = agent_id
        self.session_id = session_id

    async def handle_event(self, event: Event) -> bool:
        """Handle incoming Wyoming event."""
        _LOGGER.debug("Received event type: %s", event.type)

        if Describe.is_type(event.type):
            # Return service info - expose as handle (conversation) service
            info = Info(
                handle=[
                    HandleProgram(
                        name="openclaw",
                        description="OpenClaw AI Assistant",
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

        # Handle Transcript events from Home Assistant
        if Transcript.is_type(event.type):
            transcript = Transcript.from_event(event)
            _LOGGER.info("Received transcript: %s", transcript.text)

            try:
                # Call OpenClaw agent
                response_text = await self._call_openclaw(transcript.text)
                _LOGGER.info("OpenClaw response: %s", response_text)

                # Return handled response
                handled = Handled(text=response_text)
                await async_write_event(handled.event(), self.writer)

            except Exception as e:
                _LOGGER.error("Error calling OpenClaw: %s", e)
                not_handled = NotHandled(text=f"Error: {e}")
                await async_write_event(not_handled.event(), self.writer)

            return True

        _LOGGER.warning("Unexpected event type: %s", event.type)
        return True

    async def _call_openclaw(self, text: str) -> str:
        """Call OpenClaw via OpenAI-compatible API and return response."""
        url = f"{self.gateway_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": f"openclaw:{self.agent_id}",
            "messages": [{"role": "user", "content": text}],
            "stream": False,
        }

        # Include session_id if provided for context persistence
        if self.session_id:
            payload["user"] = self.session_id

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

            # Extract the assistant's reply from OpenAI-compatible response
            choices = result.get("choices", [])
            if not choices:
                raise RuntimeError("No choices in OpenClaw response")

            message = choices[0].get("message", {})
            content = message.get("content")

            if not content:
                raise RuntimeError("No content in OpenClaw response")

            return content

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
    parser = argparse.ArgumentParser(description="Wyoming server for OpenClaw")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=10400, help="Port to listen on")
    parser.add_argument("--gateway-url", default=os.environ.get("GATEWAY_URL", "http://127.0.0.1:18789"), help="OpenClaw Gateway URL")
    parser.add_argument("--token", default=os.environ.get("GATEWAY_TOKEN"), required=os.environ.get("GATEWAY_TOKEN") is None, help="OpenClaw Gateway auth token")
    parser.add_argument("--agent-id", default="main", help="OpenClaw agent ID")
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
    _LOGGER.info("Session ID: %s", args.session_id or "none (stateless)")

    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        handler = OpenClawHandler(
            reader,
            writer,
            args.gateway_url,
            args.token,
            args.agent_id,
            args.session_id,
        )
        await handler.run()

    server = await asyncio.start_server(handle_client, args.host, args.port)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
