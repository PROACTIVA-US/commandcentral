"""
Agent session management endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.agent import AgentState
from ..services.agent_service import AgentService

router = APIRouter()


class AgentCreate(BaseModel):
    """Request body for creating an agent."""
    name: str
    description: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    system_prompt: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    skills: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    max_iterations: int = 100
    timeout_seconds: int = 300
    extra_data: Optional[dict] = None


class AgentResponse(BaseModel):
    """Response body for an agent."""
    id: str
    name: str
    description: Optional[str]
    model: str
    state: str
    project_id: Optional[str]
    session_id: Optional[str]
    iteration_count: int
    max_iterations: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    error: Optional[str]
    created_at: str


class AgentMessage(BaseModel):
    """Request body for sending a message to an agent."""
    content: str


class TokenUpdate(BaseModel):
    """Request body for updating token usage."""
    input_tokens: int
    output_tokens: int
    cost_usd: float = 0.0


@router.post("", response_model=AgentResponse)
async def create_agent(
    body: AgentCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new agent session."""
    service = AgentService(session)
    agent = await service.create_agent(
        name=body.name,
        model=body.model,
        system_prompt=body.system_prompt,
        project_id=body.project_id,
        session_id=body.session_id,
        skills=body.skills,
        tools=body.tools,
        max_iterations=body.max_iterations,
        timeout_seconds=body.timeout_seconds,
        extra_data=body.extra_data,
    )
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    state: Optional[AgentState] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """List agents with optional filters."""
    service = AgentService(session)
    agents = await service.list_agents(
        project_id=project_id,
        session_id=session_id,
        state=state,
        limit=limit,
        offset=offset,
    )
    
    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            model=agent.model,
            state=agent.state.value,
            project_id=agent.project_id,
            session_id=agent.session_id,
            iteration_count=agent.iteration_count,
            max_iterations=agent.max_iterations,
            input_tokens=agent.input_tokens,
            output_tokens=agent.output_tokens,
            total_cost_usd=agent.total_cost_usd,
            error=agent.error,
            created_at=agent.created_at.isoformat(),
        )
        for agent in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get an agent by ID."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.post("/{agent_id}/initialize", response_model=AgentResponse)
async def initialize_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Initialize an agent for execution."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = await service.initialize_agent(agent)
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.post("/{agent_id}/message", response_model=AgentResponse)
async def send_message(
    agent_id: str,
    body: AgentMessage,
    session: AsyncSession = Depends(get_session),
):
    """Send a message to an agent and run an iteration."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = await service.run_iteration(agent, body.content)
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.post("/{agent_id}/pause", response_model=AgentResponse)
async def pause_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Pause a running agent."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = await service.pause_agent(agent)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause agent in current state")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.post("/{agent_id}/resume", response_model=AgentResponse)
async def resume_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Resume a paused agent."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = await service.resume_agent(agent)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume agent in current state")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.post("/{agent_id}/terminate", response_model=AgentResponse)
async def terminate_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Terminate an agent session."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = await service.terminate_agent(agent)
    if not success:
        raise HTTPException(status_code=400, detail="Agent already terminated")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )


@router.post("/{agent_id}/tokens", response_model=AgentResponse)
async def update_tokens(
    agent_id: str,
    body: TokenUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update token usage for an agent."""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await service.update_tokens(
        agent,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        cost_usd=body.cost_usd,
    )
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model=agent.model,
        state=agent.state.value,
        project_id=agent.project_id,
        session_id=agent.session_id,
        iteration_count=agent.iteration_count,
        max_iterations=agent.max_iterations,
        input_tokens=agent.input_tokens,
        output_tokens=agent.output_tokens,
        total_cost_usd=agent.total_cost_usd,
        error=agent.error,
        created_at=agent.created_at.isoformat(),
    )
