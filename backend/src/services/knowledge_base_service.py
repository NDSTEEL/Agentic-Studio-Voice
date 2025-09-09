"""
Knowledge Base Service
Business logic for knowledge base management and merging
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import gzip
import json

from src.schemas.knowledge_categories import (
    validate_knowledge_category,
    merge_knowledge_categories,
    KNOWLEDGE_CATEGORIES
)


class KnowledgeBaseService:
    """
    Service class for knowledge base operations, validation, and optimization
    """
    
    def __init__(self):
        self.max_size_mb = 50  # Maximum knowledge base size in MB
        self.compression_threshold = 10  # Start compression at 10MB
        
    def validate_crawled_content(self, crawled_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and filter crawled content by knowledge categories
        
        Args:
            crawled_data: Raw crawled content to validate
            
        Returns:
            Dict[str, Any]: Validated and filtered knowledge data
        """
        validated_data = {}
        
        for category, data in crawled_data.items():
            # Only process known categories
            if category not in KNOWLEDGE_CATEGORIES:
                continue
                
            # Skip if data is incomplete
            if not isinstance(data, dict) or not data.get('title') or not data.get('content'):
                continue
                
            # Validate confidence score
            confidence = data.get('confidence_score', 0.0)
            if confidence > 1.0:
                continue
                
            try:
                # Use existing validation logic
                validated_category = validate_knowledge_category(category, data)
                validated_data[category] = validated_category.dict()
            except Exception:
                # Skip invalid categories
                continue
                
        return validated_data
    
    def merge_knowledge_categories(self, existing: Dict[str, Any], new_data: Dict[str, Any], min_confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Merge new crawled knowledge with existing knowledge using confidence scores
        
        Args:
            existing: Current knowledge base
            new_data: New crawled knowledge
            min_confidence_threshold: Minimum confidence to accept updates
            
        Returns:
            Dict[str, Any]: Merged knowledge base
        """
        merged = existing.copy()
        
        for category, new_category_data in new_data.items():
            if not isinstance(new_category_data, dict):
                continue
                
            new_confidence = new_category_data.get('confidence_score', 0.0)
            
            # Only accept high confidence updates
            if new_confidence < min_confidence_threshold:
                continue
                
            # If category doesn't exist, add it
            if category not in merged:
                merged[category] = new_category_data
                continue
                
            # If new data has higher confidence, replace
            existing_confidence = merged[category].get('confidence_score', 0.0)
            if new_confidence > existing_confidence:
                merged[category] = new_category_data
                
        return merged
    
    def validate_knowledge_base_size(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate knowledge base size and provide breakdown
        
        Args:
            knowledge_base: Knowledge base to validate
            
        Returns:
            Dict[str, Any]: Size validation results
        """
        # Estimate size in MB
        kb_json = json.dumps(knowledge_base)
        size_bytes = sys.getsizeof(kb_json)
        size_mb = size_bytes / (1024 * 1024)
        
        # Category breakdown
        categories_breakdown = {}
        for category, data in knowledge_base.items():
            if data:
                category_json = json.dumps(data)
                category_size_mb = sys.getsizeof(category_json) / (1024 * 1024)
                categories_breakdown[category] = round(category_size_mb, 2)
        
        return {
            'is_valid': size_mb <= self.max_size_mb,
            'estimated_size_mb': round(size_mb, 2),
            'max_size_mb': self.max_size_mb,
            'categories_breakdown': categories_breakdown,
            'needs_compression': size_mb > self.compression_threshold
        }
    
    def compress_knowledge_base(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress knowledge base by removing redundant data and optimizing content
        
        Args:
            knowledge_base: Knowledge base to compress
            
        Returns:
            Dict[str, Any]: Compressed knowledge base
        """
        compressed = {}
        
        for category, data in knowledge_base.items():
            if not data:
                continue
                
            compressed_data = {
                'title': data.get('title', ''),
                'content': self._compress_content(data.get('content', '')),
                'confidence_score': data.get('confidence_score', 0.0)
            }
            
            # Keep only top keywords
            if 'keywords' in data:
                keywords = data['keywords'][:10]  # Top 10 keywords only
                compressed_data['keywords'] = keywords
                
            # Compress structured data
            if 'structured_data' in data:
                compressed_data['structured_data'] = self._compress_structured_data(
                    data['structured_data']
                )
                
            compressed[category] = compressed_data
            
        return compressed
    
    def get_knowledge_base_stats(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive statistics about knowledge base
        
        Args:
            knowledge_base: Knowledge base to analyze
            
        Returns:
            Dict[str, Any]: Statistics and quality metrics
        """
        total_categories = len([cat for cat, data in knowledge_base.items() if data])
        total_content_length = sum(
            len(data.get('content', '')) for data in knowledge_base.values() if data
        )
        
        # Calculate quality score based on completeness and confidence
        quality_scores = []
        for data in knowledge_base.values():
            if not data:
                continue
                
            score = 0.0
            # Title and content completeness
            if data.get('title'):
                score += 0.3
            if data.get('content') and len(data['content']) > 50:
                score += 0.4
            # Confidence score
            score += data.get('confidence_score', 0.0) * 0.3
            
            quality_scores.append(score)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            'total_categories': total_categories,
            'max_categories': len(KNOWLEDGE_CATEGORIES),
            'completeness_ratio': total_categories / len(KNOWLEDGE_CATEGORIES),
            'total_content_length': total_content_length,
            'avg_content_length': total_content_length / max(total_categories, 1),
            'quality_score': round(avg_quality, 2)
        }
    
    def _compress_content(self, content: str) -> str:
        """
        Compress text content by removing redundancy
        
        Args:
            content: Text content to compress
            
        Returns:
            str: Compressed content
        """
        if len(content) <= 500:
            return content
            
        # Simple compression: take first 400 characters + last 100 characters
        return content[:400] + "..." + content[-100:]
    
    def _compress_structured_data(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress structured data by limiting items and fields
        
        Args:
            structured_data: Structured data to compress
            
        Returns:
            Dict[str, Any]: Compressed structured data
        """
        compressed = {}
        
        for key, value in structured_data.items():
            if isinstance(value, list):
                # Limit lists to 5 items
                compressed[key] = value[:5]
            elif isinstance(value, str) and len(value) > 200:
                # Truncate long strings
                compressed[key] = value[:200] + "..."
            else:
                compressed[key] = value
                
        return compressed