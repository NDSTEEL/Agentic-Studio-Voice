"""
Voice Agent Service
Business logic for voice agent management with tenant isolation
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.models.voice_agent import VoiceAgent
from src.schemas.knowledge_categories import (
    validate_knowledge_category, 
    get_empty_knowledge_base,
    merge_knowledge_categories
)


class VoiceAgentService:
    """
    Service class for voice agent CRUD operations with tenant isolation
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
    
    def create_agent(self, tenant_id: str, agent_data: Dict[str, Any]) -> VoiceAgent:
        """
        Create a new voice agent for a specific tenant
        
        Args:
            tenant_id: UUID of the tenant
            agent_data: Dictionary containing agent creation data
            
        Returns:
            VoiceAgent: Created voice agent instance
            
        Raises:
            ValueError: If validation fails
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate and prepare knowledge base
            knowledge_base = agent_data.get('knowledge_base', {})
            if not knowledge_base:
                knowledge_base = get_empty_knowledge_base()
            
            # Validate each category in knowledge base
            validated_kb = {}
            for category, data in knowledge_base.items():
                if data is not None:
                    validated_kb[category] = validate_knowledge_category(category, data).dict()
                else:
                    validated_kb[category] = None
            
            # Create voice agent instance
            voice_agent = VoiceAgent(
                tenant_id=tenant_id,
                name=agent_data['name'],
                description=agent_data.get('description', ''),
                knowledge_base=validated_kb,
                voice_config=agent_data.get('voice_config', {}),
                status='inactive',  # New agents start inactive
                is_active=True
            )
            
            # Save to database (mocked for now)
            if self.db:
                self.db.add(voice_agent)
                self.db.commit()
                self.db.refresh(voice_agent)
            
            return voice_agent
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            raise ValueError(f"Failed to create voice agent: {str(e)}")
    
    def get_agents_for_tenant(self, tenant_id: str) -> List[VoiceAgent]:
        """
        Get all voice agents for a specific tenant
        
        Args:
            tenant_id: UUID of the tenant
            
        Returns:
            List[VoiceAgent]: List of voice agents owned by the tenant
        """
        try:
            if self.db:
                return (
                    self.db.query(VoiceAgent)
                    .filter(VoiceAgent.tenant_id == tenant_id)
                    .filter(VoiceAgent.is_active == True)
                    .order_by(VoiceAgent.created_at.desc())
                    .all()
                )
            else:
                # Mock data for testing
                return []
                
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to retrieve voice agents: {str(e)}")
    
    def get_agent_by_id(self, agent_id: str, tenant_id: str) -> Optional[VoiceAgent]:
        """
        Get a specific voice agent by ID with tenant isolation
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[VoiceAgent]: Voice agent if found and owned by tenant, None otherwise
        """
        try:
            if self.db:
                return (
                    self.db.query(VoiceAgent)
                    .filter(VoiceAgent.id == agent_id)
                    .filter(VoiceAgent.tenant_id == tenant_id)  # Tenant isolation
                    .filter(VoiceAgent.is_active == True)
                    .first()
                )
            else:
                # Mock data for testing
                return None
                
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to retrieve voice agent: {str(e)}")
    
    def update_agent(self, agent_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[VoiceAgent]:
        """
        Update a voice agent with tenant isolation
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            update_data: Dictionary containing update data
            
        Returns:
            Optional[VoiceAgent]: Updated voice agent if found and owned by tenant
        """
        try:
            agent = self.get_agent_by_id(agent_id, tenant_id)
            if not agent:
                return None
            
            # Update allowed fields
            if 'name' in update_data:
                agent.name = update_data['name']
            if 'description' in update_data:
                agent.description = update_data['description']
            if 'voice_config' in update_data:
                agent.voice_config = update_data['voice_config']
            if 'knowledge_base' in update_data:
                # Merge knowledge base updates
                agent.knowledge_base = merge_knowledge_categories(
                    agent.knowledge_base, 
                    update_data['knowledge_base']
                )
            if 'status' in update_data:
                agent.status = update_data['status']
            
            # Save changes
            if self.db:
                self.db.commit()
                self.db.refresh(agent)
            
            return agent
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            raise ValueError(f"Failed to update voice agent: {str(e)}")
    
    def delete_agent(self, agent_id: str, tenant_id: str) -> bool:
        """
        Soft delete a voice agent with tenant isolation
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            bool: True if agent was deleted, False if not found
        """
        try:
            agent = self.get_agent_by_id(agent_id, tenant_id)
            if not agent:
                return False
            
            # Soft delete by setting is_active to False
            agent.is_active = False
            
            if self.db:
                self.db.commit()
            
            return True
            
        except Exception as e:
            if self.db:
                self.db.rollback()
            raise ValueError(f"Failed to delete voice agent: {str(e)}")
    
    def activate_agent(self, agent_id: str, tenant_id: str) -> Optional[VoiceAgent]:
        """
        Activate a voice agent for receiving calls
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[VoiceAgent]: Activated agent if successful
        """
        return self.update_agent(agent_id, tenant_id, {'status': 'active'})
    
    def deactivate_agent(self, agent_id: str, tenant_id: str) -> Optional[VoiceAgent]:
        """
        Deactivate a voice agent from receiving calls
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[VoiceAgent]: Deactivated agent if successful
        """
        return self.update_agent(agent_id, tenant_id, {'status': 'inactive'})