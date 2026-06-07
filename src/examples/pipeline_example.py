#!/usr/bin/env python3
"""Example: Full pipeline - SRT + FFmpeg + Audio Analysis.

Usage:
    python pipeline_example.py srt://192.168.1.100:9000

Shows real-time:
    - SRT statistics (RTT, bandwidth, loss)
    - Audio levels (DBFS, LUFS)
    - Loudness history
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio
from backend.stream_pipeline import StreamPipeline, PipelineConfig


async def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline_example.py <srt_url>")
        sys.exit(1)

    url = sys.argv[1]

    print(f"Starting pipeline: {url}")
    print("Press Ctrl+C to exit
")

    config = PipelineConfig(srt_url=url)
    pipeline = StreamPipeline(config)

    # Setup callbacks
    def on_srt_stats(stats):
        print(f"\r[SRT] RTT: {stats.get('rtt_ms', 0):5.1f}ms | "
              f"BW: {stats.get('bandwidth_mbps', 0):5.1f}Mbps | "
              f"Loss: {stats.get('loss_rate_percent', 0):5.2f}% | "
              f"State: {stats.get('state', 'unknown')}", end="")

    def on_audio(analysis):
        dbfs = analysis.get('dbfs', {})
        lufs = analysis.get('lufs', {})
        print(f"\n[AUDIO] DBFS: {dbfs.get('left', 0):5.1f}/{dbfs.get('right', 0):5.1f}dB | "
              f"LUFS(M): {lufs.get('m', 0):5.1f} | "
              f"LUFS(S): {lufs.get('s', 0):5.1f} | "
              f"TP: {analysis.get('true_peak', 0):5.1f}dB")

    def on_history(history):
        if history:
            print(f"\n[HISTORY] Last 5 values: {history[-5:]}")

    def on_error(msg):
        print(f"\n[ERROR] {msg}")

    pipeline.on_srt_stats(on_srt_stats)
    pipeline.on_audio_analysis(on_audio)
    pipeline.on_loudness_history(on_history)
    pipeline.on_error(on_error)

    # Start
    started = await pipeline.start()

    if not started:
        print("Failed to start pipeline")
        sys.exit(1)

    print("✅ Pipeline started!
")

    # Run
    try:
        while pipeline.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("

Stopping...")
    finally:
        await pipeline.stop()
        print("Done")

if __name__ == "__main__":
    asyncio.run(main())
