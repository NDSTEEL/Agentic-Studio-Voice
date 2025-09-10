"""
Monitoring Service
Integrated monitoring service that coordinates call logging, metrics collection, and health monitoring
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import uuid
from pathlib import Path

from .call_logger import CallLogger, CallRecord, CallStatus
from .metrics_collector import MetricsCollector, PerformanceMetric, MetricType, AgentMetrics
from .health_monitor import HealthMonitor, HealthCheck, HealthStatus, SystemHealth

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Integrated monitoring service
    Coordinates call logging, performance metrics, and health monitoring
    """
    
    def __init__(self, 
                 storage_path: str = "./monitoring_data",
                 enable_auto_start: bool = False):  # Changed default to False for tests
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize monitoring components
        self.call_logger = CallLogger(storage_path=str(self.storage_path / "calls"))
        self.metrics_collector = MetricsCollector()
        self.health_monitor = HealthMonitor()
        
        # Integration hooks for pipeline services
        self.integration_hooks: Dict[str, Any] = {}
        
        # Pipeline monitoring data
        self.pipeline_monitoring: Dict[str, Dict[str, Any]] = {}
        
        # Consolidated alerting
        self.consolidated_alerts: List[Dict[str, Any]] = []
        self.alert_consolidation_window = 300  # 5 minutes
        
        # Auto-start background tasks only if there's a running event loop
        if enable_auto_start:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._auto_start_background_tasks())
            except RuntimeError:
                # No event loop running, skip auto-start
                logger.info("No event loop running, skipping auto-start of background tasks")
        
        logger.info(f"MonitoringService initialized with storage path: {self.storage_path}")
    
    async def _auto_start_background_tasks(self):
        """Auto-start background monitoring tasks"""
        try:
            await self.metrics_collector.start_background_aggregation()
            await self.health_monitor.start_continuous_monitoring()
            logger.info("Started background monitoring tasks")
        except Exception as e:
            logger.error(f"Error starting background tasks: {str(e)}")
    
    def start_monitoring_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start comprehensive monitoring for an agent
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Monitoring start result
        """
        try:
            agent_id = agent_config['agent_id']
            
            # Register with health monitor
            health_result = self.health_monitor.register_agent(agent_config)
            
            # Set up metrics collection thresholds
            if 'performance_thresholds' in agent_config:
                thresholds = agent_config['performance_thresholds']
                metric_thresholds = {}
                
                for metric_name, threshold_config in thresholds.items():
                    try:
                        metric_type = MetricType(metric_name)
                        metric_thresholds[metric_type] = threshold_config
                    except ValueError:
                        logger.warning(f"Unknown metric type: {metric_name}")
                
                if metric_thresholds:
                    self.metrics_collector.set_alert_thresholds(agent_id, metric_thresholds)
            
            # Set up pipeline integration if configured
            if 'pipeline_id' in agent_config:
                self._setup_pipeline_integration(agent_config)
            
            logger.info(f"Started monitoring for agent {agent_id}")
            
            return {
                'status': 'monitoring_started',
                'agent_id': agent_id,
                'health_monitoring': health_result['status'] == 'registered',
                'metrics_collection': True,
                'call_logging': True
            }
            
        except Exception as e:
            logger.error(f"Error starting agent monitoring: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _setup_pipeline_integration(self, agent_config: Dict[str, Any]):
        """Set up integration with pipeline services"""
        agent_id = agent_config['agent_id']
        pipeline_id = agent_config['pipeline_id']
        
        # Store pipeline integration info
        self.integration_hooks[agent_id] = {
            'pipeline_id': pipeline_id,
            'tenant_id': agent_config.get('tenant_id'),
            'integration_type': 'pipeline_monitoring'
        }
        
        logger.debug(f"Set up pipeline integration for agent {agent_id} with pipeline {pipeline_id}")
    
    def start_call_monitoring(self,
                             call_id: str,
                             agent_id: str,
                             tenant_id: str,
                             caller_number: str,
                             enable_recording: bool = False,
                             enable_transcription: bool = False,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start monitoring a call with integrated logging and metrics"""
        try:
            # Start call logging
            call_result = self.call_logger.start_call(
                call_id=call_id,
                agent_id=agent_id,
                tenant_id=tenant_id,
                caller_number=caller_number,
                enable_recording=enable_recording,
                enable_transcription=enable_transcription,
                metadata=metadata
            )
            
            # Record call start metric
            self.metrics_collector.record_metric(PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                agent_id=agent_id,
                metric_type=MetricType.ACTIVE_CONNECTIONS,
                value=len(self.call_logger.active_calls),
                timestamp=datetime.now(),
                context={'call_id': call_id, 'event': 'call_started'}
            ))
            
            logger.info(f"Started call monitoring: {call_id} for agent {agent_id}")
            
            return call_result
            
        except Exception as e:
            logger.error(f"Error starting call monitoring: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def log_call_event(self, call_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Log call event with integrated metrics collection"""
        try:
            # Log the event
            log_result = self.call_logger.log_event(call_id, event)
            
            # Extract metrics from event if applicable
            if call_id in self.call_logger.active_calls:
                call_record = self.call_logger.active_calls[call_id]
                agent_id = call_record.agent_id
                
                # Record response time metrics for agent responses
                if event.get('type') == 'agent_response' and 'response_time' in event:
                    self.metrics_collector.record_response_time(
                        agent_id,
                        event['response_time'],
                        {'call_id': call_id, 'message_type': 'response'}
                    )
                
                # Record intent accuracy metrics
                if event.get('type') == 'intent_recognized' and 'confidence' in event:
                    self.metrics_collector.record_metric(PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        agent_id=agent_id,
                        metric_type=MetricType.INTENT_ACCURACY,
                        value=event['confidence'],
                        timestamp=datetime.now(),
                        context={'call_id': call_id, 'intent': event.get('intent')}
                    ))
            
            return log_result
            
        except Exception as e:
            logger.error(f"Error logging call event: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def record_interaction_metrics(self, call_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Record interaction-specific metrics during a call"""
        try:
            if call_id not in self.call_logger.active_calls:
                return {'status': 'error', 'error': 'Call not found'}
            
            call_record = self.call_logger.active_calls[call_id]
            agent_id = call_record.agent_id
            results = []
            
            # Record various interaction metrics
            for metric_name, value in metrics.items():
                if metric_name == 'response_time':
                    result = self.metrics_collector.record_response_time(
                        agent_id, value, {'call_id': call_id}
                    )
                    results.append(result)
                
                elif metric_name == 'user_satisfaction_prediction':
                    result = self.metrics_collector.record_metric(PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        agent_id=agent_id,
                        metric_type=MetricType.USER_SATISFACTION,
                        value=value,
                        timestamp=datetime.now(),
                        context={'call_id': call_id, 'prediction': True}
                    ))
                    results.append(result)
                
                elif metric_name == 'intent_confidence':
                    result = self.metrics_collector.record_metric(PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        agent_id=agent_id,
                        metric_type=MetricType.INTENT_ACCURACY,
                        value=value,
                        timestamp=datetime.now(),
                        context={'call_id': call_id}
                    ))
                    results.append(result)
            
            return {
                'status': 'recorded',
                'metrics_count': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error recording interaction metrics: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def end_call_monitoring(self,
                           call_id: str,
                           end_reason: str = 'completed',
                           customer_satisfaction: Optional[int] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """End call monitoring with integrated cleanup"""
        try:
            # End call logging
            call_result = self.call_logger.end_call(
                call_id=call_id,
                end_reason=end_reason,
                customer_satisfaction=customer_satisfaction,
                metadata=metadata
            )
            
            if call_result['status'] == 'completed':
                # Get completed call record
                if call_id in self.call_logger.call_records:
                    call_record = self.call_logger.call_records[call_id]
                    agent_id = call_record.agent_id
                    
                    # Record final metrics
                    self.metrics_collector.record_metric(PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        agent_id=agent_id,
                        metric_type=MetricType.ACTIVE_CONNECTIONS,
                        value=len(self.call_logger.active_calls),
                        timestamp=datetime.now(),
                        context={'call_id': call_id, 'event': 'call_ended'}
                    ))
                    
                    # Record customer satisfaction if provided
                    if customer_satisfaction is not None:
                        self.metrics_collector.record_metric(PerformanceMetric(
                            metric_id=str(uuid.uuid4()),
                            agent_id=agent_id,
                            metric_type=MetricType.USER_SATISFACTION,
                            value=customer_satisfaction,
                            timestamp=datetime.now(),
                            context={'call_id': call_id, 'final_rating': True}
                        ))
                    
                    # Calculate call throughput
                    current_throughput = self._calculate_agent_throughput(agent_id)
                    self.metrics_collector.record_throughput(agent_id, current_throughput)
            
            return call_result
            
        except Exception as e:
            logger.error(f"Error ending call monitoring: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_agent_throughput(self, agent_id: str) -> float:
        """Calculate current throughput for agent (calls per minute)"""
        try:
            # Count calls in the last hour for the agent
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_calls = self.call_logger.search_calls(
                agent_id=agent_id,
                start_date=one_hour_ago,
                limit=1000
            )
            
            if not recent_calls:
                return 0.0
            
            # Calculate calls per minute
            return len(recent_calls) / 60.0
            
        except Exception as e:
            logger.error(f"Error calculating throughput for {agent_id}: {str(e)}")
            return 0.0
    
    async def perform_health_check(self, agent_id: str) -> Dict[str, Any]:
        """Perform health check with integrated metrics recording"""
        try:
            # Perform health check
            health_result = await self.health_monitor.perform_health_check(agent_id)
            
            # Record health metrics
            if 'response_time' in health_result:
                self.metrics_collector.record_response_time(
                    agent_id,
                    health_result['response_time'],
                    {'check_type': 'health_check'}
                )
            
            # Record system metrics if available
            if 'system_metrics' in health_result:
                system_metrics = health_result['system_metrics']
                
                if 'cpu_usage' in system_metrics and 'memory_usage' in system_metrics:
                    self.metrics_collector.record_system_metrics(
                        agent_id,
                        system_metrics['cpu_usage'],
                        system_metrics['memory_usage'],
                        system_metrics.get('disk_usage')
                    )
            
            return health_result
            
        except Exception as e:
            logger.error(f"Error performing health check: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def start_pipeline_monitoring(self, pipeline_state) -> Dict[str, Any]:
        """Start monitoring for pipeline execution"""
        try:
            pipeline_id = pipeline_state.pipeline_id
            
            # Store pipeline monitoring info
            self.pipeline_monitoring[pipeline_id] = {
                'pipeline_id': pipeline_id,
                'tenant_id': pipeline_state.tenant_id,
                'start_time': pipeline_state.started_at,
                'status': pipeline_state.status,
                'stage_metrics': {},
                'performance_data': {}
            }
            
            logger.info(f"Started pipeline monitoring for {pipeline_id}")
            
            return {
                'status': 'monitoring_started',
                'pipeline_id': pipeline_id
            }
            
        except Exception as e:
            logger.error(f"Error starting pipeline monitoring: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def record_pipeline_stage_metrics(self, pipeline_id: str, stage_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Record metrics for pipeline stage execution"""
        try:
            if pipeline_id not in self.pipeline_monitoring:
                return {'status': 'error', 'error': 'Pipeline not monitored'}
            
            stage_name = stage_metrics['stage_name']
            
            # Store stage metrics
            self.pipeline_monitoring[pipeline_id]['stage_metrics'][stage_name] = {
                'execution_time': stage_metrics.get('execution_time', 0),
                'success': stage_metrics.get('success', False),
                'performance_score': stage_metrics.get('performance_score', 0),
                'resources_created': stage_metrics.get('resources_created', []),
                'timestamp': datetime.now()
            }
            
            # Record metrics for created agents in this stage
            if 'resources_created' in stage_metrics:
                for resource_id in stage_metrics['resources_created']:
                    if resource_id.startswith('agent-'):
                        # Record pipeline creation time as response time metric
                        self.metrics_collector.record_response_time(
                            resource_id,
                            stage_metrics.get('execution_time', 0),
                            {
                                'pipeline_id': pipeline_id,
                                'stage': stage_name,
                                'creation_event': True
                            }
                        )
            
            logger.debug(f"Recorded pipeline stage metrics for {pipeline_id}:{stage_name}")
            
            return {
                'status': 'recorded',
                'pipeline_id': pipeline_id,
                'stage_name': stage_name
            }
            
        except Exception as e:
            logger.error(f"Error recording pipeline stage metrics: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def get_pipeline_performance(self, pipeline_id: str) -> Dict[str, Any]:
        """Get performance summary for pipeline"""
        if pipeline_id not in self.pipeline_monitoring:
            return {'error': 'Pipeline not found'}
        
        pipeline_data = self.pipeline_monitoring[pipeline_id]
        
        # Calculate overall performance
        total_time = 0
        completed_stages = 0
        successful_stages = 0
        
        for stage_name, stage_data in pipeline_data['stage_metrics'].items():
            total_time += stage_data['execution_time']
            completed_stages += 1
            if stage_data['success']:
                successful_stages += 1
        
        return {
            'pipeline_id': pipeline_id,
            'tenant_id': pipeline_data['tenant_id'],
            'total_execution_time': total_time,
            'completed_stages': completed_stages,
            'successful_stages': successful_stages,
            'success_rate': successful_stages / completed_stages if completed_stages > 0 else 0,
            'stage_metrics': pipeline_data['stage_metrics']
        }
    
    def configure_alerts(self, agent_id: str, alert_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure integrated alerts for agent"""
        try:
            # Configure metrics alerts
            metrics_thresholds = {}
            
            if 'response_time_threshold' in alert_config:
                metrics_thresholds[MetricType.RESPONSE_TIME] = {
                    'warning': alert_config['response_time_threshold'] * 0.8,
                    'critical': alert_config['response_time_threshold']
                }
            
            if 'error_rate_threshold' in alert_config:
                metrics_thresholds[MetricType.ERROR_RATE] = {
                    'warning': alert_config['error_rate_threshold'] * 0.8,
                    'critical': alert_config['error_rate_threshold']
                }
            
            if metrics_thresholds:
                self.metrics_collector.set_alert_thresholds(agent_id, metrics_thresholds)
            
            # Configure health alerts
            health_thresholds = {}
            
            if 'consecutive_health_failures' in alert_config:
                health_thresholds['consecutive_failures'] = alert_config['consecutive_health_failures']
            
            if 'customer_satisfaction_threshold' in alert_config:
                # This would be handled by custom logic
                pass
            
            if health_thresholds:
                self.health_monitor.set_alert_thresholds(health_thresholds)
            
            logger.info(f"Configured alerts for agent {agent_id}")
            
            return {
                'status': 'configured',
                'agent_id': agent_id,
                'metrics_alerts': len(metrics_thresholds),
                'health_alerts': len(health_thresholds)
            }
            
        except Exception as e:
            logger.error(f"Error configuring alerts: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def process_pending_alerts(self):
        """Process and consolidate pending alerts"""
        try:
            # Get active alerts from metrics collector and health monitor
            active_alerts = []
            
            # Collect alerts from metrics collector for all agents
            for agent_id in self.metrics_collector.aggregated_metrics.keys():
                agent_alerts = self.metrics_collector._get_active_alerts(agent_id)
                active_alerts.extend(agent_alerts)
            
            # Collect alerts from health monitor for all monitored agents
            for agent_id in self.health_monitor.monitored_agents.keys():
                agent_info = self.health_monitor.monitored_agents[agent_id]
                
                # Create health alerts for unhealthy agents
                if agent_info['status'] == HealthStatus.UNHEALTHY:
                    health_alert = {
                        'type': 'health_status',
                        'level': 'critical',
                        'agent_id': agent_id,
                        'message': f"Agent {agent_id} is unhealthy",
                        'timestamp': datetime.now(),
                        'context': {
                            'status': agent_info['status'].value,
                            'consecutive_failures': agent_info.get('consecutive_failures', 0)
                        }
                    }
                    active_alerts.append(health_alert)
                elif agent_info['status'] == HealthStatus.DEGRADED:
                    health_alert = {
                        'type': 'health_status',
                        'level': 'warning',
                        'agent_id': agent_id,
                        'message': f"Agent {agent_id} is degraded",
                        'timestamp': datetime.now(),
                        'context': {
                            'status': agent_info['status'].value,
                            'consecutive_failures': agent_info.get('consecutive_failures', 0)
                        }
                    }
                    active_alerts.append(health_alert)
            
            # Consolidate similar alerts within the consolidation window
            if active_alerts:
                consolidated_alerts = self._consolidate_alerts(active_alerts)
                
                # Send consolidated alerts
                for alert in consolidated_alerts:
                    self.send_consolidated_alert(alert)
                    
                logger.info(f"Processed {len(active_alerts)} alerts, sent {len(consolidated_alerts)} consolidated alerts")
            else:
                logger.debug("No active alerts to process")
                
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
    
    def _consolidate_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate similar alerts within the consolidation window"""
        if not alerts:
            return []
        
        # Group alerts by agent_id and alert type
        alert_groups = {}
        
        for alert in alerts:
            key = (alert.get('agent_id'), alert.get('type'), alert.get('level'))
            if key not in alert_groups:
                alert_groups[key] = []
            alert_groups[key].append(alert)
        
        consolidated = []
        
        # Consolidate each group
        for (agent_id, alert_type, level), group_alerts in alert_groups.items():
            if len(group_alerts) == 1:
                # Single alert, no consolidation needed
                consolidated.append(group_alerts[0])
            else:
                # Multiple alerts of same type, consolidate them
                first_alert = group_alerts[0]
                consolidated_alert = {
                    'type': alert_type,
                    'level': level,
                    'agent_id': agent_id,
                    'message': f"Multiple {alert_type} alerts for agent {agent_id}",
                    'timestamp': datetime.now(),
                    'context': {
                        'alert_count': len(group_alerts),
                        'first_alert_time': first_alert['timestamp'],
                        'details': [alert.get('message', '') for alert in group_alerts]
                    }
                }
                consolidated.append(consolidated_alert)
        
        return consolidated
    
    def send_consolidated_alert(self, alert: Dict[str, Any]):
        """Send consolidated alert to configured alert channels"""
        try:
            # Store for testing/local access
            self.consolidated_alerts.append(alert)
            
            # In a real implementation, this would send to various channels:
            # - Email notifications
            # - Slack/Teams webhooks
            # - SMS alerts
            # - Push notifications
            # - Logging systems
            
            # For now, log the alert at appropriate level based on severity
            if alert.get('level') == 'critical':
                logger.critical(f"CRITICAL ALERT: {alert.get('message', 'Unknown alert')} - Agent: {alert.get('agent_id', 'Unknown')}")
            elif alert.get('level') == 'warning':
                logger.warning(f"WARNING ALERT: {alert.get('message', 'Unknown alert')} - Agent: {alert.get('agent_id', 'Unknown')}")
            else:
                logger.info(f"INFO ALERT: {alert.get('message', 'Unknown alert')} - Agent: {alert.get('agent_id', 'Unknown')}")
            
            # Simulate sending to external channels (would be real HTTP requests, etc.)
            alert_payload = {
                'timestamp': alert['timestamp'].isoformat() if isinstance(alert.get('timestamp'), datetime) else str(alert.get('timestamp')),
                'severity': alert.get('level', 'info'),
                'agent_id': alert.get('agent_id', 'unknown'),
                'message': alert.get('message', 'No message'),
                'context': alert.get('context', {})
            }
            
            # In real implementation, would make HTTP requests to alert channels
            logger.debug(f"Alert sent to monitoring channels: {json.dumps(alert_payload, indent=2)}")
            
            return {
                'status': 'sent',
                'alert_id': alert.get('agent_id', '') + '_' + str(alert.get('timestamp', datetime.now()).timestamp()),
                'channels': ['logging', 'storage']  # In real implementation: ['email', 'slack', 'sms']
            }
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def record_response_time(self, agent_id: str, response_time: float):
        """Record response time metric"""
        return self.metrics_collector.record_response_time(agent_id, response_time)
    
    def record_error_rate(self, agent_id: str, error_rate: float):
        """Record error rate metric"""
        return self.metrics_collector.record_error_rate(agent_id, error_rate)
    
    def get_call_summary(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive call summary"""
        return self.call_logger.get_call_summary(call_id)
    
    def get_agent_metrics(self, agent_id: str) -> AgentMetrics:
        """Get comprehensive agent metrics"""
        agent_metrics = self.metrics_collector.aggregate_metrics_by_agent(agent_id)
        
        # Add call statistics
        call_analytics = self.call_logger.generate_analytics(agent_id=agent_id)
        agent_metrics.total_calls = call_analytics.get('total_calls', 0)
        agent_metrics.average_satisfaction = call_analytics.get('average_satisfaction', 0.0)
        
        return agent_metrics
    
    def export_dashboard_data(self,
                             agent_id: str,
                             time_range: timedelta,
                             format: str = 'json') -> str:
        """Export comprehensive dashboard data for agent"""
        try:
            # Get agent info
            agent_health = self.health_monitor.get_agent_health_status(agent_id)
            agent_metrics = self.get_agent_metrics(agent_id)
            
            # Get call summary
            end_date = datetime.now()
            start_date = end_date - time_range
            
            recent_calls = self.call_logger.search_calls(
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date,
                limit=100
            )
            
            call_summary = {
                'total_calls': len(recent_calls),
                'completed_calls': len([c for c in recent_calls if c.status == CallStatus.COMPLETED]),
                'average_duration': sum(c.duration for c in recent_calls) / len(recent_calls) if recent_calls else 0
            }
            
            # Get performance metrics time series
            response_times = self.metrics_collector.get_time_series(
                agent_id,
                MetricType.RESPONSE_TIME,
                start_date,
                end_date
            )
            
            dashboard_data = {
                'agent_info': {
                    'agent_id': agent_id,
                    'export_timestamp': datetime.now().isoformat(),
                    'time_range_hours': time_range.total_seconds() / 3600
                },
                'health_status': agent_health,
                'call_summary': call_summary,
                'performance_metrics': {
                    'response_times': [point['value'] for point in response_times],
                    'average_response_time': agent_metrics.average_response_time,
                    'current_throughput': agent_metrics.current_throughput,
                    'error_rate': agent_metrics.error_rate
                }
            }
            
            if format == 'json':
                return json.dumps(dashboard_data, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting dashboard data: {str(e)}")
            return json.dumps({'error': str(e)})
    
    async def shutdown(self):
        """Shutdown monitoring service and cleanup resources"""
        try:
            # Stop background tasks
            self.metrics_collector.stop_background_aggregation()
            self.health_monitor.stop_continuous_monitoring()
            
            # Close health monitor session
            await self.health_monitor.close()
            
            logger.info("MonitoringService shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")