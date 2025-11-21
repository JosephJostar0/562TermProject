# Context
You are an expert Serverless Cloud Architect and Python Developer. Your task is to write a highly optimized AWS Lambda function handler in **Python 3.14**.

# Constraint Checklist & Confidence Score
1. Use the `Pillow` (PIL) library for image processing. Assume it is already installed in the AWS Lambda Layer.
2. **Compatibility:** Use Modern Pillow syntax (e.g., `Image.Resampling.LANCZOS` instead of `Image.ANTIALIAS`).
3. **Robustness:** The function must NEVER crash. Handle exceptions and return `"success": false` with error details.
4. **Performance:** Optimize for fast execution on both x86_64 and arm64.

# Function Specifications (Function 2: Resize)

## Goal
Resize the input image to a specific resolution (Target: 800x600) to reduce payload size for downstream functions.

## Input Payload (JSON)
Structure:
```json
{
  "image": "base64_encoded_string...",
  "params": { 
      "width": 800, 
      "height": 600 
  }
}
````

*Note: If `params` are missing, default to width=800, height=600.*

## Output Payload (JSON)

Structure:

```json
{
  "success": boolean,
  "image": "base64_encoded_string_resized...",
  "execution_time_ms": float,
  "error": "string_or_null"
}
```

## Specific Logic Requirements

1.  **Timing (`execution_time_ms`):**
      - Measure the **entire** process: Base64 Decode -\> Resize Logic -\> Base64 Encode.
2.  **Image Processing:**
      - Decode the base64 string.
      - Parse `width` and `height` from `params` (default to 800x600 if integer values are missing).
      - **Operation:** Resize the image to the exact target dimensions `(width, height)`.
      - **Resampling Method:** Use `Image.Resampling.LANCZOS` (High quality downsampling).
      - **Output Format:** Save to buffer as **JPEG** (Standardize format), `quality=85`.
      - Encode back to Base64.

# Task

Generate the complete `lambda_handler(event, context)` Python code. Do not include explanations, just the code.
