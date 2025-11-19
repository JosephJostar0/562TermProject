# TCSS 562 Term Project: Lambda Function Interface Specifications (API Contract)
### Last Updated: 2025-11-18
### Status: Frozen / Confirmed

## 1. Global Conventions
- **Protocol:** JSON for all Inputs (Events) and Outputs.
- **Image Encoding:** All image data MUST be Base64 encoded strings (UTF-8).
- **Error Handling:** Functions must NOT crash. Catch all exceptions and return `success: false`.
- **Telemetry:** `execution_time_ms` measures purely the logic duration (excluding cold start/runtime init overhead).

## 2. Function Definitions

### Function 1: Greyscale
- **Goal:** Convert input image to greyscale.
- **Input:**
  ```json
  {
    "image": "base64_string...",
    "params": {}
  }
    ```

- **Output:**
    ```json
    {
      "success": true,
      "image": "base64_string...",
      "execution_time_ms": float,
      "error": string or null
    }
    ```

### Function 2: Resize

  - **Goal:** Resize image to fixed resolution (Target: 800x600).
  - **Input:**
    ```json
    {
      "image": "base64_string...",
      "params": { "width": 800, "height": 600 }
    }
    ```
  - **Output:**
    ```json
    {
      "success": true,
      "image": "base64_string...",
      "execution_time_ms": float,
      "error": string or null
    }
    ```

### Function 3: Color Depth Map (CPU Intensive)

  - **Goal:** Perform CPU-heavy bit-depth reduction (e.g., 10-bit to 8-bit mapping).
  - **Input:**
    ```json
    {
      "image": "base64_string...",
      "params": { "target_depth": 8 }
    }
    ```
  - **Output:**
    ```json
    {
      "success": true,
      "image": "base64_string...",
      "execution_time_ms": float,
      "error": string or null
    }
    ```

### Function 4: Rotate

  - **Goal:** Rotate image by N degrees.
  - **Input:**
    ```json
    {
      "image": "base64_string...",
      "params": { "angle": 90 }
    }
    ```
  - **Output:**
    ```json
    {
      "success": true,
      "image": "base64_string...",
      "execution_time_ms": float,
      "error": string or null
    }
    ```

### Function 5: Format Convert & Upload (I/O Intensive)

  - **Goal:** Convert format (e.g., to PNG) and upload to S3.
  - **Input:**
    ```json
    {
      "image": "base64_string...",
      "params": {
        "target_format": "PNG",
        "bucket_name": "your-s3-bucket-name",
        "s3_key": "output/filename.png"
      }
    }
    ```
  - **Output:**
    ```json
    {
      "success": true,
      "s3_url": "https://...",
      "execution_time_ms": float,
      "error": string or null
    }
    ```

<!-- end list -->
