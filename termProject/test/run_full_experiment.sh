#!/bin/bash

# Define image set
IMAGES=("std.jpg" "heavy.jpg" "light.jpg")
MODELS=("gpt")
ARCHS=("x86" "arm")

# Loop execution
for model in "${MODELS[@]}"; do
    for arch in "${ARCHS[@]}"; do
        for img in "${IMAGES[@]}"; do
            echo "========================================================"
            echo "🧪 Running Experiment: Model=$model | Arch=$arch | Img=$img"
            echo "========================================================"
            
            # Call Python script, automatically generating different CSVs based on the image name
            # Note: Ensure these images exist in the images/ directory
            python3 benchmark.py \
                --model "$model" \
                --arch "$arch" \
                --image "images/$img" \
                --runs 50 \
                --warmup 5
            
            # Sleep briefly to prevent AWS Rate Limiting or Lambda hotspot issues
            sleep 5 
        done
    done
done