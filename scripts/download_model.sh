#!/usr/bin/env bash
set -euo pipefail

# Download a quantized GGML Alpaca-7B model file.
#
# This script downloads a pre-quantized model that works with llama-cpp-python.
# You must have enough disk space (≈4GB) and a stable connection.
#
# Usage:
#   ./scripts/download_model.sh
#
# After downloading, set LLM_MODEL_PATH to the downloaded file path.

MODEL_DIR="$(pwd)/models"
MODEL_FILE="ggml-alpaca-7b-q4.bin"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_PATH" ]; then
  echo "Model already exists at $MODEL_PATH"
  exit 0
fi

# NOTE: Many Hugging Face model files require authentication (HF token).
# If you have an HF token, set it in HUGGINGFACE_TOKEN before running.
#
#   export HUGGINGFACE_TOKEN="<your token>"
#   ./scripts/download_model.sh
#
# If you do not have a token, you can manually download the model from Hugging Face
# and place it under `models/`.

MODEL_URL="https://huggingface.co/antimatter15/alpaca-7b/resolve/main/ggml-alpaca-7b-q4.bin"

auth_header=""
if [ -n "${HUGGINGFACE_TOKEN-}" ]; then
  auth_header=( -H "Authorization: Bearer $HUGGINGFACE_TOKEN" )
else
  echo "WARNING: No HUGGINGFACE_TOKEN set. Some models require authentication and may return an error."
fi

echo "Downloading model (this can take a while): $MODEL_URL"
echo "Saving to: $MODEL_PATH"

curl -L "${auth_header[@]}" -o "$MODEL_PATH" "$MODEL_URL"

if [ ! -s "$MODEL_PATH" ]; then
  echo "Download failed or produced an empty file."
  echo "If the model requires authentication, please set HUGGINGFACE_TOKEN and try again."
  exit 1
fi

echo "Download complete. Set: export LLM_MODEL_PATH=\"$MODEL_PATH\""
