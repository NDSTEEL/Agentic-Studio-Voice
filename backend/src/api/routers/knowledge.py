"""
Knowledge Base API Router
FastAPI endpoints for knowledge base management with tenant isolation
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.voice_agent_service import VoiceAgentService
from src.schemas.knowledge_schemas import (
    KnowledgeBaseResponse,
    KnowledgeCategoryUpdateRequest,
    KnowledgeExportResponse,
    KnowledgeValidationResponse,
    KnowledgeMergeRequest,
    KnowledgeCrawledContentRequest
)
from src.api.dependencies.auth import get_current_user
from datetime import datetime


router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.get("/{agent_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    agent_id: str = Path(description="UUID of the voice agent"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get knowledge base for a specific voice agent
    
    - **agent_id**: UUID of the voice agent
    
    Returns the complete knowledge base with statistics and size information.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Get knowledge base from agent
        knowledge_base = agent.get('knowledge_base', {})
        
        # Get service for analysis
        kb_service = KnowledgeBaseService()
        
        # Get stats and size info
        stats = kb_service.get_knowledge_base_stats(knowledge_base)
        size_info = kb_service.validate_knowledge_base_size(knowledge_base)
        
        return KnowledgeBaseResponse(
            knowledge_base=knowledge_base,
            stats=stats,
            size_info=size_info,
            last_updated=agent.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge base"
        )


@router.put("/{agent_id}/categories/{category_name}")
async def update_knowledge_category(
    category_update: KnowledgeCategoryUpdateRequest,
    agent_id: str = Path(description="UUID of the voice agent"),
    category_name: str = Path(description="Name of the knowledge category"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update a specific knowledge category for a voice agent
    
    - **agent_id**: UUID of the voice agent
    - **category_name**: Name of the knowledge category to update
    - **title**: New title for the category
    - **content**: New content for the category
    - **confidence_score**: Confidence score between 0 and 1
    
    Returns success status with updated category information.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Get current knowledge base
        knowledge_base = agent.get('knowledge_base', {})
        
        # Update the specific category
        knowledge_base[category_name] = category_update.dict()
        
        # Update agent with new knowledge base
        updated_agent = voice_service.update_agent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data={'knowledge_base': knowledge_base}
        )
        
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update knowledge category"
            )
        
        return {
            "status": "success",
            "category": category_name,
            "updated_data": category_update.dict(),
            "message": f"Knowledge category '{category_name}' updated successfully"
        }
        
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
            detail="Failed to update knowledge category"
        )


@router.delete("/{agent_id}/categories/{category_name}")
async def delete_knowledge_category(
    agent_id: str = Path(description="UUID of the voice agent"),
    category_name: str = Path(description="Name of the knowledge category to delete"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a specific knowledge category from a voice agent
    
    - **agent_id**: UUID of the voice agent
    - **category_name**: Name of the knowledge category to delete
    
    Removes the specified category from the agent's knowledge base.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Get current knowledge base
        knowledge_base = agent.get('knowledge_base', {})
        
        # Check if category exists
        if category_name not in knowledge_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge category '{category_name}' not found"
            )
        
        # Remove the category
        del knowledge_base[category_name]
        
        # Update agent with modified knowledge base
        updated_agent = voice_service.update_agent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data={'knowledge_base': knowledge_base}
        )
        
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete knowledge category"
            )
        
        return {
            "status": "success",
            "category": category_name,
            "message": f"Knowledge category '{category_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete knowledge category"
        )


@router.get("/{agent_id}/export", response_model=KnowledgeExportResponse)
async def export_knowledge_base(
    agent_id: str = Path(description="UUID of the voice agent"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    format: str = "json",
):
    """
    Export complete knowledge base for a voice agent
    
    - **agent_id**: UUID of the voice agent
    - **format**: Export format (default: json)
    
    Returns the complete knowledge base in the requested format.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Get knowledge base
        knowledge_base = agent.get('knowledge_base', {})
        
        # Count total categories with data
        total_categories = len([cat for cat, data in knowledge_base.items() if data])
        
        return KnowledgeExportResponse(
            export_data=knowledge_base,
            export_format=format,
            export_timestamp=datetime.utcnow(),
            total_categories=total_categories
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export knowledge base"
        )


