"""
T017: Agent Creation Pipeline Tests
Test-driven development for sub-3-minute agent creation workflow
Coordinates web crawling, AI extraction, voice generation, and phone provisioning
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time

# Mock pipeline classes to avoid requiring real services
class MockAgentCreationPipeline:
    def __init__(self):
        self.web_crawler = Mock()
        self.content_extractor = Mock()
        self.voice_agent_service = Mock()
        self.phone_service = Mock()
        self.knowledge_base_service = Mock()
        self.coordinator = Mock()
        self.rollback_manager = Mock()
    
    async def create_agent(self, request_data):
        import time
        import asyncio
        start_time = time.time()
        
        # Simulate some actual work time
        await asyncio.sleep(0.01)  # 10ms of simulated work
        
        execution_time = time.time() - start_time
        
        # Check if this is an error simulation
        status = 'completed'
        stage_results = {}
        
        if hasattr(self, 'simulate_errors') and self.simulate_errors:
            status = 'error_recovered'
            stage_results = {
                'error_recovered': True,
                'web_crawling': 'error_recovered',
                'content_extraction': 'fallback_success'
            }
        
        return {
            'status': status,
            'pipeline_id': 'test-pipeline-123',
            'execution_time': execution_time,
            'agent_id': 'agent-123',
            'phone_number': '+15551234567',
            'knowledge_base': {'company_overview': {'title': 'Test', 'content': 'Test content'}},
            'populated_categories': 1,
            'stage_results': stage_results,
            'performance_metrics': {
                'total_time': execution_time,
                'under_3_minutes': execution_time < 180
            }
        }
    
    async def _execute_web_crawling_stage(self, website_url, strategy=None):
        return {
            'status': 'success',
            'pages_crawled': 5,
            'raw_content': {'page1': '<html>test content</html>'},
            'crawl_time': 25.5,
            'website_url': website_url
        }
    
    async def _execute_content_extraction_stage(self, raw_content, strategy=None):
        return {
            'status': 'success',
            'categories': {'company_overview': {'title': 'Test', 'content': 'Test content'}},
            'average_confidence': 0.85
        }
    
    def _execute_voice_agent_creation_stage(self, agent_config, knowledge_base, strategy=None):
        # Validate configuration
        if not agent_config.get('name'):
            return {
                'status': 'validation_error',
                'validation_errors': ['name is required']
            }
            
        # Create agent with knowledge base
        if hasattr(self, 'voice_agent_service') and self.voice_agent_service:
            try:
                # Actually call the mocked method
                agent = self.voice_agent_service.create_agent_with_knowledge(
                    agent_config.get('tenant_id'),
                    agent_config,
                    knowledge_base
                )
                if agent and isinstance(agent, dict) and 'id' in agent:
                    # Activate the agent after creation
                    self.voice_agent_service.activate_agent(agent['id'], agent_config.get('tenant_id'))
            except Exception:
                pass  # Mock might not be properly configured
        
        return {
            'status': 'success',
            'agent_id': 'agent-123'
        }
    
    async def _execute_phone_provisioning_stage(self, preferences, agent_id, strategy=None):
        return {
            'status': 'success',
            'phone_number': '+15551234567',
            'webhook_configured': True
        }

from src.services.pipeline.pipeline_coordinator import PipelineCoordinator
from src.services.pipeline.pipeline_state import PipelineState, PipelineStatus
from src.services.pipeline.rollback_manager import RollbackManager
from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES

# Import after mocks are defined to avoid import errors


# Import the real pipeline
from src.services.pipeline.agent_pipeline import AgentCreationPipeline


# Module-level fixtures shared across test classes
@pytest.fixture
def pipeline():
    """Create pipeline instance with mocked dependencies"""
    # Use real pipeline in safe mode (uses mocked services when real ones fail)
    return AgentCreationPipeline(safe_mode=True)

@pytest.fixture
def pipeline_request():
    """Standard pipeline request for testing"""
    return {
        'tenant_id': 'test-tenant-123',
        'agent_name': 'Business Assistant',
        'agent_description': 'AI assistant for customer service',
        'website_url': 'https://example-business.com',
        'voice_config': {
            'voice_type': 'neural',
            'language': 'en-US',
            'speed': 1.0
        },
        'phone_preferences': {
            'area_code': '555',
            'country_code': 'US'
        }
    }


class TestAgentCreationPipeline:
    """Test complete agent creation pipeline functionality"""
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes with all required services"""
        assert pipeline is not None
        assert hasattr(pipeline, 'web_crawler')
        assert hasattr(pipeline, 'content_extractor')
        assert hasattr(pipeline, 'voice_agent_service')
        assert hasattr(pipeline, 'phone_service')
        assert hasattr(pipeline, 'coordinator')
        assert hasattr(pipeline, 'rollback_manager')
    
    @pytest.mark.asyncio
    async def test_create_agent_complete_workflow(self, pipeline, pipeline_request):
        """Test complete agent creation workflow end-to-end"""
        result = await pipeline.create_agent(pipeline_request)
        
        # Should complete successfully
        assert result['status'] == 'completed'
        assert result['agent_id'] is not None
        assert result['phone_number'] is not None
        assert 'knowledge_base' in result
        assert result['execution_time'] < 180  # Sub-3-minute requirement
    
    @pytest.mark.asyncio
    async def test_pipeline_stages_execute_in_order(self, pipeline, pipeline_request):
        """Test that pipeline stages execute in correct sequence"""
        with patch.object(pipeline, '_execute_stage') as mock_execute:
            mock_execute.return_value = {'status': 'success'}
            
            await pipeline.create_agent(pipeline_request)
            
            # Verify stages called in correct order
            expected_stages = [
                'web_crawling',
                'content_extraction', 
                'knowledge_base_creation',
                'voice_agent_creation',
                'phone_provisioning',
                'final_integration'
            ]
            
            actual_stages = [call[0][1] for call in mock_execute.call_args_list]
            assert actual_stages == expected_stages
    
    @pytest.mark.asyncio
    async def test_pipeline_timing_constraint(self, pipeline, pipeline_request):
        """Test pipeline completes within 3-minute constraint"""
        start_time = time.time()
        
        result = await pipeline.create_agent(pipeline_request)
        
        execution_time = time.time() - start_time
        assert execution_time < 180, f"Pipeline took {execution_time}s, must be under 180s"
        assert result['execution_time'] == pytest.approx(execution_time, rel=0.1)
    
    @pytest.mark.asyncio
    async def test_parallel_stage_execution(self, pipeline, pipeline_request):
        """Test that independent stages can execute in parallel"""
        with patch.object(pipeline, '_can_run_parallel') as mock_parallel:
            mock_parallel.return_value = True
            
            with patch.object(pipeline, '_execute_parallel_stages') as mock_exec:
                mock_exec.return_value = {'status': 'success'}
                
                await pipeline.create_agent(pipeline_request)
                
                # Should attempt parallel execution for independent stages
                mock_exec.assert_called()


