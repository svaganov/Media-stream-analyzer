import pytest
import asyncio

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health endpoint is accessible"""
    # Requires running server
    pass

@pytest.mark.asyncio
async def test_srt_connection_cycle():
    """Test full SRT connection lifecycle"""
    from src.inputs.srt.srt_connection import SRTConnectionManager, SRTConnectionConfig, SRTMode

    config = SRTConnectionConfig(
        mode=SRTMode.CALLER,
        host="127.0.0.1",
        port=9999,
        auto_reconnect=False,
    )

    manager = SRTConnectionManager(config)
    assert manager.state.value == "STOPPED"

    # Start (will fail quickly)
    try:
        await asyncio.wait_for(manager.start(), timeout=2.0)
    except asyncio.TimeoutError:
        pass

    # Stop
    await manager.stop()
    assert manager.state.value == "STOPPED"
