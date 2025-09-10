"""
T024: Agent Performance Monitoring Tests
Test-driven development for call logging, recording, metrics collection, and health monitoring
Tests agent status monitoring and performance metrics collection systems
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
import json
import tempfile
import os

from src.services.monitoring.call_logger import CallLogger, CallRecord, CallStatus
from src.services.monitoring.metrics_collector import (
    MetricsCollector, PerformanceMetric, MetricType, AgentMetrics
)
from src.services.monitoring.health_monitor import (
    HealthMonitor, HealthCheck, HealthStatus, SystemHealth
)
from src.services.monitoring.monitoring_service import MonitoringService


class TestCallLogger:
    """Test call logging and recording functionality"""
    
    @pytest.fixture
    def call_logger(self):
        """Create call logger instance with temp storage"""
        return CallLogger(storage_path="/tmp/test_call_logs")
    
    @pytest.fixture
    def sample_call_record(self):
        """Sample call record for testing"""
        return CallRecord(
            call_id="call-123",
            agent_id="agent-456",
            tenant_id="tenant-789",
            caller_number="+15551234567",
            start_time=datetime.now(),
            status=CallStatus.IN_PROGRESS,
            duration=0.0
        )
    
    def test_call_logger_initialization(self, call_logger):
        """Test call logger initializes correctly"""
        assert call_logger is not None
        assert hasattr(call_logger, 'storage_path')
        assert hasattr(call_logger, 'active_calls')
        assert hasattr(call_logger, 'call_records')
    
    def test_start_call_logging(self, call_logger, sample_call_record):
        """Test call logging starts correctly"""
        result = call_logger.start_call(
            call_id=sample_call_record.call_id,
            agent_id=sample_call_record.agent_id,
            tenant_id=sample_call_record.tenant_id,
            caller_number=sample_call_record.caller_number
        )
        
        assert result['status'] == 'started'
        assert result['call_id'] == sample_call_record.call_id
        assert sample_call_record.call_id in call_logger.active_calls
        
        # Verify call record created
        call_record = call_logger.active_calls[sample_call_record.call_id]
        assert call_record.agent_id == sample_call_record.agent_id
        assert call_record.status == CallStatus.IN_PROGRESS
    
    def test_log_call_event(self, call_logger, sample_call_record):
        """Test logging call events during conversation"""
        # Start call first
        call_logger.start_call(
            sample_call_record.call_id,
            sample_call_record.agent_id,
            sample_call_record.tenant_id,
            sample_call_record.caller_number
        )
        
        # Log events
        events = [
            {'type': 'user_message', 'content': 'Hello', 'timestamp': datetime.now()},
            {'type': 'agent_response', 'content': 'Hi there!', 'timestamp': datetime.now()},
            {'type': 'intent_recognized', 'intent': 'greeting', 'confidence': 0.95}
        ]
        
        for event in events:
            result = call_logger.log_event(sample_call_record.call_id, event)
            assert result['status'] == 'logged'
        
        # Verify events stored
        call_record = call_logger.active_calls[sample_call_record.call_id]
        assert len(call_record.events) == 3
        assert call_record.events[0]['type'] == 'user_message'
        assert call_record.events[1]['content'] == 'Hi there!'
    
    def test_end_call_logging(self, call_logger, sample_call_record):
        """Test call logging ends correctly with summary"""
        # Start call
        call_logger.start_call(
            sample_call_record.call_id,
            sample_call_record.agent_id,
            sample_call_record.tenant_id,
            sample_call_record.caller_number
        )
        
        # Add some events
        call_logger.log_event(sample_call_record.call_id, {
            'type': 'user_message',
            'content': 'Test message'
        })
        
        # End call
        result = call_logger.end_call(
            sample_call_record.call_id,
            end_reason='completed',
            customer_satisfaction=8
        )
        
        assert result['status'] == 'completed'
        assert result['duration'] > 0
        assert result['event_count'] == 1
        
        # Verify call moved to completed records
        assert sample_call_record.call_id not in call_logger.active_calls
        assert sample_call_record.call_id in call_logger.call_records
        
        completed_record = call_logger.call_records[sample_call_record.call_id]
        assert completed_record.status == CallStatus.COMPLETED
        assert completed_record.end_reason == 'completed'
        assert completed_record.customer_satisfaction == 8
    
    def test_call_recording_functionality(self, call_logger, sample_call_record):
        """Test call recording starts and stops correctly"""
        # Start call with recording
        result = call_logger.start_call(
            sample_call_record.call_id,
            sample_call_record.agent_id,
            sample_call_record.tenant_id,
            sample_call_record.caller_number,
            enable_recording=True
        )
        
        assert result['recording_enabled'] is True
        
        # Simulate recording audio chunks
        audio_chunks = [
            b'audio_data_chunk_1',
            b'audio_data_chunk_2',
            b'audio_data_chunk_3'
        ]
        
        for chunk in audio_chunks:
            call_logger.record_audio_chunk(sample_call_record.call_id, chunk)
        
        # End call and verify recording saved
        result = call_logger.end_call(sample_call_record.call_id, 'completed')
        
        assert 'recording_file' in result
        assert result['recording_size'] > 0
        
        # Verify recording file exists (mocked)
        call_record = call_logger.call_records[sample_call_record.call_id]
        assert call_record.recording_file is not None
        assert call_record.recording_size > 0
    
    def test_call_transcription_integration(self, call_logger, sample_call_record):
        """Test call transcription is generated for recordings"""
        # Mock the transcription service within call_logger
        with patch.object(call_logger, 'transcription_service') as mock_transcription:
            mock_transcription.transcribe_audio.return_value = {
                'text': 'Hello, this is a test conversation.',
                'confidence': 0.92,
                'words': [
                    {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                    {'word': 'this', 'start': 0.6, 'end': 0.8}
                ]
            }
            
            # Start call with recording and transcription
            call_logger.start_call(
                sample_call_record.call_id,
                sample_call_record.agent_id,
                sample_call_record.tenant_id,
                sample_call_record.caller_number,
                enable_recording=True,
                enable_transcription=True
            )
            
            # Add some audio chunks
            call_logger.record_audio_chunk(sample_call_record.call_id, b'audio_data')
            
            # End call to trigger transcription
            result = call_logger.end_call(sample_call_record.call_id, 'completed')
            
            assert result['transcription_available'] is True
            
            call_record = call_logger.call_records[sample_call_record.call_id]
            assert call_record.transcription is not None
            assert 'Hello' in call_record.transcription['text']
    
    def test_call_search_and_filtering(self, call_logger):
        """Test searching and filtering call records"""
        # Create multiple call records
        call_ids = []
        for i in range(5):
            call_id = f"call-{i}"
            call_logger.start_call(
                call_id,
                f"agent-{i % 2}",  # Two different agents
                "tenant-123",
                f"+155512345{i}"
            )
            call_logger.end_call(call_id, 'completed')
            call_ids.append(call_id)
        
        # Search by agent
        results = call_logger.search_calls(agent_id="agent-0")
        agent_0_calls = [r for r in results if r.agent_id == "agent-0"]
        assert len(agent_0_calls) == 3  # Calls 0, 2, 4
        
        # Search by date range
        today = datetime.now()
        results = call_logger.search_calls(
            start_date=today,
            end_date=today
        )
        assert len(results) == 5  # All calls from today
        
        # Search by call status
        results = call_logger.search_calls(status=CallStatus.COMPLETED)
        assert len(results) == 5  # All completed
    
    def test_call_analytics_generation(self, call_logger):
        """Test generation of call analytics and summaries"""
        # Create calls with various outcomes
        call_scenarios = [
            {'id': 'call-success', 'satisfaction': 9, 'duration': 300},
            {'id': 'call-neutral', 'satisfaction': 6, 'duration': 180},
            {'id': 'call-poor', 'satisfaction': 3, 'duration': 60},
            {'id': 'call-dropped', 'satisfaction': None, 'duration': 30}
        ]
        
        for scenario in call_scenarios:
            call_logger.start_call(
                scenario['id'],
                "agent-analytics",
                "tenant-123",
                "+15551234567"
            )
            
            # Simulate call duration
            call_record = call_logger.active_calls[scenario['id']]
            call_record.start_time = datetime.now() - timedelta(seconds=scenario['duration'])
            
            call_logger.end_call(
                scenario['id'],
                'completed' if scenario['satisfaction'] else 'dropped',
                customer_satisfaction=scenario['satisfaction']
            )
        
        # Generate analytics
        analytics = call_logger.generate_analytics(
            agent_id="agent-analytics",
            time_period=timedelta(days=1)
        )
        
        assert analytics['total_calls'] == 4
        assert analytics['completed_calls'] == 3
        assert analytics['dropped_calls'] == 1
        assert analytics['average_satisfaction'] == 6.0  # (9+6+3)/3
        assert analytics['average_duration'] > 0


class TestMetricsCollector:
    """Test performance metrics collection system"""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector instance"""
        return MetricsCollector()
    
    @pytest.fixture
    def sample_performance_metric(self):
        """Sample performance metric"""
        return PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            agent_id="agent-123",
            metric_type=MetricType.RESPONSE_TIME,
            value=1.25,
            timestamp=datetime.now(),
            context={'endpoint': '/api/chat', 'user_id': 'user-456'}
        )
    
    def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector initializes correctly"""
        assert metrics_collector is not None
        assert hasattr(metrics_collector, 'metrics_buffer')
        assert hasattr(metrics_collector, 'aggregated_metrics')
        assert hasattr(metrics_collector, 'collection_interval')
    
    def test_record_performance_metric(self, metrics_collector, sample_performance_metric):
        """Test recording individual performance metrics"""
        result = metrics_collector.record_metric(sample_performance_metric)
        
        assert result['status'] == 'recorded'
        assert result['metric_id'] == sample_performance_metric.metric_id
        
        # Verify metric in buffer
        assert len(metrics_collector.metrics_buffer) == 1
        recorded_metric = metrics_collector.metrics_buffer[0]
        assert recorded_metric.agent_id == sample_performance_metric.agent_id
        assert recorded_metric.value == sample_performance_metric.value
    
    def test_record_response_time_metrics(self, metrics_collector):
        """Test recording response time metrics for agents"""
        agent_id = "agent-response-time"
        
        # Record multiple response times
        response_times = [0.5, 1.2, 0.8, 2.1, 0.9]
        for rt in response_times:
            metrics_collector.record_response_time(agent_id, rt, {'query_type': 'greeting'})
        
        # Verify metrics recorded
        assert len(metrics_collector.metrics_buffer) == 5
        
        # Check specific values
        recorded_times = [m.value for m in metrics_collector.metrics_buffer]
        assert recorded_times == response_times
    
    def test_record_throughput_metrics(self, metrics_collector):
        """Test recording throughput metrics"""
        agent_id = "agent-throughput"
        
        # Record throughput over time
        throughput_data = [
            {'requests_per_minute': 45, 'timestamp': datetime.now() - timedelta(minutes=5)},
            {'requests_per_minute': 52, 'timestamp': datetime.now() - timedelta(minutes=4)},
            {'requests_per_minute': 38, 'timestamp': datetime.now() - timedelta(minutes=3)},
        ]
        
        for data in throughput_data:
            metrics_collector.record_throughput(
                agent_id,
                data['requests_per_minute'],
                data['timestamp']
            )
        
        # Verify throughput metrics
        throughput_metrics = [
            m for m in metrics_collector.metrics_buffer 
            if m.metric_type == MetricType.THROUGHPUT
        ]
        assert len(throughput_metrics) == 3
        assert throughput_metrics[0].value == 45
    
    def test_record_error_rate_metrics(self, metrics_collector):
        """Test recording error rate metrics"""
        agent_id = "agent-errors"
        
        # Record error events
        error_scenarios = [
            {'error_type': 'timeout', 'count': 3},
            {'error_type': 'validation_error', 'count': 1},
            {'error_type': 'service_unavailable', 'count': 2}
        ]
        
        total_requests = 100
        
        for scenario in error_scenarios:
            error_rate = scenario['count'] / total_requests
            metrics_collector.record_error_rate(
                agent_id,
                error_rate,
                {'error_type': scenario['error_type'], 'total_requests': total_requests}
            )
        
        # Verify error rate metrics
        error_metrics = [
            m for m in metrics_collector.metrics_buffer
            if m.metric_type == MetricType.ERROR_RATE
        ]
        assert len(error_metrics) == 3
        assert error_metrics[0].value == 0.03  # 3/100
    
    def test_agent_metrics_aggregation(self, metrics_collector):
        """Test aggregation of metrics by agent"""
        agent_id = "agent-aggregation"
        
        # Record various metrics for same agent
        metrics_collector.record_response_time(agent_id, 1.0)
        metrics_collector.record_response_time(agent_id, 1.5)
        metrics_collector.record_throughput(agent_id, 50)
        metrics_collector.record_error_rate(agent_id, 0.02)
        
        # Trigger aggregation
        aggregated = metrics_collector.aggregate_metrics_by_agent(agent_id)
        
        assert aggregated.agent_id == agent_id
        assert aggregated.average_response_time == 1.25  # (1.0 + 1.5) / 2
        assert aggregated.current_throughput == 50
        assert aggregated.error_rate == 0.02
        assert aggregated.total_requests > 0
    
    def test_time_series_metrics(self, metrics_collector):
        """Test time series metrics collection and querying"""
        agent_id = "agent-timeseries"
        
        # Record metrics over time
        base_time = datetime.now() - timedelta(hours=1)
        for i in range(60):  # 60 data points over 1 hour
            timestamp = base_time + timedelta(minutes=i)
            response_time = 1.0 + (i % 10) * 0.1  # Varying response time
            
            metric = PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                agent_id=agent_id,
                metric_type=MetricType.RESPONSE_TIME,
                value=response_time,
                timestamp=timestamp
            )
            metrics_collector.record_metric(metric)
        
        # Query time series data
        time_series = metrics_collector.get_time_series(
            agent_id,
            MetricType.RESPONSE_TIME,
            start_time=base_time,
            end_time=datetime.now()
        )
        
        assert len(time_series) == 60
        # Convert timestamp back for comparison
        first_timestamp = datetime.fromisoformat(time_series[0]['timestamp'])
        assert first_timestamp == base_time
        assert time_series[-1]['value'] == 1.9  # Last value in pattern
    
    def test_metrics_alerts_and_thresholds(self, metrics_collector):
        """Test metrics alert system with configurable thresholds"""
        agent_id = "agent-alerts"
        
        # Configure thresholds
        metrics_collector.set_alert_thresholds(agent_id, {
            MetricType.RESPONSE_TIME: {'warning': 2.0, 'critical': 5.0},
            MetricType.ERROR_RATE: {'warning': 0.05, 'critical': 0.10},
            MetricType.THROUGHPUT: {'warning': 10, 'critical': 5}  # Low throughput alerts
        })
        
        # Record metrics that trigger alerts
        alerts = []
        
        # Add alert callback to capture alerts
        metrics_collector.add_alert_callback(lambda alert: alerts.append(alert))
            
        # Trigger warning alert
        metrics_collector.record_response_time(agent_id, 3.0)
        
        # Trigger critical alert
        metrics_collector.record_error_rate(agent_id, 0.12)
        
        assert len(alerts) == 2
        assert alerts[0]['level'] == 'warning'
        assert alerts[0]['metric_type'] == MetricType.RESPONSE_TIME
        assert alerts[1]['level'] == 'critical'
        assert alerts[1]['metric_type'] == MetricType.ERROR_RATE
    
    def test_metrics_export_and_persistence(self, metrics_collector):
        """Test metrics export to various formats"""
        agent_id = "agent-export"
        
        # Record sample metrics
        for i in range(10):
            metrics_collector.record_response_time(agent_id, 1.0 + i * 0.1)
            metrics_collector.record_throughput(agent_id, 50 + i)
        
        # Export to JSON
        json_export = metrics_collector.export_metrics(agent_id, format='json')
        json_data = json.loads(json_export)
        
        assert 'agent_id' in json_data
        assert 'metrics' in json_data
        assert len(json_data['metrics']) == 20  # 10 response time + 10 throughput
        
        # Export to CSV format
        csv_export = metrics_collector.export_metrics(agent_id, format='csv')
        assert 'agent_id,metric_type,value,timestamp' in csv_export
        # Count non-empty lines (subtract 1 for trailing empty line from split)
        non_empty_lines = [line for line in csv_export.split('\n') if line.strip()]
        assert len(non_empty_lines) == 21  # Header + 20 metrics
    
    def test_real_time_metrics_streaming(self, metrics_collector):
        """Test real-time metrics streaming to monitoring dashboard"""
        agent_id = "agent-streaming"
        
        # Set up mock streaming connection
        mock_stream = Mock()
        metrics_collector.add_stream_subscriber(mock_stream)
        
        # Record metrics - should trigger streaming
        metrics_collector.record_response_time(agent_id, 1.5)
        metrics_collector.record_throughput(agent_id, 45)
        
        # Verify streaming calls
        assert mock_stream.send_metric.call_count == 2
        
        # Check streamed data structure
        call_args = mock_stream.send_metric.call_args_list
        first_metric = call_args[0][0][0]  # First argument of first call
        
        assert hasattr(first_metric, 'agent_id')
        assert hasattr(first_metric, 'metric_type')
        assert hasattr(first_metric, 'value')


class TestHealthMonitor:
    """Test agent status monitoring and health checks"""
    
    @pytest.fixture
    def health_monitor(self):
        """Create health monitor instance"""
        return HealthMonitor()
    
    @pytest.fixture
    def sample_agent_config(self):
        """Sample agent configuration for health monitoring"""
        return {
            'agent_id': 'agent-health-123',
            'tenant_id': 'tenant-456',
            'name': 'Customer Service Agent',
            'health_check_interval': 30,
            'endpoints': {
                'chat': '/api/agents/agent-health-123/chat',
                'status': '/api/agents/agent-health-123/status'
            }
        }
    
    def test_health_monitor_initialization(self, health_monitor):
        """Test health monitor initializes correctly"""
        assert health_monitor is not None
        assert hasattr(health_monitor, 'monitored_agents')
        assert hasattr(health_monitor, 'health_checks')
        assert hasattr(health_monitor, 'check_interval')
    
    def test_register_agent_for_monitoring(self, health_monitor, sample_agent_config):
        """Test registering agent for health monitoring"""
        result = health_monitor.register_agent(sample_agent_config)
        
        assert result['status'] == 'registered'
        assert result['agent_id'] == sample_agent_config['agent_id']
        
        # Verify agent is tracked
        assert sample_agent_config['agent_id'] in health_monitor.monitored_agents
        agent_info = health_monitor.monitored_agents[sample_agent_config['agent_id']]
        assert agent_info['status'] == HealthStatus.UNKNOWN
        assert agent_info['last_check'] is None
    
    @pytest.mark.asyncio
    async def test_perform_health_check(self, health_monitor, sample_agent_config):
        """Test performing health check on registered agent"""
        # Register agent first
        health_monitor.register_agent(sample_agent_config)
        
        # Mock the health check response
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'status': 'healthy',
                'response_time': 0.15,
                'memory_usage': 45.2,
                'cpu_usage': 12.8,
                'active_conversations': 3
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await health_monitor.perform_health_check(sample_agent_config['agent_id'])
            
            assert result['status'] == HealthStatus.HEALTHY
            # Response time will be calculated by the actual HTTP request timing, not from the response
            assert 'response_time' in result
            assert result['system_metrics']['memory_usage'] == 45.2
            
            # Verify agent status updated
            agent_info = health_monitor.monitored_agents[sample_agent_config['agent_id']]
            assert agent_info['status'] == HealthStatus.HEALTHY
            assert agent_info['last_check'] is not None
    
    @pytest.mark.asyncio
    async def test_health_check_failure_detection(self, health_monitor, sample_agent_config):
        """Test detection and handling of agent health check failures"""
        health_monitor.register_agent(sample_agent_config)
        
        # Mock failing health check
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            result = await health_monitor.perform_health_check(sample_agent_config['agent_id'])
            
            assert result['status'] == HealthStatus.UNHEALTHY
            assert 'error' in result
            assert 'timeout' in result['error'].lower()
            
            # Verify agent marked as unhealthy
            agent_info = health_monitor.monitored_agents[sample_agent_config['agent_id']]
            assert agent_info['status'] == HealthStatus.UNHEALTHY
            assert agent_info['consecutive_failures'] == 1
    
    @pytest.mark.asyncio
    async def test_continuous_health_monitoring(self, health_monitor, sample_agent_config):
        """Test continuous health monitoring with automatic checks"""
        health_monitor.register_agent(sample_agent_config)
        
        # Mock successful health checks
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {'status': 'healthy', 'response_time': 0.1}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Start continuous monitoring
            monitoring_task = asyncio.create_task(
                health_monitor.start_continuous_monitoring(check_interval=1)
            )
            
            # Let it run for a few seconds
            await asyncio.sleep(2.5)
            
            # Stop monitoring
            monitoring_task.cancel()
            
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
            # Should have performed multiple checks
            agent_info = health_monitor.monitored_agents[sample_agent_config['agent_id']]
            assert agent_info['total_checks'] >= 2
            assert mock_get.call_count >= 2
    
    def test_system_health_aggregation(self, health_monitor):
        """Test aggregation of system-wide health status"""
        # Register multiple agents with different health statuses
        agents = [
            {'id': 'agent-1', 'status': HealthStatus.HEALTHY},
            {'id': 'agent-2', 'status': HealthStatus.HEALTHY},
            {'id': 'agent-3', 'status': HealthStatus.DEGRADED},
            {'id': 'agent-4', 'status': HealthStatus.UNHEALTHY},
            {'id': 'agent-5', 'status': HealthStatus.HEALTHY}
        ]
        
        for agent in agents:
            health_monitor.monitored_agents[agent['id']] = {
                'status': agent['status'],
                'last_check': datetime.now(),
                'consecutive_failures': 0 if agent['status'] == HealthStatus.HEALTHY else 1
            }
        
        # Get system health summary
        system_health = health_monitor.get_system_health()
        
        assert system_health.total_agents == 5
        assert system_health.healthy_agents == 3
        assert system_health.degraded_agents == 1
        assert system_health.unhealthy_agents == 1
        assert system_health.overall_status == HealthStatus.DEGRADED  # Mixed health
    
    def test_health_alerts_and_notifications(self, health_monitor, sample_agent_config):
        """Test health alert system and notifications"""
        health_monitor.register_agent(sample_agent_config)
        
        # Configure alert thresholds
        health_monitor.set_alert_thresholds({
            'consecutive_failures': 3,
            'response_time_threshold': 2.0,
            'memory_usage_threshold': 90.0
        })
        
        alerts = []
        # Add alert callback to capture alerts
        health_monitor.add_alert_callback(lambda alert: alerts.append(alert))
            
        # Simulate multiple failures to trigger alert
        agent_info = health_monitor.monitored_agents[sample_agent_config['agent_id']]
        agent_info['consecutive_failures'] = 3
        agent_info['status'] = HealthStatus.UNHEALTHY
        
        health_monitor._check_alert_conditions(sample_agent_config['agent_id'])
        
        assert len(alerts) == 1
        assert alerts[0]['type'] == 'consecutive_failures'
        assert alerts[0]['agent_id'] == sample_agent_config['agent_id']
    
    def test_health_history_tracking(self, health_monitor, sample_agent_config):
        """Test tracking health history over time"""
        health_monitor.register_agent(sample_agent_config)
        
        # Simulate health status changes over time
        status_changes = [
            (HealthStatus.HEALTHY, datetime.now() - timedelta(minutes=10)),
            (HealthStatus.DEGRADED, datetime.now() - timedelta(minutes=5)),
            (HealthStatus.UNHEALTHY, datetime.now() - timedelta(minutes=2)),
            (HealthStatus.HEALTHY, datetime.now())
        ]
        
        for status, timestamp in status_changes:
            health_monitor._record_health_status(
                sample_agent_config['agent_id'],
                status,
                timestamp
            )
        
        # Get health history
        history = health_monitor.get_health_history(
            sample_agent_config['agent_id'],
            duration=timedelta(minutes=15)
        )
        
        assert len(history) == 4
        # Compare status values instead of enum objects
        assert history[0]['status'] == HealthStatus.HEALTHY.value
        assert history[-1]['status'] == HealthStatus.HEALTHY.value
        
        # Verify uptime calculation
        uptime_stats = health_monitor.calculate_uptime(
            sample_agent_config['agent_id'],
            duration=timedelta(minutes=15)
        )
        
        assert 'uptime_percentage' in uptime_stats
        assert uptime_stats['uptime_percentage'] <= 100


class TestMonitoringService:
    """Test integrated monitoring service functionality"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service with all components"""
        temp_dir = tempfile.mkdtemp()
        service = MonitoringService(storage_path=temp_dir, enable_auto_start=False)
        yield service
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def agent_config(self):
        """Agent configuration for integration testing"""
        return {
            'agent_id': 'agent-integration-123',
            'tenant_id': 'tenant-789',
            'name': 'Integration Test Agent',
            'pipeline_id': 'pipeline-456'
        }
    
    def test_monitoring_service_initialization(self, monitoring_service):
        """Test monitoring service initializes all components"""
        assert monitoring_service is not None
        assert hasattr(monitoring_service, 'call_logger')
        assert hasattr(monitoring_service, 'metrics_collector')
        assert hasattr(monitoring_service, 'health_monitor')
        assert hasattr(monitoring_service, 'integration_hooks')
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_flow(self, monitoring_service, agent_config):
        """Test complete monitoring flow from call start to completion"""
        agent_id = agent_config['agent_id']
        call_id = f"call-{uuid.uuid4()}"
        
        # 1. Start monitoring agent
        result = monitoring_service.start_monitoring_agent(agent_config)
        assert result['status'] == 'monitoring_started'
        
        # 2. Start call logging
        call_result = monitoring_service.start_call_monitoring(
            call_id=call_id,
            agent_id=agent_id,
            tenant_id=agent_config['tenant_id'],
            caller_number="+15551234567",
            enable_recording=True
        )
        assert call_result['status'] == 'started'
        
        # 3. Record performance metrics during call
        monitoring_service.record_interaction_metrics(call_id, {
            'response_time': 1.2,
            'intent_confidence': 0.89,
            'user_satisfaction_prediction': 0.75
        })
        
        # 4. Log call events
        events = [
            {'type': 'user_message', 'content': 'Hello'},
            {'type': 'agent_response', 'content': 'Hi! How can I help?'},
            {'type': 'intent_recognized', 'intent': 'greeting', 'confidence': 0.95}
        ]
        
        for event in events:
            monitoring_service.log_call_event(call_id, event)
        
        # 5. Perform health check (mock it since we don't have a real agent running)
        with patch.object(monitoring_service.health_monitor, 'perform_health_check') as mock_health:
            mock_health.return_value = {
                'status': HealthStatus.HEALTHY,
                'response_time': 0.1,
                'system_metrics': {'memory_usage': 45.2, 'cpu_usage': 12.8}
            }
            health_result = await monitoring_service.perform_health_check(agent_id)
            assert health_result['status'] == HealthStatus.HEALTHY
        
        # 6. End call monitoring
        end_result = monitoring_service.end_call_monitoring(
            call_id,
            end_reason='completed',
            customer_satisfaction=8
        )
        assert end_result['status'] == 'completed'
        
        # 7. Verify integrated data
        call_summary = monitoring_service.get_call_summary(call_id)
        assert call_summary['call_id'] == call_id
        assert call_summary['agent_id'] == agent_id
        assert call_summary['event_count'] == 3
        assert call_summary['customer_satisfaction'] == 8
        
        # 8. Get aggregated metrics
        agent_metrics = monitoring_service.get_agent_metrics(agent_id)
        assert agent_metrics.agent_id == agent_id
        assert agent_metrics.total_calls == 1
        assert agent_metrics.average_satisfaction == 8.0
    
    def test_pipeline_integration_monitoring(self, monitoring_service):
        """Test monitoring integration with pipeline services"""
        # Mock pipeline state since pipeline module is not available  
        from unittest.mock import Mock
        
        pipeline_state = Mock()
        pipeline_state.pipeline_id = 'pipeline-monitoring-test'
        pipeline_state.tenant_id = 'tenant-123' 
        pipeline_state.status = 'VOICE_AGENT_CREATION'
        pipeline_state.started_at = datetime.now()
        
        # Start monitoring pipeline
        result = monitoring_service.start_pipeline_monitoring(pipeline_state)
        assert result['status'] == 'monitoring_started'
        
        # Simulate pipeline stage completion with metrics
        stage_metrics = {
            'stage_name': 'voice_agent_creation',
            'execution_time': 15.5,
            'success': True,
            'resources_created': ['agent-123'],
            'performance_score': 0.92
        }
        
        monitoring_service.record_pipeline_stage_metrics(
            pipeline_state.pipeline_id,
            stage_metrics
        )
        
        # Get pipeline performance summary
        pipeline_summary = monitoring_service.get_pipeline_performance(
            pipeline_state.pipeline_id
        )
        
        assert pipeline_summary['pipeline_id'] == pipeline_state.pipeline_id
        assert pipeline_summary['completed_stages'] >= 1
        assert 'voice_agent_creation' in pipeline_summary['stage_metrics']
    
    def test_alert_coordination_system(self, monitoring_service, agent_config):
        """Test coordinated alert system across all monitoring components"""
        agent_id = agent_config['agent_id']
        
        # Start monitoring
        monitoring_service.start_monitoring_agent(agent_config)
        
        # Configure alert thresholds
        monitoring_service.configure_alerts(agent_id, {
            'response_time_threshold': 2.0,
            'error_rate_threshold': 0.05,
            'consecutive_health_failures': 3,
            'customer_satisfaction_threshold': 5.0
        })
        
        alerts_received = []
        
        # Add a callback to capture alerts
        monitoring_service.metrics_collector.add_alert_callback(lambda alert: alerts_received.append(alert))
            
        # Trigger multiple alert conditions
        monitoring_service.record_response_time(agent_id, 3.5)  # Above threshold
        monitoring_service.record_error_rate(agent_id, 0.08)   # Above threshold
        
        # Should generate alerts
        assert len(alerts_received) == 2
        assert any(alert['metric_type'] == MetricType.RESPONSE_TIME for alert in alerts_received)
        assert any(alert['metric_type'] == MetricType.ERROR_RATE for alert in alerts_received)
    
    def test_monitoring_dashboard_data_export(self, monitoring_service, agent_config):
        """Test data export for monitoring dashboard"""
        agent_id = agent_config['agent_id']
        
        # Generate sample monitoring data
        monitoring_service.start_monitoring_agent(agent_config)
        
        # Simulate multiple calls and metrics
        for i in range(5):
            call_id = f"call-dashboard-{i}"
            monitoring_service.start_call_monitoring(
                call_id, agent_id, agent_config['tenant_id'], f"+155512345{i}"
            )
            monitoring_service.record_interaction_metrics(call_id, {
                'response_time': 1.0 + i * 0.2,
                'user_satisfaction_prediction': 0.8 + i * 0.02
            })
            monitoring_service.end_call_monitoring(
                call_id, 'completed', customer_satisfaction=8 + i % 3
            )
        
        # Export dashboard data
        dashboard_data = monitoring_service.export_dashboard_data(
            agent_id,
            time_range=timedelta(hours=1),
            format='json'
        )
        
        data = json.loads(dashboard_data)
        
        assert 'agent_info' in data
        assert 'call_summary' in data
        assert 'performance_metrics' in data
        assert 'health_status' in data
        
        assert data['call_summary']['total_calls'] == 5
        assert len(data['performance_metrics']['response_times']) == 5
        assert data['agent_info']['agent_id'] == agent_id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])