import pytest
import asyncio

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def srt_config():
    from src.inputs.srt.srt_connection import SRTConnectionConfig, SRTMode
    return SRTConnectionConfig(
        mode=SRTMode.CALLER,
        host="127.0.0.1",
        port=9999,
        auto_reconnect=False,
    )
