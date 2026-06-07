"""
FastAPI Application for Media Stream Analyzer

REST API + WebSocket for real-time metrics.
Sprint 3: Added FFT spectrum, time windows, history endpoints.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.time_window import TimeWindow, window_manager
from src.metrics.aggregator import MetricsAggregator
from src.metrics.history_buffer import MultiWindowHistory, CHART_CONFIGS


# ===== Pydantic Models =====

class SessionStartRequest(BaseModel):
    input_type: str = "icecast"
    source_url: str = "https://solovievfm.hostingradio.ru/solovievfm256.mp3"

class TimeWindowRequest(BaseModel):
    window: str = "15m"  # 1m, 5m, 15m, 30m, 60m

class SessionStatus(BaseModel):
    active: bool
    duration: float
    input_type: str
    source_url: str
    time_window: str
    metrics_count: int


# ===== Global State =====

session_active = False
session_start_time = None
current_input_type = "icecast"
current_source_url = ""
current_time_window = TimeWindow.FIFTEEN_MINUTES

aggregator: Optional[MetricsAggregator] = None
history = MultiWindowHistory()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


# ===== Background Task =====

async def metrics_broadcast_task():
    """Broadcast metrics to all WebSocket clients every 1 second."""
    while True:
        if session_active and aggregator:
            try:
                metrics = aggregator.to_dict()
                if metrics:
                    await manager.broadcast({
                        "type": "metrics",
                        "data": metrics
                    })
            except Exception as e:
                print(f"Broadcast error: {e}")

        await asyncio.sleep(1.0)


# ===== FastAPI App =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    asyncio.create_task(metrics_broadcast_task())
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Media Stream Analyzer",
    description="Professional audio/video stream analysis API",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="src/web"), name="static")


# ===== REST API Endpoints =====

@app.post("/api/session/start")
async def start_session(request: SessionStartRequest):
    """Start analysis session."""
    global session_active, session_start_time, current_input_type, current_source_url
    global aggregator

    if session_active:
        raise HTTPException(status_code=400, detail="Session already active")

    session_active = True
    session_start_time = time.time()
    current_input_type = request.input_type
    current_source_url = request.source_url

    # Initialize aggregator
    aggregator = MetricsAggregator(time_window=current_time_window)
    aggregator.start_session()

    # Register metrics in history
    for metric in ["bitrate", "jitter", "dbfs_peak", "lufs_integrated"]:
        history.register_metric(metric)

    return {"status": "started", "input_type": request.input_type, "url": request.source_url}


@app.post("/api/session/stop")
async def stop_session():
    """Stop analysis session."""
    global session_active, aggregator

    if not session_active:
        raise HTTPException(status_code=400, detail="No active session")

    session_active = False
    if aggregator:
        aggregator.stop_session()

    return {"status": "stopped"}


@app.post("/api/session/reset")
async def reset_session():
    """Reset all measurements."""
    global aggregator, history

    if aggregator:
        aggregator.reset()

    history.reset()

    return {"status": "reset"}


@app.post("/api/session/window")
async def set_time_window(request: TimeWindowRequest):
    """Change time window for charts."""
    global current_time_window, aggregator

    window_map = {
        "1m": TimeWindow.ONE_MINUTE,
        "5m": TimeWindow.FIVE_MINUTES,
        "15m": TimeWindow.FIFTEEN_MINUTES,
        "30m": TimeWindow.THIRTY_MINUTES,
        "60m": TimeWindow.SIXTY_MINUTES,
    }

    if request.window not in window_map:
        raise HTTPException(status_code=400, detail=f"Invalid window: {request.window}")

    current_time_window = window_map[request.window]

    if aggregator:
        aggregator.set_time_window(current_time_window)

    return {"status": "ok", "window": request.window}


@app.get("/api/session/status")
async def get_status():
    """Get current session status."""
    duration = 0.0
    if session_active and session_start_time:
        duration = time.time() - session_start_time

    return {
        "active": session_active,
        "duration": round(duration, 1),
        "input_type": current_input_type,
        "source_url": current_source_url,
        "time_window": current_time_window.value,
        "metrics_count": aggregator.window_mgr.get_registered_metrics().__len__() if aggregator else 0
    }


@app.get("/api/metrics/current")
async def get_current_metrics():
    """Get current metrics snapshot."""
    if not aggregator:
        raise HTTPException(status_code=400, detail="No active session")

    return aggregator.to_dict()


@app.get("/api/metrics/history/{metric_name}")
async def get_metric_history(metric_name: str, window: str = "15m", points: int = 200):
    """
    Get history data for charting.

    Args:
        metric_name: Metric name (bitrate, jitter, dbfs_peak, lufs_integrated)
        window: Time window (1m, 5m, 15m, 30m, 60m)
        points: Max points to return (downsampled if needed)
    """
    if not aggregator:
        raise HTTPException(status_code=400, detail="No active session")

    window_map = {
        "1m": TimeWindow.ONE_MINUTE,
        "5m": TimeWindow.FIVE_MINUTES,
        "15m": TimeWindow.FIFTEEN_MINUTES,
        "30m": TimeWindow.THIRTY_MINUTES,
        "60m": TimeWindow.SIXTY_MINUTES,
    }

    if window not in window_map:
        raise HTTPException(status_code=400, detail=f"Invalid window: {window}")

    # Get from time window manager
    history_data = aggregator.get_history(metric_name, window_map[window])

    # Downsample if needed
    if len(history_data) > points:
        step = len(history_data) // points
        history_data = history_data[::step]

    return {
        "metric": metric_name,
        "window": window,
        "points": len(history_data),
        "data": history_data
    }


@app.get("/api/metrics/stats/{metric_name}")
async def get_metric_stats(metric_name: str, window: str = "15m"):
    """Get statistics (min/max/avg) for a metric in a window."""
    if not aggregator:
        raise HTTPException(status_code=400, detail="No active session")

    window_map = {
        "1m": TimeWindow.ONE_MINUTE,
        "5m": TimeWindow.FIVE_MINUTES,
        "15m": TimeWindow.FIFTEEN_MINUTES,
        "30m": TimeWindow.THIRTY_MINUTES,
        "60m": TimeWindow.SIXTY_MINUTES,
    }

    if window not in window_map:
        raise HTTPException(status_code=400, detail=f"Invalid window: {window}")

    stats = aggregator.window_mgr.get_stats(metric_name, window_map[window])

    return {
        "metric": metric_name,
        "window": window,
        "stats": {
            "count": stats.count,
            "current": round(stats.current, 2),
            "minimum": round(stats.minimum, 2),
            "maximum": round(stats.maximum, 2),
            "average": round(stats.average, 2),
            "median": round(stats.median, 2),
            "p95": round(stats.p95, 2),
            "p99": round(stats.p99, 2),
            "std_dev": round(stats.std_dev, 2)
        }
    }


@app.get("/api/metrics/spectrum")
async def get_spectrum():
    """Get current FFT spectrum data."""
    if not aggregator or not aggregator._current_metrics:
        raise HTTPException(status_code=400, detail="No active session")

    m = aggregator._current_metrics
    return {
        "peak_frequency": int(m.spectrum_peak_freq),
        "peak_magnitude_db": round(m.spectrum_peak_db, 1),
        "bands": [round(b, 1) for b in m.spectrum_bands],
        "sample_rate": 48000,
        "fft_size": 1024
    }


@app.get("/api/inputs/list")
async def list_inputs():
    """List available input types."""
    return {
        "inputs": [
            {"id": "icecast", "name": "IceCast", "formats": ["MP3", "AAC", "AAC+", "HE-AAC v2"]},
            {"id": "sdi", "name": "SDI (DeckLink)", "formats": ["SDI"]},
            {"id": "ndi", "name": "NDI", "formats": ["NDI"]},
            {"id": "srt", "name": "SRT", "formats": ["SRT"]},
            {"id": "rtmp", "name": "RTMP", "formats": ["RTMP"]},
            {"id": "hls", "name": "HLS", "formats": ["HLS"]},
            {"id": "rtsp", "name": "RTSP", "formats": ["RTSP"]},
            {"id": "mpegts", "name": "MPEG-TS", "formats": ["UDP/RTP"]},
        ]
    }


@app.get("/api/charts/config")
async def get_chart_configs():
    """Get chart configurations for frontend."""
    return CHART_CONFIGS


# ===== WebSocket Endpoint =====

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metrics.

    Client receives:
        - metrics updates every 1 second
        - spectrum data every 50ms (when requested)

    Client can send:
        - {"action": "subscribe_spectrum", "enabled": true}
        - {"action": "set_window", "window": "15m"}
    """
    await manager.connect(websocket)
    subscribe_spectrum = False

    try:
        while True:
            # Check for client messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=0.05
                )

                if data.get("action") == "subscribe_spectrum":
                    subscribe_spectrum = data.get("enabled", False)

                elif data.get("action") == "set_window":
                    window = data.get("window", "15m")
                    await set_time_window(TimeWindowRequest(window=window))

            except asyncio.TimeoutError:
                pass

            # Send spectrum data if subscribed (50fps)
            if subscribe_spectrum and aggregator and aggregator._current_metrics:
                m = aggregator._current_metrics
                await websocket.send_json({
                    "type": "spectrum",
                    "data": {
                        "peak_frequency": int(m.spectrum_peak_freq),
                        "peak_magnitude_db": round(m.spectrum_peak_db, 1),
                        "bands": [round(b, 1) for b in m.spectrum_bands]
                    }
                })

            await asyncio.sleep(0.02)  # 50fps

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ===== Health Check =====

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "sprint": "Sprint 3: FFT Spectrum + Time Windows",
        "session_active": session_active,
        "time_window": current_time_window.value
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
