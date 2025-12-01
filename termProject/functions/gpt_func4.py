import base64
import io
import json
import time
from PIL import Image


def lambda_handler(event, context):
    start = time.perf_counter()
    try:
        # Validate input
        if "image" not in event:
            raise ValueError("Missing 'image' in event")

        b64_data = event["image"]
        params = event.get("params", {})
        angle = params.get("angle", 90)

        # Decode Base64 → Image
        try:
            img_bytes = base64.b64decode(b64_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 data: {e}")

        with Image.open(io.BytesIO(img_bytes)) as img:
            # Rotate
            rotated = img.rotate(angle, expand=True)

            # Save to buffer as JPEG
            buffer = io.BytesIO()
            rotated.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

        # Encode back to Base64
        out_b64 = base64.b64encode(buffer.read()).decode("utf-8")

        end = time.perf_counter()
        return {
            "success": True,
            "image": out_b64,
            "execution_time_ms": round((end - start) * 1000, 4),
            "error": None,
        }

    except Exception as err:
        end = time.perf_counter()
        return {
            "success": False,
            "image": None,
            "execution_time_ms": round((end - start) * 1000, 4),
            "error": str(err),
        }
