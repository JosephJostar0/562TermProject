#!/bin/bash

# COPY THIS FILE TO 'deploy_all.sh' AND FILL IN YOUR CONFIG
# DO NOT COMMIT 'deploy_all.sh'

# === Configuration Section ===
# Replace with your actual ARN
LAYER_ARN_X86="" # <--- YOUR ACTUAL X86 LAYER ARN
LAYER_ARN_ARM="" # <--- YOUR ACTUAL ARM LAYER ARN
# Ensure this role has S3 access permissions
ROLE_ARN=""      # <--- YOUR ACTUAL IAM ROLE ARN
# Path to code
PATH_TO_CODE="termProject/functions/deepseek" 

# Function list (filenames corresponding to function names)
# FUNCTIONS=("gpt_func1" "gpt_func2" "gpt_func3" "gpt_func4" "gpt_func5")
FUNCTIONS=("deepseek_func1" "deepseek_func2" "deepseek_func3" "deepseek_func4" "deepseek_func5")

for func in "${FUNCTIONS[@]}"; do
    echo "Processing $func..."
    
    # 1. Prepare deployment package (Assumes renaming .py to lambda_function.py inside the zip)
    # Create temporary directory for packaging to avoid polluting source files
    mkdir -p build_temp
    cp "${PATH_TO_CODE}/${func}.py" build_temp/lambda_function.py
    cd build_temp
    zip -r "../${func}.zip" lambda_function.py
    cd ..
    rm -rf build_temp

    # 2. Deploy x86 version
    echo "  Creating x86 version: ${func}-x86"
    aws lambda create-function \
        --function-name "${func}-x86" \
        --runtime "python3.14" \
        --role "$ROLE_ARN" \
        --handler "lambda_function.lambda_handler" \
        --zip-file "fileb://${func}.zip" \
        --architectures "x86_64" \
        --layers "$LAYER_ARN_X86" \
        --timeout 30 \
        --memory-size 512

    # 3. Deploy ARM version
    echo "  Creating ARM version: ${func}-arm"
    aws lambda create-function \
        --function-name "${func}-arm" \
        --runtime "python3.14" \
        --role "$ROLE_ARN" \
        --handler "lambda_function.lambda_handler" \
        --zip-file "fileb://${func}.zip" \
        --architectures "arm64" \
        --layers "$LAYER_ARN_ARM" \
        --timeout 30 \
        --memory-size 512
        
    # Clean up zip
    rm "${func}.zip"
done

echo "🎉 All functions deployed!"