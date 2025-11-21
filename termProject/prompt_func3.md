# Context
You are an expert Serverless Cloud Architect and Python Developer. Your task is to write a highly optimized AWS Lambda function handler in **Python 3.14**.

# Constraint Checklist & Confidence Score
1. Use the `Pillow` (PIL) library.
2. **CPU Intensity:** The logic MUST perform mathematical calculations to simulate high-quality image processing (e.g., Tone Mapping/Gamma Correction). Do NOT just perform a simple bit-shift, as that is too fast for a benchmark.
3. **Robustness:** Catch all exceptions. Return `"success": false` on failure.
4. **Performance:** The goal is to benchmark CPU processing power (Floating Point Operations).

# Function Specifications (Function 3: Color Depth Map)

## Goal
Perform a CPU-intensive "Color Depth Reduction" simulation. To ensure high CPU usage, apply a Gamma Correction curve while re-mapping the pixel values.

## Input Payload (JSON)
```json
{
  "image": "base64_encoded_string...",
  "params": { "target_depth": 8 }
}
````

*Note: If `target_depth` is not provided, default to 8.*

## Output Payload (JSON)

```json
{
  "success": boolean,
  "image": "base64_encoded_string_processed...",
  "execution_time_ms": float,
  "error": "string_or_null"
}
```

## Specific Logic Requirements

1.  **Timing (`execution_time_ms`):**
      - Measure: Base64 Decode -\> **Math Heavy Processing** -\> Base64 Encode.
2.  **Image Processing:**
      - Decode Base64 to image.
      - **Algorithm (Simulated 10-bit Tone Map):**
          - Instead of simple rounding, apply a **Gamma Correction (Gamma=2.2)** to every pixel channel.
          - Formula implication: `New_Pixel = 255 * ((Old_Pixel / 255) ^ (1 / 2.2))`
          - Implementation Hint: Use `Image.point()` with a lookup table generated via a loop containing the `pow()` function. This forces the CPU to calculate floating-point values for the table generation.
      - After applying the Gamma curve, ensure the image is in standard RGB mode.
      - Save to buffer as **JPEG**, `quality=85`.
      - Encode back to Base64.

# Task

Generate the complete `lambda_handler(event, context)` Python code. Do not include explanations, just the code.
