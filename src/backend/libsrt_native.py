"""Native libsrt integration using ctypes.

Direct binding to libsrt shared library for real-time SRT statistics.
"""
import ctypes
import ctypes.util
import logging
import platform
import struct
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import IntEnum

logger = logging.getLogger(__name__)


# SRT Constants
class SRT_SOCKOPT(IntEnum):
    """SRT socket options."""
    SRTO_MSS = 0          # Maximum Segment Size
    SRTO_SNDSYN = 1       # Sending sync mode
    SRTO_RCVSYN = 2       # Receiving sync mode
    SRTO_ISN = 3          # Initial Sequence Number
    SRTO_FC = 4           # Flight Capacity
    SRTO_SNDBUF = 5       # Send Buffer Size
    SRTO_RCVBUF = 6       # Receive Buffer Size
    SRTO_LINGER = 7       # Linger time on close
    SRTO_UDP_SNDBUF = 8   # UDP Send Buffer Size
    SRTO_UDP_RCVBUF = 9   # UDP Receive Buffer Size
    SRTO_RENDEZVOUS = 12  # Rendezvous mode
    SRTO_SNDTIMEO = 13    # Send timeout
    SRTO_RCVTIMEO = 14    # Receive timeout
    SRTO_REUSEADDR = 15   # Reuse address
    SRTO_MAXBW = 16       # Maximum bandwidth
    SRTO_STATE = 17       # Socket state
    SRTO_EVENT = 18       # Socket events
    SRTO_SNDDATA = 19     # Data in send buffer
    SRTO_RCVDATA = 20     # Data in receive buffer
    SRTO_SENDER = 21      # Sender mode
    SRTO_TSBPDMODE = 22   # TSBPD mode
    SRTO_LATENCY = 23     # Latency
    SRTO_TSBPDDELAY = 24  # TSBPD delay
    SRTO_INPUTBW = 25     # Input bandwidth
    SRTO_OHEADBW = 26     # Overhead bandwidth
    SRTO_PASSPHRASE = 27  # Passphrase for encryption
    SRTO_PBKEYLEN = 28    # Crypto key length
    SRTO_KMSTATE = 29     # Keying material state
    SRTO_IPTTL = 30       # IP Time To Live
    SRTO_IPTOS = 31       # IP Type of Service
    SRTO_TLPKTDROP = 32   # Too-late packet drop
    SRTO_SNDDROPDELAY = 33 # Send drop delay
    SRTO_NAKREPORT = 34   # NAK report mode
    SRTO_VERSION = 35     # Version
    SRTO_PEERVERSION = 36 # Peer version
    SRTO_CONNTIMEO = 37   # Connection timeout
    SRTO_DRIFTTRACER = 38 # Drift tracer
    SRTO_LOSSMAXTTL = 39  # Max reorder tolerance
    SRTO_RCVLATENCY = 40  # Receive latency
    SRTO_PEERLATENCY = 41 # Peer latency
    SRTO_MINVERSION = 42  # Minimum version
    SRTO_STREAMID = 43    # Stream ID
    SRTO_CONGESTION = 44 # Congestion controller
    SRTO_MESSAGEAPI = 45 # Message API
    SRTO_PAYLOADSIZE = 46 # Payload size
    SRTO_TRANSTYPE = 47  # Transmission type
    SRTO_KMREFRESHRATE = 48 # Key refresh rate
    SRTO_KMPREANNOUNCE = 49 # Key pre-announce
    SRTO_ENFORCEDENCRYPTION = 50 # Enforced encryption
    SRTO_IPV6ONLY = 51   # IPv6 only
    SRTO_PEERIDLETIMEO = 52 # Peer idle timeout
    SRTO_BINDTODEVICE = 53 # Bind to device
    SRTO_GROUPCONNECT = 54 # Group connect
    SRTO_GROUPSTABTIMEO = 55 # Group stability timeout
    SRTO_GROUPTYPE = 56  # Group type
    SRTO_PACKETFILTER = 57 # Packet filter
    SRTO_RETRANSMITALGO = 58 # Retransmit algorithm