@router.post("/{agent_id}/validate", response_model=KnowledgeValidationResponse)
async def validate_knowledge_base(
    agent_id: str = Path(description="UUID of the voice agent"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Validate knowledge base for a voice agent
    
    - **agent_id**: UUID of the voice agent
    
    Returns validation results including errors, size validation, and quality metrics.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Get knowledge base
        knowledge_base = agent.get('knowledge_base', {})
        
        # Validate using service
        kb_service = KnowledgeBaseService()
        
        # Perform validations
        size_validation = kb_service.validate_knowledge_base_size(knowledge_base)
        quality_metrics = kb_service.get_knowledge_base_stats(knowledge_base)
        
        # Check for validation errors
        validation_errors = []
        if not size_validation['is_valid']:
            validation_errors.append(f"Knowledge base size ({size_validation['estimated_size_mb']}MB) exceeds limit ({size_validation['max_size_mb']}MB)")
        
        if quality_metrics['quality_score'] < 0.3:
            validation_errors.append("Knowledge base quality score is below acceptable threshold")
        
        return KnowledgeValidationResponse(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            size_validation=size_validation,
            quality_metrics=quality_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate knowledge base"
        )


@router.post("/{agent_id}/merge")
async def merge_knowledge_data(
    merge_request: KnowledgeMergeRequest,
    agent_id: str = Path(description="UUID of the voice agent"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Merge new knowledge data into existing knowledge base
    
    - **agent_id**: UUID of the voice agent
    - **new_knowledge_data**: New knowledge data to merge
    - **min_confidence_threshold**: Minimum confidence threshold for merging
    - **overwrite_existing**: Whether to overwrite existing data with lower confidence
    
    Merges new knowledge data using confidence scores and validation.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Get current knowledge base
        existing_knowledge = agent.get('knowledge_base', {})
        
        # Validate and merge using service
        kb_service = KnowledgeBaseService()
        
        # Validate new data first
        validated_new_data = kb_service.validate_crawled_content(merge_request.new_knowledge_data)
        
        # Merge with existing
        merged_knowledge = kb_service.merge_knowledge_categories(
            existing=existing_knowledge,
            new_data=validated_new_data,
            min_confidence_threshold=merge_request.min_confidence_threshold
        )
        
        # Update agent with merged knowledge base
        updated_agent = voice_service.update_agent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data={'knowledge_base': merged_knowledge}
        )
        
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to merge knowledge data"
            )
        
        # Calculate merge statistics
        original_categories = len([cat for cat, data in existing_knowledge.items() if data])
        merged_categories = len([cat for cat, data in merged_knowledge.items() if data])
        new_categories = len([cat for cat, data in validated_new_data.items() if data])
        
        return {
            "status": "success",
            "merge_stats": {
                "original_categories": original_categories,
                "new_categories_provided": new_categories,
                "final_categories": merged_categories,
                "categories_updated": merged_categories - original_categories
            },
            "message": "Knowledge data merged successfully"
        }
        
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
            detail="Failed to merge knowledge data"
        )


@router.post("/{agent_id}/process-crawled")
async def process_crawled_content(
    crawled_request: KnowledgeCrawledContentRequest,
    agent_id: str = Path(description="UUID of the voice agent"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Process and validate crawled content for knowledge base
    
    - **agent_id**: UUID of the voice agent
    - **crawled_data**: Raw crawled content to validate and process
    - **validation_options**: Optional validation settings
    
    Processes crawled content and returns validated knowledge data ready for merging.
    """
    try:
        # Verify agent exists and user has access
        voice_service = VoiceAgentService()
        tenant_id = current_user['tenant_id']
        
        agent = voice_service.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voice agent not found"
            )
        
        # Process crawled content using service
        kb_service = KnowledgeBaseService()
        
        validated_data = kb_service.validate_crawled_content(crawled_request.crawled_data)
        
        # Calculate processing statistics
        original_categories = len(crawled_request.crawled_data)
        validated_categories = len([cat for cat, data in validated_data.items() if data])
        
        return {
            "status": "success",
            "validated_data": validated_data,
            "processing_stats": {
                "original_categories": original_categories,
                "validated_categories": validated_categories,
                "validation_rate": validated_categories / max(original_categories, 1)
            },
            "message": "Crawled content processed and validated successfully"
        }
        
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
            detail="Failed to process crawled content"
        )