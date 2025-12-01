import base64
import time
import io
from PIL import Image, UnidentifiedImageError


def lambda_handler(event, context):
    start_time = time.time()

    try:
        # Extract base64 image
        img_b64 = event.get("image")
        if not img_b64 or not isinstance(img_b64, str):
            raise ValueError("Invalid or missing 'image' field.")

        # Parse params
        params = event.get("params", {})
        width = params.get("width", 800)
        height = params.get("height", 600)

        # Validate width/height
        if not isinstance(width, int) or width <= 0:
            width = 800
        if not isinstance(height, int) or height <= 0:
            height = 600

        # Decode base64
        try:
            img_bytes = base64.b64decode(img_b64)
        except Exception:
            raise ValueError("Base64 decode failed.")

        # Load image
        try:
            with Image.open(io.BytesIO(img_bytes)) as img:
                img = img.convert("RGB")
        except UnidentifiedImageError:
            raise ValueError("Unsupported or corrupted image format.")

        # Resize
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)

        # Encode to JPEG
        output_buffer = io.BytesIO()
        img_resized.save(output_buffer, format="JPEG", quality=85)
        output_b64 = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

        exec_time = (time.time() - start_time) * 1000.0

        return {
            "success": True,
            "image": output_b64,
            "execution_time_ms": exec_time,
            "error": None
        }

    except Exception as e:
        exec_time = (time.time() - start_time) * 1000.0
        return {
            "success": False,
            "image": None,
            "execution_time_ms": exec_time,
            "error": str(e)
        }