class SRT_TRANSTYPE(IntEnum):
    """SRT transmission types."""
    SRTT_LIVE = 0
    SRTT_FILE = 1
    SRTT_INVALID = 2


class SRT_SOCKSTATUS(IntEnum):
    """SRT socket status."""
    SRTS_INIT = 1
    SRTS_OPENED = 2
    SRTS_LISTENING = 3
    SRTS_CONNECTING = 4
    SRTS_CONNECTED = 5
    SRTS_BROKEN = 6
    SRTS_CLOSING = 7
    SRTS_CLOSED = 8
    SRTS_NONEXIST = 9


# SRT Performance Monitor Structure (srt_bstats)
# This matches the C structure srt_bstats
class CByteCounters(ctypes.Structure):
    """Byte counters structure."""
    _fields_ = [
        ("pkt", ctypes.c_uint64),
        ("bytes", ctypes.c_uint64),
        ("pktUnique", ctypes.c_uint64),
        ("bytesUnique", ctypes.c_uint64),
        ("pktRecvTotal", ctypes.c_uint64),
        ("bytesRecvTotal", ctypes.c_uint64),
        ("pktRcvLossTotal", ctypes.c_uint64),
        ("pktRcvDropTotal", ctypes.c_uint64),
        ("pktRcvUndecryptTotal", ctypes.c_uint64),
        ("bytesRcvLossTotal", ctypes.c_uint64),
        ("bytesRcvDropTotal", ctypes.c_uint64),
        ("bytesRcvUndecryptTotal", ctypes.c_uint64),
    ]


class CPacketCounters(ctypes.Structure):
    _fields_ = [
        ("pktSent", ctypes.c_uint64),
        ("pktRecvUnique", ctypes.c_uint64),
        ("pktRecv", ctypes.c_uint64),
        ("pktSndLoss", ctypes.c_uint64),
        ("pktRcvLoss", ctypes.c_uint64),
        ("pktRetrans", ctypes.c_uint64),
        ("pktRcvRetrans", ctypes.c_uint64),
        ("pktSentACK", ctypes.c_uint64),
        ("pktRecvACK", ctypes.c_uint64),
        ("pktSentNAK", ctypes.c_uint64),
        ("pktRecvNAK", ctypes.c_uint64),
        ("pktSndDrop", ctypes.c_uint64),
        ("pktRcvDrop", ctypes.c_uint64),
        ("pktRcvUndecrypt", ctypes.c_uint64),
        ("pktSndFilterExtra", ctypes.c_uint64),
        ("pktRcvFilterExtra", ctypes.c_uint64),
        ("pktRcvFilterSupply", ctypes.c_uint64),
        ("pktRcvFilterLoss", ctypes.c_uint64),
        ("pktSndBypass", ctypes.c_uint64),
        ("pktRcvBypass", ctypes.c_uint64),
    ]


