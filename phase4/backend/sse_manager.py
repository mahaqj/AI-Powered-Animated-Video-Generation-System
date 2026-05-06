"""
SSE Manager: per-run Server-Sent Events channels.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

logger = logging.getLogger("phase4.sse_manager")


class SSEChannel:
    """A per-run async queue that streams SSE-formatted strings."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self._closed = False

    async def publish(self, event: str, data: dict) -> None:
        """Format and enqueue an SSE message."""
        message = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        await self.queue.put((event, message))
        logger.debug(f"[SSE:{self.run_id}] Published event={event}")

    async def stream(self) -> AsyncGenerator[str, None]:
        """Yield SSE strings; closes after 'done' or 'error' event."""
        while True:
            try:
                event, message = await asyncio.wait_for(self.queue.get(), timeout=15)
                yield message
                if event in ("done", "error"):
                    self._closed = True
                    return
            except asyncio.TimeoutError:
                # keepalive comment
                yield ": keepalive\n\n"


class SSEManager:
    """Registry of active SSE channels keyed by run_id."""

    def __init__(self):
        self._channels: dict[str, SSEChannel] = {}

    def create_channel(self, run_id: str) -> SSEChannel:
        channel = SSEChannel(run_id)
        self._channels[run_id] = channel
        return channel

    def get_channel(self, run_id: str) -> Optional[SSEChannel]:
        return self._channels.get(run_id)

    def close_channel(self, run_id: str) -> None:
        self._channels.pop(run_id, None)


# Module-level singleton
sse_manager = SSEManager()
