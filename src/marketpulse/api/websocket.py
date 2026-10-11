import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
from marketpulse.ingest.stream_simulator import StreamSimulator
from marketpulse.streaming.consumer import StreamConsumer

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.simulator = StreamSimulator(speed_factor=0.2)
        self.consumer = StreamConsumer()
        self.simulator.start(callback=self.on_tick)

    def on_tick(self, tick: dict):
        self.consumer.process_tick(tick)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_tick(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()
