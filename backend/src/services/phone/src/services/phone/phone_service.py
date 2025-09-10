"""Phone service for managing phone numbers and call routing."""

from typing import List, Optional, Dict, Any
import logging
from .twilio_client import TwilioPhoneClient
from src.models.voice_agent import VoiceAgent
from src.models.tenant import Tenant
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PhoneService:
    """Service for managing phone numbers and call operations."""
    
    def __init__(
        self, 
        twilio_client: Optional[TwilioPhoneClient] = None,
        db_session: Optional[Session] = None
    ):
        """Initialize phone service.
        
        Args:
            twilio_client: Twilio client instance (creates default if None)
            db_session: Database session for agent/phone number persistence
        """
        self.twilio_client = twilio_client or TwilioPhoneClient()
        self.db_session = db_session
        
    async def search_available_numbers(
        self,
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search for available phone numbers based on preferences.
        
        Args:
            preferences: Search criteria including:
                - area_code: Preferred area code
                - contains: Pattern that number must contain
                - country_code: Country code (default: US)
                - limit: Maximum results to return
                
        Returns:
            List of available phone numbers with details
        """
        try:
            area_code = preferences.get("area_code")
            contains = preferences.get("contains")
            country_code = preferences.get("country_code", "US")
            limit = preferences.get("limit", 20)
            
            logger.info(f"Searching for phone numbers with area_code={area_code}, contains={contains}")
            
            available_numbers = await self.twilio_client.search_phone_numbers(
                area_code=area_code,
                contains=contains,
                country_code=country_code,
                limit=limit
            )
            
            # Enhance results with additional metadata
            enhanced_numbers = []
            for number in available_numbers:
                enhanced_number = {
                    **number,
                    "cost_per_month": "$1.00",  # Standard Twilio pricing
                    "setup_fee": "$0.00",
                    "recommended": self._is_recommended_number(number)
                }
                enhanced_numbers.append(enhanced_number)
                
            return enhanced_numbers
            
        except Exception as e:
            logger.error(f"Failed to search available numbers: {e}")
            raise
            
    async def provision_number(
        self,
        phone_number: str,
        tenant_id: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Provision a phone number for a tenant.
        
        Args:
            phone_number: Phone number to provision
            tenant_id: ID of the tenant requesting the number
            configuration: Optional configuration including webhook URLs
            
        Returns:
            Provisioned number details
        """
        try:
            config = configuration or {}
            
            # Generate webhook URLs based on tenant
            voice_url = config.get("voice_url") or f"/webhook/voice/{tenant_id}"
            sms_url = config.get("sms_url") or f"/webhook/sms/{tenant_id}"
            friendly_name = config.get("friendly_name") or f"Number for Tenant {tenant_id}"
            
            logger.info(f"Provisioning number {phone_number} for tenant {tenant_id}")
            
            provisioned_number = await self.twilio_client.provision_phone_number(
                phone_number=phone_number,
                voice_url=voice_url,
                sms_url=sms_url,
                friendly_name=friendly_name
            )
            
            # Add tenant information to result
            result = {
                **provisioned_number,
                "tenant_id": tenant_id,
                "provisioned_at": self._get_current_timestamp(),
                "monthly_cost": "$1.00"
            }
            
            logger.info(f"Successfully provisioned {phone_number} for tenant {tenant_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to provision number {phone_number} for tenant {tenant_id}: {e}")
            raise
            
    async def get_tenant_numbers(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all phone numbers provisioned for a tenant.
        
        Args:
            tenant_id: Tenant ID to filter by
            
        Returns:
            List of tenant's phone numbers
        """
        try:
            all_numbers = await self.twilio_client.list_provisioned_numbers()
            
            # Filter by tenant (based on friendly name pattern)
            tenant_numbers = [
                {
                    **number,
                    "tenant_id": tenant_id,
                    "monthly_cost": "$1.00"
                }
                for number in all_numbers
                if f"Tenant {tenant_id}" in (number.get("friendly_name", "") or "")
            ]
            
            return tenant_numbers
            
        except Exception as e:
            logger.error(f"Failed to get numbers for tenant {tenant_id}: {e}")
            raise
            
    async def release_number(self, number_sid: str, tenant_id: str) -> bool:
        """Release a phone number.
        
        Args:
            number_sid: SID of the number to release
            tenant_id: Tenant ID (for authorization)
            
        Returns:
            True if successfully released
        """
        try:
            # Verify tenant owns this number
            tenant_numbers = await self.get_tenant_numbers(tenant_id)
            number_sids = [num["sid"] for num in tenant_numbers]
            
            if number_sid not in number_sids:
                raise ValueError(f"Number {number_sid} not found for tenant {tenant_id}")
                
            success = await self.twilio_client.release_phone_number(number_sid)
            
            if success:
                logger.info(f"Released number {number_sid} for tenant {tenant_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to release number {number_sid} for tenant {tenant_id}: {e}")
            raise
            
    async def update_number_configuration(
        self,
        number_sid: str,
        tenant_id: str,
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update configuration for a phone number.
        
        Args:
            number_sid: SID of the number to update
            tenant_id: Tenant ID (for authorization)
            configuration: New configuration settings
            
        Returns:
            Updated number details
        """
        try:
            # Verify tenant owns this number
            tenant_numbers = await self.get_tenant_numbers(tenant_id)
            number_sids = [num["sid"] for num in tenant_numbers]
            
            if number_sid not in number_sids:
                raise ValueError(f"Number {number_sid} not found for tenant {tenant_id}")
                
            voice_url = configuration.get("voice_url")
            sms_url = configuration.get("sms_url")
            
            updated_number = await self.twilio_client.update_phone_number_webhooks(
                number_sid=number_sid,
                voice_url=voice_url,
                sms_url=sms_url
            )
            
            logger.info(f"Updated configuration for number {number_sid}")
            return updated_number
            
        except Exception as e:
            logger.error(f"Failed to update number {number_sid} for tenant {tenant_id}: {e}")
            raise
            
    def _is_recommended_number(self, number: Dict[str, Any]) -> bool:
        """Determine if a number is recommended based on capabilities.
        
        Args:
            number: Phone number details
            
        Returns:
            True if number is recommended
        """
        capabilities = number.get("capabilities", {})
        
        # Recommend numbers with both voice and SMS capabilities
        return capabilities.get("voice", False) and capabilities.get("sms", False)
        
    async def provision_phone_number_for_agent(self, 
                                    phone_number: str, 
                                    agent_id: str,
                                    db_session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Provision phone number for agent and update database
        
        Args:
            phone_number: Phone number to provision
            agent_id: Agent ID to associate with
            db_session: Database session (uses self.db_session if not provided)
            
        Returns:
            Provisioning result with phone_sid and phone_number
        """
        session = db_session or self.db_session
        if not session:
            raise ValueError("Database session is required for agent phone provisioning")
        
        try:
            # Get the voice agent from database
            agent = session.query(VoiceAgent).filter(VoiceAgent.id == agent_id).first()
            if not agent:
                raise ValueError(f"Voice agent {agent_id} not found")
            
            # Check if agent already has a phone number
            if agent.phone_number:
                raise ValueError(f"Agent {agent_id} already has phone number {agent.phone_number}")
            
            # Provision the phone number via Twilio
            result = await self.provision_number(
                phone_number=phone_number,
                tenant_id=str(agent.tenant_id),
                configuration={
                    'friendly_name': f'Agent {agent.name}',
                    'agent_id': agent_id
                }
            )
            
            # Update the agent record with the phone number
            agent.phone_number = phone_number
            agent.updated_at = self._get_current_datetime()
            
            # Add phone number configuration to agent config
            if not agent.configuration:
                agent.configuration = {}
            agent.configuration['phone_config'] = {
                'phone_sid': result.get('sid'),
                'twilio_phone_number': phone_number,
                'provisioned_at': self._get_current_timestamp()
            }
            
            session.commit()
            
            logger.info(f"Successfully provisioned phone {phone_number} for agent {agent_id}")
            
            return {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': result.get('sid'),
                'agent_id': agent_id,
                'agent_name': agent.name
            }
            
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to provision phone for agent {agent_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def configure_agent_webhook(self, 
                                    phone_sid: str, 
                                    agent_id: str) -> Dict[str, Any]:
        """
        Configure webhook for agent phone number
        
        Args:
            phone_sid: Phone number SID
            agent_id: Agent ID for webhook routing
            
        Returns:
            Configuration result with webhook_url
        """
        try:
            # Generate webhook URL for the agent
            webhook_url = f"https://api.voice-agent-platform.com/webhook/agent/{agent_id}/voice"
            sms_webhook_url = f"https://api.voice-agent-platform.com/webhook/agent/{agent_id}/sms"
            
            # Update the phone number with webhook configuration
            result = await self.twilio_client.update_phone_number_webhooks(
                number_sid=phone_sid,
                voice_url=webhook_url,
                sms_url=sms_webhook_url
            )
            
            return {
                'status': 'success',
                'phone_sid': phone_sid,
                'agent_id': agent_id,
                'webhook_url': webhook_url,
                'sms_webhook_url': sms_webhook_url
            }
            
        except Exception as e:
            logger.error(f"Failed to configure webhook for agent {agent_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
        
    def _get_current_datetime(self):
        """Get current datetime object.
        
        Returns:
            Current datetime object
        """
        from datetime import datetime
        return datetime.utcnow()
        
    async def get_agent_phone_number(self, agent_id: str, db_session: Optional[Session] = None) -> Optional[str]:
        """Get phone number associated with an agent.
        
        Args:
            agent_id: Agent ID to look up
            db_session: Database session (uses self.db_session if not provided)
            
        Returns:
            Phone number string or None if not found
        """
        session = db_session or self.db_session
        if not session:
            return None
            
        try:
            agent = session.query(VoiceAgent).filter(VoiceAgent.id == agent_id).first()
            return agent.phone_number if agent else None
        except Exception as e:
            logger.error(f"Failed to get phone number for agent {agent_id}: {str(e)}")
            return None
            
    async def release_agent_phone_number(self, agent_id: str, db_session: Optional[Session] = None) -> bool:
        """Release phone number from an agent and update database.
        
        Args:
            agent_id: Agent ID to release phone number from
            db_session: Database session (uses self.db_session if not provided)
            
        Returns:
            True if successfully released
        """
        session = db_session or self.db_session
        if not session:
            raise ValueError("Database session is required for agent phone release")
            
        try:
            # Get the voice agent from database
            agent = session.query(VoiceAgent).filter(VoiceAgent.id == agent_id).first()
            if not agent:
                raise ValueError(f"Voice agent {agent_id} not found")
                
            if not agent.phone_number:
                raise ValueError(f"Agent {agent_id} has no phone number to release")
                
            # Get phone configuration to find SID
            phone_config = agent.configuration.get('phone_config', {}) if agent.configuration else {}
            phone_sid = phone_config.get('phone_sid')
            
            if phone_sid:
                # Release the phone number via Twilio
                success = await self.twilio_client.release_phone_number(phone_sid)
                if not success:
                    logger.warning(f"Failed to release phone number via Twilio for agent {agent_id}")
            
            # Update the agent record to remove phone number
            agent.phone_number = None
            agent.updated_at = self._get_current_datetime()
            
            # Remove phone configuration
            if agent.configuration and 'phone_config' in agent.configuration:
                del agent.configuration['phone_config']
                
            session.commit()
            
            logger.info(f"Successfully released phone number for agent {agent_id}")
            return True
            
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to release phone for agent {agent_id}: {str(e)}")
            raise
            
    async def provision_phone_number(self, 
                                   phone_number: str, 
                                   agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Provision phone number for use (pipeline-compatible method)
        
        This method is called by the agent pipeline and should provision a phone number
        either for a specific agent or just generally.
        
        Args:
            phone_number: Phone number to provision
            agent_id: Optional agent ID to associate with
            
        Returns:
            Provisioning result with phone_sid and phone_number
        """
        try:
            # If agent_id provided, use the agent-specific method
            if agent_id:
                return await self.provision_phone_number_for_agent(phone_number, agent_id)
            
            # Otherwise, provision for general use (fallback for pipeline compatibility)
            result = await self.twilio_client.provision_phone_number(
                phone_number=phone_number,
                friendly_name="Agent Pipeline Number"
            )
            
            return {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': result.get('sid'),
                'friendly_name': result.get('friendly_name'),
                'capabilities': result.get('capabilities', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to provision phone number {phone_number}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def preallocate_numbers(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preallocate phone numbers for performance optimization
        
        Args:
            preferences: Number preferences including count, country_code, etc.
            
        Returns:
            Result with preallocated numbers or count
        """
        try:
            count = preferences.get('count', 5)
            country_code = preferences.get('country_code', 'US')
            
            # Search for available numbers
            available_numbers = await self.search_available_numbers({
                'country_code': country_code,
                'limit': count
            })
            
            if len(available_numbers) >= count:
                # Return the first `count` numbers for preallocation
                preallocated = available_numbers[:count]
                
                logger.info(f"Preallocated {len(preallocated)} phone numbers")
                
                return {
                    'status': 'success',
                    'preallocated_count': len(preallocated),
                    'numbers': preallocated
                }
            else:
                # Not enough numbers available
                logger.warning(f"Only {len(available_numbers)} numbers available, requested {count}")
                return {
                    'status': 'partial',
                    'preallocated_count': len(available_numbers),
                    'numbers': available_numbers
                }
                
        except Exception as e:
            logger.error(f"Failed to preallocate numbers: {str(e)}")
            return {
                'status': 'error',
                'preallocated_count': 0,
                'error': str(e)
            }

    async def list_agents_with_phone_numbers(self, tenant_id: Optional[str] = None, db_session: Optional[Session] = None) -> List[Dict[str, Any]]:
        """List all agents with their phone numbers.
        
        Args:
            tenant_id: Optional tenant ID to filter by
            db_session: Database session (uses self.db_session if not provided)
            
        Returns:
            List of agents with phone number information
        """
        session = db_session or self.db_session
        if not session:
            return []
            
        try:
            query = session.query(VoiceAgent).filter(VoiceAgent.phone_number.isnot(None))
            
            if tenant_id:
                query = query.filter(VoiceAgent.tenant_id == tenant_id)
                
            agents = query.all()
            
            result = []
            for agent in agents:
                phone_config = agent.configuration.get('phone_config', {}) if agent.configuration else {}
                result.append({
                    'agent_id': str(agent.id),
                    'agent_name': agent.name,
                    'tenant_id': str(agent.tenant_id),
                    'phone_number': agent.phone_number,
                    'phone_sid': phone_config.get('phone_sid'),
                    'status': agent.status,
                    'is_active': agent.is_active,
                    'provisioned_at': phone_config.get('provisioned_at')
                })
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to list agents with phone numbers: {str(e)}")
            return []