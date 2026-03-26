from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from models.activity import Activity, ActivityCreate
from services.orchestrator import OrchestratorService

router = APIRouter(prefix="/api/v1", tags=["activities"])


def get_service(request: Request) -> OrchestratorService:
    return request.app.state.service


@router.post("/activities", response_model=Activity)
async def log_activity(
    data: ActivityCreate, service: OrchestratorService = Depends(get_service)
) -> Activity:
    return await service.log_activity(data)


@router.get("/activities", response_model=list[Activity])
async def get_activities(
    project: str, limit: int = 100, service: OrchestratorService = Depends(get_service)
) -> list[Activity]:
    return service.get_activities(project, limit)


@router.get("/tasks/{task_id}/activities", response_model=list[Activity])
async def get_task_activities(
    task_id: str, service: OrchestratorService = Depends(get_service)
) -> list[Activity]:
    return service.get_task_activities(task_id)


@router.get("/export", response_class=PlainTextResponse)
async def export_project(
    project: str, service: OrchestratorService = Depends(get_service)
) -> str:
    return service.export_project(project)
