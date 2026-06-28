#!/bin/bash
# Optional setup for `subject` mode only (the ML cutout). The bold/veil/skyline/
# full styles need NOTHING but ImageMagick — skip this unless you want cutouts.
#
# Creates a local venv and downloads the U2Net model (~176MB). Runs entirely
# offline afterwards. Needs Python 3.10–3.13 (3.14 has no onnxruntime wheels yet).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

PY="${PYTHON:-python3}"
echo "Using $($PY --version)"

$PY -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

mkdir -p models
MODEL="models/u2net.onnx"
URL="https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
if [ ! -f "$MODEL" ]; then
  echo "Downloading U2Net model (~176MB)..."
  curl -L -o "$MODEL" "$URL"
fi

echo "Done. subject mode is ready."
