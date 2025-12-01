import base64
import io
import time
import traceback
from typing import Any, Dict
from PIL import Image
import math


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for Color Depth Map (Gamma Correction + simulated 10-bit tone mapping
    + optional color depth reduction). Returns base64 JPEG data and execution timing.
    """
    start_time = None
    try:
        # Validate input
        if not isinstance(event, dict):
            raise ValueError("Event must be a JSON object.")

        img_b64 = event.get("image")
        if not img_b64 or not isinstance(img_b64, str):
            raise ValueError(
                "Missing or invalid 'image' field (expected base64 string).")

        params = event.get("params", {}) or {}
        target_depth = params.get("target_depth", 8)
        try:
            target_depth = int(target_depth)
        except Exception:
            target_depth = 8

        # Clamp sensible range for target depth
        if target_depth < 1:
            target_depth = 1
        if target_depth > 8:
            target_depth = 8

        # Start timing exactly at decode step as specified
        start_time = time.perf_counter()

        # 1) Base64 Decode
        img_bytes = base64.b64decode(img_b64)

        # Load image
        buf = io.BytesIO(img_bytes)
        with Image.open(buf) as img:
            # Ensure in RGB
            img = img.convert("RGB")

            # --- Math Heavy Processing: Generate Gamma Lookup Table using pow() in a loop ---
            # Simulated 10-bit tone mapping + gamma correction (Gamma = 2.2)
            gamma = 2.2
            gamma_inv = 1.0 / gamma

            # Build gamma -> 10-bit -> back to 8-bit table
            gamma_table = []
            for i in range(256):
                # Normalize to [0,1]
                normalized = i / 255.0

                # Apply gamma correction using pow (forcing floating point heavy work)
                corrected = math.pow(normalized, gamma_inv)

                # Simulate 10-bit tone map quantization (0..1023)
                ten_bit = round(corrected * 1023.0) / 1023.0

                # Map back to 8-bit range
                mapped = ten_bit * 255.0

                # Clamp and round
                v = int(round(mapped))
                if v < 0:
                    v = 0
                elif v > 255:
                    v = 255

                gamma_table.append(v)

            # Apply gamma table to image (applied per channel)
            img = img.point(gamma_table)

            # --- Color Depth Reduction (if target_depth < 8) ---
            if target_depth < 8:
                levels = (1 << target_depth)
                if levels <= 1:
                    # All black (degenerate)
                    reduction_table = [0] * 256
                else:
                    reduction_table = []
                    for i in range(256):
                        # heavy math operations to compute quantization mapping
                        normalized = i / 255.0
                        # map to [0, levels-1], round to nearest level, then map back
                        level_index = float(normalized) * (levels - 1)
                        level_index = math.floor(level_index + 0.5)  # round
                        quant = level_index / float(levels - 1)
                        mapped = quant * 255.0
                        v = int(round(mapped))
                        if v < 0:
                            v = 0
                        elif v > 255:
                            v = 255
                        reduction_table.append(v)

                # Apply reduction table
                img = img.point(reduction_table)

            # Save to JPEG buffer with required quality
            out_buf = io.BytesIO()
            # Use optimize=True to keep output size reasonable; Pillow handles format
            img.save(out_buf, format="JPEG", quality=85, optimize=True)
            out_bytes = out_buf.getvalue()

        # 3) Base64 Encode
        out_b64 = base64.b64encode(out_bytes).decode("utf-8")

        end_time = time.perf_counter()
        exec_ms = (end_time - start_time) * 1000.0

        return {
            "success": True,
            "image": out_b64,
            "execution_time_ms": float(exec_ms),
            "error": None,
        }

    except Exception as e:
        # If timing started, measure time until exception for diagnostic value
        exec_ms = None
        try:
            if start_time is not None:
                exec_ms = (time.perf_counter() - start_time) * 1000.0
        except Exception:
            exec_ms = None

        tb = traceback.format_exc()
        error_msg = f"{str(e)}; traceback: {tb}"

        response = {
            "success": False,
            "image": None,
            "execution_time_ms": float(exec_ms) if exec_ms is not None else 0.0,
            "error": error_msg,
        }
        return response
