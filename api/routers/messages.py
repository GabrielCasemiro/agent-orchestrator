from fastapi import APIRouter, Depends, Request

from models.message import Message, MessageCreate
from services.orchestrator import OrchestratorService

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])


def get_service(request: Request) -> OrchestratorService:
    return request.app.state.service


@router.post("", response_model=Message)
async def send_message(
    data: MessageCreate, service: OrchestratorService = Depends(get_service)
) -> Message:
    return await service.send_message(data)


@router.get("", response_model=list[Message])
async def get_messages(
    project: str, limit: int = 50, service: OrchestratorService = Depends(get_service)
) -> list[Message]:
    return service.get_messages(project, limit)
