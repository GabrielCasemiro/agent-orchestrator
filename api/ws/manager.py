from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if project not in self.connections:
            self.connections[project] = []
        self.connections[project].append(websocket)

    def disconnect(self, project: str, websocket: WebSocket) -> None:
        if project in self.connections:
            self.connections[project] = [
                ws for ws in self.connections[project] if ws is not websocket
            ]

    async def broadcast(self, project: str, data: dict) -> None:
        if project not in self.connections:
            return
        broken: list[WebSocket] = []
        for ws in self.connections[project]:
            try:
                await ws.send_json(data)
            except Exception:
                broken.append(ws)
        for ws in broken:
            self.connections[project] = [
                conn for conn in self.connections[project] if conn is not ws
            ]
