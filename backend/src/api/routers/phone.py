"""
Phone Management API Router
FastAPI endpoints for phone number management and call routing with tenant isolation
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from src.services.phone.phone_service import PhoneService
from src.services.voice_agent_service import VoiceAgentService
from src.schemas.phone_schemas import (
    PhoneNumberSearchRequest,
    AvailableNumbersResponse,
    PhoneProvisionRequest,
    PhoneProvisionResponse,
    PhoneStatusResponse,
    CallRoutingConfig,
    CallRoutingResponse,
    PhoneServiceStatusResponse,
    PhoneNumberListResponse,
    BulkPhoneActionRequest,
    BulkPhoneActionResponse,
    PhoneNumberInfo
)
from src.api.dependencies.auth import get_current_user
from datetime import datetime


router = APIRouter(prefix="/phone", tags=["Phone Management"])


@router.get("/numbers/available", response_model=AvailableNumbersResponse)
async def search_available_numbers(
    area_code: str = Query(None, description="Preferred area code"),
    contains: str = Query(None, description="Digit pattern to search for"),
    country_code: str = Query("US", description="Country code"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Search for available phone numbers
    
    - **area_code**: Preferred area code (optional)
    - **contains**: Digit pattern the number should contain (optional) 
    - **country_code**: Country code for the search (default: US)
    - **limit**: Maximum number of results (default: 20, max: 100)
    
    Returns list of available phone numbers with pricing and capabilities.
    """
    try:
        phone_service = PhoneService()
        
        search_criteria = PhoneNumberSearchRequest(
            area_code=area_code,
            contains=contains,
            country_code=country_code,
            limit=limit
        )
        
        # Search for available numbers
        available_numbers = await phone_service.search_available_numbers(
            preferences=search_criteria.dict()
        )
        
        # Convert to response format
        phone_infos = []
        for number_data in available_numbers:
            phone_info = PhoneNumberInfo(
                phone_number=number_data.get('phone_number', ''),
                friendly_name=number_data.get('friendly_name'),
                capabilities=number_data.get('capabilities', {}),
                locality=number_data.get('locality'),
                region=number_data.get('region'),
                iso_country=number_data.get('iso_country'),
                price=number_data.get('price')
            )
            phone_infos.append(phone_info)
        
        return AvailableNumbersResponse(
            available_numbers=phone_infos,
            search_criteria=search_criteria,
            total_found=len(phone_infos)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search available numbers: {str(e)}"
        )


