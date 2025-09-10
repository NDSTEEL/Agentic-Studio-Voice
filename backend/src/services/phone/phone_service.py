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
        """Search for available phone numbers based on preferences."""
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
            
            # Enhance results with cost and recommendation info
            enhanced_results = []
            for number in available_numbers:
                enhanced_number = number.copy()
                enhanced_number['cost_per_month'] = '$1.00'
                enhanced_number['recommended'] = self._is_recommended_number(number)
                enhanced_results.append(enhanced_number)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Failed to search available numbers: {e}")
            raise
    
    async def provision_phone_number(self, 
                                   phone_number: str, 
                                   agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Provision phone number for use (pipeline-compatible method)
        """
        try:
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
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status for monitoring."""
        try:
            twilio_status = self.twilio_client.get_service_status()
            service_type = twilio_status.get('service_type', 'unknown')
            
            return {
                "status": "healthy" if service_type == 'real' else "mock",
                "service_type": service_type,
                "twilio_status": twilio_status
            }
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {
                "status": "error",
                "service_type": "unknown",
                "error": str(e)
            }

    async def provision_phone_number_for_agent(self, phone_number: str, agent_id: str) -> Dict[str, Any]:
        """
        Provision a phone number for a specific voice agent.
        
        Args:
            phone_number: The phone number to provision
            agent_id: The ID of the voice agent
            
        Returns:
            Dict with status and provisioning details
        """
        if not self.db_session:
            raise ValueError("Database session is required for agent phone number operations")
        
        try:
            # Convert agent_id to UUID
            try:
                agent_uuid = uuid.UUID(agent_id)
            except ValueError as ve:
                self.db_session.rollback()
                return {
                    'status': 'error',
                    'error': f'Invalid agent ID format: {agent_id}'
                }
                
            # Find the agent
            agent = self.db_session.query(VoiceAgent).filter(
                VoiceAgent.id == agent_uuid
            ).first()
            
            if not agent:
                self.db_session.rollback()
                return {
                    'status': 'error',
                    'error': f'Agent with ID {agent_id} not found'
                }
            
            # Check if agent already has a phone number
            if agent.phone_number:
                self.db_session.rollback()
                return {
                    'status': 'error',
                    'error': f'Agent {agent.name} already has phone number {agent.phone_number}'
                }
            
            # Provision the phone number with Twilio
            twilio_result = await self.twilio_client.provision_phone_number(
                phone_number=phone_number,
                friendly_name=f"Number for Agent {agent.name}"
            )
            
            # Update the agent with the phone number and configuration
            agent.phone_number = phone_number
            
            # Add phone configuration to agent
            if not agent.configuration:
                agent.configuration = {}
            
            agent.configuration['phone_config'] = {
                'phone_sid': twilio_result.get('sid'),
                'twilio_phone_number': phone_number,
                'provisioned_at': datetime.utcnow().isoformat(),
                'friendly_name': twilio_result.get('friendly_name')
            }
            
            # Mark configuration as modified for SQLAlchemy (skip for mock objects in tests)
            if hasattr(agent, '_sa_instance_state'):
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(agent, 'configuration')
            
            # Commit the database changes
            self.db_session.commit()
            
            logger.info(f"Successfully provisioned phone number {phone_number} for agent {agent.name}")
            
            return {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': twilio_result.get('sid'),
                'agent_id': agent_id,
                'agent_name': agent.name,
                'provisioned_at': agent.configuration['phone_config']['provisioned_at']
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to provision phone number {phone_number} for agent {agent_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def get_agent_phone_number(self, agent_id: str) -> Optional[str]:
        """
        Get the phone number associated with a voice agent.
        
        Args:
            agent_id: The ID of the voice agent
            
        Returns:
            The phone number string, or None if agent not found or has no phone
        """
        if not self.db_session:
            return None
        
        try:
            agent = self.db_session.query(VoiceAgent).filter(
                VoiceAgent.id == uuid.UUID(agent_id)
            ).first()
            
            if not agent:
                return None
                
            return agent.phone_number
            
        except Exception as e:
            logger.error(f"Failed to get phone number for agent {agent_id}: {str(e)}")
            return None

    async def release_agent_phone_number(self, agent_id: str) -> bool:
        """
        Release the phone number from a voice agent.
        
        Args:
            agent_id: The ID of the voice agent
            
        Returns:
            True if successfully released, False otherwise
            
        Raises:
            ValueError: If agent not found or has no phone number to release
        """
        if not self.db_session:
            raise ValueError("Database session is required for agent phone number operations")
        
        try:
            # Convert agent_id to UUID
            try:
                agent_uuid = uuid.UUID(agent_id)
            except ValueError as ve:
                self.db_session.rollback()
                raise ValueError(f"Invalid agent ID format: {agent_id}")
                
            # Find the agent
            agent = self.db_session.query(VoiceAgent).filter(
                VoiceAgent.id == agent_uuid
            ).first()
            
            if not agent:
                self.db_session.rollback()
                raise ValueError(f"Agent with ID {agent_id} not found")
            
            # Check if agent has a phone number
            if not agent.phone_number:
                self.db_session.rollback()
                raise ValueError(f"Agent {agent.name} has no phone number to release")
            
            # Get phone SID from configuration for Twilio release
            phone_sid = None
            if agent.configuration and 'phone_config' in agent.configuration:
                phone_sid = agent.configuration['phone_config'].get('phone_sid')
            
            # Release from Twilio if we have the SID
            if phone_sid:
                twilio_released = await self.twilio_client.release_phone_number(phone_sid)
                if not twilio_released:
                    logger.warning(f"Failed to release phone number {phone_sid} from Twilio, but proceeding to clear from agent")
            
            # Clear the phone number from the agent
            agent.phone_number = None
            
            # Remove phone configuration
            if agent.configuration and 'phone_config' in agent.configuration:
                del agent.configuration['phone_config']
                # Mark configuration as modified for SQLAlchemy (skip for mock objects in tests)
                if hasattr(agent, '_sa_instance_state'):
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(agent, 'configuration')
            
            # Commit the database changes
            self.db_session.commit()
            
            logger.info(f"Successfully released phone number for agent {agent.name}")
            return True
            
        except ValueError:
            # Re-raise ValueError as it's expected
            raise
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to release phone number for agent {agent_id}: {str(e)}")
            return False

    async def list_agents_with_phone_numbers(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all voice agents that have phone numbers assigned.
        
        Args:
            tenant_id: Optional tenant ID to filter by
            
        Returns:
            List of agent dictionaries with phone number information
        """
        if not self.db_session:
            return []
        
        try:
            # Build query to find agents with phone numbers
            query = self.db_session.query(VoiceAgent).filter(
                VoiceAgent.phone_number.is_not(None)
            )
            
            # Apply tenant filter if provided
            if tenant_id:
                query = query.filter(VoiceAgent.tenant_id == uuid.UUID(tenant_id))
            
            agents = query.all()
            
            result = []
            for agent in agents:
                phone_config = agent.configuration.get('phone_config', {}) if agent.configuration else {}
                
                agent_info = {
                    'agent_id': str(agent.id),
                    'agent_name': agent.name,
                    'tenant_id': str(agent.tenant_id),
                    'phone_number': agent.phone_number,
                    'phone_sid': phone_config.get('phone_sid'),
                    'status': agent.status,
                    'is_active': agent.is_active,
                    'provisioned_at': phone_config.get('provisioned_at'),
                    'friendly_name': phone_config.get('friendly_name')
                }
                
                result.append(agent_info)
            
            logger.info(f"Found {len(result)} agents with phone numbers")
            return result
            
        except Exception as e:
            logger.error(f"Failed to list agents with phone numbers: {str(e)}")
            return []

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        return datetime.utcnow().isoformat() + 'Z'

    def _is_recommended_number(self, number: Dict[str, Any]) -> bool:
        """Check if a phone number is recommended based on capabilities."""
        capabilities = number.get('capabilities', {})
        return capabilities.get('voice', False) and capabilities.get('sms', False)

    async def provision_number(self, phone_number: str, tenant_id: str) -> Dict[str, Any]:
        """Provision a phone number for a tenant."""
        try:
            result = await self.twilio_client.provision_phone_number(
                phone_number=phone_number,
                friendly_name=f"Number for Tenant {tenant_id}"
            )
            
            return {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': result.get('sid'),
                'tenant_id': tenant_id,
                'friendly_name': result.get('friendly_name'),
                'capabilities': result.get('capabilities', {}),
                'provisioned_at': self._get_current_timestamp(),
                'monthly_cost': '$1.00'
            }
            
        except Exception as e:
            logger.error(f"Failed to provision phone number {phone_number} for tenant {tenant_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def get_tenant_numbers(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all phone numbers for a specific tenant."""
        try:
            all_numbers = await self.twilio_client.list_provisioned_numbers()
            
            # Filter numbers by tenant based on friendly_name
            tenant_numbers = []
            for number in all_numbers:
                friendly_name = number.get('friendly_name', '')
                if f"Tenant {tenant_id}" in friendly_name:
                    enhanced_number = number.copy()
                    enhanced_number['tenant_id'] = tenant_id
                    tenant_numbers.append(enhanced_number)
            
            return tenant_numbers
            
        except Exception as e:
            logger.error(f"Failed to get tenant numbers for {tenant_id}: {str(e)}")
            return []

    async def release_number(self, number_sid: str, tenant_id: str) -> bool:
        """Release a phone number owned by a tenant."""
        try:
            # Verify the number belongs to the tenant
            tenant_numbers = await self.get_tenant_numbers(tenant_id)
            number_found = any(num['sid'] == number_sid for num in tenant_numbers)
            
            if not number_found:
                raise ValueError(f"Number {number_sid} not found for tenant {tenant_id}")
            
            # Release the number
            return await self.twilio_client.release_phone_number(number_sid)
            
        except Exception as e:
            logger.error(f"Failed to release number {number_sid} for tenant {tenant_id}: {str(e)}")
            raise

    async def get_phone_numbers_by_tenant(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all phone numbers associated with a specific tenant.
        
        This method combines both direct tenant phone numbers and agent-associated numbers.
        
        Args:
            tenant_id: The tenant ID to get phone numbers for
            
        Returns:
            List of phone number dictionaries with details
        """
        try:
            logger.info(f"Getting phone numbers for tenant {tenant_id}")
            
            # Get numbers directly provisioned for tenant
            tenant_numbers = await self.get_tenant_numbers(tenant_id)
            
            # Get numbers associated with tenant's agents
            agent_numbers = await self.list_agents_with_phone_numbers(tenant_id)
            
            # Combine and format results
            all_numbers = []
            
            # Add direct tenant numbers
            for number in tenant_numbers:
                all_numbers.append({
                    'phone_number': number.get('phone_number'),
                    'phone_sid': number.get('sid'),
                    'tenant_id': tenant_id,
                    'status': number.get('status', 'active'),
                    'type': 'tenant',
                    'friendly_name': number.get('friendly_name'),
                    'capabilities': number.get('capabilities', {}),
                    'voice_url': number.get('voice_url'),
                    'sms_url': number.get('sms_url'),
                    'assigned_to': None,
                    'assigned_to_type': None,
                    'provisioned_at': self._get_current_timestamp()
                })
            
            # Add agent numbers
            for agent_info in agent_numbers:
                all_numbers.append({
                    'phone_number': agent_info.get('phone_number'),
                    'phone_sid': agent_info.get('phone_sid'),
                    'tenant_id': tenant_id,
                    'status': 'active' if agent_info.get('is_active') else 'inactive',
                    'type': 'agent',
                    'friendly_name': agent_info.get('friendly_name'),
                    'capabilities': {'voice': True, 'sms': True},  # Agent numbers support voice/sms
                    'voice_url': None,  # Agent-specific webhook handling
                    'sms_url': None,
                    'assigned_to': agent_info.get('agent_id'),
                    'assigned_to_type': 'voice_agent',
                    'assigned_to_name': agent_info.get('agent_name'),
                    'provisioned_at': agent_info.get('provisioned_at')
                })
            
            logger.info(f"Found {len(all_numbers)} phone numbers for tenant {tenant_id}")
            return all_numbers
            
        except Exception as e:
            logger.error(f"Failed to get phone numbers for tenant {tenant_id}: {str(e)}")
            return []

    async def update_phone_number_status(self, phone_number: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a phone number.
        
        This method handles status updates for both Twilio-managed numbers
        and database-tracked phone number assignments.
        
        Args:
            phone_number: The phone number to update
            status: New status ('active', 'inactive', 'suspended', 'maintenance')
            
        Returns:
            Dictionary containing update result and phone number details
        """
        try:
            logger.info(f"Updating phone number {phone_number} status to {status}")
            
            valid_statuses = ['active', 'inactive', 'suspended', 'maintenance']
            if status not in valid_statuses:
                return {
                    'status': 'error',
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                }
            
            # Find the phone number in Twilio
            all_numbers = await self.twilio_client.list_provisioned_numbers()
            target_number = None
            
            for number in all_numbers:
                if number.get('phone_number') == phone_number:
                    target_number = number
                    break
            
            if not target_number:
                return {
                    'status': 'error',
                    'error': f'Phone number {phone_number} not found in provisioned numbers'
                }
            
            # For status updates, we handle them differently based on the status
            result = {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': target_number.get('sid'),
                'old_status': target_number.get('status'),
                'new_status': status,
                'updated_at': self._get_current_timestamp()
            }
            
            # If updating agent phone number status, also update the agent
            if self.db_session:
                try:
                    agent = self.db_session.query(VoiceAgent).filter(
                        VoiceAgent.phone_number == phone_number
                    ).first()
                    
                    if agent:
                        # Update agent status based on phone status
                        if status == 'active':
                            agent.is_active = True
                            if agent.status == 'inactive':
                                agent.status = 'active'
                        elif status == 'inactive':
                            agent.is_active = False
                            agent.status = 'inactive'
                        elif status in ['suspended', 'maintenance']:
                            agent.is_active = False
                            # Don't change agent status for temporary phone issues
                        
                        # Update phone configuration with new status
                        if agent.configuration and 'phone_config' in agent.configuration:
                            agent.configuration['phone_config']['status'] = status
                            agent.configuration['phone_config']['status_updated_at'] = result['updated_at']
                            
                            # Mark configuration as modified for SQLAlchemy
                            if hasattr(agent, '_sa_instance_state'):
                                from sqlalchemy.orm.attributes import flag_modified
                                flag_modified(agent, 'configuration')
                        
                        self.db_session.commit()
                        
                        result['agent_updated'] = True
                        result['agent_id'] = str(agent.id)
                        result['agent_name'] = agent.name
                        
                except Exception as db_e:
                    logger.warning(f"Failed to update agent status for {phone_number}: {str(db_e)}")
                    if self.db_session:
                        self.db_session.rollback()
                    result['agent_updated'] = False
                    result['agent_error'] = str(db_e)
            
            logger.info(f"Successfully updated phone number {phone_number} status to {status}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update phone number {phone_number} status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'phone_number': phone_number
            }

    async def delete_phone_number(self, phone_number: str, tenant_id: str) -> Dict[str, Any]:
        """
        Delete a phone number and remove it from both Twilio and local database.
        
        This method handles complete phone number deletion including:
        - Releasing from Twilio
        - Removing agent assignments
        - Cleaning up database records
        
        Args:
            phone_number: The phone number to delete
            tenant_id: The tenant ID that owns the number
            
        Returns:
            Dictionary containing deletion result details
        """
        try:
            logger.info(f"Deleting phone number {phone_number} for tenant {tenant_id}")
            
            # Find the phone number in Twilio
            all_numbers = await self.twilio_client.list_provisioned_numbers()
            target_number = None
            
            for number in all_numbers:
                if number.get('phone_number') == phone_number:
                    target_number = number
                    break
            
            if not target_number:
                return {
                    'status': 'error',
                    'error': f'Phone number {phone_number} not found in provisioned numbers'
                }
            
            number_sid = target_number.get('sid')
            
            # Verify tenant ownership (either direct tenant or agent assignment)
            tenant_numbers = await self.get_phone_numbers_by_tenant(tenant_id)
            owned_number = None
            
            for num in tenant_numbers:
                if num.get('phone_number') == phone_number:
                    owned_number = num
                    break
            
            if not owned_number:
                return {
                    'status': 'error',
                    'error': f'Phone number {phone_number} not owned by tenant {tenant_id}'
                }
            
            deletion_result = {
                'status': 'success',
                'phone_number': phone_number,
                'phone_sid': number_sid,
                'tenant_id': tenant_id,
                'type': owned_number.get('type'),
                'deleted_at': self._get_current_timestamp(),
                'twilio_released': False,
                'agent_updated': False
            }
            
            # If assigned to agent, release from agent first
            if owned_number.get('type') == 'agent' and owned_number.get('assigned_to'):
                try:
                    agent_id = owned_number.get('assigned_to')
                    release_result = await self.release_agent_phone_number(agent_id)
                    deletion_result['agent_updated'] = release_result
                    deletion_result['agent_id'] = agent_id
                    
                except Exception as agent_e:
                    logger.warning(f"Failed to release phone from agent: {str(agent_e)}")
                    deletion_result['agent_error'] = str(agent_e)
            
            # Release from Twilio
            try:
                twilio_released = await self.twilio_client.release_phone_number(number_sid)
                deletion_result['twilio_released'] = twilio_released
                
                if not twilio_released:
                    # Continue with cleanup even if Twilio release failed
                    logger.warning(f"Twilio release failed for {phone_number}, continuing with cleanup")
                    deletion_result['warnings'] = ['Twilio release failed but local cleanup completed']
                    
            except Exception as twilio_e:
                logger.warning(f"Twilio release error for {phone_number}: {str(twilio_e)}")
                deletion_result['twilio_error'] = str(twilio_e)
                deletion_result['warnings'] = [f'Twilio release error: {str(twilio_e)}']
            
            logger.info(f"Successfully deleted phone number {phone_number}")
            return deletion_result
            
        except Exception as e:
            logger.error(f"Failed to delete phone number {phone_number}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'phone_number': phone_number,
                'tenant_id': tenant_id
            }

    async def bulk_phone_operations(self, operations: List[Dict[str, Any]], tenant_id: str) -> Dict[str, Any]:
        """
        Perform bulk operations on phone numbers for a tenant.
        
        Supported operations:
        - provision: Provision new phone numbers
        - release: Release existing phone numbers  
        - update_status: Update phone number status
        - assign_agent: Assign phone number to agent
        - unassign_agent: Remove phone number from agent
        
        Args:
            operations: List of operation dictionaries with 'action' and parameters
            tenant_id: The tenant ID performing the operations
            
        Returns:
            Dictionary containing bulk operation results
        """
        try:
            logger.info(f"Starting bulk phone operations for tenant {tenant_id}")
            
            if not operations:
                return {
                    'status': 'error',
                    'error': 'No operations provided'
                }
            
            if len(operations) > 50:
                return {
                    'status': 'error',
                    'error': 'Maximum 50 operations allowed per bulk request'
                }
            
            results = {
                'status': 'completed',
                'tenant_id': tenant_id,
                'total_operations': len(operations),
                'successful_operations': 0,
                'failed_operations': 0,
                'operation_results': [],
                'started_at': self._get_current_timestamp(),
                'errors': []
            }
            
            for i, operation in enumerate(operations):
                operation_id = f"op_{i + 1}"
                
                try:
                    action = operation.get('action')
                    if not action:
                        raise ValueError("Operation 'action' is required")
                    
                    operation_result = {
                        'operation_id': operation_id,
                        'action': action,
                        'status': 'pending'
                    }
                    
                    # Handle different operation types
                    if action == 'provision':
                        phone_number = operation.get('phone_number')
                        if not phone_number:
                            raise ValueError("'phone_number' is required for provision action")
                        
                        result = await self.provision_number(phone_number, tenant_id)
                        operation_result.update({
                            'status': result.get('status', 'error'),
                            'phone_number': phone_number,
                            'phone_sid': result.get('phone_sid'),
                            'details': result
                        })
                        
                    elif action == 'release':
                        phone_sid = operation.get('phone_sid')
                        if not phone_sid:
                            raise ValueError("'phone_sid' is required for release action")
                        
                        released = await self.release_number(phone_sid, tenant_id)
                        operation_result.update({
                            'status': 'success' if released else 'error',
                            'phone_sid': phone_sid,
                            'released': released
                        })
                        
                    elif action == 'update_status':
                        phone_number = operation.get('phone_number')
                        status = operation.get('status')
                        if not phone_number or not status:
                            raise ValueError("'phone_number' and 'status' are required for update_status action")
                        
                        result = await self.update_phone_number_status(phone_number, status)
                        operation_result.update({
                            'status': result.get('status', 'error'),
                            'phone_number': phone_number,
                            'new_status': status,
                            'details': result
                        })
                        
                    elif action == 'assign_agent':
                        phone_number = operation.get('phone_number')
                        agent_id = operation.get('agent_id')
                        if not phone_number or not agent_id:
                            raise ValueError("'phone_number' and 'agent_id' are required for assign_agent action")
                        
                        result = await self.provision_phone_number_for_agent(phone_number, agent_id)
                        operation_result.update({
                            'status': result.get('status', 'error'),
                            'phone_number': phone_number,
                            'agent_id': agent_id,
                            'details': result
                        })
                        
                    elif action == 'unassign_agent':
                        agent_id = operation.get('agent_id')
                        if not agent_id:
                            raise ValueError("'agent_id' is required for unassign_agent action")
                        
                        released = await self.release_agent_phone_number(agent_id)
                        operation_result.update({
                            'status': 'success' if released else 'error',
                            'agent_id': agent_id,
                            'released': released
                        })
                        
                    else:
                        raise ValueError(f"Unsupported action: {action}")
                    
                    # Track success/failure
                    if operation_result['status'] == 'success':
                        results['successful_operations'] += 1
                    else:
                        results['failed_operations'] += 1
                        
                except Exception as op_e:
                    logger.error(f"Bulk operation {operation_id} failed: {str(op_e)}")
                    operation_result.update({
                        'status': 'error',
                        'error': str(op_e)
                    })
                    results['failed_operations'] += 1
                    results['errors'].append(f"Operation {operation_id}: {str(op_e)}")
                
                results['operation_results'].append(operation_result)
            
            # Set overall status
            if results['failed_operations'] == 0:
                results['status'] = 'success'
            elif results['successful_operations'] == 0:
                results['status'] = 'failed'
            else:
                results['status'] = 'partial_success'
            
            results['completed_at'] = self._get_current_timestamp()
            
            logger.info(f"Bulk operations completed: {results['successful_operations']} success, {results['failed_operations']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Bulk phone operations failed for tenant {tenant_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'tenant_id': tenant_id,
                'total_operations': len(operations) if operations else 0
            }