"""Phone service for managing phone numbers and call routing."""

from typing import List, Optional, Dict, Any
import logging
from ..twilio.twilio_phone_client import TwilioPhoneClient
from sqlalchemy.orm import Session
from src.models.voice_agent import VoiceAgent
import os
import uuid
from datetime import datetime


logger = logging.getLogger(__name__)


class PhoneService:
    """Service class for managing phone numbers and call routing."""
    
    def __init__(self, twilio_client: Optional[TwilioPhoneClient] = None, db_session: Optional[Session] = None):
        """Initialize the PhoneService with a Twilio client and optional database session."""
        self.twilio_client = twilio_client or TwilioPhoneClient()
        self.db_session = db_session
        self.logger = logger
        
    async def search_available_numbers(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for available phone numbers based on preferences.
        
        Args:
            preferences: Dictionary containing search criteria like area_code, contains, limit
            
        Returns:
            List of available phone numbers with metadata
        """
        try:
            # Extract preferences
            area_code = preferences.get('area_code')
            contains = preferences.get('contains')
            country_code = preferences.get('country_code', 'US')
            limit = preferences.get('limit', 10)
            
            # Search using Twilio client
            raw_numbers = await self.twilio_client.search_phone_numbers(
                area_code=area_code,
                contains=contains,
                country_code=country_code,
                limit=limit
            )
            
            # Enhance results with pricing and recommendations
            enhanced_numbers = []
            for number in raw_numbers:
                enhanced_number = number.copy()
                enhanced_number['cost_per_month'] = '$1.00'  # Standard Twilio pricing
                enhanced_number['recommended'] = self._is_recommended_number(number)
                enhanced_numbers.append(enhanced_number)
                
            return enhanced_numbers
            
        except Exception as e:
            self.logger.error(f"Error searching for phone numbers: {e}")
            raise
    
    async def provision_number(self, phone_number: str, tenant_id: str) -> Dict[str, Any]:
        """
        Provision a phone number for a tenant.
        
        Args:
            phone_number: The phone number to provision
            tenant_id: The tenant ID
            
        Returns:
            Provisioning result with tenant_id, provisioned_at, monthly_cost
        """
        try:
            # Create friendly name for the number
            friendly_name = f"Number for Tenant {tenant_id}"
            
            # Provision via Twilio
            result = await self.twilio_client.provision_phone_number(
                phone_number=phone_number,
                friendly_name=friendly_name
            )
            
            # Add tenant-specific metadata
            result['tenant_id'] = tenant_id
            result['provisioned_at'] = self._get_current_timestamp()
            result['monthly_cost'] = '$1.00'
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error provisioning phone number {phone_number} for tenant {tenant_id}: {e}")
            raise
    
    async def get_tenant_numbers(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all phone numbers for a specific tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            List of phone numbers belonging to the tenant
        """
        try:
            # Get all provisioned numbers
            all_numbers = await self.twilio_client.list_provisioned_numbers()
            
            # Filter by tenant (based on friendly name convention)
            tenant_numbers = []
            for number in all_numbers:
                friendly_name = number.get('friendly_name', '')
                if f"Tenant {tenant_id}" in friendly_name:
                    # Add tenant_id to the result
                    number['tenant_id'] = tenant_id
                    tenant_numbers.append(number)
                    
            return tenant_numbers
            
        except Exception as e:
            self.logger.error(f"Error getting numbers for tenant {tenant_id}: {e}")
            raise
    
    async def release_number(self, phone_number_or_sid: str, tenant_id: str) -> bool:
        """
        Release a phone number from a tenant.
        
        Args:
            phone_number_or_sid: The phone number or SID to release
            tenant_id: The tenant ID (for ownership verification)
            
        Returns:
            True if successfully released
        """
        try:
            # Verify tenant owns this number
            tenant_numbers = await self.get_tenant_numbers(tenant_id)
            
            # Find the number in tenant's list
            number_to_release = None
            for number in tenant_numbers:
                if (number.get('phone_number') == phone_number_or_sid or 
                    number.get('sid') == phone_number_or_sid):
                    number_to_release = number
                    break
            
            if not number_to_release:
                raise ValueError(f"Number {phone_number_or_sid} not found for tenant {tenant_id}")
            
            # Use the SID for release
            sid = number_to_release.get('sid', phone_number_or_sid)
            return await self.twilio_client.release_phone_number(sid)
            
        except Exception as e:
            self.logger.error(f"Error releasing number {phone_number_or_sid} for tenant {tenant_id}: {e}")
            raise
    
    def is_recommended_number(self, phone_number: Dict[str, Any]) -> bool:
        """
        Public method to check if a number is recommended.
        
        Args:
            phone_number: Phone number data dictionary
            
        Returns:
            True if the number is recommended
        """
        return self._is_recommended_number(phone_number)
    
    def _is_recommended_number(self, phone_number: Dict[str, Any]) -> bool:
        """
        Determine if a phone number is recommended based on capabilities.
        
        Args:
            phone_number: Phone number data with capabilities
            
        Returns:
            True if recommended (has voice and SMS capabilities)
        """
        capabilities = phone_number.get('capabilities', {})
        return capabilities.get('voice', False) and capabilities.get('sms', False)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + 'Z'
    
    # Database-related methods (require db_session)
    
    async def provision_phone_number_for_agent(self, phone_number: str, agent_id: str) -> Dict[str, Any]:
        """
        Provision a phone number for a specific voice agent.
        
        Args:
            phone_number: The phone number to provision
            agent_id: The agent ID
            
        Returns:
            Provisioning result
        """
        if not self.db_session:
            raise ValueError("Database session is required for agent operations")
        
        try:
            # Find the agent
            agent = self.db_session.query(VoiceAgent).filter(VoiceAgent.id == agent_id).first()
            if not agent:
                self.db_session.rollback()
                return {
                    'status': 'error',
                    'error': f'Agent {agent_id} not found'
                }
            
            # Check if agent already has a phone number
            if agent.phone_number:
                self.db_session.rollback()
                return {
                    'status': 'error',
                    'error': f'Agent {agent_id} already has phone number {agent.phone_number}'
                }
            
            # Provision via Twilio
            friendly_name = f"Number for Agent {agent.name}"
            twilio_result = await self.twilio_client.provision_phone_number(
                phone_number=phone_number,
                friendly_name=friendly_name
            )
            
            # Update agent record
            agent.phone_number = phone_number
            if not agent.configuration:
                agent.configuration = {}
            
            agent.configuration['phone_config'] = {
                'phone_sid': twilio_result['sid'],
                'twilio_phone_number': phone_number,
                'provisioned_at': self._get_current_timestamp()
            }
            
            self.db_session.commit()
            
            return {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': twilio_result['sid'],
                'agent_id': agent_id
            }
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Error provisioning phone for agent {agent_id}: {e}")
            raise
    
    async def get_agent_phone_number(self, agent_id: str) -> Optional[str]:
        """
        Get the phone number for a specific agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            Phone number if found, None otherwise
        """
        if not self.db_session:
            return None
        
        try:
            agent = self.db_session.query(VoiceAgent).filter(VoiceAgent.id == agent_id).first()
            return agent.phone_number if agent else None
            
        except Exception as e:
            self.logger.error(f"Error getting phone number for agent {agent_id}: {e}")
            return None
    
    async def release_agent_phone_number(self, agent_id: str) -> bool:
        """
        Release the phone number from a specific agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            True if successfully released
        """
        if not self.db_session:
            raise ValueError("Database session is required for agent operations")
        
        try:
            # Find the agent
            agent = self.db_session.query(VoiceAgent).filter(VoiceAgent.id == agent_id).first()
            if not agent:
                self.db_session.rollback()
                raise ValueError(f"Agent {agent_id} not found")
            
            if not agent.phone_number:
                self.db_session.rollback()
                raise ValueError(f"Agent {agent_id} has no phone number to release")
            
            # Get phone SID from configuration
            phone_config = agent.configuration.get('phone_config', {})
            phone_sid = phone_config.get('phone_sid')
            
            if phone_sid:
                # Release via Twilio
                await self.twilio_client.release_phone_number(phone_sid)
            
            # Update agent record
            agent.phone_number = None
            if 'phone_config' in agent.configuration:
                del agent.configuration['phone_config']
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Error releasing phone number for agent {agent_id}: {e}")
            raise
    
    async def list_agents_with_phone_numbers(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all agents that have phone numbers.
        
        Args:
            tenant_id: Optional tenant filter
            
        Returns:
            List of agents with their phone number information
        """
        if not self.db_session:
            return []
        
        try:
            query = self.db_session.query(VoiceAgent).filter(VoiceAgent.phone_number.isnot(None))
            
            if tenant_id:
                query = query.filter(VoiceAgent.tenant_id == tenant_id)
            
            agents = query.all()
            
            result = []
            for agent in agents:
                phone_config = agent.configuration.get('phone_config', {})
                result.append({
                    'agent_id': str(agent.id),
                    'agent_name': agent.name,
                    'phone_number': agent.phone_number,
                    'phone_sid': phone_config.get('phone_sid'),
                    'status': agent.status,
                    'is_active': agent.is_active,
                    'provisioned_at': phone_config.get('provisioned_at')
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error listing agents with phone numbers: {e}")
            return []