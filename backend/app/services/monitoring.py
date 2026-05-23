"""
Monitoring System with Prometheus Metrics
Provides metrics collection for payments, settlements, reconciliation, queues, and system health
"""

import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Metric record"""
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    help_text: Optional[str] = None
    
    def to_prometheus(self) -> str:
        """Convert to Prometheus format"""
        label_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"
        
        help_line = f"# HELP {self.name} {self.help_text}\n" if self.help_text else ""
        type_line = f"# TYPE {self.name} {self.metric_type.value}\n"
        metric_line = f"{self.name}{label_str} {self.value}\n"
        
        return help_line + type_line + metric_line


class MonitoringSystem:
    """
    Monitoring system with Prometheus metrics
    Provides metrics collection for payments, settlements, reconciliation, queues, and system health
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default metrics"""
        # Payment metrics
        self.register_counter("payments_total", "Total number of payments")
        self.register_counter("payments_success_total", "Total number of successful payments")
        self.register_counter("payments_failed_total", "Total number of failed payments")
        self.register_gauge("payments_pending", "Number of pending payments")
        self.register_histogram("payment_amount", "Payment amount distribution")
        
        # Settlement metrics
        self.register_counter("settlements_total", "Total number of settlements")
        self.register_counter("settlements_completed_total", "Total number of completed settlements")
        self.register_gauge("settlements_pending", "Number of pending settlements")
        self.register_gauge("platform_fees_total", "Total platform fees collected")
        
        # Escrow metrics
        self.register_gauge("escrow_held_total", "Total amount held in escrow")
        self.register_gauge("escrow_count", "Number of active escrows")
        self.register_counter("escrow_released_total", "Total number of escrow releases")
        self.register_counter("disputes_total", "Total number of disputes")
        
        # Reconciliation metrics
        self.register_counter("reconciliation_runs_total", "Total number of reconciliation runs")
        self.register_gauge("reconciliation_issues_total", "Total number of reconciliation issues")
        self.register_counter("reconciliation_issues_resolved_total", "Total number of resolved issues")
        
        # Queue metrics
        self.register_gauge("queue_payment_pending", "Payment queue pending jobs")
        self.register_gauge("queue_webhook_pending", "Webhook queue pending jobs")
        self.register_gauge("queue_settlement_pending", "Settlement queue pending jobs")
        self.register_gauge("queue_dead_letter", "Dead letter queue size")
        
        # Fraud metrics
        self.register_counter("fraud_alerts_total", "Total number of fraud alerts")
        self.register_gauge("fraud_alerts_unresolved", "Number of unresolved fraud alerts")
        self.register_gauge("blocked_entities", "Number of blocked entities")
        
        # Ledger metrics
        self.register_gauge("ledger_entries_total", "Total number of ledger entries")
        self.register_gauge("wallet_balance_total", "Total wallet balance")
        self.register_gauge("wallet_count", "Number of wallets")
        
        # System metrics
        self.register_gauge("system_uptime", "System uptime in seconds")
        self.register_counter("api_requests_total", "Total API requests")
        self.register_gauge("api_request_duration", "API request duration")
    
    def register_counter(self, name: str, help_text: str = None) -> None:
        """Register a counter metric"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0.0
                self._metrics[name] = []
    
    def register_gauge(self, name: str, help_text: str = None) -> None:
        """Register a gauge metric"""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = 0.0
                self._metrics[name] = []
    
    def register_histogram(self, name: str, help_text: str = None, buckets: List[float] = None) -> None:
        """Register a histogram metric"""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = []
                self._metrics[name] = []
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        with self._lock:
            if name in self._counters:
                self._counters[name] += value
                metric = Metric(
                    name=name,
                    metric_type=MetricType.COUNTER,
                    value=self._counters[name],
                    labels=labels or {},
                    timestamp=datetime.utcnow()
                )
                self._metrics[name].append(metric)
                self._metric_history[name].append(metric)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric"""
        with self._lock:
            if name in self._gauges:
                self._gauges[name] = value
                metric = Metric(
                    name=name,
                    metric_type=MetricType.GAUGE,
                    value=value,
                    labels=labels or {},
                    timestamp=datetime.utcnow()
                )
                self._metrics[name].append(metric)
                self._metric_history[name].append(metric)
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value for a histogram metric"""
        with self._lock:
            if name in self._histograms:
                self._histograms[name].append(value)
                metric = Metric(
                    name=name,
                    metric_type=MetricType.HISTOGRAM,
                    value=value,
                    labels=labels or {},
                    timestamp=datetime.utcnow()
                )
                self._metrics[name].append(metric)
                self._metric_history[name].append(metric)
    
    def get_metric(self, name: str) -> Optional[float]:
        """Get current value of a metric"""
        with self._lock:
            if name in self._counters:
                return self._counters[name]
            elif name in self._gauges:
                return self._gauges[name]
            elif name in self._histograms:
                values = self._histograms[name]
                return sum(values) / len(values) if values else 0
        return None
    
    def get_metric_history(self, name: str, limit: int = 100) -> List[Metric]:
        """Get history of a metric"""
        with self._lock:
            history = list(self._metric_history[name])
            return history[-limit:]
    
    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus format"""
        with self._lock:
            output = []
            
            # Export counters
            for name, value in self._counters.items():
                if self._metrics[name]:
                    latest = self._metrics[name][-1]
                    output.append(latest.to_prometheus())
            
            # Export gauges
            for name, value in self._gauges.items():
                if self._metrics[name]:
                    latest = self._metrics[name][-1]
                    output.append(latest.to_prometheus())
            
            # Export histograms (simplified)
            for name, values in self._histograms.items():
                if values:
                    avg = sum(values) / len(values)
                    metric = Metric(
                        name=f"{name}_avg",
                        metric_type=MetricType.GAUGE,
                        value=avg,
                        labels={},
                        timestamp=datetime.utcnow(),
                        help_text=f"Average of {name}"
                    )
                    output.append(metric.to_prometheus())
            
            return "\n".join(output)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self._lock:
            summary = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values) if values else 0
                    }
                    for name, values in self._histograms.items()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            return summary
    
    def reset_metric(self, name: str) -> None:
        """Reset a metric to zero"""
        with self._lock:
            if name in self._counters:
                self._counters[name] = 0.0
            elif name in self._gauges:
                self._gauges[name] = 0.0
            elif name in self._histograms:
                self._histograms[name] = []
    
    def reset_all(self) -> None:
        """Reset all metrics"""
        with self._lock:
            for name in self._counters:
                self._counters[name] = 0.0
            for name in self._gauges:
                self._gauges[name] = 0.0
            for name in self._histograms:
                self._histograms[name] = []
            self._metrics.clear()
            self._metric_history.clear()


# Global monitoring system instance
monitoring_system = MonitoringSystem()


# Context manager for timing operations
class Timer:
    """Timer for measuring operation duration"""
    
    def __init__(self, metric_name: str, labels: Dict[str, str] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        monitoring_system.observe_histogram(self.metric_name, duration, self.labels)
        monitoring_system.set_gauge(f"{self.metric_name}_current", duration, self.labels)