class CStats(ctypes.Structure):
    """SRT statistics structure (srt_bstats)."""
    _fields_ = [
        ("msTimeStamp", ctypes.c_int64),       # time since the UDT entity is started, in milliseconds
        ("pktSentTotal", ctypes.c_int64),      # total number of sent data packets, including retransmissions
        ("pktRecvTotal", ctypes.c_int64),      # total number of received packets
        ("pktSndLossTotal", ctypes.c_int64),   # total number of lost packets (sender side)
        ("pktRcvLossTotal", ctypes.c_int64),   # total number of lost packets (receiver side)
        ("pktRetransTotal", ctypes.c_int64),   # total number of retransmitted packets
        ("pktSentACKTotal", ctypes.c_int64),   # total number of sent ACK packets
        ("pktRecvACKTotal", ctypes.c_int64),   # total number of received ACK packets
        ("pktSentNAKTotal", ctypes.c_int64),   # total number of sent NAK packets
        ("pktRecvNAKTotal", ctypes.c_int64),   # total number of received NAK packets
        ("pktSndDropTotal", ctypes.c_int64),   # total number of dropped packets (sender side)
        ("pktRcvDropTotal", ctypes.c_int64),   # total number of dropped packets (receiver side)
        ("pktRcvUndecryptTotal", ctypes.c_int64), # total number of undecrypted packets
        ("byteSentTotal", ctypes.c_int64),     # total number of sent data bytes, including retransmissions
        ("byteRecvTotal", ctypes.c_int64),     # total number of received bytes
        ("byteRcvLossTotal", ctypes.c_int64),  # total number of lost bytes
        ("byteRcvDropTotal", ctypes.c_int64),  # total number of dropped bytes
        ("byteRcvUndecryptTotal", ctypes.c_int64), # total number of undecrypted bytes
        ("pktSent", ctypes.c_int64),           # number of sent data packets
        ("pktRecv", ctypes.c_int64),           # number of received packets
        ("pktSndLoss", ctypes.c_int64),        # number of lost packets (sender side)
        ("pktRcvLoss", ctypes.c_int64),        # number of lost packets (receiver side)
        ("pktRetrans", ctypes.c_int64),        # number of retransmitted packets
        ("pktRcvRetrans", ctypes.c_int64),     # number of retransmitted packets received
        ("pktSentACK", ctypes.c_int64),        # number of sent ACK packets
        ("pktRecvACK", ctypes.c_int64),        # number of received ACK packets
        ("pktSentNAK", ctypes.c_int64),        # number of sent NAK packets
        ("pktRecvNAK", ctypes.c_int64),        # number of received NAK packets
        ("pktSndDrop", ctypes.c_int64),        # number of dropped packets (sender side)
        ("pktRcvDrop", ctypes.c_int64),        # number of dropped packets (receiver side)
        ("pktRcvUndecrypt", ctypes.c_int64),   # number of undecrypted packets
        ("byteSent", ctypes.c_int64),          # number of sent data bytes
        ("byteRecv", ctypes.c_int64),          # number of received bytes
        ("byteRcvLoss", ctypes.c_int64),       # number of lost bytes
        ("byteRcvDrop", ctypes.c_int64),       # number of dropped bytes
        ("byteRcvUndecrypt", ctypes.c_int64),  # number of undecrypted bytes
        ("usPktSndPeriod", ctypes.c_double),   # packet sending period, in microseconds
        ("pktFlowWindow", ctypes.c_int64),     # flow window size, in number of packets
        ("pktCongestionWindow", ctypes.c_int64), # congestion window size, in number of packets
        ("pktFlightSize", ctypes.c_int64),     # number of packets on flight
        ("msRTT", ctypes.c_double),            # RTT, in milliseconds
        ("mbpsBandwidth", ctypes.c_double),    # estimated bandwidth, in Mb/s
        ("byteAvailSndBuf", ctypes.c_int64),   # available send buffer size
        ("byteAvailRcvBuf", ctypes.c_int64),   # available receive buffer size
        ("mbpsMaxBW", ctypes.c_double),        # transmit bandwidth limit, in Mb/s
        ("byteMSS", ctypes.c_int64),           # Maximum Segment Size
        ("pktSndBuf", ctypes.c_int64),         # number of packets in sender buffer
        ("byteSndBuf", ctypes.c_int64),        # number of bytes in sender buffer
        ("msSndBuf", ctypes.c_int64),          # number of milliseconds of data in sender buffer
        ("msSndTsbPdDelay", ctypes.c_int64),   # sender TsbPd delay
        ("pktRcvBuf", ctypes.c_int64),         # number of packets in receiver buffer
        ("byteRcvBuf", ctypes.c_int64),        # number of bytes in receiver buffer
        ("msRcvBuf", ctypes.c_int64),          # number of milliseconds of data in receiver buffer
        ("msRcvTsbPdDelay", ctypes.c_int64),   # receiver TsbPd delay
        ("pktReorderTolerance", ctypes.c_int32), # packet reorder tolerance
        ("pktRcvAvgBelatedTime", ctypes.c_double), # average belated time
        ("pktRcvBelated", ctypes.c_int64),     # number of belated packets
    ]


