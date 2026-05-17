from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.core.events import manager
import asyncio

router = APIRouter()

@router.websocket("/agents")
async def agent_stream(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
