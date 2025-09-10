"""
Phone Management API Schemas
Pydantic models for phone number and call management endpoints
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PhoneNumberSearchRequest(BaseModel):
    """Request model for searching available phone numbers"""
    area_code: Optional[str] = Field(None, description="Preferred area code (e.g., '415')")
    contains: Optional[str] = Field(None, description="Digit pattern the number should contain")
    country_code: str = Field(default="US", description="Country code for the phone number")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results to return")


class PhoneNumberInfo(BaseModel):
    """Model for phone number information"""
    phone_number: str = Field(description="Phone number in E.164 format")
    friendly_name: Optional[str] = Field(None, description="Human-readable name for the number")
    capabilities: Dict[str, bool] = Field(description="Voice/SMS capabilities")
    locality: Optional[str] = Field(None, description="City/locality of the number")
    region: Optional[str] = Field(None, description="State/region of the number")
    iso_country: Optional[str] = Field(None, description="ISO country code")
    price: Optional[str] = Field(None, description="Monthly cost of the number")


class AvailableNumbersResponse(BaseModel):
    """Response model for available phone numbers search"""
    available_numbers: List[PhoneNumberInfo] = Field(description="List of available phone numbers")
    search_criteria: PhoneNumberSearchRequest = Field(description="Search criteria used")
    total_found: int = Field(description="Total number of available numbers found")


class PhoneProvisionRequest(BaseModel):
    """Request model for provisioning a phone number"""
    phone_number: str = Field(description="Phone number to provision (E.164 format)")
    friendly_name: Optional[str] = Field(None, description="Human-readable name for the number")
    agent_id: Optional[str] = Field(None, description="Optional agent ID to associate with number")


class PhoneProvisionResponse(BaseModel):
    """Response model for phone number provisioning"""
    status: str = Field(description="Provision status (success/error)")
    phone_number: str = Field(description="Provisioned phone number")
    phone_sid: Optional[str] = Field(None, description="Twilio SID for the provisioned number")
    friendly_name: Optional[str] = Field(None, description="Human-readable name")
    capabilities: Dict[str, bool] = Field(description="Voice/SMS capabilities")
    webhook_urls: Optional[Dict[str, str]] = Field(None, description="Configured webhook URLs")
    error: Optional[str] = Field(None, description="Error message if provisioning failed")


class PhoneStatusResponse(BaseModel):
    """Response model for phone number status"""
    phone_number: str = Field(description="Phone number")
    status: str = Field(description="Current status (active/inactive/error)")
    phone_sid: Optional[str] = Field(None, description="Twilio SID")
    friendly_name: Optional[str] = Field(None, description="Human-readable name")
    capabilities: Dict[str, bool] = Field(description="Voice/SMS capabilities")
    configuration: Dict[str, Any] = Field(description="Current configuration")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    agent_id: Optional[str] = Field(None, description="Associated agent ID")


class CallRoutingConfig(BaseModel):
    """Model for call routing configuration"""
    phone_number: str = Field(description="Phone number to configure")
    agent_id: Optional[str] = Field(None, description="Agent ID to route calls to")
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL for call handling")
    voice_url: Optional[str] = Field(None, description="Voice handling URL")
    status_callback_url: Optional[str] = Field(None, description="Status callback URL")
    record_calls: bool = Field(default=False, description="Whether to record calls")
    transcribe_calls: bool = Field(default=False, description="Whether to transcribe calls")


class CallRoutingResponse(BaseModel):
    """Response model for call routing configuration"""
    status: str = Field(description="Configuration status (success/error)")
    phone_number: str = Field(description="Configured phone number")
    configuration: CallRoutingConfig = Field(description="Applied configuration")
    webhook_urls: Dict[str, str] = Field(description="Generated webhook URLs")
    error: Optional[str] = Field(None, description="Error message if configuration failed")


class PhoneServiceStatusResponse(BaseModel):
    """Response model for phone service status"""
    status: str = Field(description="Service status (healthy/mock/error)")
    service_type: str = Field(description="Service type (real/mock/unknown)")
    twilio_status: Dict[str, Any] = Field(description="Underlying Twilio service status")
    active_numbers: int = Field(description="Number of active phone numbers")
    last_check: datetime = Field(description="Last status check timestamp")


class PhoneNumberListResponse(BaseModel):
    """Response model for listing tenant phone numbers"""
    phone_numbers: List[PhoneStatusResponse] = Field(description="List of tenant phone numbers")
    total: int = Field(description="Total number of phone numbers")
    active_count: int = Field(description="Number of active phone numbers")
    tenant_id: str = Field(description="Tenant ID for the numbers")


class BulkPhoneActionRequest(BaseModel):
    """Request model for bulk phone number actions"""
    phone_numbers: List[str] = Field(description="List of phone numbers to act on")
    action: str = Field(description="Action to perform (release/configure/status)")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Optional configuration for bulk actions")


class BulkPhoneActionResponse(BaseModel):
    """Response model for bulk phone number actions"""
    action: str = Field(description="Action that was performed")
    results: List[Dict[str, Any]] = Field(description="Results for each phone number")
    success_count: int = Field(description="Number of successful operations")
    error_count: int = Field(description="Number of failed operations")
    total_count: int = Field(description="Total number of operations attempted")