"""
Voice Agents API Router
FastAPI endpoints for voice agent management with tenant isolation
"""
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.services.voice_agent_service import VoiceAgentService
from src.schemas.voice_agent_schemas import (
    VoiceAgentCreateRequest,
    VoiceAgentUpdateRequest,
    VoiceAgentResponse,
    VoiceAgentListResponse,
    VoiceAgentActivationRequest,
    VoiceAgentKnowledgeUpdateRequest
)
from src.api.dependencies.auth import get_current_user
from src.websocket.progress_tracker import ProgressTracker
from src.api.websocket_routes import get_progress_manager, get_websocket_manager


router = APIRouter(prefix="/agents", tags=["Voice Agents"])


@router.post("/create-with-progress", status_code=status.HTTP_202_ACCEPTED)
async def create_voice_agent_with_progress(
    agent_request: VoiceAgentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new voice agent and return a session ID for progress tracking
    
    This endpoint starts the agent creation process and immediately returns
    a session ID that clients can use to track progress via WebSocket.
    
    Returns:
    - session_id: Use this to connect to WebSocket for real-time updates
    - message: Status message
    """
    # Initialize progress tracking
    progress_manager = get_progress_manager()
    websocket_manager = get_websocket_manager()
    progress_tracker = ProgressTracker(progress_manager, websocket_manager)
    
    # Start the session immediately
    session_id = progress_manager.create_session("agent_creation")
    
    # Start the creation process asynchronously
    import asyncio
    
    async def create_agent_async():
        try:
            async with progress_tracker.track_operation(
                "agent_creation", 
                f"Creating voice agent: {agent_request.name}"
            ) as session:
                # Override the session to use our pre-created one
                session.session_id = session_id
                
                await session.update("Initializing voice agent creation", 10)
                
                service = VoiceAgentService()
                tenant_id = current_user['tenant_id']
                
                await session.update("Validating request data", 20)
                await session.update("Setting up agent configuration", 40)
                await session.update("Initializing knowledge base", 60)
                await session.update("Creating voice agent in database", 80)
                
                voice_agent = service.create_agent(
                    tenant_id=tenant_id,
                    agent_data=agent_request.dict()
                )
                
                await session.update("Finalizing agent setup", 95)
                
                response = VoiceAgentResponse(**voice_agent)
                
                await session.complete(
                    success=True,
                    result=f"Voice agent '{agent_request.name}' created successfully with ID: {response.agent_id}"
                )
                
        except Exception as e:
            progress_manager.complete_session(
                session_id, 
                success=False, 
                result=f"Failed to create voice agent: {str(e)}"
            )
            await websocket_manager.broadcast_session_complete(session_id)
    
    # Start the background task
    asyncio.create_task(create_agent_async())
    
    # Return session ID immediately for progress tracking
    return {
        "session_id": session_id,
        "message": "Agent creation started. Use session_id to track progress via WebSocket.",
        "websocket_url": "/api/v1/ws/progress"
    }


@router.post("/", response_model=VoiceAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_agent(
    agent_request: VoiceAgentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new voice agent for the authenticated tenant
    
    - **name**: Required. Display name for the voice agent
    - **description**: Optional. Description of the agent's purpose
    - **knowledge_base**: Optional. Initial knowledge base data
    - **voice_config**: Optional. Voice synthesis configuration
    
    Returns the created voice agent with generated ID and metadata.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Create voice agent
        voice_agent = service.create_agent(
            tenant_id=tenant_id,
            agent_data=agent_request.dict()
        )
        
        # Convert to response model  
        return VoiceAgentResponse(**voice_agent)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create voice agent"
        )


@router.get("/", response_model=VoiceAgentListResponse)
async def list_voice_agents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List all voice agents for the authenticated tenant
    
    - **page**: Page number for pagination (default: 1)
    - **limit**: Number of items per page (default: 10, max: 100)
    
    Returns paginated list of voice agents owned by the tenant.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Get agents for tenant
        agents = service.get_agents_for_tenant(tenant_id)
        
        # Apply pagination (simplified for now)
        total = len(agents)
        start = (page - 1) * limit
        end = start + limit
        paginated_agents = agents[start:end]
        
        # Convert to response models
        agent_responses = [
            VoiceAgentResponse(**agent)
            for agent in paginated_agents
        ]
        
        return VoiceAgentListResponse(
            agents=agent_responses,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice agents"
        )


@router.get("/{agent_id}", response_model=VoiceAgentResponse)
async def get_voice_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get a specific voice agent by ID
    
    - **agent_id**: UUID of the voice agent
    
    Returns the voice agent if it exists and is owned by the authenticated tenant.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Get agent with tenant isolation
        voice_agent = service.get_agent_by_id(agent_id, tenant_id)
        
        if not voice_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        return VoiceAgentResponse(**voice_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice agent"
        )


@router.put("/{agent_id}", response_model=VoiceAgentResponse)
async def update_voice_agent(
    agent_id: str,
    agent_update: VoiceAgentUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update a voice agent
    
    - **agent_id**: UUID of the voice agent
    - **name**: Optional. New name for the agent
    - **description**: Optional. New description
    - **knowledge_base**: Optional. Updated knowledge base data
    - **voice_config**: Optional. Updated voice configuration
    - **status**: Optional. New status (active/inactive/training)
    
    Returns the updated voice agent.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Update agent with tenant isolation
        voice_agent = service.update_agent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data=agent_update.dict(exclude_unset=True)
        )
        
        if not voice_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        return VoiceAgentResponse(**voice_agent)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update voice agent"
        )


@router.put("/{agent_id}/knowledge", response_model=VoiceAgentResponse)
async def update_voice_agent_knowledge(
    agent_id: str,
    knowledge_update: VoiceAgentKnowledgeUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update a voice agent's knowledge base
    
    - **agent_id**: UUID of the voice agent
    - **knowledge_base**: Updated knowledge base data with 18-category structure
    
    Returns the updated voice agent with new knowledge base.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Update knowledge base
        voice_agent = service.update_agent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data={'knowledge_base': knowledge_update.knowledge_base}
        )
        
        if not voice_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        return VoiceAgentResponse(**voice_agent)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update voice agent knowledge"
        )


@router.post("/{agent_id}/activate", response_model=VoiceAgentResponse)
async def activate_voice_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Activate a voice agent to start receiving calls
    
    - **agent_id**: UUID of the voice agent
    
    Returns the activated voice agent.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Activate agent
        voice_agent = service.activate_agent(agent_id, tenant_id)
        
        if not voice_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        return VoiceAgentResponse(**voice_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate voice agent"
        )


@router.post("/{agent_id}/deactivate", response_model=VoiceAgentResponse)
async def deactivate_voice_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Deactivate a voice agent to stop receiving calls
    
    - **agent_id**: UUID of the voice agent
    
    Returns the deactivated voice agent.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Deactivate agent
        voice_agent = service.deactivate_agent(agent_id, tenant_id)
        
        if not voice_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        return VoiceAgentResponse(**voice_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate voice agent"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete (soft delete) a voice agent
    
    - **agent_id**: UUID of the voice agent
    
    Marks the agent as inactive and removes it from listings.
    """
    try:
        service = VoiceAgentService()
        
        # Extract tenant ID from authenticated user
        tenant_id = current_user['tenant_id']
        
        # Delete agent
        success = service.delete_agent(agent_id, tenant_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete voice agent"
        )