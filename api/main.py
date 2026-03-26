import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from routers.activities import router as activities_router
from routers.agents import router as agents_router
from routers.messages import router as messages_router
from routers.tasks import router as tasks_router
from services.orchestrator import OrchestratorService
from ws.manager import ConnectionManager

app = FastAPI(title="Agent Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage backend — set STORAGE=memory to use in-memory (default: sqlite)
STORAGE = os.environ.get("STORAGE", "sqlite")

if STORAGE == "memory":
    from repositories.memory import (
        InMemoryActivityRepository,
        InMemoryAgentRepository,
        InMemoryMessageRepository,
        InMemoryTaskRepository,
    )
    agent_repo = InMemoryAgentRepository()
    message_repo = InMemoryMessageRepository()
    task_repo = InMemoryTaskRepository()
    activity_repo = InMemoryActivityRepository()
else:
    from repositories.sqlite import (
        SQLiteDB,
        SQLiteActivityRepository,
        SQLiteAgentRepository,
        SQLiteMessageRepository,
        SQLiteTaskRepository,
    )
    db_path = os.environ.get("DB_PATH", "orchestrator.db")
    db = SQLiteDB(db_path)
    agent_repo = SQLiteAgentRepository(db)
    message_repo = SQLiteMessageRepository(db)
    task_repo = SQLiteTaskRepository(db)
    activity_repo = SQLiteActivityRepository(db)

ws_manager = ConnectionManager()

app.state.service = OrchestratorService(
    agent_repo=agent_repo,
    message_repo=message_repo,
    task_repo=task_repo,
    activity_repo=activity_repo,
    ws_manager=ws_manager,
)

app.include_router(agents_router)
app.include_router(messages_router)
app.include_router(tasks_router)
app.include_router(activities_router)


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": "agent-orchestrator", "storage": STORAGE}


@app.websocket("/ws/{project}")
async def websocket_endpoint(websocket: WebSocket, project: str) -> None:
    await ws_manager.connect(project, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(project, websocket)
