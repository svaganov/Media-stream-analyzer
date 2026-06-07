#!/usr/bin/env python3
"""Example: Connect to SRT stream and print statistics.

Usage:
    python srt_stats_example.py srt://192.168.1.100:9000

Requires:
    - libsrt installed (apt-get install libsrt-dev / brew install srt)
    - Python dependencies: pip install -r requirements.txt
"""
import sys
import time
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.libsrt_native import get_srt_lib, SRTNativeStats
from backend.srt_connection import SRTConnection, SRTConnectionConfig, SRTMode


def print_stats(stats: SRTNativeStats):
    """Print statistics in a formatted way."""
    print(f"\rRTT: {stats.rtt_ms:6.1f}ms | "
          f"BW: {stats.bandwidth_mbps:5.1f}Mbps | "
          f"Loss: {stats.loss_rate_percent:5.2f}% | "
          f"Drop: {stats.drop_rate_percent:5.2f}% | "
          f"RcvBuf: {stats.ms_rcv_buf:4d}ms | "
          f"Flight: {stats.pkt_flight_size:3d}", end="", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python srt_stats_example.py <srt_url>")
        print("Example: python srt_stats_example.py srt://192.168.1.100:9000")
        sys.exit(1)

    url = sys.argv[1]

    # Parse URL
    url = url.replace("srt://", "")
    if "?" in url:
        url = url.split("?")[0]
    host, port = url.split(":")
    port = int(port)

    print(f"Connecting to SRT stream: {host}:{port}")
    print("Press Ctrl+C to exit\n")

    # Initialize SRT library
    try:
        srt_lib = get_srt_lib()
        print("✅ SRT library loaded")
    except RuntimeError as e:
        print(f"❌ Failed to load SRT: {e}")
        sys.exit(1)

    # Create connection
    config = SRTConnectionConfig(
        host=host,
        port=port,
        mode=SRTMode.CALLER,
        latency_ms=120
    )

    conn = SRTConnection(config)
    conn.on_stats(print_stats)

    # Connect
    if not conn.connect():
        print("Failed to connect")
        sys.exit(1)

    print("✅ Connected! Collecting statistics...\n")

    # Run until interrupted
    try:
        while conn.is_connected:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nDisconnecting...")
    finally:
        conn.disconnect()
        srt_lib.cleanup()
        print("\nDone")


if __name__ == "__main__":
    main()