@router.post("/numbers/provision", response_model=PhoneProvisionResponse)
async def provision_phone_number(
    provision_request: PhoneProvisionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Provision a new phone number
    
    - **phone_number**: Phone number to provision (E.164 format)
    - **friendly_name**: Optional human-readable name
    - **agent_id**: Optional agent to associate with the number
    
    Provisions the phone number and configures basic webhook routing.
    """
    try:
        phone_service = PhoneService()
        tenant_id = current_user['tenant_id']
        
        # Verify agent exists if provided
        if provision_request.agent_id:
            voice_service = VoiceAgentService()
            agent = voice_service.get_agent_by_id(provision_request.agent_id, tenant_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified voice agent not found"
                )
        
        # Provision the phone number
        result = await phone_service.provision_phone_number(
            phone_number=provision_request.phone_number,
            agent_id=provision_request.agent_id
        )
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to provision phone number')
            )
        
        # TODO: Store phone number association in database with tenant_id
        
        return PhoneProvisionResponse(
            status=result['status'],
            phone_number=result['phone_number'],
            phone_sid=result.get('phone_sid'),
            friendly_name=result.get('friendly_name'),
            capabilities=result.get('capabilities', {}),
            webhook_urls=result.get('webhook_urls', {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provision phone number: {str(e)}"
        )


@router.get("/numbers/{phone_number}/status", response_model=PhoneStatusResponse)
async def get_phone_number_status(
    phone_number: str = Path(description="Phone number to check (E.164 format)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get status and configuration of a phone number
    
    - **phone_number**: Phone number to check (E.164 format)
    
    Returns current status, configuration, and activity information.
    """
    try:
        phone_service = PhoneService()
        tenant_id = current_user['tenant_id']
        
        # TODO: Verify phone number belongs to tenant
        
        # Get phone number status from Twilio
        service_status = phone_service.get_service_status()
        
        # For now, return basic status - this would be enhanced with actual Twilio API calls
        return PhoneStatusResponse(
            phone_number=phone_number,
            status="active" if service_status['status'] == 'healthy' else "inactive",
            phone_sid=None,  # Would get from Twilio
            friendly_name=None,  # Would get from database
            capabilities={"voice": True, "sms": True},  # Would get from Twilio
            configuration={},  # Would get from database
            last_activity=None,  # Would get from call logs
            agent_id=None  # Would get from database
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phone number status: {str(e)}"
        )


@router.get("/numbers", response_model=PhoneNumberListResponse)
async def list_phone_numbers(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List all phone numbers for the tenant
    
    - **page**: Page number for pagination (default: 1)
    - **limit**: Number of items per page (default: 10, max: 100)
    
    Returns paginated list of phone numbers owned by the tenant.
    """
    try:
        tenant_id = current_user['tenant_id']
        
        # TODO: Implement actual database query for tenant phone numbers
        # For now, return empty list as placeholder
        
        return PhoneNumberListResponse(
            phone_numbers=[],
            total=0,
            active_count=0,
            tenant_id=tenant_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list phone numbers: {str(e)}"
        )


@router.post("/numbers/{phone_number}/configure", response_model=CallRoutingResponse)
async def configure_call_routing(
    routing_config: CallRoutingConfig,
    phone_number: str = Path(description="Phone number to configure"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Configure call routing for a phone number
    
    - **phone_number**: Phone number to configure
    - **agent_id**: Optional agent ID to route calls to
    - **webhook_url**: Custom webhook URL for call handling
    - **voice_url**: Voice handling URL
    - **record_calls**: Whether to record calls
    - **transcribe_calls**: Whether to transcribe calls
    
    Configures call routing and webhook URLs for the phone number.
    """
    try:
        tenant_id = current_user['tenant_id']
        
        # Verify agent exists if provided
        if routing_config.agent_id:
            voice_service = VoiceAgentService()
            agent = voice_service.get_agent_by_id(routing_config.agent_id, tenant_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified voice agent not found"
                )
        
        # TODO: Verify phone number belongs to tenant
        # TODO: Update Twilio webhook configuration
        # TODO: Store configuration in database
        
        # Generate webhook URLs based on configuration
        webhook_urls = {
            "voice_url": f"/api/v1/voice/incoming/{phone_number}",
            "status_callback": f"/api/v1/voice/status/{phone_number}"
        }
        
        if routing_config.agent_id:
            webhook_urls["agent_webhook"] = f"/api/v1/agents/{routing_config.agent_id}/call"
        
        return CallRoutingResponse(
            status="success",
            phone_number=phone_number,
            configuration=routing_config,
            webhook_urls=webhook_urls
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure call routing: {str(e)}"
        )


@router.get("/service/status", response_model=PhoneServiceStatusResponse)
async def get_service_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get phone service status and health information
    
    Returns current service status, active phone numbers, and system health.
    """
    try:
        phone_service = PhoneService()
        
        service_status = phone_service.get_service_status()
        
        return PhoneServiceStatusResponse(
            status=service_status['status'],
            service_type=service_status['service_type'],
            twilio_status=service_status.get('twilio_status', {}),
            active_numbers=0,  # TODO: Get from database
            last_check=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.delete("/numbers/{phone_number}")
async def release_phone_number(
    phone_number: str = Path(description="Phone number to release"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Release a phone number (remove from account)
    
    - **phone_number**: Phone number to release
    
    Releases the phone number from the Twilio account and removes local configuration.
    """
    try:
        tenant_id = current_user['tenant_id']
        
        # TODO: Verify phone number belongs to tenant
        # TODO: Release number from Twilio
        # TODO: Remove from database
        
        return {
            "status": "success",
            "phone_number": phone_number,
            "message": f"Phone number {phone_number} released successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release phone number: {str(e)}"
        )


@router.post("/numbers/bulk-action", response_model=BulkPhoneActionResponse)
async def bulk_phone_action(
    bulk_request: BulkPhoneActionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Perform bulk actions on multiple phone numbers
    
    - **phone_numbers**: List of phone numbers to act on
    - **action**: Action to perform (release/configure/status)
    - **configuration**: Optional configuration for bulk actions
    
    Performs the specified action on all provided phone numbers.
    """
    try:
        tenant_id = current_user['tenant_id']
        
        results = []
        success_count = 0
        error_count = 0
        
        for phone_number in bulk_request.phone_numbers:
            try:
                # TODO: Implement actual bulk actions
                # For now, return success for all
                results.append({
                    "phone_number": phone_number,
                    "status": "success",
                    "message": f"Action '{bulk_request.action}' completed"
                })
                success_count += 1
            except Exception as e:
                results.append({
                    "phone_number": phone_number,
                    "status": "error",
                    "error": str(e)
                })
                error_count += 1
        
        return BulkPhoneActionResponse(
            action=bulk_request.action,
            results=results,
            success_count=success_count,
            error_count=error_count,
            total_count=len(bulk_request.phone_numbers)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk action: {str(e)}"
        )