#!/bin/bash

# Define Python version
PY_VERSION="3.14"
# Define target directory structure (AWS Lambda requires Layer structure to be python/...)
TARGET_DIR="python"

echo "=== Starting x86_64 Layer Build ==="
# Clean up old files
rm -rf layer_x86 && mkdir -p layer_x86/$TARGET_DIR

# Use Docker to simulate x86 environment for installation
# Note: We use --platform linux/amd64 to enforce architecture
# Use --only-binary=:all: to force pre-compiled Wheels, avoiding source compilation dependency issues
docker run --rm -v $(pwd):/var/task --platform linux/amd64 python:$PY_VERSION-slim \
    pip install \
    -r /var/task/requirements.txt \
    -t /var/task/layer_x86/$TARGET_DIR \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version $PY_VERSION \
    --only-binary=:all: \
    --upgrade

# Package zip
cd layer_x86
zip -r ../pillow_layer_x86_64.zip .
cd ..
echo "✅ x86_64 Layer packaged: pillow_layer_x86_64.zip"

echo "=== Starting ARM64 (Graviton) Layer Build ==="
# Clean up old files
rm -rf layer_arm && mkdir -p layer_arm/$TARGET_DIR

# Use Docker to simulate ARM64 environment
docker run --rm -v $(pwd):/var/task --platform linux/arm64 python:$PY_VERSION-slim \
    pip install \
    -r /var/task/requirements.txt \
    -t /var/task/layer_arm/$TARGET_DIR \
    --platform manylinux2014_aarch64 \
    --implementation cp \
    --python-version $PY_VERSION \
    --only-binary=:all: \
    --upgrade

# Package zip
cd layer_arm
zip -r ../pillow_layer_arm64.zip .
cd ..
echo "✅ ARM64 Layer packaged: pillow_layer_arm64.zip"