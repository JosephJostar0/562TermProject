# Context
You are an expert Serverless Cloud Architect and Python Developer. Your task is to write a highly optimized AWS Lambda function handler in **Python 3.14**.

# Constraint Checklist & Confidence Score
1. Use the `Pillow` (PIL) library.
2. **Robustness:** Handle all exceptions. Return `"success": false` on failure.
3. **Consistency:** Ensure the rotation does not crop the image logic (handle canvas size changes).
4. **Performance:** Optimize for execution on x86_64 and arm64.

# Function Specifications (Function 4: Rotate)

## Goal
Rotate the input image by a specified angle (N degrees).

## Input Payload (JSON)
```json
{
  "image": "base64_encoded_string...",
  "params": { "angle": 90 }
}
````

*Note: If `angle` is not provided, default to 90 degrees.*

## Output Payload (JSON)

```json
{
  "success": boolean,
  "image": "base64_encoded_string_rotated...",
  "execution_time_ms": float,
  "error": "string_or_null"
}
```

## Specific Logic Requirements

1.  **Timing (`execution_time_ms`):**
      - Measure: Base64 Decode -\> **Rotation Logic** -\> Base64 Encode.
2.  **Image Processing:**
      - Decode Base64 to image.
      - Parse `angle` from `params` (default = 90).
      - **Operation:** Rotate the image.
      - **Crucial:** Use `.rotate(angle, expand=True)` to ensure the image frame resizes to accommodate the new orientation (preventing cropping).
      - Save to buffer as **JPEG**, `quality=85`.
      - Encode back to Base64.

# Task

Generate the complete `lambda_handler(event, context)` Python code. Do not include explanations, just the code.
