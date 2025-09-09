"""
Content Extraction Service
TODO: [MOCK_REGISTRY] Mock AI content extraction - needs real LLM integration
AI-powered content extraction and categorization for knowledge base building
"""
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

from src.schemas.knowledge_categories import (
    KNOWLEDGE_CATEGORIES,
    get_extraction_rules,
    validate_category_data
)


class ContentExtractionService:
    """
    Service for AI-powered content extraction and categorization
    TODO: [MOCK_REGISTRY] Mock implementation - needs real LLM integration
    """
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.max_content_length = 10000  # Characters
    
    def extract_and_categorize(self, html_content: str) -> Dict[str, Any]:
        """
        TODO: [MOCK_REGISTRY] Mock AI categorization - needs real LLM/NLP processing
        
        Extract and categorize content using AI/NLP
        
        Args:
            html_content: Raw HTML content to process
            
        Returns:
            Dictionary with categorized content
        """
        # Mock AI-powered categorization
        # In real implementation, this would use OpenAI, Claude, or local LLM
        
        mock_categories = {}
        
        # Simple keyword-based mock categorization
        if self._contains_keywords(html_content, ['about', 'company', 'mission', 'vision']):
            mock_categories['company_overview'] = {
                'title': 'Company Overview',
                'content': self._extract_text_content(html_content, ['about', 'company']),
                'keywords': ['company', 'mission', 'vision', 'values'],
                'confidence_score': 0.88,
                'extraction_method': 'ai_categorization'
            }
        
        if self._contains_keywords(html_content, ['product', 'service', 'solution', 'offering']):
            mock_categories['products_services'] = {
                'title': 'Products & Services',
                'content': self._extract_text_content(html_content, ['product', 'service']),
                'keywords': ['products', 'services', 'solutions', 'offerings'],
                'confidence_score': 0.85,
                'extraction_method': 'ai_categorization',
                'structured_data': {
                    'products': self._extract_product_list(html_content),
                    'services': self._extract_service_list(html_content)
                }
            }
        
        if self._contains_keywords(html_content, ['price', 'pricing', 'cost', 'plan', 'package']):
            mock_categories['pricing_packages'] = {
                'title': 'Pricing Information',
                'content': self._extract_text_content(html_content, ['price', 'pricing']),
                'keywords': ['pricing', 'plans', 'packages', 'cost'],
                'confidence_score': 0.82,
                'extraction_method': 'ai_categorization',
                'structured_data': {
                    'packages': self._extract_pricing_packages(html_content)
                }
            }
        
        if self._contains_keywords(html_content, ['contact', 'phone', 'email', 'address']):
            mock_categories['contact_information'] = {
                'title': 'Contact Information',
                'content': self._extract_text_content(html_content, ['contact', 'phone', 'email']),
                'keywords': ['contact', 'phone', 'email', 'address'],
                'confidence_score': 0.95,
                'extraction_method': 'ai_categorization',
                'structured_data': {
                    'phone': self._extract_phone_numbers(html_content),
                    'email': self._extract_email_addresses(html_content),
                    'address': self._extract_addresses(html_content)
                }
            }
        
        # Validate all extracted categories
        validated_categories = {}
        for category, data in mock_categories.items():
            try:
                validated_categories[category] = validate_category_data(category, data)
            except ValueError as e:
                print(f"Validation error for {category}: {e}")
                continue
        
        return validated_categories
    
    def process_html_content(self, html_content: str) -> Dict[str, Any]:
        """
        TODO: [MOCK_REGISTRY] Mock HTML processing - needs real HTML parsing
        
        Process raw HTML content and extract structured information
        """
        # Mock HTML processing
        processed_data = {
            'text_content': self._strip_html_tags(html_content),
            'metadata': {
                'word_count': len(html_content.split()),
                'processing_timestamp': datetime.now().isoformat(),
                'content_quality_score': 0.8
            },
            'extracted_elements': {
                'headings': self._extract_headings(html_content),
                'paragraphs': self._extract_paragraphs(html_content),
                'links': self._extract_links(html_content),
                'images': self._extract_images(html_content)
            }
        }
        
        return processed_data
    
    def _contains_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains any of the specified keywords"""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)
    
    def _extract_text_content(self, html_content: str, focus_keywords: List[str]) -> str:
        """Extract relevant text content based on focus keywords"""
        # Simple mock extraction - in reality would use NLP/LLM
        sentences = html_content.split('.')
        relevant_sentences = []
        
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            if any(keyword.lower() in sentence.lower() for keyword in focus_keywords):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            return '. '.join(relevant_sentences) + '.'
        else:
            # Fallback to first paragraph
            return self._strip_html_tags(html_content)[:500] + '...'
    
    def _extract_product_list(self, html_content: str) -> List[Dict[str, str]]:
        """Mock product extraction"""
        return [
            {'name': 'Premium Solution', 'category': 'Software', 'description': 'Advanced features'},
            {'name': 'Basic Package', 'category': 'Service', 'description': 'Essential features'}
        ]
    
    def _extract_service_list(self, html_content: str) -> List[Dict[str, str]]:
        """Mock service extraction"""
        return [
            {'name': 'Consulting', 'type': 'Professional', 'description': 'Expert guidance'},
            {'name': 'Support', 'type': 'Technical', 'description': '24/7 assistance'}
        ]
    
    def _extract_pricing_packages(self, html_content: str) -> List[Dict[str, str]]:
        """Mock pricing package extraction"""
        return [
            {'name': 'Starter', 'price': '$29/month', 'features': 'Basic features'},
            {'name': 'Professional', 'price': '$99/month', 'features': 'Advanced features'},
            {'name': 'Enterprise', 'price': 'Custom', 'features': 'All features + support'}
        ]
    
    def _extract_phone_numbers(self, html_content: str) -> List[str]:
        """Extract phone numbers using regex"""
        phone_pattern = r'[\+]?[1-9]?[0-9]{0,3}[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phones = re.findall(phone_pattern, html_content)
        return phones[:3]  # Limit to first 3 phone numbers
    
    def _extract_email_addresses(self, html_content: str) -> List[str]:
        """Extract email addresses using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html_content)
        return emails[:5]  # Limit to first 5 email addresses
    
    def _extract_addresses(self, html_content: str) -> List[str]:
        """Mock address extraction"""
        # In real implementation, would use NER or address parsing libraries
        return ['123 Business Street, City, State 12345']
    
    def _strip_html_tags(self, html_content: str) -> str:
        """Remove HTML tags from content"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_content)
    
    def _extract_headings(self, html_content: str) -> List[str]:
        """Extract heading tags"""
        heading_pattern = r'<h[1-6][^>]*>(.*?)</h[1-6]>'
        headings = re.findall(heading_pattern, html_content, re.IGNORECASE)
        return [self._strip_html_tags(h) for h in headings]
    
    def _extract_paragraphs(self, html_content: str) -> List[str]:
        """Extract paragraph content"""
        para_pattern = r'<p[^>]*>(.*?)</p>'
        paragraphs = re.findall(para_pattern, html_content, re.IGNORECASE | re.DOTALL)
        return [self._strip_html_tags(p).strip() for p in paragraphs if p.strip()]
    
    def _extract_links(self, html_content: str) -> List[Dict[str, str]]:
        """Extract links and their text"""
        link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        links = re.findall(link_pattern, html_content, re.IGNORECASE)
        return [{'url': url, 'text': self._strip_html_tags(text).strip()} 
                for url, text in links if text.strip()][:10]  # Limit to 10 links
    
    def _extract_images(self, html_content: str) -> List[Dict[str, str]]:
        """Extract image sources and alt text"""
        img_pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?[^>]*>'
        images = re.findall(img_pattern, html_content, re.IGNORECASE)
        return [{'src': src, 'alt': alt or ''} for src, alt in images][:5]  # Limit to 5 images
    
    def analyze_content_quality(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the quality of extracted content
        """
        quality_metrics = {
            'completeness_score': 0.0,
            'confidence_average': 0.0,
            'category_coverage': 0,
            'content_richness': 0.0,
            'structured_data_ratio': 0.0
        }
        
        if not extracted_data:
            return quality_metrics
        
        # Calculate completeness (how many categories found)
        quality_metrics['category_coverage'] = len(extracted_data)
        quality_metrics['completeness_score'] = min(len(extracted_data) / 10, 1.0)  # Out of 10 key categories
        
        # Calculate average confidence
        confidences = [cat.get('confidence_score', 0.0) for cat in extracted_data.values()]
        if confidences:
            quality_metrics['confidence_average'] = sum(confidences) / len(confidences)
        
        # Calculate content richness (average content length)
        content_lengths = [len(cat.get('content', '')) for cat in extracted_data.values()]
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            quality_metrics['content_richness'] = min(avg_length / 500, 1.0)  # Normalized to 500 chars
        
        # Calculate structured data ratio
        structured_count = sum(1 for cat in extracted_data.values() 
                             if cat.get('structured_data') and len(cat['structured_data']) > 0)
        if extracted_data:
            quality_metrics['structured_data_ratio'] = structured_count / len(extracted_data)
        
        return quality_metrics