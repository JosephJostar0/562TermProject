# Context
You are an expert Serverless Cloud Architect and Python Developer. Your task is to write a highly optimized AWS Lambda function handler in **Python 3.14**.

# Constraint Checklist & Confidence Score
1. Use the `Pillow` (PIL) library for image processing. Assume it is already installed in the AWS Lambda Layer (do NOT use `pip install`).
2. Use standard libraries: `json`, `base64`, `io`, `time`.
3. **Robustness:** The function must NEVER crash. It must handle all exceptions (e.g., bad Base64, invalid image data) and return a JSON response with `"success": false` and the error message.
4. **Performance:** The code must run efficiently on both x86_64 and arm64 architectures.

# Function Specifications (Function 1: Greyscale)

## Goal
Convert an input Base64-encoded image string into a Greyscale image and return it as a Base64 string.

## Input Payload (JSON)
The Lambda `event` object will contain a body (which might be a JSON string or a dict, handle both). Structure:
```json
{
  "image": "base64_encoded_string_of_input_image...",
  "params": {}
}
````

## Output Payload (JSON)

You must return a JSON object (dictionary) strictly adhering to this schema:

```json
{
  "success": boolean,
  "image": "base64_encoded_string_of_output_image_or_null_if_failed",
  "execution_time_ms": float,
  "error": "error_message_string_or_null"
}
```

## Specific Logic Requirements

1.  **Timing (`execution_time_ms`):**
      - Start the timer **immediately before** you attempt to decode the input Base64 string.
      - Stop the timer **immediately after** you define the final output Base64 string.
      - This ensures we measure the cost of I/O serialization/deserialization + Image Processing.
2.  **Image Processing:**
      - Decode the base64 string to bytes.
      - Open the image using `PIL.Image`.
      - Convert the image to Greyscale (mode 'L').
      - Save the resulting image to a memory buffer (`io.BytesIO`).
      - **Critical:** To prevent payload size explosion, save the output image as **JPEG** with `quality=85` (unless the input suggests a specific need for PNG, but default to JPEG for efficiency).
      - Encode the buffer back to a Base64 string.

# Task

Generate the complete `lambda_handler(event, context)` Python code. Do not include explanations, just the code.
