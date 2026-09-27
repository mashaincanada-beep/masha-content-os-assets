#!/usr/bin/env bash
# One-time setup for a fresh session (about 1-2 minutes). Safe to re-run.
set -e
pip install --break-system-packages -q kokoro-onnx soundfile faster-whisper numpy scipy pillow praat-parselmouth 2>&1 | grep -v "WARNING: Running pip" || true
python3 -c "import playwright" 2>/dev/null || pip install --break-system-packages -q playwright
D="$HOME/.cache/micstudy"; mkdir -p "$D"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "$D/$f" ] || curl -sSL -o "$D/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
python3 - <<'PY'
import os
from kokoro_onnx import Kokoro
d=os.path.expanduser("~/.cache/micstudy"); Kokoro(d+"/kokoro-v1.0.onnx", d+"/voices-v1.0.bin")
from faster_whisper import WhisperModel; WhisperModel("base.en", device="cpu", compute_type="int8")
print("setup ok")
PY
python3 "$(dirname "$0")/voices.py" status || true
