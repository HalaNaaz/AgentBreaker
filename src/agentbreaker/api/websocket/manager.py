"""WebSocket connection manager for real-time live assessment progress streaming."""

import asyncio
import contextlib

from fastapi import WebSocket

from agentbreaker.api.schemas.events import AssessmentEvent


class WebSocketManager:
    """Manages active WebSocket client connections isolated by assessment ID."""

    MAX_CONNECTIONS_PER_ASSESSMENT = 10
    MAX_GLOBAL_CONNECTIONS = 100

    def __init__(self) -> None:
        # Maps assessment_id -> list of active WebSockets
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, assessment_id: str, websocket: WebSocket) -> bool:
        """Register and accept a new client subscription to an assessment channel."""
        async with self._lock:
            total_active = sum(len(conns) for conns in self._connections.values())
            asm_active = len(self._connections.get(assessment_id, []))

            if (
                total_active >= self.MAX_GLOBAL_CONNECTIONS
                or asm_active >= self.MAX_CONNECTIONS_PER_ASSESSMENT
            ):
                await websocket.close(code=4029, reason="Connection limit exceeded")
                return False

            await websocket.accept()
            self._connections.setdefault(assessment_id, []).append(websocket)
            return True

    async def disconnect(self, assessment_id: str, websocket: WebSocket) -> None:
        """Remove a disconnected client from the active subscription list."""
        async with self._lock:
            if assessment_id in self._connections:
                if websocket in self._connections[assessment_id]:
                    self._connections[assessment_id].remove(websocket)
                if not self._connections[assessment_id]:
                    del self._connections[assessment_id]

    async def broadcast(self, assessment_id: str, event: AssessmentEvent) -> None:
        """Broadcast an event exclusively to subscribed clients with slow-consumer protection."""
        payload = event.model_dump(mode="json")
        async with self._lock:
            subscribers = list(self._connections.get(assessment_id, []))

        stale_clients: list[WebSocket] = []
        for ws in subscribers:
            try:
                # Bounded dispatch: evict slow consumers stalling over 1.5s
                await asyncio.wait_for(ws.send_json(payload), timeout=1.5)
            except Exception:
                stale_clients.append(ws)

        if stale_clients:
            async with self._lock:
                for ws in stale_clients:
                    if (
                        assessment_id in self._connections
                        and ws in self._connections[assessment_id]
                    ):
                        self._connections[assessment_id].remove(ws)
                if assessment_id in self._connections and not self._connections[assessment_id]:
                    del self._connections[assessment_id]

    async def close_all(self) -> None:
        """Cleanly close all active WebSocket connections on application shutdown."""
        async with self._lock:
            for _asm_id, sockets in list(self._connections.items()):
                for ws in sockets:
                    with contextlib.suppress(Exception):
                        await ws.close()
            self._connections.clear()


ws_manager = WebSocketManager()
