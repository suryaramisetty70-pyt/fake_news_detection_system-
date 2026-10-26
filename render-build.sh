#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Installing system packages for OCR ==="
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-hin tesseract-ocr-tel tesseract-ocr-tam || true

echo "=== Upgrading pip and installing Python dependencies ==="
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "=== Build Complete ==="
