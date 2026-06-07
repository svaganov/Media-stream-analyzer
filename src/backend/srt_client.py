"""SRT client for connecting to SRT streams and extracting statistics."""
import asyncio
import json
import logging
import subprocess
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SRTStats:
    """SRT connection statistics."""
    timestamp: float

    # Connection metrics
    rtt: float = 0.0  # ms
    rtt_variance: float = 0.0  # ms
    bandwidth: float = 0.0  # Mbps (estimated)
    bandwidth_max: float = 0.0  # Mbps
    recv_rate: float = 0.0  # Mbps
    send_rate: float = 0.0  # Mbps

    # Packet metrics
    pkt_rcv_total: int = 0
    pkt_rcv_loss: int = 0
    pkt_rcv_drop: int = 0
    pkt_rcv_retrans: int = 0
    pkt_rcv_belated: int = 0
    pkt_rcv_undecrypt: int = 0
    pkt_snd_total: int = 0
    pkt_snd_loss: int = 0
    pkt_snd_drop: int = 0

    # Loss metrics
    pkt_loss_rate: float = 0.0  # percentage
    pkt_drop_rate: float = 0.0  # percentage

    # Buffer metrics
    byte_avail_rcv_buf: int = 0
    byte_avail_snd_buf: int = 0
    ms_rcv_buf: int = 0  # receive buffer time span
    ms_snd_buf: int = 0  # send buffer time span
    ms_rcv_tsbpd_delay: int = 0  # TSBPD delay

    # Connection status
    status: str = "disconnected"  # connected, disconnected, reconnecting, error
    uptime_ms: int = 0

    # Latency
    latency_ms: int = 120  # configured latency

    @property
    def pkt_loss_percent(self) -> float:
        if self.pkt_rcv_total > 0:
            return (self.pkt_rcv_loss / self.pkt_rcv_total) * 100
        return 0.0

    @property
    def pkt_drop_percent(self) -> float:
        if self.pkt_rcv_total > 0:
            return (self.pkt_rcv_drop / self.pkt_rcv_total) * 100
        return 0.0

    @property
    def buffer_health_percent(self) -> float:
        """Calculate buffer health percentage."""
        # Simplified: based on available buffer vs typical max
        max_buf = 8192 * 188  # Typical MPEG-TS buffer size
        if max_buf > 0:
            return min(100, (self.byte_avail_rcv_buf / max_buf) * 100)
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "rtt": round(self.rtt, 1),
            "rtt_variance": round(self.rtt_variance, 1),
            "bandwidth": round(self.bandwidth, 1),
            "bandwidth_max": round(self.bandwidth_max, 1),
            "recv_rate": round(self.recv_rate, 1),
            "send_rate": round(self.send_rate, 1),
            "pkt_rcv_total": self.pkt_rcv_total,
            "pkt_rcv_loss": self.pkt_rcv_loss,
            "pkt_rcv_drop": self.pkt_rcv_drop,
            "pkt_rcv_retrans": self.pkt_rcv_retrans,
            "pkt_loss_rate": round(self.pkt_loss_percent, 2),
            "pkt_drop_rate": round(self.pkt_drop_percent, 2),
            "byte_avail_rcv_buf": self.byte_avail_rcv_buf,
            "ms_rcv_buf": self.ms_rcv_buf,
            "ms_rcv_tsbpd_delay": self.ms_rcv_tsbpd_delay,
            "buffer_health": round(self.buffer_health_percent, 1),
            "status": self.status,
            "uptime_ms": self.uptime_ms,
            "latency_ms": self.latency_ms,
        }


