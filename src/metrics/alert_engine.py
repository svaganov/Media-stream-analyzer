"""Threshold-based alerting engine"""
from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    metric: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: float

class AlertEngine:
    """Monitors metrics and triggers alerts based on thresholds"""

    def __init__(self):
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.callbacks: List[Callable[[Alert], None]] = []
        self.active_alerts: Dict[str, Alert] = {}

    def set_threshold(self, metric: str, warning: float, critical: float):
        """Set thresholds for a metric"""
        self.thresholds[metric] = {
            "warning": warning,
            "critical": critical,
        }

    def add_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback"""
        self.callbacks.append(callback)

    def check(self, metric: str, value: float, timestamp: float) -> List[Alert]:
        """Check metric against thresholds"""
        if metric not in self.thresholds:
            return []

        thresholds = self.thresholds[metric]
        alerts = []

        if value >= thresholds["critical"]:
            alert = Alert(metric, AlertSeverity.CRITICAL, 
                         f"{metric} critical: {value}", value, thresholds["critical"], timestamp)
            alerts.append(alert)
            self.active_alerts[metric] = alert
        elif value >= thresholds["warning"]:
            alert = Alert(metric, AlertSeverity.WARNING,
                         f"{metric} warning: {value}", value, thresholds["warning"], timestamp)
            alerts.append(alert)
            self.active_alerts[metric] = alert
        elif metric in self.active_alerts:
            # Clear alert
            del self.active_alerts[metric]

        for alert in alerts:
            for cb in self.callbacks:
                cb(alert)

        return alerts

    def get_active_alerts(self) -> List[Alert]:
        return list(self.active_alerts.values())
