import base64
import io
import json
import traceback
from time import perf_counter
from typing import Any, Dict
from PIL import Image


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    result = {
        "success": False,
        "image": "",
        "execution_time_ms": 0.0,
        "error": None,
    }

    try:
        start = perf_counter()

        image_b64 = event.get("image")
        params = event.get("params") or {}
        _ = params.get("target_depth", 8)

        if not image_b64 or not isinstance(image_b64, str):
            raise ValueError("Missing 'image'.")

        # Step 1: Decode Base64
        image_bytes = base64.b64decode(image_b64)
        img_stream = io.BytesIO(image_bytes)

        with Image.open(img_stream) as img:
            img.load()

            # *** FIX: convert to grayscale BEFORE mode "I"
            img_gray = img.convert("L")      # now guaranteed 0–255
            img_i = img_gray.convert("I")    # safe 32-bit integer

            # Step 3: Simulate 10-bit (0–255 → 0–1020)
            img_10bit = img_i.point(
                lambda p: p * 4 if isinstance(p, (int, float)) else 0
            )

            # Step 4: Gamma mapping
            gamma = 2.2
            inv_gamma = 1.0 / gamma

            img_gamma = img_10bit.point(
                lambda p, _inv=inv_gamma:
                    255.0 * ((p / 1023.0) ** _inv)
                    if isinstance(p, (int, float)) else 0
            )

            # Step 5: Downsample to 8-bit grayscale
            img_out = img_gamma.convert("L")

            # Step 6: Save JPEG
            out_buf = io.BytesIO()
            img_out.save(out_buf, format="JPEG", quality=85)
            out_bytes = out_buf.getvalue()

        # Step 7: Encode
        out_b64 = base64.b64encode(out_bytes).decode("utf-8")

        result["success"] = True
        result["image"] = out_b64
        result["execution_time_ms"] = float((perf_counter() - start) * 1000.0)

        return result

    except Exception as exc:
        result["error"] = f"{exc}\n{traceback.format_exc()}"
        return result