class SRTClient:
    """SRT client for connecting to streams and collecting statistics."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, 
                 mode: str = "caller", latency: int = 120):
        self.host = host
        self.port = port
        self.mode = mode
        self.latency = latency

        self._process: Optional[subprocess.Popen] = None
        self._stats_thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        self._start_time: Optional[float] = None

        # Callbacks
        self._stats_callbacks: List[Callable[[SRTStats], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        # Current stats
        self._current_stats = SRTStats(timestamp=time.time())

        logger.info(f"SRTClient initialized: {host}:{port} (mode={mode})")

    def on_stats(self, callback: Callable[[SRTStats], None]):
        """Register statistics callback."""
        self._stats_callbacks.append(callback)

    def on_error(self, callback: Callable[[str], None]):
        """Register error callback."""
        self._error_callbacks.append(callback)

    def _notify_stats(self, stats: SRTStats):
        """Notify all statistics callbacks."""
        for callback in self._stats_callbacks:
            try:
                callback(stats)
            except Exception as e:
                logger.error(f"Stats callback error: {e}")

    def _notify_error(self, message: str):
        """Notify all error callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error callback error: {e}")

    def connect(self) -> bool:
        """Connect to SRT stream using srt-live-transmit."""
        try:
            # Use srt-live-transmit as a bridge to get statistics
            # This reads from SRT and outputs to null, while we parse stats
            cmd = [
                "srt-live-transmit",
                f"srt://{self.host}:{self.port}?mode={self.mode}&latency={self.latency}",
                "file://con",
                "-v",  # verbose for stats
                "-statsout", "-",  # output stats to stdout
                "-statsfreq", "1",  # 1 second frequency
            ]

            logger.info(f"Starting SRT connection: {' '.join(cmd)}")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            self._running = True
            self._start_time = time.time()

            # Start stats collection thread
            self._stats_thread = threading.Thread(target=self._collect_stats)
            self._stats_thread.daemon = True
            self._stats_thread.start()

            self._connected = True
            logger.info("SRT connection established")
            return True

        except FileNotFoundError:
            logger.error("srt-live-transmit not found. Please install SRT tools.")
            self._notify_error("srt-live-transmit not found")
            return False
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._notify_error(str(e))
            return False

    def _collect_stats(self):
        """Collect statistics from srt-live-transmit output."""
        if not self._process or not self._process.stdout:
            return

        try:
            for line in self._process.stdout:
                if not self._running:
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse SRT statistics from output
                # srt-live-transmit outputs JSON stats when -statsout is used
                try:
                    if line.startswith('{'):
                        stats_data = json.loads(line)
                        self._parse_stats(stats_data)
                except json.JSONDecodeError:
                    # Not JSON, might be connection info
                    if "connected" in line.lower():
                        self._current_stats.status = "connected"
                    elif "disconnect" in line.lower():
                        self._current_stats.status = "disconnected"

        except Exception as e:
            logger.error(f"Stats collection error: {e}")
            self._notify_error(str(e))

    def _parse_stats(self, data: Dict[str, Any]):
        """Parse SRT statistics from JSON data."""
        stats = SRTStats(timestamp=time.time())

        # Map srt-live-transmit JSON fields to our structure
        # Field names may vary based on SRT version

        if "msRTT" in data:
            stats.rtt = float(data["msRTT"])
        if "msRTTVar" in data:
            stats.rtt_variance = float(data["msRTTVar"])
        if "mbpsBandwidth" in data:
            stats.bandwidth = float(data["mbpsBandwidth"])
        if "mbpsMaxBW" in data:
            stats.bandwidth_max = float(data["mbpsMaxBW"])
        if "mbpsRecvRate" in data:
            stats.recv_rate = float(data["mbpsRecvRate"])
        if "mbpsSendRate" in data:
            stats.send_rate = float(data["mbpsSendRate"])

        # Packet stats
        if "pktRcvTotal" in data:
            stats.pkt_rcv_total = int(data["pktRcvTotal"])
        if "pktRcvLossTotal" in data:
            stats.pkt_rcv_loss = int(data["pktRcvLossTotal"])
        if "pktRcvDropTotal" in data:
            stats.pkt_rcv_drop = int(data["pktRcvDropTotal"])
        if "pktRetransTotal" in data:
            stats.pkt_rcv_retrans = int(data["pktRetransTotal"])
        if "pktRcvBelated" in data:
            stats.pkt_rcv_belated = int(data["pktRcvBelated"])
        if "pktRcvUndecryptTotal" in data:
            stats.pkt_rcv_undecrypt = int(data["pktRcvUndecryptTotal"])

        # Buffer stats
        if "byteAvailRcvBuf" in data:
            stats.byte_avail_rcv_buf = int(data["byteAvailRcvBuf"])
        if "msRcvBuf" in data:
            stats.ms_rcv_buf = int(data["msRcvBuf"])
        if "msRcvTsbPdDelay" in data:
            stats.ms_rcv_tsbpd_delay = int(data["msRcvTsbPdDelay"])

        # Calculate uptime
        if self._start_time:
            stats.uptime_ms = int((time.time() - self._start_time) * 1000)

        stats.status = "connected"
        stats.latency_ms = self.latency

        self._current_stats = stats
        self._notify_stats(stats)

    def get_stats(self) -> SRTStats:
        """Get current statistics."""
        return self._current_stats

    def disconnect(self):
        """Disconnect from SRT stream."""
        self._running = False
        self._connected = False

        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")

        if self._stats_thread and self._stats_thread.is_alive():
            self._stats_thread.join(timeout=2)

        self._current_stats.status = "disconnected"
        logger.info("SRT connection closed")

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected and self._running

    @property
    def url(self) -> str:
        """Get SRT URL."""
        return f"srt://{self.host}:{self.port}"
