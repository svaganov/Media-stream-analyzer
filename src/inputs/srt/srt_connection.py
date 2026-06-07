"""
SRT Connection Manager
Handles SRT socket lifecycle: Caller, Listener, Rendezvous modes
Based on libsrt Python bindings (pysrt) or subprocess to srt-live-transmit

For production: use pysrt (pip install pysrt) or ctypes bindings to libsrt
For testing: uses FFmpeg with srt protocol
"""

import asyncio
import logging
import subprocess
import time
from typing import Optional, Callable, Literal, Dict, Any
from enum import Enum
from dataclasses import dataclass

from .srt_statistics import SRTStatsCollector, SRTConnectionState, SRTMetricsSnapshot

logger = logging.getLogger(__name__)


class SRTMode(Enum):
    CALLER = "caller"
    LISTENER = "listener"
    RENDEZVOUS = "rendezvous"


@dataclass
class SRTConnectionConfig:
    """SRT connection configuration"""
    mode: SRTMode = SRTMode.CALLER
    host: str = "127.0.0.1"
    port: int = 9000
    # SRT options
    latency_ms: int = 120
    peer_latency_ms: int = 120
    max_bw_mbps: int = 0  # 0 = unlimited
    mss_bytes: int = 1500
    encryption: Literal["none", "aes-128", "aes-256"] = "none"
    passphrase: str = ""
    stream_id: str = ""
    # Tuning
    rcv_buf_size: int = 8192  # packets
    snd_buf_size: int = 8192  # packets
    # Reconnect
    auto_reconnect: bool = True
    reconnect_delay_sec: float = 5.0
    max_reconnects: int = 0  # 0 = unlimited


