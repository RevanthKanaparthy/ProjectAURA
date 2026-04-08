#!/bin/bash
set -e
echo "Installing runtime dependencies..."
pip install --no-cache-dir -r requirements-runtime.txt
echo "Runtime dependencies installed"
exec "$@"
