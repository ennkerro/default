"""
Yksinkertainen WebSocket-yleislahetys.

Kaikki liitetyt asiakkaat (osallistujien odotusnakymat + admin-sivu) saavat
saman tilapaivityksen samasta kanavasta - ei erillisia rooleja tai huoneita,
koska koko sovellus palvelee yhta tapahtumaa kerrallaan.
"""
import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        async with self._lock:
            connections = list(self._connections)
        dead = []
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)


manager = ConnectionManager()
