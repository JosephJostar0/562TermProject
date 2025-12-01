# Context

You are an expert Serverless Cloud Architect and Python Developer. Your task is to write a highly optimized AWS Lambda function handler in **Python 3.14**.

# Constraint Checklist & Confidence Score

1. Use the `Pillow` (PIL) library.
2. **CPU Intensity:** The logic MUST perform mathematical calculations to simulate high-quality image processing (e.g., Tone Mapping / Gamma Correction) on **high bit-depth data**. All math must be floating-point and executed per-pixel.
3. **Robustness:** Catch all exceptions. Return `"success": false` on failure.
4. **Performance:** The goal is to benchmark CPU processing power (Floating Point Operations).
5. **CRITICAL FIX:** Every `.point(lambda p: ...)` lambda **MUST first check** whether `p` is an `int` or `float`. Pillow will call the lambda once with an `ImagePointTransform` object to test linearity, and this must not crash.

# Function Specifications (Function 3: Color Depth Map)

## Goal

Perform a CPU-intensive "Color Depth Reduction" simulation. To ensure high CPU usage and robustness against Pillow’s `.point()` evaluation behavior, the function must:

* Force-convert the image to a high-precision mode,
* Simulate 10-bit data,
* Apply heavy floating-point gamma correction,
* **Ensure all lambda functions in `.point()` are type-safe**.

## Input Payload (JSON)

```json
{
  "image": "base64_encoded_string...",
  "params": { "target_depth": 8 }
}
```

*If `target_depth` is missing, default to 8.*

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

### 1. Timing

Measure: **Base64 Decode → Math-Heavy Processing → Base64 Encode**
Return total duration as `execution_time_ms`.

---

### 2. Processing Pipeline (Strict Order)

#### **Step 1 — Base64 Decode**

Decode Base64 string → bytes → `PIL.Image`.

#### **Step 2 — Force Upscaling**

Convert image to **Mode `"I"`** (32-bit signed integer pixels).
This is required to allow values >255 and avoid LUT overflow.

#### **Step 3 — Simulate 10-bit Sensor Data**

Multiply each pixel by `4` (`0–255 → 0–1020`).
Use:

```
img.point(lambda p: p * 4 if isinstance(p, (int, float)) else 0)
```

The `isinstance` check is *mandatory* to avoid Pillow calling the lambda with `ImagePointTransform` and causing TypeError.

#### **Step 4 — CPU-Heavy Gamma Correction (Gamma = 2.2)**

Formula:

```
NewPixel = 255 * ((OldPixel / 1023.0) ** (1 / 2.2))
```

Implement using `.point(lambda p: ...)` with floating-point math.
The lambda must **also** check input type:

```
lambda p: 255.0 * ((p / 1023.0) ** inv_gamma)
          if isinstance(p, (int, float)) else 0
```

This forces per-pixel floating-point operations and avoids the Pillow evaluation crash.

#### **Step 5 — Downsampling**

Convert processed image to **mode `"L"`** (8-bit grayscale) or `"RGB"`.
Use `"L"` for deterministic JPEG output.

#### **Step 6 — Save to Buffer**

Save as **JPEG**, `quality=85`.

#### **Step 7 — Base64 Encode**

Encode JPEG bytes → Base64 string.

---

## Error Handling

* Wrap entire processing logic in `try/except`.
* On failure, return:

  ```json
  {
    "success": false,
    "image": "",
    "execution_time_ms": 0.0,
    "error": "error_message + traceback"
  }
  ```

---

## Task

Generate the complete `lambda_handler(event, context)` Python function code.
Do **not** include explanations — output **only** the code.
