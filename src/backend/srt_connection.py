"""High-level SRT connection using native libsrt.

Provides real-time connection with automatic statistics collection.
"""
import asyncio
import logging
import socket
import struct
import threading
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import IntEnum

from .libsrt_native import (
    LibSRTNative, SRTNativeStats, SRT_SOCKOPT, SRT_TRANSTYPE,
    SRT_SOCKSTATUS, get_srt_lib
)

logger = logging.getLogger(__name__)


class SRTMode(IntEnum):
    """SRT connection modes."""
    CALLER = 0
    LISTENER = 1
    RENDEZVOUS = 2


@dataclass
class SRTConnectionConfig:
    """SRT connection configuration."""
    host: str = "127.0.0.1"
    port: int = 9000
    mode: SRTMode = SRTMode.CALLER
    latency_ms: int = 120
    passphrase: Optional[str] = None
    pbkeylen: int = 16  # AES-128
    max_bw_mbps: int = 0  # 0 = unlimited
    stream_id: Optional[str] = None
    transtype: SRT_TRANSTYPE = SRT_TRANSTYPE.SRTT_LIVE

    @property
    def url(self) -> str:
        params = f"?latency={self.latency_ms}"
        if self.stream_id:
            params += f"&streamid={self.stream_id}"
        return f"srt://{self.host}:{self.port}{params}"


