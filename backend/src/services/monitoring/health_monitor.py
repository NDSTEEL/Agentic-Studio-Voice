"""
Health Monitor
Agent status monitoring and health checks system
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
import logging
from collections import deque, defaultdict
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


@dataclass
class HealthCheck:
    """Individual health check result"""
    agent_id: str
    timestamp: datetime
    status: HealthStatus
    response_time: float
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    check_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        return data


@dataclass
class SystemHealth:
    """System-wide health summary"""
    total_agents: int = 0
    healthy_agents: int = 0
    degraded_agents: int = 0
    unhealthy_agents: int = 0
    unknown_agents: int = 0
    maintenance_agents: int = 0
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    last_updated: datetime = field(default_factory=datetime.now)
    
    def calculate_overall_status(self):
        """Calculate overall system status based on agent statuses"""
        if self.total_agents == 0:
            self.overall_status = HealthStatus.UNKNOWN
            return
        
        unhealthy_percentage = self.unhealthy_agents / self.total_agents
        degraded_percentage = self.degraded_agents / self.total_agents
        
        if unhealthy_percentage > 0.5:  # More than 50% unhealthy
            self.overall_status = HealthStatus.UNHEALTHY
        elif unhealthy_percentage > 0.2 or degraded_percentage > 0.3:  # Significant issues
            self.overall_status = HealthStatus.DEGRADED
        elif self.healthy_agents == self.total_agents:  # All healthy
            self.overall_status = HealthStatus.HEALTHY
        else:
            self.overall_status = HealthStatus.DEGRADED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['overall_status'] = self.overall_status.value
        data['last_updated'] = self.last_updated.isoformat()
        return data


class HealthMonitor:
    """
    Agent health monitoring system
    Performs health checks, tracks agent status, and manages health alerts
    """
    
    def __init__(self, 
                 check_interval: int = 30,
                 timeout: int = 10,
                 history_size: int = 1000):
        self.check_interval = check_interval
        self.timeout = timeout
        self.history_size = history_size
        
        # Monitored agents registry
        self.monitored_agents: Dict[str, Dict[str, Any]] = {}
        
        # Health check results
        self.health_checks: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        
        # Alert thresholds and callbacks
        self.alert_thresholds: Dict[str, float] = {
            'consecutive_failures': 3,
            'response_time_threshold': 2.0,
            'memory_usage_threshold': 90.0,
            'cpu_usage_threshold': 85.0
        }
        self.alert_callbacks: List[Callable] = []
        
        # Background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info("HealthMonitor initialized")
    
    def register_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register agent for health monitoring
        
        Args:
            agent_config: Agent configuration including health check endpoints
            
        Returns:
            Registration result
        """
        try:
            agent_id = agent_config['agent_id']
            
            agent_info = {
                'agent_id': agent_id,
                'tenant_id': agent_config.get('tenant_id'),
                'name': agent_config.get('name', agent_id),
                'endpoints': agent_config.get('endpoints', {}),
                'health_check_url': agent_config.get('health_check_url', 
                                                   f'/api/agents/{agent_id}/health'),
                'check_interval': agent_config.get('health_check_interval', self.check_interval),
                'status': HealthStatus.UNKNOWN,
                'last_check': None,
                'consecutive_failures': 0,
                'total_checks': 0,
                'uptime_start': datetime.now(),
                'metadata': agent_config.get('metadata', {})
            }
            
            self.monitored_agents[agent_id] = agent_info
            
            logger.info(f"Registered agent {agent_id} for health monitoring")
            
            return {
                'status': 'registered',
                'agent_id': agent_id,
                'health_check_url': agent_info['health_check_url']
            }
            
        except Exception as e:
            logger.error(f"Error registering agent: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def unregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """Unregister agent from monitoring"""
        if agent_id in self.monitored_agents:
            del self.monitored_agents[agent_id]
            if agent_id in self.health_checks:
                del self.health_checks[agent_id]
            logger.info(f"Unregistered agent {agent_id}")
            return {'status': 'unregistered', 'agent_id': agent_id}
        else:
            return {'status': 'not_found', 'agent_id': agent_id}
    
    async def perform_health_check(self, agent_id: str) -> Dict[str, Any]:
        """
        Perform health check on specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Health check result
        """
        if agent_id not in self.monitored_agents:
            return {'status': 'error', 'error': 'Agent not registered'}
        
        agent_info = self.monitored_agents[agent_id]
        start_time = datetime.now()
        
        try:
            # Prepare health check URL
            base_url = agent_info.get('base_url', 'http://localhost:8000')
            health_url = base_url + agent_info['health_check_url']
            
            # Initialize session if needed
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            # Perform health check request
            async with self._session.get(health_url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status == 200:
                    health_data = await response.json()
                    
                    # Create health check result
                    health_check = HealthCheck(
                        agent_id=agent_id,
                        timestamp=start_time,
                        status=HealthStatus(health_data.get('status', 'healthy')),
                        response_time=response_time,
                        system_metrics={
                            'memory_usage': health_data.get('memory_usage', 0.0),
                            'cpu_usage': health_data.get('cpu_usage', 0.0),
                            'disk_usage': health_data.get('disk_usage', 0.0),
                            'active_conversations': health_data.get('active_conversations', 0)
                        },
                        check_details=health_data
                    )
                    
                    # Update agent status
                    self._update_agent_status(agent_id, health_check)
                    
                    # Store health check result
                    self.health_checks[agent_id].append(health_check)
                    
                    logger.debug(f"Health check passed for agent {agent_id}: {response_time:.3f}s")
                    
                    result = health_check.to_dict()
                    result['status'] = health_check.status
                    return result
                
                else:
                    # HTTP error status
                    error_msg = f"HTTP {response.status}"
                    health_check = HealthCheck(
                        agent_id=agent_id,
                        timestamp=start_time,
                        status=HealthStatus.UNHEALTHY,
                        response_time=response_time,
                        error_message=error_msg
                    )
                    
                    self._update_agent_status(agent_id, health_check)
                    self.health_checks[agent_id].append(health_check)
                    
                    return {
                        'status': HealthStatus.UNHEALTHY,
                        'error': error_msg,
                        'response_time': response_time
                    }
        
        except asyncio.TimeoutError:
            error_msg = f"Health check timeout after {self.timeout}s"
            health_check = HealthCheck(
                agent_id=agent_id,
                timestamp=start_time,
                status=HealthStatus.UNHEALTHY,
                response_time=self.timeout,
                error_message=error_msg
            )
            
            self._update_agent_status(agent_id, health_check)
            self.health_checks[agent_id].append(health_check)
            
            logger.warning(f"Health check timeout for agent {agent_id}")
            
            return {
                'status': HealthStatus.UNHEALTHY,
                'error': error_msg,
                'response_time': self.timeout
            }
        
        except Exception as e:
            error_msg = f"Health check error: {str(e)}"
            health_check = HealthCheck(
                agent_id=agent_id,
                timestamp=start_time,
                status=HealthStatus.UNHEALTHY,
                response_time=(datetime.now() - start_time).total_seconds(),
                error_message=error_msg
            )
            
            self._update_agent_status(agent_id, health_check)
            self.health_checks[agent_id].append(health_check)
            
            logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
            
            return {
                'status': HealthStatus.UNHEALTHY,
                'error': error_msg
            }
    
    def _update_agent_status(self, agent_id: str, health_check: HealthCheck):
        """Update agent status based on health check result"""
        agent_info = self.monitored_agents[agent_id]
        agent_info['last_check'] = health_check.timestamp
        agent_info['total_checks'] += 1
        
        previous_status = agent_info['status']
        agent_info['status'] = health_check.status
        
        if health_check.status == HealthStatus.HEALTHY:
            agent_info['consecutive_failures'] = 0
        else:
            agent_info['consecutive_failures'] += 1
        
        # Check for status change
        if previous_status != health_check.status:
            logger.info(f"Agent {agent_id} status changed: {previous_status.value} -> {health_check.status.value}")
        
        # Check alert conditions
        self._check_alert_conditions(agent_id)
    
    def _check_alert_conditions(self, agent_id: str):
        """Check if agent violates alert thresholds"""
        agent_info = self.monitored_agents[agent_id]
        alerts = []
        
        # Check consecutive failures
        if agent_info['consecutive_failures'] >= self.alert_thresholds['consecutive_failures']:
            alerts.append({
                'type': 'consecutive_failures',
                'agent_id': agent_id,
                'value': agent_info['consecutive_failures'],
                'threshold': self.alert_thresholds['consecutive_failures'],
                'level': 'critical'
            })
        
        # Check response time (from latest health check)
        if agent_id in self.health_checks and self.health_checks[agent_id]:
            latest_check = self.health_checks[agent_id][-1]
            
            if latest_check.response_time >= self.alert_thresholds['response_time_threshold']:
                alerts.append({
                    'type': 'high_response_time',
                    'agent_id': agent_id,
                    'value': latest_check.response_time,
                    'threshold': self.alert_thresholds['response_time_threshold'],
                    'level': 'warning'
                })
            
            # Check system metrics
            if latest_check.system_metrics:
                memory_usage = latest_check.system_metrics.get('memory_usage', 0)
                if memory_usage >= self.alert_thresholds['memory_usage_threshold']:
                    alerts.append({
                        'type': 'high_memory_usage',
                        'agent_id': agent_id,
                        'value': memory_usage,
                        'threshold': self.alert_thresholds['memory_usage_threshold'],
                        'level': 'warning'
                    })
                
                cpu_usage = latest_check.system_metrics.get('cpu_usage', 0)
                if cpu_usage >= self.alert_thresholds['cpu_usage_threshold']:
                    alerts.append({
                        'type': 'high_cpu_usage',
                        'agent_id': agent_id,
                        'value': cpu_usage,
                        'threshold': self.alert_thresholds['cpu_usage_threshold'],
                        'level': 'warning'
                    })
        
        # Send alerts
        for alert in alerts:
            self._send_alert(alert)
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Send alert to registered callbacks"""
        try:
            for callback in self.alert_callbacks:
                callback(alert)
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
    
    def send_alert(self, alert: Dict[str, Any]):
        """Public method to send alerts (for testing)"""
        self._send_alert(alert)
    
    def set_alert_thresholds(self, thresholds: Dict[str, float]):
        """Set alert thresholds"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"Updated alert thresholds: {thresholds}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    async def start_continuous_monitoring(self, check_interval: Optional[int] = None):
        """Start continuous health monitoring for all registered agents"""
        interval = check_interval or self.check_interval
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        self._monitoring_task = asyncio.create_task(
            self._continuous_monitoring_loop(interval)
        )
        
        logger.info(f"Started continuous health monitoring with {interval}s interval")
    
    async def _continuous_monitoring_loop(self, interval: int):
        """Continuous monitoring loop"""
        while True:
            try:
                # Perform health checks for all registered agents
                check_tasks = []
                for agent_id in list(self.monitored_agents.keys()):
                    task = asyncio.create_task(
                        self.perform_health_check(agent_id)
                    )
                    check_tasks.append(task)
                
                # Wait for all checks to complete
                if check_tasks:
                    await asyncio.gather(*check_tasks, return_exceptions=True)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(interval)
    
    def stop_continuous_monitoring(self):
        """Stop continuous monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
            logger.info("Stopped continuous health monitoring")
    
    def get_system_health(self) -> SystemHealth:
        """Get system-wide health summary"""
        system_health = SystemHealth()
        system_health.total_agents = len(self.monitored_agents)
        
        # Count agents by status
        for agent_info in self.monitored_agents.values():
            status = agent_info['status']
            if status == HealthStatus.HEALTHY:
                system_health.healthy_agents += 1
            elif status == HealthStatus.DEGRADED:
                system_health.degraded_agents += 1
            elif status == HealthStatus.UNHEALTHY:
                system_health.unhealthy_agents += 1
            elif status == HealthStatus.MAINTENANCE:
                system_health.maintenance_agents += 1
            else:
                system_health.unknown_agents += 1
        
        system_health.calculate_overall_status()
        system_health.last_updated = datetime.now()
        
        return system_health
    
    def get_agent_health_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get health status for specific agent"""
        if agent_id not in self.monitored_agents:
            return None
        
        agent_info = self.monitored_agents[agent_id]
        
        # Get recent health checks
        recent_checks = []
        if agent_id in self.health_checks:
            recent_checks = list(self.health_checks[agent_id])[-10:]  # Last 10 checks
        
        return {
            'agent_id': agent_id,
            'current_status': agent_info['status'].value,
            'last_check': agent_info['last_check'].isoformat() if agent_info['last_check'] else None,
            'consecutive_failures': agent_info['consecutive_failures'],
            'total_checks': agent_info['total_checks'],
            'uptime_start': agent_info['uptime_start'].isoformat(),
            'recent_checks': [check.to_dict() for check in recent_checks]
        }
    
    def get_health_history(self, agent_id: str, duration: timedelta) -> List[Dict[str, Any]]:
        """Get health history for agent within specified duration"""
        if agent_id not in self.health_checks:
            return []
        
        cutoff_time = datetime.now() - duration
        history = []
        
        for check in self.health_checks[agent_id]:
            if check.timestamp >= cutoff_time:
                history.append(check.to_dict())
        
        return history
    
    def _record_health_status(self, agent_id: str, status: HealthStatus, timestamp: datetime):
        """Record health status change (for testing)"""
        if agent_id not in self.monitored_agents:
            return
        
        health_check = HealthCheck(
            agent_id=agent_id,
            timestamp=timestamp,
            status=status,
            response_time=0.0
        )
        
        self.health_checks[agent_id].append(health_check)
        self.monitored_agents[agent_id]['status'] = status
    
    def calculate_uptime(self, agent_id: str, duration: timedelta) -> Dict[str, Any]:
        """Calculate uptime statistics for agent"""
        if agent_id not in self.health_checks:
            return {'uptime_percentage': 0.0, 'total_checks': 0}
        
        cutoff_time = datetime.now() - duration
        relevant_checks = [
            check for check in self.health_checks[agent_id]
            if check.timestamp >= cutoff_time
        ]
        
        if not relevant_checks:
            return {'uptime_percentage': 0.0, 'total_checks': 0}
        
        healthy_checks = [
            check for check in relevant_checks
            if check.status == HealthStatus.HEALTHY
        ]
        
        uptime_percentage = (len(healthy_checks) / len(relevant_checks)) * 100
        
        return {
            'uptime_percentage': uptime_percentage,
            'total_checks': len(relevant_checks),
            'healthy_checks': len(healthy_checks),
            'unhealthy_checks': len(relevant_checks) - len(healthy_checks),
            'time_period_hours': duration.total_seconds() / 3600
        }
    
    def export_health_data(self, 
                          agent_ids: Optional[List[str]] = None,
                          time_range: Optional[timedelta] = None,
                          format: str = 'json') -> str:
        """Export health monitoring data"""
        target_agents = agent_ids or list(self.monitored_agents.keys())
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'system_health': self.get_system_health().to_dict(),
            'agents': {}
        }
        
        for agent_id in target_agents:
            if agent_id not in self.monitored_agents:
                continue
            
            agent_data = {
                'agent_info': self.monitored_agents[agent_id],
                'current_status': self.get_agent_health_status(agent_id)
            }
            
            # Add health history if time range specified
            if time_range:
                agent_data['health_history'] = self.get_health_history(agent_id, time_range)
                agent_data['uptime_stats'] = self.calculate_uptime(agent_id, time_range)
            
            export_data['agents'][agent_id] = agent_data
        
        if format == 'json':
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def close(self):
        """Clean up resources"""
        self.stop_continuous_monitoring()
        
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("HealthMonitor closed")