"""
Metrics Collector
Performance metrics collection system for agent monitoring and analytics
"""
import json
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import statistics
import logging
import uuid
from pathlib import Path
import csv
from io import StringIO

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_LATENCY = "network_latency"
    QUEUE_SIZE = "queue_size"
    ACTIVE_CONNECTIONS = "active_connections"
    CACHE_HIT_RATE = "cache_hit_rate"
    USER_SATISFACTION = "user_satisfaction"
    INTENT_ACCURACY = "intent_accuracy"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    metric_id: str
    agent_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['metric_type'] = self.metric_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['metric_type'] = MetricType(data['metric_type'])
        return cls(**data)


@dataclass
class AgentMetrics:
    """Aggregated metrics for a specific agent"""
    agent_id: str
    total_requests: int = 0
    average_response_time: float = 0.0
    current_throughput: float = 0.0
    error_rate: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    uptime_percentage: float = 0.0
    average_satisfaction: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


class MetricsCollector:
    """
    Performance metrics collection and aggregation system
    Handles real-time metric recording, aggregation, and alerting
    """
    
    def __init__(self, buffer_size: int = 10000, collection_interval: int = 60):
        self.buffer_size = buffer_size
        self.collection_interval = collection_interval
        
        # In-memory metrics buffer for fast access
        self.metrics_buffer: deque = deque(maxlen=buffer_size)
        
        # Aggregated metrics by agent
        self.aggregated_metrics: Dict[str, AgentMetrics] = {}
        
        # Time series data for each agent and metric type
        self.time_series: Dict[str, Dict[MetricType, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=1440))  # 24 hours at 1-minute intervals
        )
        
        # Alert thresholds and subscribers
        self.alert_thresholds: Dict[str, Dict[MetricType, Dict[str, float]]] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Streaming subscribers
        self.stream_subscribers: List[Any] = []
        
        # Background tasks
        self._aggregation_task: Optional[asyncio.Task] = None
        
        logger.info("MetricsCollector initialized")
    
    def record_metric(self, metric: PerformanceMetric) -> Dict[str, Any]:
        """
        Record a performance metric
        
        Args:
            metric: Performance metric to record
            
        Returns:
            Result dictionary with recording status
        """
        try:
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Add to time series
            self.time_series[metric.agent_id][metric.metric_type].append({
                'timestamp': metric.timestamp,
                'value': metric.value,
                'context': metric.context
            })
            
            # Update aggregated metrics
            self._update_aggregated_metrics(metric)
            
            # Check alert conditions
            self._check_alert_conditions(metric)
            
            # Stream to subscribers
            self._stream_metric(metric)
            
            logger.debug(f"Recorded metric: {metric.metric_type.value} = {metric.value} for {metric.agent_id}")
            
            return {
                'status': 'recorded',
                'metric_id': metric.metric_id,
                'buffer_size': len(self.metrics_buffer)
            }
            
        except Exception as e:
            logger.error(f"Error recording metric: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def record_response_time(self,
                           agent_id: str,
                           response_time: float,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Record response time metric"""
        metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            agent_id=agent_id,
            metric_type=MetricType.RESPONSE_TIME,
            value=response_time,
            timestamp=datetime.now(),
            context=context or {}
        )
        return self.record_metric(metric)
    
    def record_throughput(self,
                         agent_id: str,
                         requests_per_minute: float,
                         timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Record throughput metric"""
        metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            agent_id=agent_id,
            metric_type=MetricType.THROUGHPUT,
            value=requests_per_minute,
            timestamp=timestamp or datetime.now()
        )
        return self.record_metric(metric)
    
    def record_error_rate(self,
                         agent_id: str,
                         error_rate: float,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Record error rate metric"""
        metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            agent_id=agent_id,
            metric_type=MetricType.ERROR_RATE,
            value=error_rate,
            timestamp=datetime.now(),
            context=context or {}
        )
        return self.record_metric(metric)
    
    def record_system_metrics(self,
                             agent_id: str,
                             cpu_usage: float,
                             memory_usage: float,
                             disk_usage: Optional[float] = None) -> Dict[str, Any]:
        """Record system resource metrics"""
        results = []
        
        # Record CPU usage
        cpu_metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            agent_id=agent_id,
            metric_type=MetricType.CPU_USAGE,
            value=cpu_usage,
            timestamp=datetime.now()
        )
        results.append(self.record_metric(cpu_metric))
        
        # Record memory usage
        memory_metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            agent_id=agent_id,
            metric_type=MetricType.MEMORY_USAGE,
            value=memory_usage,
            timestamp=datetime.now()
        )
        results.append(self.record_metric(memory_metric))
        
        # Record disk usage if provided
        if disk_usage is not None:
            disk_metric = PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                agent_id=agent_id,
                metric_type=MetricType.DISK_USAGE,
                value=disk_usage,
                timestamp=datetime.now()
            )
            results.append(self.record_metric(disk_metric))
        
        return {
            'status': 'recorded',
            'metrics_recorded': len(results),
            'results': results
        }
    
    def _update_aggregated_metrics(self, metric: PerformanceMetric):
        """Update aggregated metrics for agent"""
        agent_id = metric.agent_id
        
        if agent_id not in self.aggregated_metrics:
            self.aggregated_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        
        agent_metrics = self.aggregated_metrics[agent_id]
        agent_metrics.last_updated = datetime.now()
        
        # Update based on metric type
        if metric.metric_type == MetricType.RESPONSE_TIME:
            # Calculate rolling average response time
            response_times = [
                point['value'] for point in 
                self.time_series[agent_id][MetricType.RESPONSE_TIME]
            ]
            agent_metrics.average_response_time = statistics.mean(response_times) if response_times else 0.0
        
        elif metric.metric_type == MetricType.THROUGHPUT:
            agent_metrics.current_throughput = metric.value
        
        elif metric.metric_type == MetricType.ERROR_RATE:
            agent_metrics.error_rate = metric.value
        
        elif metric.metric_type == MetricType.CPU_USAGE:
            agent_metrics.cpu_usage = metric.value
        
        elif metric.metric_type == MetricType.MEMORY_USAGE:
            agent_metrics.memory_usage = metric.value
        
        elif metric.metric_type == MetricType.USER_SATISFACTION:
            # Calculate rolling average satisfaction
            satisfaction_scores = [
                point['value'] for point in 
                self.time_series[agent_id][MetricType.USER_SATISFACTION]
            ]
            agent_metrics.average_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 0.0
        
        # Update total requests counter
        agent_metrics.total_requests += 1
    
    def aggregate_metrics_by_agent(self, agent_id: str) -> AgentMetrics:
        """Get aggregated metrics for specific agent"""
        if agent_id not in self.aggregated_metrics:
            return AgentMetrics(agent_id=agent_id)
        
        return self.aggregated_metrics[agent_id]
    
    def get_time_series(self,
                       agent_id: str,
                       metric_type: MetricType,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get time series data for specific agent and metric type
        
        Args:
            agent_id: Agent identifier
            metric_type: Type of metric
            start_time: Start time for filtering (optional)
            end_time: End time for filtering (optional)
            
        Returns:
            List of time series data points
        """
        if agent_id not in self.time_series or metric_type not in self.time_series[agent_id]:
            return []
        
        data_points = list(self.time_series[agent_id][metric_type])
        
        # Apply time filtering if specified
        if start_time or end_time:
            filtered_points = []
            for point in data_points:
                point_time = point['timestamp']
                
                if start_time and point_time < start_time:
                    continue
                
                if end_time and point_time > end_time:
                    continue
                
                filtered_points.append(point)
            
            data_points = filtered_points
        
        # Convert timestamps to ISO format for serialization
        for point in data_points:
            point['timestamp'] = point['timestamp'].isoformat()
        
        return data_points
    
    def set_alert_thresholds(self,
                            agent_id: str,
                            thresholds: Dict[MetricType, Dict[str, float]]):
        """
        Set alert thresholds for agent metrics
        
        Args:
            agent_id: Agent identifier
            thresholds: Dict of metric types to threshold levels
                       e.g., {MetricType.RESPONSE_TIME: {'warning': 2.0, 'critical': 5.0}}
        """
        self.alert_thresholds[agent_id] = thresholds
        logger.info(f"Set alert thresholds for agent {agent_id}: {len(thresholds)} metrics")
    
    def _check_alert_conditions(self, metric: PerformanceMetric):
        """Check if metric violates alert thresholds"""
        agent_id = metric.agent_id
        
        if agent_id not in self.alert_thresholds:
            return
        
        if metric.metric_type not in self.alert_thresholds[agent_id]:
            return
        
        thresholds = self.alert_thresholds[agent_id][metric.metric_type]
        
        # Check critical threshold first
        if 'critical' in thresholds and metric.value >= thresholds['critical']:
            self._trigger_alert({
                'level': 'critical',
                'agent_id': agent_id,
                'metric_type': metric.metric_type,
                'value': metric.value,
                'threshold': thresholds['critical'],
                'timestamp': metric.timestamp
            })
        
        # Check warning threshold
        elif 'warning' in thresholds and metric.value >= thresholds['warning']:
            self._trigger_alert({
                'level': 'warning',
                'agent_id': agent_id,
                'metric_type': metric.metric_type,
                'value': metric.value,
                'threshold': thresholds['warning'],
                'timestamp': metric.timestamp
            })
    
    def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger alert to registered callbacks"""
        try:
            for callback in self.alert_callbacks:
                callback(alert)
        except Exception as e:
            logger.error(f"Error triggering alert: {str(e)}")
    
    def trigger_alert(self, alert: Dict[str, Any]):
        """Public method to trigger alerts (for testing)"""
        self._trigger_alert(alert)
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def add_stream_subscriber(self, subscriber):
        """Add streaming subscriber for real-time metrics"""
        self.stream_subscribers.append(subscriber)
        logger.info(f"Added stream subscriber: {subscriber}")
    
    def _stream_metric(self, metric: PerformanceMetric):
        """Stream metric to all subscribers"""
        try:
            for subscriber in self.stream_subscribers:
                if hasattr(subscriber, 'send_metric'):
                    subscriber.send_metric(metric)
        except Exception as e:
            logger.error(f"Error streaming metric: {str(e)}")
    
    def export_metrics(self,
                      agent_id: str,
                      format: str = 'json',
                      time_range: Optional[timedelta] = None) -> str:
        """
        Export metrics for specific agent
        
        Args:
            agent_id: Agent identifier
            format: Export format ('json' or 'csv')
            time_range: Time range for export (optional)
            
        Returns:
            Exported metrics as string
        """
        # Get metrics for agent
        agent_metrics = []
        
        end_time = datetime.now()
        start_time = end_time - time_range if time_range else None
        
        for metric in self.metrics_buffer:
            if metric.agent_id != agent_id:
                continue
            
            if start_time and metric.timestamp < start_time:
                continue
            
            agent_metrics.append(metric)
        
        if format == 'json':
            return self._export_metrics_json(agent_id, agent_metrics)
        elif format == 'csv':
            return self._export_metrics_csv(agent_id, agent_metrics)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_metrics_json(self, agent_id: str, metrics: List[PerformanceMetric]) -> str:
        """Export metrics to JSON format"""
        export_data = {
            'agent_id': agent_id,
            'export_timestamp': datetime.now().isoformat(),
            'metrics_count': len(metrics),
            'metrics': [metric.to_dict() for metric in metrics]
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def _export_metrics_csv(self, agent_id: str, metrics: List[PerformanceMetric]) -> str:
        """Export metrics to CSV format"""
        output = StringIO()
        
        if not metrics:
            return ""
        
        # CSV headers
        headers = ['agent_id', 'metric_type', 'value', 'timestamp', 'context']
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Write metric data
        for metric in metrics:
            row = [
                metric.agent_id,
                metric.metric_type.value,
                metric.value,
                metric.timestamp.isoformat(),
                json.dumps(metric.context)
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def get_agent_performance_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive performance summary for agent"""
        if agent_id not in self.aggregated_metrics:
            return {'agent_id': agent_id, 'no_data': True}
        
        agent_metrics = self.aggregated_metrics[agent_id]
        
        # Calculate percentiles for response time
        response_times = [
            point['value'] for point in 
            self.time_series[agent_id].get(MetricType.RESPONSE_TIME, [])
        ]
        
        response_time_stats = {}
        if response_times:
            response_time_stats = {
                'min': min(response_times),
                'max': max(response_times),
                'median': statistics.median(response_times),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                'p99': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
            }
        
        return {
            'agent_id': agent_id,
            'summary': agent_metrics.to_dict(),
            'response_time_stats': response_time_stats,
            'metrics_collected': len([m for m in self.metrics_buffer if m.agent_id == agent_id]),
            'time_series_points': {
                metric_type.value: len(self.time_series[agent_id].get(metric_type, []))
                for metric_type in MetricType
                if metric_type in self.time_series[agent_id]
            }
        }
    
    def calculate_sla_compliance(self,
                                agent_id: str,
                                sla_targets: Dict[MetricType, float],
                                time_period: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """
        Calculate SLA compliance for agent metrics
        
        Args:
            agent_id: Agent identifier
            sla_targets: SLA targets for different metrics
            time_period: Time period for calculation
            
        Returns:
            SLA compliance report
        """
        end_time = datetime.now()
        start_time = end_time - time_period
        
        compliance_report = {
            'agent_id': agent_id,
            'time_period_hours': time_period.total_seconds() / 3600,
            'sla_compliance': {},
            'overall_compliance': 0.0
        }
        
        total_metrics = 0
        compliant_metrics = 0
        
        for metric_type, target_value in sla_targets.items():
            time_series_data = self.get_time_series(
                agent_id, metric_type, start_time, end_time
            )
            
            if not time_series_data:
                continue
            
            # Convert timestamps back to datetime for processing
            for point in time_series_data:
                point['timestamp'] = datetime.fromisoformat(point['timestamp'])
            
            # Calculate compliance based on metric type
            if metric_type in [MetricType.RESPONSE_TIME, MetricType.ERROR_RATE]:
                # For these metrics, lower is better
                compliant_points = [p for p in time_series_data if p['value'] <= target_value]
            else:
                # For throughput, higher is better
                compliant_points = [p for p in time_series_data if p['value'] >= target_value]
            
            compliance_rate = len(compliant_points) / len(time_series_data) if time_series_data else 0.0
            
            compliance_report['sla_compliance'][metric_type.value] = {
                'target_value': target_value,
                'compliance_rate': compliance_rate,
                'total_measurements': len(time_series_data),
                'compliant_measurements': len(compliant_points)
            }
            
            total_metrics += 1
            if compliance_rate >= 0.95:  # 95% compliance threshold
                compliant_metrics += 1
        
        compliance_report['overall_compliance'] = compliant_metrics / total_metrics if total_metrics > 0 else 0.0
        
        return compliance_report
    
    async def start_background_aggregation(self, interval: int = 60):
        """Start background task for periodic metric aggregation"""
        if self._aggregation_task:
            self._aggregation_task.cancel()
        
        self._aggregation_task = asyncio.create_task(
            self._background_aggregation_loop(interval)
        )
        logger.info(f"Started background aggregation with {interval}s interval")
    
    async def _background_aggregation_loop(self, interval: int):
        """Background loop for metric aggregation"""
        while True:
            try:
                await asyncio.sleep(interval)
                await self._perform_background_aggregation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background aggregation: {str(e)}")
    
    async def _perform_background_aggregation(self):
        """Perform background metric aggregation and cleanup"""
        logger.debug("Performing background metric aggregation")
        
        # Clean up old metrics from buffer
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Remove old metrics
        metrics_to_keep = []
        for metric in self.metrics_buffer:
            if metric.timestamp >= cutoff_time:
                metrics_to_keep.append(metric)
        
        # Update buffer
        self.metrics_buffer.clear()
        self.metrics_buffer.extend(metrics_to_keep)
        
        logger.debug(f"Cleaned up old metrics, kept {len(metrics_to_keep)} recent metrics")
    
    def stop_background_aggregation(self):
        """Stop background aggregation task"""
        if self._aggregation_task:
            self._aggregation_task.cancel()
            self._aggregation_task = None
            logger.info("Stopped background aggregation")
    
    def get_real_time_dashboard_data(self, agent_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get real-time data for monitoring dashboard"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'agents': {}
        }
        
        target_agents = agent_ids or list(self.aggregated_metrics.keys())
        
        for agent_id in target_agents:
            if agent_id not in self.aggregated_metrics:
                continue
            
            agent_metrics = self.aggregated_metrics[agent_id]
            
            # Get recent metrics (last 5 minutes)
            recent_cutoff = datetime.now() - timedelta(minutes=5)
            recent_response_times = [
                point['value'] for point in 
                self.time_series[agent_id].get(MetricType.RESPONSE_TIME, [])
                if point['timestamp'] >= recent_cutoff
            ]
            
            dashboard_data['agents'][agent_id] = {
                'status': 'active' if recent_response_times else 'inactive',
                'current_metrics': agent_metrics.to_dict(),
                'recent_activity': {
                    'response_times': recent_response_times[-10:],  # Last 10 measurements
                    'current_throughput': agent_metrics.current_throughput,
                    'error_rate': agent_metrics.error_rate
                },
                'alerts': self._get_active_alerts(agent_id)
            }
        
        return dashboard_data
    
    def _get_active_alerts(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get active alerts for agent based on current metrics and thresholds"""
        active_alerts = []
        
        try:
            # Check if agent has configured thresholds
            if agent_id not in self.alert_thresholds:
                return active_alerts
            
            # Check if we have aggregated metrics for this agent
            if agent_id not in self.aggregated_metrics:
                return active_alerts
            
            agent_metrics = self.aggregated_metrics[agent_id]
            thresholds = self.alert_thresholds[agent_id]
            
            # Check response time alerts
            if (MetricType.RESPONSE_TIME in thresholds and 
                agent_metrics.average_response_time > 0):
                
                rt_thresholds = thresholds[MetricType.RESPONSE_TIME]
                
                if ('critical' in rt_thresholds and 
                    agent_metrics.average_response_time >= rt_thresholds['critical']):
                    active_alerts.append({
                        'type': 'performance_alert',
                        'level': 'critical',
                        'agent_id': agent_id,
                        'metric_type': MetricType.RESPONSE_TIME,
                        'message': f"Response time critically high: {agent_metrics.average_response_time:.2f}s",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.average_response_time,
                            'threshold': rt_thresholds['critical'],
                            'metric': 'average_response_time'
                        }
                    })
                elif ('warning' in rt_thresholds and 
                      agent_metrics.average_response_time >= rt_thresholds['warning']):
                    active_alerts.append({
                        'type': 'performance_alert',
                        'level': 'warning',
                        'agent_id': agent_id,
                        'metric_type': MetricType.RESPONSE_TIME,
                        'message': f"Response time elevated: {agent_metrics.average_response_time:.2f}s",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.average_response_time,
                            'threshold': rt_thresholds['warning'],
                            'metric': 'average_response_time'
                        }
                    })
            
            # Check error rate alerts
            if (MetricType.ERROR_RATE in thresholds and 
                agent_metrics.error_rate > 0):
                
                er_thresholds = thresholds[MetricType.ERROR_RATE]
                
                if ('critical' in er_thresholds and 
                    agent_metrics.error_rate >= er_thresholds['critical']):
                    active_alerts.append({
                        'type': 'performance_alert',
                        'level': 'critical',
                        'agent_id': agent_id,
                        'metric_type': MetricType.ERROR_RATE,
                        'message': f"Error rate critically high: {agent_metrics.error_rate:.2%}",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.error_rate,
                            'threshold': er_thresholds['critical'],
                            'metric': 'error_rate'
                        }
                    })
                elif ('warning' in er_thresholds and 
                      agent_metrics.error_rate >= er_thresholds['warning']):
                    active_alerts.append({
                        'type': 'performance_alert',
                        'level': 'warning',
                        'agent_id': agent_id,
                        'metric_type': MetricType.ERROR_RATE,
                        'message': f"Error rate elevated: {agent_metrics.error_rate:.2%}",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.error_rate,
                            'threshold': er_thresholds['warning'],
                            'metric': 'error_rate'
                        }
                    })
            
            # Check throughput alerts (low throughput is concerning)
            if (MetricType.THROUGHPUT in thresholds and 
                agent_metrics.current_throughput >= 0):
                
                tp_thresholds = thresholds[MetricType.THROUGHPUT]
                
                if ('critical' in tp_thresholds and 
                    agent_metrics.current_throughput <= tp_thresholds['critical']):
                    active_alerts.append({
                        'type': 'performance_alert',
                        'level': 'critical',
                        'agent_id': agent_id,
                        'metric_type': MetricType.THROUGHPUT,
                        'message': f"Throughput critically low: {agent_metrics.current_throughput:.2f} req/min",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.current_throughput,
                            'threshold': tp_thresholds['critical'],
                            'metric': 'current_throughput'
                        }
                    })
                elif ('warning' in tp_thresholds and 
                      agent_metrics.current_throughput <= tp_thresholds['warning']):
                    active_alerts.append({
                        'type': 'performance_alert',
                        'level': 'warning',
                        'agent_id': agent_id,
                        'metric_type': MetricType.THROUGHPUT,
                        'message': f"Throughput low: {agent_metrics.current_throughput:.2f} req/min",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.current_throughput,
                            'threshold': tp_thresholds['warning'],
                            'metric': 'current_throughput'
                        }
                    })
            
            # Check CPU usage alerts  
            if (MetricType.CPU_USAGE in thresholds and 
                agent_metrics.cpu_usage > 0):
                
                cpu_thresholds = thresholds[MetricType.CPU_USAGE]
                
                if ('critical' in cpu_thresholds and 
                    agent_metrics.cpu_usage >= cpu_thresholds['critical']):
                    active_alerts.append({
                        'type': 'resource_alert',
                        'level': 'critical',
                        'agent_id': agent_id,
                        'metric_type': MetricType.CPU_USAGE,
                        'message': f"CPU usage critically high: {agent_metrics.cpu_usage:.1f}%",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.cpu_usage,
                            'threshold': cpu_thresholds['critical'],
                            'metric': 'cpu_usage'
                        }
                    })
                elif ('warning' in cpu_thresholds and 
                      agent_metrics.cpu_usage >= cpu_thresholds['warning']):
                    active_alerts.append({
                        'type': 'resource_alert',
                        'level': 'warning',
                        'agent_id': agent_id,
                        'metric_type': MetricType.CPU_USAGE,
                        'message': f"CPU usage high: {agent_metrics.cpu_usage:.1f}%",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.cpu_usage,
                            'threshold': cpu_thresholds['warning'],
                            'metric': 'cpu_usage'
                        }
                    })
            
            # Check memory usage alerts
            if (MetricType.MEMORY_USAGE in thresholds and 
                agent_metrics.memory_usage > 0):
                
                mem_thresholds = thresholds[MetricType.MEMORY_USAGE]
                
                if ('critical' in mem_thresholds and 
                    agent_metrics.memory_usage >= mem_thresholds['critical']):
                    active_alerts.append({
                        'type': 'resource_alert',
                        'level': 'critical',
                        'agent_id': agent_id,
                        'metric_type': MetricType.MEMORY_USAGE,
                        'message': f"Memory usage critically high: {agent_metrics.memory_usage:.1f}%",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.memory_usage,
                            'threshold': mem_thresholds['critical'],
                            'metric': 'memory_usage'
                        }
                    })
                elif ('warning' in mem_thresholds and 
                      agent_metrics.memory_usage >= mem_thresholds['warning']):
                    active_alerts.append({
                        'type': 'resource_alert',
                        'level': 'warning',
                        'agent_id': agent_id,
                        'metric_type': MetricType.MEMORY_USAGE,
                        'message': f"Memory usage high: {agent_metrics.memory_usage:.1f}%",
                        'timestamp': datetime.now(),
                        'context': {
                            'current_value': agent_metrics.memory_usage,
                            'threshold': mem_thresholds['warning'],
                            'metric': 'memory_usage'
                        }
                    })
            
            if active_alerts:
                logger.debug(f"Found {len(active_alerts)} active alerts for agent {agent_id}")
            
            return active_alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts for {agent_id}: {str(e)}")
            return []