class SRTConnection:
    """High-level SRT connection manager.

    Handles connection lifecycle, statistics collection, and error recovery.
    """

    def __init__(self, config: Optional[SRTConnectionConfig] = None):
        self.config = config or SRTConnectionConfig()
        self._srt = get_srt_lib()

        self._sock: int = -1
        self._connected = False
        self._running = False
        self._start_time: Optional[float] = None

        # Statistics thread
        self._stats_thread: Optional[threading.Thread] = None
        self._stats_interval: float = 1.0  # 1 second

        # Callbacks
        self._stats_callbacks: List[Callable[[SRTNativeStats], None]] = []
        self._state_callbacks: List[Callable[[str], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        # Current stats
        self._current_stats: Optional[SRTNativeStats] = None

        logger.info(f"SRTConnection created: {self.config.url}")

    def on_stats(self, callback: Callable[[SRTNativeStats], None]):
        """Register statistics callback (called every second)."""
        self._stats_callbacks.append(callback)

    def on_state_change(self, callback: Callable[[str], None]):
        """Register connection state change callback."""
        self._state_callbacks.append(callback)

    def on_error(self, callback: Callable[[str], None]):
        """Register error callback."""
        self._error_callbacks.append(callback)

    def _notify_stats(self, stats: SRTNativeStats):
        """Notify statistics callbacks."""
        for cb in self._stats_callbacks:
            try:
                cb(stats)
            except Exception as e:
                logger.error(f"Stats callback error: {e}")

    def _notify_state(self, state: str):
        """Notify state change callbacks."""
        for cb in self._state_callbacks:
            try:
                cb(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")

    def _notify_error(self, message: str):
        """Notify error callbacks."""
        for cb in self._error_callbacks:
            try:
                cb(message)
            except Exception as e:
                logger.error(f"Error callback error: {e}")

    def connect(self) -> bool:
        """Connect to SRT stream.

        Returns True if connected successfully.
        """
        try:
            # Create socket
            self._sock = self._srt.create_socket()
            logger.info(f"Created SRT socket: {self._sock}")

            # Set options
            self._setup_socket_options()

            # Resolve address
            addr_info = socket.getaddrinfo(
                self.config.host, self.config.port,
                socket.AF_UNSPEC, socket.SOCK_DGRAM
            )

            if not addr_info:
                raise RuntimeError(f"Could not resolve {self.config.host}:{self.config.port}")

            family, socktype, proto, canonname, sockaddr = addr_info[0]

            # Create Python socket for address binding
            py_sock = socket.socket(family, socktype)

            try:
                if self.config.mode == SRTMode.CALLER:
                    # Caller mode: connect to remote
                    logger.info(f"Connecting to {self.config.host}:{self.config.port}...")

                    # Bind to any local address
                    py_sock.bind(("0.0.0.0" if family == socket.AF_INET else "::", 0))

                    # Get the bound address for SRT
                    local_addr = py_sock.getsockname()

                    # For SRT caller, we typically don't bind first, just connect
                    # But the native API needs a sockaddr
                    # Simplified: use srt_connect with resolved address

                    # Create sockaddr structure
                    if family == socket.AF_INET:
                        addr_struct = struct.pack(
                            "!HH4s8s",
                            family,  # sin_family
                            socket.htons(self.config.port),  # sin_port
                            socket.inet_aton(sockaddr[0]),  # sin_addr
                            b"\x00" * 8  # padding
                        )
                    else:
                        # IPv6 - simplified
                        addr_struct = struct.pack(
                            "!HHI16sI",
                            family,
                            socket.htons(self.config.port),
                            0,  # flowinfo
                            socket.inet_pton(family, sockaddr[0]),
                            0  # scope_id
                        )

                    # Connect
                    result = self._srt._lib.srt_connect(
                        self._sock,
                        addr_struct,
                        len(addr_struct)
                    )

                    if result == -1:
                        error = self._srt.get_last_error()
                        raise RuntimeError(f"srt_connect failed: {error}")

                elif self.config.mode == SRTMode.LISTENER:
                    # Listener mode: bind and listen
                    logger.info(f"Binding to {self.config.host}:{self.config.port}...")

                    py_sock.bind((self.config.host, self.config.port))

                    # Get bound address
                    local_addr = py_sock.getsockname()

                    if family == socket.AF_INET:
                        addr_struct = struct.pack(
                            "!HH4s8s",
                            family,
                            socket.htons(local_addr[1]),
                            socket.inet_aton(local_addr[0]),
                            b"\x00" * 8
                        )
                    else:
                        addr_struct = struct.pack(
                            "!HHI16sI",
                            family,
                            socket.htons(local_addr[1]),
                            0,
                            socket.inet_pton(family, local_addr[0]),
                            0
                        )

                    # Bind SRT socket
                    result = self._srt._lib.srt_bind(
                        self._sock,
                        addr_struct,
                        len(addr_struct)
                    )

                    if result == -1:
                        error = self._srt.get_last_error()
                        raise RuntimeError(f"srt_bind failed: {error}")

                    # Listen
                    result = self._srt._lib.srt_listen(self._sock, 1)
                    if result == -1:
                        error = self._srt.get_last_error()
                        raise RuntimeError(f"srt_listen failed: {error}")

                    logger.info("Waiting for incoming connection...")

                    # Accept
                    client_addr_len = ctypes.c_int(128)
                    client_addr = ctypes.create_string_buffer(128)

                    client_sock = self._srt._lib.srt_accept(
                        self._sock,
                        client_addr,
                        ctypes.byref(client_addr_len)
                    )

                    if client_sock == -1:
                        error = self._srt.get_last_error()
                        raise RuntimeError(f"srt_accept failed: {error}")

                    # Close listening socket, use client socket
                    self._srt.close(self._sock)
                    self._sock = client_sock

                else:
                    raise NotImplementedError(f"Mode {self.config.mode} not yet implemented")

            finally:
                py_sock.close()

            # Wait for connection to establish
            self._wait_for_connection()

            self._connected = True
            self._running = True
            self._start_time = time.time()

            # Start statistics collection
            self._stats_thread = threading.Thread(target=self._collect_stats, daemon=True)
            self._stats_thread.start()

            self._notify_state("connected")
            logger.info(f"SRT connected: {self.config.url}")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._notify_error(str(e))
            self._cleanup()
            return False

    def _setup_socket_options(self):
        """Configure socket options."""
        # Set latency
        self._srt.set_sock_opt(
            self._sock, 0, SRT_SOCKOPT.SRTO_LATENCY,
            self.config.latency_ms
        )

        # Set transmission type (LIVE)
        self._srt.set_sock_opt(
            self._sock, 0, SRT_SOCKOPT.SRTO_TRANSTYPE,
            int(self.config.transtype)
        )

        # Set max bandwidth
        if self.config.max_bw_mbps > 0:
            self._srt.set_sock_opt(
                self._sock, 0, SRT_SOCKOPT.SRTO_MAXBW,
                self.config.max_bw_mbps * 1000000 // 8  # Convert to bytes/sec
            )

        # Set passphrase if provided
        if self.config.passphrase:
            self._srt.set_sock_opt(
                self._sock, 0, SRT_SOCKOPT.SRTO_PASSPHRASE,
                self.config.passphrase
            )
            self._srt.set_sock_opt(
                self._sock, 0, SRT_SOCKOPT.SRTO_PBKEYLEN,
                self.config.pbkeylen
            )

        # Set stream ID if provided
        if self.config.stream_id:
            self._srt.set_sock_opt(
                self._sock, 0, SRT_SOCKOPT.SRTO_STREAMID,
                self.config.stream_id
            )

        logger.info("Socket options configured")

    def _wait_for_connection(self, timeout: float = 10.0):
        """Wait for connection to establish."""
        start = time.time()
        while time.time() - start < timeout:
            state = self._srt.get_sock_state(self._sock)
            if state == SRT_SOCKSTATUS.SRTS_CONNECTED:
                return
            elif state in (SRT_SOCKSTATUS.SRTS_BROKEN, SRT_SOCKSTATUS.SRTS_NONEXIST):
                raise RuntimeError("Connection failed")
            time.sleep(0.1)

        raise TimeoutError("Connection timeout")

    def _collect_stats(self):
        """Collect statistics in background thread."""
        while self._running and self._connected:
            try:
                if self._sock >= 0:
                    stats = self._srt.get_stats(self._sock, clear=False)
                    self._current_stats = stats
                    self._notify_stats(stats)

                    # Check connection state
                    state = self._srt.get_sock_state(self._sock)
                    if state not in (SRT_SOCKSTATUS.SRTS_CONNECTED, SRT_SOCKSTATUS.SRTS_CONNECTING):
                        logger.warning(f"Connection lost, state: {state}")
                        self._connected = False
                        self._notify_state("disconnected")
                        break

            except Exception as e:
                logger.error(f"Stats collection error: {e}")
                self._notify_error(str(e))

            time.sleep(self._stats_interval)

    def receive(self, buffer_size: int = 188 * 7) -> Optional[bytes]:
        """Receive data from SRT stream.

        Returns bytes or None if no data available.
        """
        if not self._connected or self._sock < 0:
            return None

        try:
            # Use srt_recvmsg2
            buffer = ctypes.create_string_buffer(buffer_size)

            result = self._srt._lib.srt_recvmsg2(
                self._sock,
                buffer,
                buffer_size,
                None  # No message control
            )

            if result > 0:
                return buffer[:result]
            elif result == -1:
                error = self._srt.get_last_error()
                if "AGAIN" not in error.upper() and "TIMEOUT" not in error.upper():
                    logger.warning(f"Receive error: {error}")
                return None
            else:
                return None

        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None

    def get_stats(self) -> Optional[SRTNativeStats]:
        """Get current statistics."""
        if not self._connected or self._sock < 0:
            return None

        try:
            return self._srt.get_stats(self._sock, clear=False)
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return None

    def get_state(self) -> str:
        """Get connection state as string."""
        if self._sock < 0:
            return "closed"

        state = self._srt.get_sock_state(self._sock)
        states = {
            SRT_SOCKSTATUS.SRTS_INIT: "init",
            SRT_SOCKSTATUS.SRTS_OPENED: "opened",
            SRT_SOCKSTATUS.SRTS_LISTENING: "listening",
            SRT_SOCKSTATUS.SRTS_CONNECTING: "connecting",
            SRT_SOCKSTATUS.SRTS_CONNECTED: "connected",
            SRT_SOCKSTATUS.SRTS_BROKEN: "broken",
            SRT_SOCKSTATUS.SRTS_CLOSING: "closing",
            SRT_SOCKSTATUS.SRTS_CLOSED: "closed",
            SRT_SOCKSTATUS.SRTS_NONEXIST: "nonexist",
        }
        return states.get(state, f"unknown({state})")

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected and self._sock >= 0

    @property
    def uptime_seconds(self) -> float:
        """Get connection uptime in seconds."""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def disconnect(self):
        """Disconnect from stream."""
        logger.info("Disconnecting...")
        self._running = False
        self._connected = False

        if self._stats_thread and self._stats_thread.is_alive():
            self._stats_thread.join(timeout=2)

        self._cleanup()
        self._notify_state("disconnected")
        logger.info("Disconnected")

    def _cleanup(self):
        """Cleanup resources."""
        if self._sock >= 0:
            try:
                self._srt.close(self._sock)
            except Exception as e:
                logger.error(f"Close error: {e}")
            self._sock = -1

    def __del__(self):
        """Destructor."""
        if self._sock >= 0:
            self.disconnect()
