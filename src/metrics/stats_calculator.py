"""Statistics calculator for metrics"""
from typing import List, Dict, Any
import statistics

def calculate_stats(values: List[float]) -> Dict[str, float]:
    """Calculate min, max, avg, median, p95, p99, std_dev"""
    if not values:
        return {"min": 0, "max": 0, "avg": 0, "median": 0, "p95": 0, "p99": 0, "std_dev": 0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return {
        "min": min(sorted_vals),
        "max": max(sorted_vals),
        "avg": sum(sorted_vals) / n,
        "median": statistics.median(sorted_vals),
        "p95": sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[0],
        "p99": sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[0],
        "std_dev": statistics.stdev(sorted_vals) if n > 1 else 0.0,
    }
