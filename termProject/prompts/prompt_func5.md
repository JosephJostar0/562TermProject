# Context
You are an expert Serverless Cloud Architect and Python Developer. Your task is to write a highly optimized AWS Lambda function handler in **Python 3.14**.

# Constraint Checklist & Confidence Score
1. Use `boto3` for S3 interactions (standard AWS SDK).
2. Use `Pillow` (PIL) for image format conversion.
3. **I/O Intensity:** This function benchmarks network I/O.
4. **Robustness:** Handle S3 errors (e.g., `ClientError`) and Image errors gracefully.
5. **Global State:** Initialize the S3 client *outside* the handler to leverage execution context reuse.

# Function Specifications (Function 5: Format Convert & Upload)

## Goal
Convert the image format (e.g., JPEG to PNG) to increase file size/processing time, then upload the result to an AWS S3 Bucket.

## Input Payload (JSON)
```json
{
  "image": "base64_encoded_string...",
  "params": {
    "target_format": "PNG",
    "bucket_name": "your-target-bucket",
    "s3_key": "output/final_image.png"
  }
}
````

*Note: Use defaults if params are missing: target\_format="PNG", bucket\_name="test-bucket", s3\_key="output/test.png".*

## Output Payload (JSON)

```json
{
  "success": boolean,
  "s3_url": "[https://s3.region.amazonaws.com/bucket/key](https://s3.region.amazonaws.com/bucket/key)",
  "execution_time_ms": float,
  "error": "string_or_null"
}
```

## Specific Logic Requirements

1.  **Timing (`execution_time_ms`):**
      - Measure: Base64 Decode -\> Format Conversion -\> **S3 Upload (`put_object`)** -\> End.
      - Do NOT include the S3 Client initialization time (do that globally).
2.  **Image Processing:**
      - Decode Base64 to image.
      - Convert the image to the `target_format` (Default: **PNG**).
      - Save to a memory buffer (`io.BytesIO`).
3.  **S3 Interaction (I/O):**
      - Upload the buffer contents to S3 using `s3_client.put_object()`.
      - Ensure you set the correct `ContentType` (e.g., `image/png`).
      - Construct the standard S3 URL for the response.

# Task

Generate the complete `lambda_handler(event, context)` Python code. Do not include explanations, just the code.
