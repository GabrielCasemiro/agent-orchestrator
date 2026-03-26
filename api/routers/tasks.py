from fastapi import APIRouter, Depends, HTTPException, Request

from models.task import Task, TaskCreate, TaskUpdate
from services.orchestrator import OrchestratorService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def get_service(request: Request) -> OrchestratorService:
    return request.app.state.service


@router.post("", response_model=Task)
async def create_task(
    data: TaskCreate, service: OrchestratorService = Depends(get_service)
) -> Task:
    return await service.create_task(data)


@router.get("", response_model=list[Task])
async def list_tasks(
    project: str, service: OrchestratorService = Depends(get_service)
) -> list[Task]:
    return service.list_tasks(project)


@router.get("/agent/{assignee_id}", response_model=list[Task])
async def get_agent_tasks(
    assignee_id: str, service: OrchestratorService = Depends(get_service)
) -> list[Task]:
    return service.get_agent_tasks(assignee_id)


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str, update: TaskUpdate, service: OrchestratorService = Depends(get_service)
) -> Task:
    task = await service.update_task(task_id, update)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
