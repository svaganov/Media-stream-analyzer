#!/usr/bin/env python3
"""Media Stream Analyzer - Backend Entry Point."""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import config
from backend.websocket_server import WebSocketServer

# Setup logging
def setup_logging():
    """Configure logging."""
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduce noise from websockets
    logging.getLogger('websockets').setLevel(logging.WARNING)


async def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Media Stream Analyzer - Backend v5.0")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"WebSocket: ws://{config.websocket.host}:{config.websocket.port}")
    logger.info(f"SRT default: {config.srt.url}")
    logger.info("=" * 60)

    server = WebSocketServer()

    # Setup graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info(f"Received signal {sig.name}, shutting down...")
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
        logger.info("Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
