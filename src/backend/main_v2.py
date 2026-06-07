#!/usr/bin/env python3
"""Media Stream Analyzer - Backend v2 with native SRT.

Uses libsrt_native for direct SRT integration.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import config
from backend.websocket_server_v2 import WebSocketServerV2
from backend.libsrt_native import get_srt_lib

def setup_logging():
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('websockets').setLevel(logging.WARNING)

async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Media Stream Analyzer - Backend v5.1 (Native SRT)")
    logger.info("=" * 60)

    # Initialize SRT library
    try:
        srt_lib = get_srt_lib()
        logger.info("✅ SRT library loaded successfully")
    except RuntimeError as e:
        logger.error(f"❌ Failed to load SRT library: {e}")
        logger.error("Install libsrt: apt-get install libsrt-dev | brew install srt")
        sys.exit(1)

    logger.info(f"WebSocket: ws://{config.websocket.host}:{config.websocket.port}")
    logger.info(f"SRT default: {config.srt.url}")
    logger.info("=" * 60)

    server = WebSocketServerV2()

    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info(f"Received {sig.name}, shutting down...")
        asyncio.create_task(server.stop())
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    try:
        await server.run_forever()
    except asyncio.CancelledError:
        logger.info("Server cancelled")
    finally:
        await server.stop()
        srt_lib.cleanup()
        logger.info("Server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
