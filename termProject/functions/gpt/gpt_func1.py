import json
import base64
import io
import time
from PIL import Image, UnidentifiedImageError


def lambda_handler(event, context):
    """
    AWS Lambda handler - Greyscale converter.
    Returns:
      {
        "success": bool,
        "image": base64_string_or_null,
        "execution_time_ms": float,
        "error": error_message_or_null
      }
    """
    # Default response parts
    output_b64 = None
    error_msg = None

    # Parse body (may be JSON string or dict)
    try:
        # event might already be the dict with image
        body = event.get("body", event)
        if isinstance(body, str):
            try:
                parsed = json.loads(body)
            except Exception:
                # If body is a plain string but not JSON, treat as error
                parsed = {"image": body}
        elif isinstance(body, dict):
            parsed = body
        else:
            # Unexpected body type
            parsed = {"image": None}

        b64_input = parsed.get("image")
        # Accept params if needed in future
        params = parsed.get("params", {}) if isinstance(parsed, dict) else {}
    except Exception as e:
        # If parsing fails, no timer was started yet per spec
        return {
            "success": False,
            "image": None,
            "execution_time_ms": 0.0,
            "error": f"Failed to parse event body: {e!s}"
        }

    # Validate presence of image
    if not b64_input:
        return {
            "success": False,
            "image": None,
            "execution_time_ms": 0.0,
            "error": "Missing 'image' field in request body."
        }

    # If image is bytes, convert to str
    if isinstance(b64_input, (bytes, bytearray)):
        try:
            b64_input = b64_input.decode("ascii")
        except Exception:
            # We'll still attempt to base64 decode below; but ensure string
            b64_input = base64.b64encode(bytes(b64_input)).decode("ascii")

    # Remove possible data URI prefix (e.g., "data:image/png;base64,....")
    if isinstance(b64_input, str) and b64_input.startswith("data:"):
        try:
            b64_input = b64_input.split(",", 1)[1]
        except Exception:
            # leave as-is; base64 decoder will likely fail and be handled below
            pass

    # Start timer immediately before attempting to decode input Base64 string.
    start_ts = time.time()

    try:
        # Decode base64 (validate=True ensures bad padding raises)
        try:
            decoded_bytes = base64.b64decode(b64_input, validate=True)
        except Exception:
            # fallback: try lenient decode (some clients omit padding)
            decoded_bytes = base64.b64decode(b64_input + "===")

        # Open image with PIL
        try:
            img = Image.open(io.BytesIO(decoded_bytes))
            img.load()  # ensure image is fully loaded into memory
        except UnidentifiedImageError as e:
            raise ValueError(
                "Decoded data is not a valid image or unsupported image format.") from e

        # Determine if source suggests PNG (alpha/transparency)
        bands = img.getbands() if hasattr(img, "getbands") else ()
        has_alpha = ("A" in bands) or (img.mode in ("RGBA", "LA")) or (
            "transparency" in getattr(img, "info", {}))

        # Convert to greyscale
        if has_alpha:
            # Preserve alpha channel: produce 'LA' (L + Alpha) and save as PNG
            gray = img.convert("L")
            # Obtain alpha channel robustly
            try:
                alpha = img.convert("RGBA").split()[-1]
            except Exception:
                # Fallback: create fully opaque alpha if extraction fails
                alpha = Image.new("L", img.size, 255)
            out_img = Image.merge("LA", (gray, alpha))
            save_format = "PNG"
            save_kwargs = {"optimize": True}
        else:
            # No alpha: convert to single-channel L and save as JPEG
            out_img = img.convert("L")
            save_format = "JPEG"
            save_kwargs = {"quality": 85, "optimize": True}

        # Save processed image to buffer
        buffer = io.BytesIO()
        # For JPEG, ensure mode is acceptable (L is okay); for PNG LA is okay
        out_img.save(buffer, format=save_format, **save_kwargs)
        buffer.seek(0)
        result_bytes = buffer.read()

        # Encode buffer back to Base64 string
        output_b64 = base64.b64encode(result_bytes).decode("ascii")

    except Exception as exc:
        # Capture exception message, but ensure timer still stops after we "define" final output (we set output_b64 to None)
        error_msg = str(exc)
        output_b64 = None
    finally:
        end_ts = time.time()
        execution_time_ms = (end_ts - start_ts) * 1000.0

    # Build final response strictly following schema
    success = output_b64 is not None
    response = {
        "success": success,
        "image": output_b64 if success else None,
        "execution_time_ms": float(execution_time_ms),
        "error": None if success else (error_msg or "Unknown error")
    }

    return response