@dataclass
class SRTNativeStats:
    """Parsed SRT statistics from native library."""
    # Connection
    rtt_ms: float = 0.0
    bandwidth_mbps: float = 0.0
    max_bw_mbps: float = 0.0

    # Packets - Total
    pkt_sent_total: int = 0
    pkt_recv_total: int = 0
    pkt_snd_loss_total: int = 0
    pkt_rcv_loss_total: int = 0
    pkt_retrans_total: int = 0
    pkt_snd_drop_total: int = 0
    pkt_rcv_drop_total: int = 0
    pkt_rcv_undecrypt_total: int = 0

    # Packets - Current interval
    pkt_sent: int = 0
    pkt_recv: int = 0
    pkt_snd_loss: int = 0
    pkt_rcv_loss: int = 0
    pkt_retrans: int = 0
    pkt_rcv_retrans: int = 0
    pkt_snd_drop: int = 0
    pkt_rcv_drop: int = 0

    # Bytes - Total
    byte_sent_total: int = 0
    byte_recv_total: int = 0

    # Bytes - Current
    byte_sent: int = 0
    byte_recv: int = 0

    # Buffer
    byte_avail_snd_buf: int = 0
    byte_avail_rcv_buf: int = 0
    pkt_snd_buf: int = 0
    byte_snd_buf: int = 0
    ms_snd_buf: int = 0
    pkt_rcv_buf: int = 0
    byte_rcv_buf: int = 0
    ms_rcv_buf: int = 0
    ms_rcv_tsbpd_delay: int = 0

    # Timing
    pkt_snd_period_us: float = 0.0
    ms_snd_tsbpd_delay: int = 0
    pkt_rcv_avg_belated_ms: float = 0.0
    pkt_rcv_belated: int = 0

    # Window
    pkt_flow_window: int = 0
    pkt_congestion_window: int = 0
    pkt_flight_size: int = 0

    # Packet size
    byte_mss: int = 0

    # Calculated
    @property
    def loss_rate_percent(self) -> float:
        if self.pkt_recv_total > 0:
            return (self.pkt_rcv_loss_total / self.pkt_recv_total) * 100
        return 0.0

    @property
    def drop_rate_percent(self) -> float:
        if self.pkt_recv_total > 0:
            return (self.pkt_rcv_drop_total / self.pkt_recv_total) * 100
        return 0.0

    @property
    def recv_rate_mbps(self) -> float:
        """Calculate receive rate in Mbps from interval bytes."""
        # Assuming 1-second interval: bytes * 8 / 1,000,000
        return (self.byte_recv * 8) / 1_000_000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rtt_ms": round(self.rtt_ms, 2),
            "bandwidth_mbps": round(self.bandwidth_mbps, 2),
            "max_bw_mbps": round(self.max_bw_mbps, 2),
            "recv_rate_mbps": round(self.recv_rate_mbps, 2),
            "pkt_sent_total": self.pkt_sent_total,
            "pkt_recv_total": self.pkt_recv_total,
            "pkt_rcv_loss_total": self.pkt_rcv_loss_total,
            "pkt_rcv_drop_total": self.pkt_rcv_drop_total,
            "pkt_retrans_total": self.pkt_retrans_total,
            "loss_rate_percent": round(self.loss_rate_percent, 3),
            "drop_rate_percent": round(self.drop_rate_percent, 3),
            "byte_avail_rcv_buf": self.byte_avail_rcv_buf,
            "ms_rcv_buf": self.ms_rcv_buf,
            "ms_rcv_tsbpd_delay": self.ms_rcv_tsbpd_delay,
            "pkt_flight_size": self.pkt_flight_size,
            "pkt_congestion_window": self.pkt_congestion_window,
            "pkt_rcv_belated": self.pkt_rcv_belated,
            "pkt_rcv_avg_belated_ms": round(self.pkt_rcv_avg_belated_ms, 2),
        }


