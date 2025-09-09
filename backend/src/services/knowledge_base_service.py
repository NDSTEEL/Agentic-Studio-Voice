"""
Knowledge Base Service
TODO: [MOCK_REGISTRY] Mock knowledge management - needs real database integration
Service for managing voice agent knowledge bases with merging and versioning
"""
from typing import Dict, List, Any, Optional
import json
import gzip
from datetime import datetime
from copy import deepcopy

from src.schemas.knowledge_categories import (
    KNOWLEDGE_CATEGORIES,
    validate_category_data,
    merge_knowledge_categories as merge_categories_util
)


class KnowledgeBaseService:
    """
    Service for managing knowledge base operations
    TODO: [MOCK_REGISTRY] Mock implementation - needs real database integration
    """
    
    def __init__(self):
        self.max_kb_size_mb = 50  # Maximum knowledge base size in MB
        self.min_confidence_threshold = 0.7
        self.max_versions_per_category = 10
    
    def merge_knowledge_categories(
        self, 
        existing: Dict[str, Any], 
        new_data: Dict[str, Any],
        min_confidence_threshold: Optional[float] = None,
        track_changes: bool = False
    ) -> Dict[str, Any]:
        """
        TODO: [MOCK_REGISTRY] Mock knowledge merging - needs real merge logic
        
        Merge existing knowledge with new extracted content
        
        Args:
            existing: Current knowledge base
            new_data: New knowledge to merge
            min_confidence_threshold: Minimum confidence to accept updates
            track_changes: Whether to track version history
            
        Returns:
            Merged knowledge base
        """
        threshold = min_confidence_threshold or self.min_confidence_threshold
        merged = deepcopy(existing)
        
        for category, new_content in new_data.items():
            if category not in KNOWLEDGE_CATEGORIES:
                continue
            
            # Check confidence threshold (skip for change tracking)
            new_confidence = new_content.get('confidence_score', 0.0)
            if not track_changes and new_confidence < threshold:
                continue
            
            existing_content = existing.get(category)
            
            # If no existing content, add new content
            if not existing_content:
                merged[category] = new_content
                if track_changes:
                    merged[category]['change_history'] = [{
                        'action': 'created',
                        'timestamp': datetime.now().isoformat(),
                        'confidence_score': new_confidence
                    }]
                continue
            
            # Compare confidence scores
            existing_confidence = existing_content.get('confidence_score', 0.0)
            
            # Update if new content has higher or equal confidence (to allow updates without confidence change)
            if new_confidence >= existing_confidence:
                # Track changes if enabled
                if track_changes:
                    change_record = {
                        'action': 'updated',
                        'timestamp': datetime.now().isoformat(),
                        'previous_title': existing_content.get('title'),
                        'previous_confidence': existing_confidence,
                        'new_confidence': new_confidence
                    }
                    
                    # Preserve existing change history
                    existing_change_history = merged[category].get('change_history', [])
                    
                    # Update content first
                    merged[category] = deepcopy(new_content)
                    
                    # Add change history to updated content
                    merged[category]['change_history'] = existing_change_history + [change_record]
                    
                    # Limit version history
                    if len(merged[category]['change_history']) > self.max_versions_per_category:
                        merged[category]['change_history'] = merged[category]['change_history'][-self.max_versions_per_category:]
                else:
                    # Update content without change tracking
                    merged[category] = deepcopy(new_content)
        
        return merged
    
    def update_voice_agent_knowledge(
        self, 
        agent_id: str, 
        knowledge_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        TODO: [MOCK_REGISTRY] Mock agent knowledge update - needs real database operations
        
        Update voice agent's knowledge base
        """
        # Mock update operation
        result = {
            'agent_id': agent_id,
            'success': True,
            'updated_categories': list(knowledge_updates.keys()),
            'timestamp': datetime.now().isoformat(),
            'validation_results': {}
        }
        
        # Validate each category
        for category, data in knowledge_updates.items():
            try:
                validated_data = validate_category_data(category, data)
                result['validation_results'][category] = {
                    'valid': True,
                    'confidence_score': validated_data.get('confidence_score', 0.0)
                }
            except ValueError as e:
                result['validation_results'][category] = {
                    'valid': False,
                    'error': str(e)
                }
                result['updated_categories'].remove(category)
        
        return result
    
    def validate_knowledge_base_size(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate knowledge base size and structure
        """
        kb_json = json.dumps(knowledge_base, indent=2)
        size_bytes = len(kb_json.encode('utf-8'))
        size_mb = size_bytes / (1024 * 1024)
        
        result = {
            'is_valid': size_mb <= self.max_kb_size_mb,
            'total_categories': len(knowledge_base),
            'estimated_size_mb': round(size_mb, 2),
            'max_size_mb': self.max_kb_size_mb,
            'categories_breakdown': {}
        }
        
        # Analyze each category
        for category, data in knowledge_base.items():
            if data:
                category_json = json.dumps(data, indent=2)
                category_size = len(category_json.encode('utf-8'))
                result['categories_breakdown'][category] = {
                    'size_bytes': category_size,
                    'content_length': len(data.get('content', '')),
                    'has_structured_data': bool(data.get('structured_data')),
                    'confidence_score': data.get('confidence_score', 0.0)
                }
        
        return result
    
    def compress_knowledge_base(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        TODO: [MOCK_REGISTRY] Mock compression - needs real compression implementation
        
        Compress knowledge base for storage efficiency
        """
        # Simple mock compression - remove duplicates and optimize structure
        compressed = {}
        
        for category, data in knowledge_base.items():
            if not data:
                continue
            
            compressed_data = {
                'title': data.get('title', ''),
                'content': self._compress_text(data.get('content', '')),
                'keywords': list(set(data.get('keywords', []))),  # Remove duplicate keywords
                'confidence_score': data.get('confidence_score', 0.0),
                'last_updated': data.get('last_updated'),
                'structured_data': self._compress_structured_data(data.get('structured_data', {}))
            }
            
            # Remove empty fields to save space
            compressed_data = {k: v for k, v in compressed_data.items() if v}
            compressed[category] = compressed_data
        
        return compressed
    
    def apply_incremental_update(
        self, 
        agent_id: str, 
        change_delta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        TODO: [MOCK_REGISTRY] Mock incremental updates - needs real delta processing
        
        Apply incremental updates to avoid full knowledge base rewrites
        """
        result = {
            'success': True,
            'agent_id': agent_id,
            'updated_categories': [],
            'timestamp': datetime.now().isoformat(),
            'operations_applied': []
        }
        
        for category, operation_data in change_delta.items():
            operation = operation_data.get('operation', 'update')
            
            if operation == 'update':
                # Mock update operation
                result['updated_categories'].append(category)
                result['operations_applied'].append({
                    'category': category,
                    'operation': 'update',
                    'fields_updated': list(operation_data.get('fields', {}).keys()),
                    'timestamp': operation_data.get('timestamp')
                })
            
            elif operation == 'add':
                # Mock add operation
                result['updated_categories'].append(category)
                result['operations_applied'].append({
                    'category': category,
                    'operation': 'add',
                    'data_size': len(str(operation_data.get('data', {}))),
                    'timestamp': operation_data.get('timestamp')
                })
            
            elif operation == 'delete':
                # Mock delete operation
                result['operations_applied'].append({
                    'category': category,
                    'operation': 'delete',
                    'timestamp': operation_data.get('timestamp')
                })
        
        return result
    
    def _compress_text(self, text: str) -> str:
        """Enhanced text compression - remove redundancy and optimize content"""
        if not text:
            return text
        
        # Remove extra whitespace and normalize
        compressed = ' '.join(text.split())
        
        # Remove redundant phrases (more aggressive)
        redundant_phrases = [
            'Our company', 'We offer', 'We provide', 'Our services include',
            'We are', 'This is', 'Please contact us', 'For more information',
            'We believe', 'Our mission is', 'We strive to', 'Our goal is'
        ]
        for phrase in redundant_phrases:
            # Replace multiple occurrences with single occurrence
            while compressed.count(phrase) > 1:
                compressed = compressed.replace(phrase + ' ', '', 1)
        
        # Remove common filler words and phrases
        filler_words = [
            ' very ', ' quite ', ' really ', ' actually ', ' basically ',
            ' essentially ', ' obviously ', ' certainly ', ' definitely '
        ]
        for filler in filler_words:
            compressed = compressed.replace(filler, ' ')
        
        # Normalize punctuation spacing
        import re
        compressed = re.sub(r'\s+([,.!?;:])', r'\1', compressed)
        compressed = re.sub(r'\s+', ' ', compressed)
        
        # Remove duplicate sentences
        sentences = compressed.split('.')
        unique_sentences = []
        seen = set()
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence.lower() not in seen:
                seen.add(sentence.lower())
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    def _compress_structured_data(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced structured data compression by removing redundancy"""
        if not structured_data:
            return structured_data
        
        compressed = {}
        
        for key, value in structured_data.items():
            if isinstance(value, list):
                # Remove duplicate items in lists
                if value and isinstance(value[0], dict):
                    # For list of dicts, remove duplicates based on key fields
                    seen = set()
                    unique_items = []
                    for item in value:
                        # Create a normalized key for comparison
                        if isinstance(item, dict):
                            # Compress text values within dict items
                            compressed_item = {}
                            for k, v in item.items():
                                if isinstance(v, str) and len(v) > 50:
                                    compressed_item[k] = self._compress_text(v)
                                else:
                                    compressed_item[k] = v
                            item_key = tuple(sorted(compressed_item.items()))
                            if item_key not in seen:
                                seen.add(item_key)
                                unique_items.append(compressed_item)
                        else:
                            unique_items.append(item)
                    compressed[key] = unique_items
                else:
                    # For simple lists, remove duplicates and compress strings
                    unique_list = []
                    seen_set = set()
                    for item in value:
                        if isinstance(item, str):
                            compressed_item = self._compress_text(item) if len(item) > 50 else item
                            if compressed_item not in seen_set:
                                seen_set.add(compressed_item)
                                unique_list.append(compressed_item)
                        else:
                            if item not in seen_set:
                                seen_set.add(item)
                                unique_list.append(item)
                    compressed[key] = unique_list
            elif isinstance(value, str) and len(value) > 50:
                # Compress long string values
                compressed[key] = self._compress_text(value)
            else:
                compressed[key] = value
        
        return compressed
    
    def get_knowledge_base_stats(self, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive statistics about a knowledge base
        """
        stats = {
            'total_categories': len(knowledge_base),
            'populated_categories': 0,
            'total_content_words': 0,
            'total_keywords': 0,
            'average_confidence': 0.0,
            'categories_with_structured_data': 0,
            'last_updated': None,
            'quality_score': 0.0,
            'completeness_ratio': 0.0
        }
        
        if not knowledge_base:
            return stats
        
        confidences = []
        last_updates = []
        
        for category, data in knowledge_base.items():
            if not data:
                continue
            
            stats['populated_categories'] += 1
            
            # Content analysis
            content = data.get('content', '')
            if content:
                stats['total_content_words'] += len(content.split())
            
            # Keywords
            keywords = data.get('keywords', [])
            stats['total_keywords'] += len(keywords)
            
            # Confidence scores
            confidence = data.get('confidence_score', 0.0)
            if confidence > 0:
                confidences.append(confidence)
            
            # Structured data
            if data.get('structured_data'):
                stats['categories_with_structured_data'] += 1
            
            # Last updated
            if data.get('last_updated'):
                last_updates.append(data['last_updated'])
        
        # Calculate averages and derived metrics
        if confidences:
            stats['average_confidence'] = sum(confidences) / len(confidences)
        
        if last_updates:
            stats['last_updated'] = max(last_updates)
        
        # Completeness ratio (out of 18 total categories)
        stats['completeness_ratio'] = stats['populated_categories'] / len(KNOWLEDGE_CATEGORIES)
        
        # Overall quality score (weighted combination of metrics)
        quality_components = [
            stats['completeness_ratio'] * 0.3,  # 30% weight
            stats['average_confidence'] * 0.4,  # 40% weight
            min(stats['categories_with_structured_data'] / max(stats['populated_categories'], 1), 1.0) * 0.2,  # 20% weight
            min(stats['total_content_words'] / 5000, 1.0) * 0.1  # 10% weight (normalized to 5000 words)
        ]
        stats['quality_score'] = sum(quality_components)
        
        return stats