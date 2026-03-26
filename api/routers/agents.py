from fastapi import APIRouter, Depends, HTTPException, Request

from models.agent import Agent, AgentCreate
from services.orchestrator import OrchestratorService

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def get_service(request: Request) -> OrchestratorService:
    return request.app.state.service


@router.post("", response_model=Agent)
async def register_agent(
    data: AgentCreate, service: OrchestratorService = Depends(get_service)
) -> Agent:
    return await service.register_agent(data)


@router.get("", response_model=list[Agent])
async def list_agents(
    project: str, service: OrchestratorService = Depends(get_service)
) -> list[Agent]:
    return service.list_agents(project)


@router.delete("/{agent_id}")
async def deregister_agent(
    agent_id: str, service: OrchestratorService = Depends(get_service)
) -> dict:
    deleted = await service.deregister_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"deleted": True}


@router.post("/{agent_id}/heartbeat", response_model=Agent)
async def heartbeat(
    agent_id: str, service: OrchestratorService = Depends(get_service)
) -> Agent:
    agent = service.heartbeat(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