class LibSRTNative:
    """Native libsrt wrapper using ctypes."""

    def __init__(self):
        self._lib = None
        self._load_library()

    def _load_library(self):
        """Load the SRT shared library."""
        lib_names = {
            "Linux": ["libsrt.so", "libsrt.so.1", "srt"],
            "Darwin": ["libsrt.dylib", "srt"],
            "Windows": ["srt.dll", "libsrt.dll"],
        }

        system = platform.system()
        names = lib_names.get(system, ["srt"])

        for name in names:
            try:
                # Try direct load first
                self._lib = ctypes.CDLL(name)
                logger.info(f"Loaded SRT library: {name}")
                break
            except OSError:
                # Try with ctypes.util.find_library
                path = ctypes.util.find_library(name.replace("lib", "").replace(".so", "").replace(".dylib", "").replace(".dll", ""))
                if path:
                    try:
                        self._lib = ctypes.CDLL(path)
                        logger.info(f"Loaded SRT library: {path}")
                        break
                    except OSError:
                        continue

        if self._lib is None:
            raise RuntimeError(
                f"Could not load libsrt. Please install SRT library.
"
                f"Ubuntu: sudo apt-get install libsrt-dev
"
                f"macOS: brew install srt
"
                f"Windows: Download from https://github.com/Haivision/srt"
            )

        self._setup_functions()

    def _setup_functions(self):
        """Setup ctypes function signatures."""
        lib = self._lib

        # srt_startup
        lib.srt_startup.argtypes = []
        lib.srt_startup.restype = ctypes.c_int

        # srt_cleanup
        lib.srt_cleanup.argtypes = []
        lib.srt_cleanup.restype = ctypes.c_int

        # srt_create_socket
        lib.srt_create_socket.argtypes = []
        lib.srt_create_socket.restype = ctypes.c_int

        # srt_close
        lib.srt_close.argtypes = [ctypes.c_int]
        lib.srt_close.restype = ctypes.c_int

        # srt_bind
        lib.srt_bind.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        lib.srt_bind.restype = ctypes.c_int

        # srt_connect
        lib.srt_connect.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        lib.srt_connect.restype = ctypes.c_int

        # srt_listen
        lib.srt_listen.argtypes = [ctypes.c_int, ctypes.c_int]
        lib.srt_listen.restype = ctypes.c_int

        # srt_accept
        lib.srt_accept.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        lib.srt_accept.restype = ctypes.c_int

        # srt_getsockopt
        lib.srt_getsockopt.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int, 
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)
        ]
        lib.srt_getsockopt.restype = ctypes.c_int

        # srt_setsockopt
        lib.srt_setsockopt.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_int
        ]
        lib.srt_setsockopt.restype = ctypes.c_int

        # srt_getsockstate
        lib.srt_getsockstate.argtypes = [ctypes.c_int]
        lib.srt_getsockstate.restype = ctypes.c_int

        # srt_bistats (the key function for statistics)
        lib.srt_bistats.argtypes = [
            ctypes.c_int, 
            ctypes.POINTER(CStats),
            ctypes.c_int,  # clear
            ctypes.c_int   # instantaneous
        ]
        lib.srt_bistats.restype = ctypes.c_int

        # srt_getlasterror_str
        lib.srt_getlasterror_str.restype = ctypes.c_char_p

        # srt_sendmsg2
        lib.srt_sendmsg2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]
        lib.srt_sendmsg2.restype = ctypes.c_int

        # srt_recvmsg2
        lib.srt_recvmsg2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]
        lib.srt_recvmsg2.restype = ctypes.c_int

        # Initialize SRT
        result = lib.srt_startup()
        if result != 0:
            logger.warning(f"srt_startup returned {result}")
        else:
            logger.info("SRT library initialized")

    def create_socket(self) -> int:
        """Create an SRT socket."""
        sock = self._lib.srt_create_socket()
        if sock == -1:
            raise RuntimeError(f"Failed to create SRT socket: {self.get_last_error()}")
        return sock

    def close(self, sock: int) -> int:
        """Close an SRT socket."""
        return self._lib.srt_close(sock)

    def set_sock_opt(self, sock: int, level: int, opt: int, value: Any) -> int:
        """Set socket option."""
        if isinstance(value, bool):
            val = ctypes.c_int(1 if value else 0)
        elif isinstance(value, int):
            val = ctypes.c_int(value)
        elif isinstance(value, str):
            val = value.encode('utf-8')
        else:
            raise TypeError(f"Unsupported option type: {type(value)}")

        if isinstance(val, bytes):
            return self._lib.srt_setsockopt(sock, level, opt, val, len(val))
        else:
            return self._lib.srt_setsockopt(sock, level, opt, ctypes.byref(val), ctypes.sizeof(val))

    def get_sock_state(self, sock: int) -> int:
        """Get socket state."""
        return self._lib.srt_getsockstate(sock)

    def get_stats(self, sock: int, clear: bool = False, instantaneous: bool = False) -> SRTNativeStats:
        """Get SRT statistics using srt_bistats."""
        stats = CStats()

        result = self._lib.srt_bistats(
            sock,
            ctypes.byref(stats),
            1 if clear else 0,
            1 if instantaneous else 0
        )

        if result != 0:
            raise RuntimeError(f"srt_bistats failed: {self.get_last_error()}")

        return self._parse_stats(stats)

    def _parse_stats(self, c_stats: CStats) -> SRTNativeStats:
        """Parse C stats structure to Python dataclass."""
        return SRTNativeStats(
            rtt_ms=c_stats.msRTT,
            bandwidth_mbps=c_stats.mbpsBandwidth,
            max_bw_mbps=c_stats.mbpsMaxBW,
            pkt_sent_total=c_stats.pktSentTotal,
            pkt_recv_total=c_stats.pktRecvTotal,
            pkt_snd_loss_total=c_stats.pktSndLossTotal,
            pkt_rcv_loss_total=c_stats.pktRcvLossTotal,
            pkt_retrans_total=c_stats.pktRetransTotal,
            pkt_snd_drop_total=c_stats.pktSndDropTotal,
            pkt_rcv_drop_total=c_stats.pktRcvDropTotal,
            pkt_rcv_undecrypt_total=c_stats.pktRcvUndecryptTotal,
            byte_sent_total=c_stats.byteSentTotal,
            byte_recv_total=c_stats.byteRecvTotal,
            pkt_sent=c_stats.pktSent,
            pkt_recv=c_stats.pktRecv,
            pkt_snd_loss=c_stats.pktSndLoss,
            pkt_rcv_loss=c_stats.pktRcvLoss,
            pkt_retrans=c_stats.pktRetrans,
            pkt_rcv_retrans=c_stats.pktRcvRetrans,
            pkt_snd_drop=c_stats.pktSndDrop,
            pkt_rcv_drop=c_stats.pktRcvDrop,
            byte_sent=c_stats.byteSent,
            byte_recv=c_stats.byteRecv,
            byte_avail_snd_buf=c_stats.byteAvailSndBuf,
            byte_avail_rcv_buf=c_stats.byteAvailRcvBuf,
            pkt_snd_buf=c_stats.pktSndBuf,
            byte_snd_buf=c_stats.byteSndBuf,
            ms_snd_buf=c_stats.msSndBuf,
            pkt_rcv_buf=c_stats.pktRcvBuf,
            byte_rcv_buf=c_stats.byteRcvBuf,
            ms_rcv_buf=c_stats.msRcvBuf,
            ms_rcv_tsbpd_delay=c_stats.msRcvTsbPdDelay,
            ms_snd_tsbpd_delay=c_stats.msSndTsbPdDelay,
            pkt_snd_period_us=c_stats.usPktSndPeriod,
            pkt_flow_window=c_stats.pktFlowWindow,
            pkt_congestion_window=c_stats.pktCongestionWindow,
            pkt_flight_size=c_stats.pktFlightSize,
            byte_mss=c_stats.byteMSS,
            pkt_rcv_avg_belated_ms=c_stats.pktRcvAvgBelatedTime,
            pkt_rcv_belated=c_stats.pktRcvBelated,
        )

    def get_last_error(self) -> str:
        """Get last error string."""
        err = self._lib.srt_getlasterror_str()
        if err:
            return err.decode('utf-8')
        return "Unknown error"

    def cleanup(self):
        """Cleanup SRT library."""
        self._lib.srt_cleanup()
        logger.info("SRT library cleaned up")


# Singleton instance
_srt_lib: Optional[LibSRTNative] = None

def get_srt_lib() -> LibSRTNative:
    """Get or create SRT library instance."""
    global _srt_lib
    if _srt_lib is None:
        _srt_lib = LibSRTNative()
    return _srt_lib
