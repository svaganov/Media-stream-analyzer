#!/bin/bash
set -e

# Wait for dependencies if needed
# (e.g., SRT listener, NDI source)

echo "Starting Media Stream Analyzer v4.0"
echo "SRT support: $(ffmpeg -protocols 2>/dev/null | grep -i srt || echo 'NOT AVAILABLE')"

exec "$@"
