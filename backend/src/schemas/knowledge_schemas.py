"""
Knowledge Base API Schemas
Pydantic models for knowledge base API endpoints
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base data"""
    knowledge_base: Dict[str, Any] = Field(description="Knowledge base data organized by categories")
    stats: Dict[str, Any] = Field(description="Knowledge base statistics and quality metrics")
    size_info: Dict[str, Any] = Field(description="Size and compression information")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")


class KnowledgeCategoryUpdateRequest(BaseModel):
    """Request model for updating a knowledge category"""
    title: str = Field(description="Title of the knowledge category")
    content: str = Field(description="Content for the knowledge category")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    keywords: Optional[List[str]] = Field(None, description="Optional keywords for the category")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Optional structured data")


class KnowledgeExportResponse(BaseModel):
    """Response model for knowledge base export"""
    export_data: Dict[str, Any] = Field(description="Complete exported knowledge base")
    export_format: str = Field(description="Format of the export (json, compressed, etc.)")
    export_timestamp: datetime = Field(description="Timestamp when export was generated")
    total_categories: int = Field(description="Number of categories in export")


class KnowledgeValidationResponse(BaseModel):
    """Response model for knowledge validation results"""
    is_valid: bool = Field(description="Whether the knowledge base is valid")
    validation_errors: List[str] = Field(description="List of validation errors")
    size_validation: Dict[str, Any] = Field(description="Size validation results")
    quality_metrics: Dict[str, Any] = Field(description="Quality assessment metrics")


class KnowledgeMergeRequest(BaseModel):
    """Request model for merging knowledge data"""
    new_knowledge_data: Dict[str, Any] = Field(description="New knowledge data to merge")
    min_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for merging")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing data with lower confidence")


class KnowledgeCrawledContentRequest(BaseModel):
    """Request model for processing crawled content"""
    crawled_data: Dict[str, Any] = Field(description="Raw crawled content to validate and process")
    validation_options: Optional[Dict[str, Any]] = Field(None, description="Optional validation settings")