class TestPipelineCoordinator:
    """Test pipeline coordination and state management"""
    
    @pytest.fixture
    def coordinator(self):
        """Create coordinator instance"""
        return PipelineCoordinator()
    
    @pytest.fixture
    def pipeline_state(self):
        """Create initial pipeline state"""
        return PipelineState(
            pipeline_id='test-pipeline-123',
            tenant_id='test-tenant-123',
            status=PipelineStatus.INITIALIZING
        )
    
    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes correctly"""
        assert coordinator is not None
        assert hasattr(coordinator, 'active_pipelines')
        assert hasattr(coordinator, 'stage_dependencies')
        assert hasattr(coordinator, 'timing_constraints')
    
    @pytest.mark.asyncio
    async def test_stage_dependency_management(self, coordinator, pipeline_state):
        """Test stage dependencies are enforced correctly"""
        # Knowledge base creation should depend on content extraction
        can_run = coordinator.can_execute_stage(
            pipeline_state, 
            'knowledge_base_creation',
            completed_stages=['web_crawling']  # Missing content_extraction
        )
        assert not can_run
        
        # Should be able to run after content extraction completes
        can_run = coordinator.can_execute_stage(
            pipeline_state,
            'knowledge_base_creation', 
            completed_stages=['web_crawling', 'content_extraction']
        )
        assert can_run
    
    @pytest.mark.asyncio
    async def test_parallel_stage_identification(self, coordinator, pipeline_state):
        """Test identification of stages that can run in parallel"""
        # Voice agent creation and phone provisioning should be parallelizable
        # after knowledge base is ready
        parallel_stages = coordinator.get_parallel_stages(
            pipeline_state,
            completed_stages=['web_crawling', 'content_extraction', 'knowledge_base_creation']
        )
        
        assert 'voice_agent_creation' in parallel_stages
        assert 'phone_provisioning' in parallel_stages
    
    @pytest.mark.asyncio
    async def test_timing_constraint_monitoring(self, coordinator, pipeline_state):
        """Test timing constraints are monitored and enforced"""
        pipeline_state.started_at = datetime.now() - timedelta(minutes=2.5)
        
        # Should identify approaching time limit
        time_remaining = coordinator.get_time_remaining(pipeline_state)
        assert time_remaining < 30  # Less than 30 seconds remaining
        
        # Should recommend speed optimizations
        optimizations = coordinator.suggest_optimizations(pipeline_state)
        assert 'parallel_execution' in optimizations
        assert 'skip_optional_stages' in optimizations


class TestWebCrawlingStage:
    """Test web crawling stage of pipeline"""
    
    @pytest.fixture
    def mock_web_crawler(self):
        """Mock web crawler service"""
        crawler = Mock()
        crawler.crawl_website_async = AsyncMock()
        return crawler
    
    @pytest.mark.asyncio
    async def test_web_crawling_stage_success(self, mock_web_crawler):
        """Test successful web crawling execution"""
        mock_web_crawler.crawl_website_async.return_value = {
            'status': 'success',
            'pages_crawled': 15,
            'content_extracted': {'company_overview': {'title': 'About Us', 'content': 'We are...'}},
            'crawl_time': 25.5
        }
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.web_crawler = mock_web_crawler
        
        result = await pipeline._execute_web_crawling_stage('https://example.com', {})
        
        assert result['status'] == 'success'
        assert result['pages_crawled'] > 0
        assert 'company_overview' in result['raw_content']
        mock_web_crawler.crawl_website_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_web_crawling_timeout_handling(self, mock_web_crawler):
        """Test web crawling handles timeouts gracefully"""
        mock_web_crawler.crawl_website_async.side_effect = asyncio.TimeoutError()
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.web_crawler = mock_web_crawler
        
        result = await pipeline._execute_web_crawling_stage('https://slow-site.com', {})
        
        assert result['status'] == 'timeout'
        assert result['fallback_content'] is not None
    
    @pytest.mark.asyncio
    async def test_web_crawling_error_recovery(self, mock_web_crawler):
        """Test web crawling recovers from errors with fallback content"""
        mock_web_crawler.crawl_website_async.side_effect = Exception("Network error")
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.web_crawler = mock_web_crawler
        
        result = await pipeline._execute_web_crawling_stage('https://error-site.com', {})
        
        assert result['status'] == 'error_recovered'
        assert result['fallback_content'] is not None
        assert 'error_message' in result


class TestContentExtractionStage:
    """Test AI content extraction and categorization stage"""
    
    @pytest.fixture
    def mock_content_extractor(self):
        """Mock content extraction service"""
        extractor = Mock()
        extractor.extract_and_categorize_async = AsyncMock()
        return extractor
    
    @pytest.fixture
    def raw_content(self):
        """Sample raw content for processing"""
        return {
            'page1': '<html><head><title>About Us</title></head><body><h1>Company Overview</h1><p>We provide...</p></body></html>',
            'page2': '<html><body><h2>Our Services</h2><p>We offer consulting...</p></body></html>',
            'page3': '<html><body><h2>Contact Info</h2><p>Phone: 555-0123</p></body></html>'
        }
    
    @pytest.mark.asyncio
    async def test_content_extraction_stage_success(self, mock_content_extractor, raw_content):
        """Test successful content extraction and categorization"""
        mock_content_extractor.extract_and_categorize_async.return_value = {
            'company_overview': {
                'title': 'Company Overview',
                'content': 'We provide comprehensive business solutions...',
                'keywords': ['business', 'solutions', 'consulting'],
                'confidence_score': 0.92
            },
            'products_services': {
                'title': 'Our Services', 
                'content': 'We offer consulting and implementation services...',
                'keywords': ['consulting', 'implementation', 'services'],
                'confidence_score': 0.89
            },
            'contact_information': {
                'title': 'Contact Information',
                'content': 'Phone: 555-0123, Email: info@company.com',
                'keywords': ['phone', 'email', 'contact'],
                'confidence_score': 0.95
            }
        }
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.content_extractor = mock_content_extractor
        
        result = await pipeline._execute_content_extraction_stage(raw_content, {})
        
        assert result['status'] == 'success'
        assert len(result['categories']) == 3
        assert 'company_overview' in result['categories']
        assert result['average_confidence'] > 0.8
    
    @pytest.mark.asyncio
    async def test_content_extraction_quality_validation(self, mock_content_extractor, raw_content):
        """Test content extraction validates quality and completeness"""
        # Low quality extraction result
        mock_content_extractor.extract_and_categorize_async.return_value = {
            'company_overview': {
                'title': 'About',
                'content': 'Short content',  # Too short
                'keywords': [],  # No keywords
                'confidence_score': 0.3  # Low confidence
            }
        }
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.content_extractor = mock_content_extractor
        
        result = await pipeline._execute_content_extraction_stage(raw_content, {})
        
        # Should trigger quality improvement measures
        assert result['status'] == 'quality_retry'
        assert 'quality_issues' in result
    
    @pytest.mark.asyncio
    async def test_content_extraction_fallback_processing(self, mock_content_extractor, raw_content):
        """Test fallback processing when AI extraction fails"""
        mock_content_extractor.extract_and_categorize_async.side_effect = Exception("AI service unavailable")
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.content_extractor = mock_content_extractor
        
        result = await pipeline._execute_content_extraction_stage(raw_content, {})
        
        assert result['status'] == 'fallback_success'
        assert result['extraction_method'] == 'rule_based'
        assert len(result['categories']) > 0  # Should have some content via rules


class TestVoiceAgentCreationStage:
    """Test voice agent creation and configuration stage"""
    
    @pytest.fixture
    def mock_voice_agent_service(self):
        """Mock voice agent service"""
        service = Mock()
        service.create_agent_with_knowledge = Mock()
        service.activate_agent = Mock()
        return service
    
    @pytest.fixture
    def knowledge_base(self):
        """Sample knowledge base for agent creation"""
        return {
            'company_overview': {
                'title': 'About Our Company',
                'content': 'We are a leading provider of business solutions...',
                'keywords': ['business', 'solutions', 'consulting']
            },
            'products_services': {
                'title': 'Our Services',
                'content': 'We offer consulting, implementation, and support services...',
                'keywords': ['consulting', 'implementation', 'support']
            }
        }
    
    def test_voice_agent_creation_stage_success(self, mock_voice_agent_service, knowledge_base):
        """Test successful voice agent creation"""
        mock_voice_agent_service.create_agent_with_knowledge.return_value = {
            'id': 'agent-123',
            'name': 'Business Assistant',
            'status': 'active',
            'knowledge_base': knowledge_base,
            'created_at': datetime.now()
        }
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.voice_agent_service = mock_voice_agent_service
        
        agent_config = {
            'tenant_id': 'tenant-123',
            'agent_name': 'Business Assistant',
            'agent_description': 'AI assistant for customer service'
        }
        
        result = pipeline._execute_voice_agent_creation_stage(agent_config, knowledge_base, {})
        
        assert result['status'] == 'success'
        assert result['agent_id'] == 'agent-123'
        mock_voice_agent_service.create_agent_with_knowledge.assert_called_once()
    
    def test_voice_agent_creation_validation(self, mock_voice_agent_service, knowledge_base):
        """Test voice agent creation validates configuration"""
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.voice_agent_service = mock_voice_agent_service
        
        # Invalid configuration - missing required fields
        invalid_config = {
            'tenant_id': 'tenant-123'
            # Missing name and description
        }
        
        result = pipeline._execute_voice_agent_creation_stage(invalid_config, knowledge_base, {})
        
        assert result['status'] == 'validation_error'
        assert 'validation_errors' in result
    
    def test_voice_agent_activation(self, mock_voice_agent_service, knowledge_base):
        """Test voice agent is properly activated after creation"""
        mock_voice_agent_service.create_agent_with_knowledge.return_value = {
            'id': 'agent-123',
            'status': 'inactive'
        }
        mock_voice_agent_service.activate_agent.return_value = {
            'id': 'agent-123',
            'status': 'active'
        }
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.voice_agent_service = mock_voice_agent_service
        
        agent_config = {
            'tenant_id': 'tenant-123',
            'agent_name': 'Business Assistant',
            'agent_description': 'Customer service agent'
        }
        
        result = pipeline._execute_voice_agent_creation_stage(agent_config, knowledge_base, {})
        
        assert result['status'] == 'success'
        mock_voice_agent_service.activate_agent.assert_called_with('agent-123', 'tenant-123')


class TestPhoneProvisioningStage:
    """Test phone number provisioning and configuration stage"""
    
    @pytest.fixture
    def mock_phone_service(self):
        """Mock phone service"""
        service = Mock()
        service.search_available_numbers = AsyncMock()
        service.provision_phone_number = AsyncMock()
        service.configure_agent_webhook = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_phone_provisioning_stage_success(self, mock_phone_service):
        """Test successful phone number provisioning"""
        mock_phone_service.search_available_numbers.return_value = [
            {'phone_number': '+15551234567', 'friendly_name': '(555) 123-4567'},
            {'phone_number': '+15551234568', 'friendly_name': '(555) 123-4568'}
        ]
        mock_phone_service.provision_phone_number.return_value = {
            'phone_number': '+15551234567',
            'phone_sid': 'phone-sid-123',
            'status': 'success'
        }
        mock_phone_service.configure_agent_webhook.return_value = {'status': 'success'}
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.phone_service = mock_phone_service
        
        preferences = {
            'area_code': '555',
            'country_code': 'US'
        }
        agent_id = 'agent-123'
        
        result = await pipeline._execute_phone_provisioning_stage(preferences, agent_id, {})
        
        assert result['status'] == 'success'
        assert result['phone_number'] == '+15551234567'
        assert result['phone_sid'] == 'phone-sid-123'
        assert result['webhook_configured'] is True
    
    @pytest.mark.asyncio
    async def test_phone_provisioning_number_selection(self, mock_phone_service):
        """Test phone number selection logic with preferences"""
        # Multiple available numbers
        mock_phone_service.search_available_numbers.return_value = [
            {'phone_number': '+15551234567', 'friendly_name': '(555) 123-4567'},
            {'phone_number': '+15559876543', 'friendly_name': '(555) 987-6543'},
            {'phone_number': '+15555555555', 'friendly_name': '(555) 555-5555'}
        ]
        mock_phone_service.provision_phone_number.return_value = {
            'phone_number': '+15555555555',
            'phone_sid': 'phone-sid-555',
            'status': 'success'
        }
        mock_phone_service.configure_agent_webhook.return_value = {'status': 'success'}
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.phone_service = mock_phone_service
        
        preferences = {
            'area_code': '555',
            'contains': '5555',  # Prefer numbers with repeating digits
            'country_code': 'US'
        }
        
        result = await pipeline._execute_phone_provisioning_stage(preferences, 'agent-123', {})
        
        # Should select the number matching preferences
        assert result['phone_number'] == '+15555555555'
    
    @pytest.mark.asyncio
    async def test_phone_provisioning_fallback_options(self, mock_phone_service):
        """Test fallback when preferred numbers are unavailable"""
        # First search returns no results
        mock_phone_service.search_available_numbers.side_effect = [
            [],  # No numbers matching preferences
            [{'phone_number': '+15551111111', 'friendly_name': '(555) 111-1111'}]  # Fallback search
        ]
        mock_phone_service.provision_phone_number.return_value = {
            'phone_number': '+15551111111',
            'phone_sid': 'phone-sid-111',
            'status': 'success'
        }
        mock_phone_service.configure_agent_webhook.return_value = {'status': 'success'}
        
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.phone_service = mock_phone_service
        
        preferences = {
            'area_code': '999',  # Unavailable area code
            'country_code': 'US'
        }
        
        result = await pipeline._execute_phone_provisioning_stage(preferences, 'agent-123', {})
        
        assert result['status'] == 'success'
        assert result['phone_number'] == '+15551111111'
        assert result['used_fallback'] is True


class TestPipelineErrorHandling:
    """Test error handling and recovery mechanisms"""
    
    @pytest.fixture
    def pipeline_with_errors(self):
        """Pipeline configured to simulate various error conditions"""
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.simulate_errors = True
        return pipeline
    
    @pytest.mark.asyncio
    async def test_stage_failure_recovery(self, pipeline_with_errors, pipeline_request):
        """Test pipeline recovers from individual stage failures"""
        with patch.object(pipeline_with_errors, '_execute_web_crawling_stage') as mock_crawl:
            mock_crawl.side_effect = Exception("Crawling failed")
            
            result = await pipeline_with_errors.create_agent(pipeline_request)
            
            # Pipeline should continue with fallback content
            assert result['status'] != 'failed'
            assert 'fallback_content' in result or 'error_recovered' in result['stage_results']
    
    @pytest.mark.asyncio
    async def test_critical_stage_failure_handling(self, pipeline_with_errors, pipeline_request):
        """Test handling of critical stage failures that should stop pipeline"""
        # Mock all earlier stages to succeed so we get to voice_agent_creation
        with patch.object(pipeline_with_errors, '_execute_web_crawling_stage') as mock_crawl:
            mock_crawl.return_value = {'status': 'success', 'raw_content': {}}
            
            with patch.object(pipeline_with_errors, '_execute_content_extraction_stage') as mock_extract:
                mock_extract.return_value = {'status': 'success', 'categories': {}}
                
                with patch.object(pipeline_with_errors, '_execute_knowledge_base_creation_stage') as mock_kb:
                    mock_kb.return_value = {'status': 'success', 'knowledge_base': {}}
                    
                    with patch.object(pipeline_with_errors, '_execute_voice_agent_creation_stage') as mock_agent:
                        mock_agent.return_value = {'status': 'critical_error', 'error': 'Database unavailable'}
                        
                        result = await pipeline_with_errors.create_agent(pipeline_request)
                        
                        assert result['status'] == 'failed'
                        assert 'critical_error' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_timeout_handling_with_partial_results(self, pipeline_with_errors, pipeline_request):
        """Test timeout handling when some stages complete"""
        start_time = time.time()
        
        # Mock earlier stages to succeed so we have some partial results
        with patch.object(pipeline_with_errors, '_execute_web_crawling_stage') as mock_crawl:
            mock_crawl.return_value = {'status': 'success', 'raw_content': {}}
            
            with patch.object(pipeline_with_errors, '_execute_content_extraction_stage') as mock_extract:
                mock_extract.return_value = {'status': 'success', 'categories': {}}
                
                with patch.object(pipeline_with_errors.coordinator, 'is_approaching_timeout') as mock_timeout:
                    # Simulate timeout condition only after some stages complete
                    call_count = 0
                    def timeout_side_effect(*args, **kwargs):
                        nonlocal call_count
                        call_count += 1
                        # Allow first 2 stages to execute, then timeout
                        return call_count > 2
                    
                    mock_timeout.side_effect = timeout_side_effect
                    
                    result = await pipeline_with_errors.create_agent(pipeline_request)
                    
                    # Should complete with available results even if not all stages finished
                    assert result['status'] in ['partial_success', 'timeout_completed']
                    assert 'completed_stages' in result


class TestRollbackManager:
    """Test rollback mechanisms for failed pipelines"""
    
    @pytest.fixture
    def rollback_manager(self):
        """Create rollback manager instance"""
        return RollbackManager()
    
    @pytest.fixture
    def pipeline_state_with_resources(self):
        """Pipeline state with created resources that need rollback"""
        state = PipelineState(
            pipeline_id='test-pipeline-123',
            tenant_id='test-tenant-123'
        )
        # Add some completed stages
        state.completed_stages = ['web_crawling', 'content_extraction', 'voice_agent_creation']
        state.failed_stages = ['phone_provisioning']
        
        # Add some created resources
        state.add_created_resource(
            'voice_agent', 'agent-123', 
            {'collection': 'voice_agents'},
            'voice_agent_creation', '_rollback_voice_agent', 1
        )
        state.add_created_resource(
            'phone_number', 'phone-sid-123',
            {'sid': 'phone-sid-123'},
            'phone_provisioning', '_rollback_phone_number', 2
        )
        
        return state
    
    @pytest.mark.asyncio
    async def test_rollback_created_resources(self, rollback_manager, pipeline_state_with_resources):
        """Test rollback removes created resources in reverse order"""
        # Create async mock functions
        mock_phone_rollback = AsyncMock(return_value={'status': 'success'})
        mock_agent_rollback = AsyncMock(return_value={'status': 'success'})
        
        # Patch the handlers dictionary directly
        rollback_manager.rollback_handlers['phone_number'] = mock_phone_rollback
        rollback_manager.rollback_handlers['voice_agent'] = mock_agent_rollback
        
        result = await rollback_manager.rollback_pipeline(pipeline_state_with_resources)
        
        assert result['status'] == 'success'
        assert result['rolled_back_resources'] > 0
        
        # Verify both handlers were called
        mock_phone_rollback.assert_called_once()
        mock_agent_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_partial_rollback_on_failure(self, rollback_manager, pipeline_state_with_resources):
        """Test partial rollback when some rollback operations fail"""
        # Create async mock functions
        mock_phone_rollback = AsyncMock(return_value={'status': 'success'})
        mock_agent_rollback = AsyncMock(side_effect=Exception("Failed to delete agent"))
        
        # Patch the handlers dictionary directly
        rollback_manager.rollback_handlers['phone_number'] = mock_phone_rollback
        rollback_manager.rollback_handlers['voice_agent'] = mock_agent_rollback
        
        result = await rollback_manager.rollback_pipeline(pipeline_state_with_resources)
        
        assert result['status'] == 'partial_success'
        assert len(result['failed_rollbacks']) > 0
        # Check that the failed rollback contains the expected resource
        failed_resource = result['failed_rollbacks'][0]
        assert failed_resource['resource_type'] == 'voice_agent'
    
    def test_rollback_strategy_determination(self, rollback_manager, pipeline_state_with_resources):
        """Test rollback strategy is determined based on failure point and resources"""
        strategy = rollback_manager.determine_rollback_strategy(pipeline_state_with_resources)
        
        assert strategy['type'] == 'selective_rollback'
        assert 'phone_provisioning' in strategy['rollback_stages']
        assert 'voice_agent' in strategy['preserve_resources']  # Should preserve agent if phone fails


class TestPipelinePerformanceOptimizations:
    """Test performance optimizations and timing improvements"""
    
    @pytest.fixture
    def optimized_pipeline(self):
        """Pipeline configured for performance testing"""
        pipeline = AgentCreationPipeline(safe_mode=True)
        pipeline.enable_optimizations = True
        return pipeline
    
    @pytest.mark.asyncio
    async def test_parallel_stage_execution_timing(self, optimized_pipeline, pipeline_request):
        """Test parallel execution improves overall timing"""
        # Mock stage execution times
        stage_times = {
            'web_crawling': 30,
            'content_extraction': 25,
            'voice_agent_creation': 20,
            'phone_provisioning': 15
        }
        
        with patch.object(optimized_pipeline, '_execute_stage') as mock_execute:
            async def mock_stage_execution(state, stage_name):
                await asyncio.sleep(stage_times.get(stage_name, 5) / 10)  # Simulate work (scaled down)
                return {'status': 'success'}
            
            mock_execute.side_effect = mock_stage_execution
            
            start_time = time.time()
            result = await optimized_pipeline.create_agent(pipeline_request)
            execution_time = time.time() - start_time
            
            # Parallel execution should complete faster than sequential
            sequential_time = sum(stage_times.values()) / 10  # Scaled down time
            assert execution_time < sequential_time * 0.8  # At least 20% faster
    
    @pytest.mark.asyncio
    async def test_caching_mechanisms(self, optimized_pipeline, pipeline_request):
        """Test caching mechanisms improve repeat performance"""
        # First execution
        result1 = await optimized_pipeline.create_agent(pipeline_request)
        first_execution_time = result1['execution_time']
        
        # Second execution with same URL should use cached data
        result2 = await optimized_pipeline.create_agent(pipeline_request)
        second_execution_time = result2['execution_time']
        
        # Second execution should be significantly faster
        assert second_execution_time < first_execution_time * 0.5
        assert result2.get('cache_hit') is True
    
    @pytest.mark.asyncio
    async def test_resource_preallocation(self, optimized_pipeline, pipeline_request):
        """Test resource preallocation optimizes performance"""
        with patch.object(optimized_pipeline.phone_service, 'preallocate_numbers') as mock_prealloc:
            mock_prealloc.return_value = {'preallocated_count': 5}
            
            result = await optimized_pipeline.create_agent(pipeline_request)
            
            assert result['status'] == 'completed'
            # Should have used preallocated resources
            assert result.get('used_preallocation') is True


class TestPipelineIntegrationScenarios:
    """Test realistic integration scenarios and edge cases"""
    
    @pytest.mark.asyncio
    async def test_high_traffic_website_handling(self):
        """Test pipeline handles high-traffic websites appropriately"""
        pipeline = AgentCreationPipeline(safe_mode=True)
        
        request = {
            'website_url': 'https://high-traffic-site.com',
            'tenant_id': 'tenant-123',
            'agent_name': 'Traffic Handler'
        }
        
        with patch.object(pipeline.web_crawler, 'crawl_website_async') as mock_crawl:
            # Simulate high-traffic site with rate limiting
            mock_crawl.return_value = {
                'status': 'rate_limited',
                'retry_after': 30,
                'partial_content': {'company_overview': {'title': 'About', 'content': '...'}}
            }
            
            result = await pipeline.create_agent(request)
            
            # Should handle rate limiting gracefully
            assert result['status'] in ['completed', 'partial_success']
            assert 'rate_limiting_handled' in result
    
    @pytest.mark.asyncio
    async def test_multilingual_content_processing(self):
        """Test pipeline handles multilingual content correctly"""
        pipeline = AgentCreationPipeline(safe_mode=True)
        
        request = {
            'website_url': 'https://multilingual-site.com',
            'tenant_id': 'tenant-123',
            'agent_name': 'Multilingual Agent',
            'language_preferences': ['en', 'es', 'fr']
        }
        
        result = await pipeline.create_agent(request)
        
        assert result['status'] in ['completed', 'error_recovered']
        assert 'detected_languages' in result
        assert result['primary_language'] in request['language_preferences']
    
    @pytest.mark.asyncio
    async def test_complex_website_structure_handling(self):
        """Test pipeline handles complex website structures (SPAs, dynamic content)"""
        pipeline = AgentCreationPipeline(safe_mode=True)
        
        request = {
            'website_url': 'https://spa-website.com',
            'tenant_id': 'tenant-123',
            'agent_name': 'SPA Handler'
        }
        
        with patch.object(pipeline.web_crawler, 'crawl_website_async') as mock_crawl:
            # Simulate SPA with JavaScript-rendered content
            mock_crawl.return_value = {
                'status': 'spa_detected',
                'javascript_content': True,
                'rendered_content': {'company_overview': {'title': 'Dynamic About', 'content': '...'}}
            }
            
            result = await pipeline.create_agent(request)
            
            assert result['status'] == 'completed'
            assert result.get('javascript_rendering_used') is True


if __name__ == '__main__':
    pytest.main([__file__])