class SRTConnectionManager:
    """
    Manages SRT connection lifecycle and statistics collection.
    Supports Caller, Listener, and Rendezvous modes.
    """

    def __init__(self, config: SRTConnectionConfig):
        self.config = config
        self.stats_collector = SRTStatsCollector()
        self._state = SRTConnectionState.STOPPED
        self._process: Optional[subprocess.Popen] = None
        self._task: Optional[asyncio.Task] = None
        self._reconnect_count = 0
        self._start_time: Optional[float] = None
        self._callbacks: list[Callable[[SRTMetricsSnapshot], None]] = []
        self._running = False

    def _build_srt_url(self) -> str:
        """Build SRT URL for FFmpeg"""
        mode = self.config.mode.value
        url = f"srt://{self.config.host}:{self.config.port}?mode={mode}"

        # Add SRT options
        url += f"&latency={self.config.latency_ms}"
        url += f"&peerlatency={self.config.peer_latency_ms}"

        if self.config.max_bw_mbps > 0:
            url += f"&maxbw={self.config.max_bw_mbps * 1000000}"

        if self.config.mss_bytes != 1500:
            url += f"&mss={self.config.mss_bytes}"

        if self.config.encryption != "none" and self.config.passphrase:
            url += f"&pbkeylen={128 if self.config.encryption == 'aes-128' else 256}"
            url += f"&passphrase={self.config.passphrase}"

        if self.config.stream_id:
            url += f"&streamid={self.config.stream_id}"

        return url

    async def start(self) -> None:
        """Start SRT connection"""
        if self._running:
            return

        self._running = True
        self._state = SRTConnectionState.CONNECTING
        self._start_time = time.time()

        self.stats_collector.update_connection_state(
            state=self._state,
            source_address=self.config.host,
            local_port=self.config.port,
            peer_latency_ms=self.config.peer_latency_ms,
            recv_latency_ms=self.config.latency_ms,
            encryption=self.config.encryption,
            stream_id=self.config.stream_id,
        )

        # Start connection task
        self._task = asyncio.create_task(self._connection_loop())
        logger.info(f"SRT connection started: {self.config.mode.value} -> {self.config.host}:{self.config.port}")

    async def _connection_loop(self) -> None:
        """Main connection loop with auto-reconnect"""
        while self._running:
            try:
                await self._connect()

                # Connection established - wait for disconnect
                await self._wait_for_disconnect()

                if not self._running:
                    break

                # Handle reconnect
                if self.config.auto_reconnect:
                    self._reconnect_count += 1
                    self.stats_collector.update_connection_state(
                        state=SRTConnectionState.CONNECTING,
                        reconnections=self._reconnect_count,
                    )
                    logger.info(f"Reconnecting in {self.config.reconnect_delay_sec}s... (attempt {self._reconnect_count})")
                    await asyncio.sleep(self.config.reconnect_delay_sec)
                else:
                    break

            except Exception as e:
                logger.error(f"Connection error: {e}")
                self._state = SRTConnectionState.BROKEN
                self.stats_collector.update_connection_state(
                    state=self._state,
                    last_error=str(e),
                    last_error_time=time.time(),
                )
                if self.config.auto_reconnect:
                    await asyncio.sleep(self.config.reconnect_delay_sec)
                else:
                    break

    async def _connect(self) -> None:
        """Establish SRT connection via FFmpeg"""
        srt_url = self._build_srt_url()

        # FFmpeg command to receive SRT and output to null (for stats)
        # In production, this would pipe to analyzer
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", srt_url,
            "-c", "copy",
            "-f", "null",
            "-",
        ]

        # For actual stats, we need to parse FFmpeg stderr or use libsrt directly
        # This is a placeholder - production would use pysrt or ctypes
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
        )

        self._state = SRTConnectionState.STREAMING
        if self._start_time:
            up_time = time.time() - self._start_time
        else:
            up_time = 0

        self.stats_collector.update_connection_state(
            state=self._state,
            up_time_seconds=up_time,
        )

        # Start stats collection loop
        stats_task = asyncio.create_task(self._stats_collection_loop())

        # Wait for process
        try:
            await asyncio.get_event_loop().run_in_executor(None, self._process.wait)
        finally:
            stats_task.cancel()
            try:
                await stats_task
            except asyncio.CancelledError:
                pass

    async def _stats_collection_loop(self) -> None:
        """Collect SRT statistics periodically"""
        while self._running and self._process and self._process.poll() is None:
            try:
                # In production: call srt_bstats() via pysrt/ctypes
                # For now: simulate with realistic data or parse FFmpeg output
                raw_stats = await self._get_srt_stats()

                if raw_stats:
                    snapshot = self.stats_collector.update_from_srt_socket(raw_stats)

                    # Update connection state
                    if self._start_time:
                        up_time = time.time() - self._start_time
                        self.stats_collector.update_connection_state(
                            up_time_seconds=up_time,
                        )

                    # Notify callbacks
                    for cb in self._callbacks:
                        try:
                            cb(snapshot)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

                await asyncio.sleep(1.0)  # 1 second interval (Makito style)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats collection error: {e}")
                await asyncio.sleep(1.0)

    async def _get_srt_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get SRT statistics from socket.

        Production: Use pysrt.srt_bstats() or ctypes call to libsrt
        Testing: Return simulated data or parse FFmpeg progress
        """
        # TODO: Implement actual libsrt call
        # For now, return simulated realistic data for testing UI
        import random

        return {
            "msTimeStamp": int((time.time() - (self._start_time or time.time())) * 1000),
            "pktRecvTotal": 1250000 + random.randint(0, 1000),
            "pktRecvUniqueTotal": 1249500 + random.randint(0, 1000),
            "pktRcvLossTotal": 500 + random.randint(0, 10),
            "pktRcvRetransTotal": 450 + random.randint(0, 10),
            "pktRcvDropTotal": 20 + random.randint(0, 5),
            "pktRcvUndecryptTotal": 0,
            "pktSentACKTotal": 50000,
            "pktSentNAKTotal": 500,
            "byteRecvTotal": 962000000 + random.randint(0, 1000000),
            "byteRecvUniqueTotal": 961500000 + random.randint(0, 1000000),
            "byteRcvLossTotal": 500000 + random.randint(0, 10000),
            "byteRcvDropTotal": 20000 + random.randint(0, 5000),
            "byteRcvUndecryptTotal": 0,
            "pktRecvUnique": 1000 + random.randint(0, 100),
            "pktRcvDrop": random.randint(0, 3),
            "pktRcvUndecrypt": 0,
            "pktRcvBelated": random.randint(0, 2),
            "pktReorderDistance": random.randint(0, 2),
            "byteRecvUnique": 1280000 + random.randint(0, 100000),
            "byteRcvDrop": random.randint(0, 5000),
            "mbpsRecvRate": 9.5 + random.uniform(-0.5, 0.5),
            "usSndDuration": 1000000,
            "msRTT": 25.0 + random.uniform(-5, 5),
            "mbpsBandwidth": 50.0 + random.uniform(-5, 5),
            "mbpsMaxBW": 0.0,
            "byteAvailRcvBuf": 6400000,
            "pktRcvBuf": 500 + random.randint(0, 50),
            "byteRcvBuf": 640000 + random.randint(0, 50000),
            "msRcvBuf": 80.0 + random.uniform(-5, 5),
            "msRcvTsbPdDelay": 120,
            "pktCongestionWindow": 1000 + random.randint(0, 100),
            "pktFlightSize": 500 + random.randint(0, 50),
            "pktReorderTolerance": 2,
            "pktRcvAvgBelatedTime": 5.0 + random.uniform(-2, 2),
            "byteMSS": 1500,
        }

    async def _wait_for_disconnect(self) -> None:
        """Wait for connection to close"""
        if self._process:
            await asyncio.get_event_loop().run_in_executor(None, self._process.wait)

    async def stop(self) -> None:
        """Stop SRT connection"""
        self._running = False
        self._state = SRTConnectionState.STOPPED

        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.stats_collector.update_connection_state(state=SRTConnectionState.STOPPED)
        logger.info("SRT connection stopped")

    def add_callback(self, callback: Callable[[SRTMetricsSnapshot], None]) -> None:
        """Add metrics callback"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[SRTMetricsSnapshot], None]) -> None:
        """Remove metrics callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_stats(self) -> SRTMetricsSnapshot:
        """Get current statistics snapshot"""
        return self.stats_collector.get_snapshot()

    def reset_stats(self) -> None:
        """Reset statistics (Makito Reset button)"""
        self.stats_collector.reset()
        self._reconnect_count = 0
        self._start_time = time.time()

    @property
    def state(self) -> SRTConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state == SRTConnectionState.STREAMING
