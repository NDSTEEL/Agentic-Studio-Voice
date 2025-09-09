"""
Voice Agent Service
Business logic for voice agent management with tenant isolation
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from google.cloud.firestore import Client

from src.services.firebase_config import get_firestore_client
from src.schemas.knowledge_categories import (
    validate_knowledge_category, 
    get_empty_knowledge_base,
    merge_knowledge_categories
)


class VoiceAgentService:
    """
    Service class for voice agent CRUD operations with tenant isolation
    """
    
    def __init__(self, firestore_client: Optional[Client] = None):
        self.db = firestore_client or get_firestore_client()
        self.collection = 'voice_agents'
    
    def create_agent(self, tenant_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new voice agent for a specific tenant
        
        Args:
            tenant_id: UUID of the tenant
            agent_data: Dictionary containing agent creation data
            
        Returns:
            Dict[str, Any]: Created voice agent data
            
        Raises:
            ValueError: If validation fails
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
            
            # Create voice agent data
            agent_id = str(uuid4())
            voice_agent_data = {
                'id': agent_id,
                'tenant_id': tenant_id,
                'name': agent_data['name'],
                'description': agent_data.get('description', ''),
                'knowledge_base': validated_kb,
                'voice_config': agent_data.get('voice_config', {}),
                'status': 'inactive',  # New agents start inactive
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Save to Firestore
            doc_ref = self.db.collection(self.collection).document(agent_id)
            doc_ref.set(voice_agent_data)
            
            return voice_agent_data
            
        except Exception as e:
            raise ValueError(f"Failed to create voice agent: {str(e)}")
    
    def get_agents_for_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all voice agents for a specific tenant
        
        Args:
            tenant_id: UUID of the tenant
            
        Returns:
            List[Dict[str, Any]]: List of voice agents owned by the tenant
        """
        try:
            # Query Firestore for tenant's voice agents
            query = (self.db.collection(self.collection)
                    .where('tenant_id', '==', tenant_id)
                    .where('is_active', '==', True)
                    .order_by('created_at', direction='DESCENDING'))
            
            docs = query.stream()
            agents = []
            for doc in docs:
                agent_data = doc.to_dict()
                agent_data['id'] = doc.id
                agents.append(agent_data)
            
            return agents
                
        except Exception as e:
            raise ValueError(f"Failed to retrieve voice agents: {str(e)}")
    
    def get_agent_by_id(self, agent_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific voice agent by ID with tenant isolation
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[Dict[str, Any]]: Voice agent if found and owned by tenant, None otherwise
        """
        try:
            # Get document from Firestore with tenant isolation
            doc_ref = self.db.collection(self.collection).document(agent_id)
            doc = doc_ref.get()
            
            if doc.exists:
                agent_data = doc.to_dict()
                agent_data['id'] = doc.id
                
                # Verify tenant ownership and active status
                if (agent_data.get('tenant_id') == tenant_id and 
                    agent_data.get('is_active', False)):
                    return agent_data
            
            return None
                
        except Exception as e:
            raise ValueError(f"Failed to retrieve voice agent: {str(e)}")
    
    def update_agent(self, agent_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a voice agent with tenant isolation
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            update_data: Dictionary containing update data
            
        Returns:
            Optional[Dict[str, Any]]: Updated voice agent if found and owned by tenant
        """
        try:
            agent = self.get_agent_by_id(agent_id, tenant_id)
            if not agent:
                return None
            
            # Prepare update data
            updates = {'updated_at': datetime.utcnow()}
            
            # Update allowed fields
            if 'name' in update_data:
                updates['name'] = update_data['name']
            if 'description' in update_data:
                updates['description'] = update_data['description']
            if 'voice_config' in update_data:
                updates['voice_config'] = update_data['voice_config']
            if 'knowledge_base' in update_data:
                # Merge knowledge base updates
                updates['knowledge_base'] = merge_knowledge_categories(
                    agent.get('knowledge_base', {}), 
                    update_data['knowledge_base']
                )
            if 'status' in update_data:
                updates['status'] = update_data['status']
            
            # Update document in Firestore
            doc_ref = self.db.collection(self.collection).document(agent_id)
            doc_ref.update(updates)
            
            # Return updated agent
            updated_agent = agent.copy()
            updated_agent.update(updates)
            return updated_agent
            
        except Exception as e:
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
            doc_ref = self.db.collection(self.collection).document(agent_id)
            doc_ref.update({
                'is_active': False,
                'updated_at': datetime.utcnow()
            })
            
            return True
            
        except Exception as e:
            raise ValueError(f"Failed to delete voice agent: {str(e)}")
    
    def activate_agent(self, agent_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Activate a voice agent for receiving calls
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[Dict[str, Any]]: Activated agent if successful
        """
        return self.update_agent(agent_id, tenant_id, {'status': 'active'})
    
    def deactivate_agent(self, agent_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Deactivate a voice agent from receiving calls
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[Dict[str, Any]]: Deactivated agent if successful
        """
        return self.update_agent(agent_id, tenant_id, {'status': 'inactive'})
    
    def create_agent_with_knowledge(self, tenant_id: str, agent_data: Dict[str, Any], knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new voice agent with pre-populated knowledge base
        
        Args:
            tenant_id: UUID of the tenant
            agent_data: Dictionary containing agent creation data
            knowledge_base: Pre-populated knowledge base from crawling
            
        Returns:
            Dict[str, Any]: Created voice agent with knowledge
        """
        # Merge the knowledge base into agent data
        agent_data_with_kb = agent_data.copy()
        agent_data_with_kb['knowledge_base'] = knowledge_base
        
        return self.create_agent(tenant_id, agent_data_with_kb)
    
    def update_agent_knowledge_from_crawl(self, agent_id: str, tenant_id: str, crawled_knowledge: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update voice agent knowledge base with new crawled data
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            crawled_knowledge: New knowledge data from web crawling
            
        Returns:
            Optional[Dict[str, Any]]: Updated agent with new knowledge
        """
        return self.update_agent(agent_id, tenant_id, {'knowledge_base': crawled_knowledge})
    
    def get_agent_with_knowledge(self, agent_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent with full knowledge base expansion
        
        Args:
            agent_id: UUID of the voice agent
            tenant_id: UUID of the tenant (for security check)
            
        Returns:
            Optional[Dict[str, Any]]: Agent with expanded knowledge base
        """
        agent = self.get_agent_by_id(agent_id, tenant_id)
        if not agent:
            return None
            
        # For now, just return the agent as-is
        # In future, this could expand knowledge base with additional processing
        return agent