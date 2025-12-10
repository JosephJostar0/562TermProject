import json
import base64
import io
import time
import traceback
from PIL import Image


def lambda_handler(event, context):
    try:
        # Parse input
        if isinstance(event, str):
            event = json.loads(event)

        image_b64 = event.get('image', '')
        params = event.get('params', {})
        target_depth = params.get('target_depth', 8)  # Default per specs

        if not image_b64:
            return {"success": False, "image": "", "execution_time_ms": 0.0, "error": "Missing 'image' in input"}

        # Start timing
        start_time = time.perf_counter()

        # Step 1: Decode base64
        image_bytes = base64.b64decode(image_b64)

        # Step 2: Open image and convert to mode "I"
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert('I')  # 32-bit signed integer mode

            # Step 3: Simulate 10-bit data (multiply by 4)
            img = img.point(lambda p: p * 4 if isinstance(p, (int, float)) else 0)

            # Step 4: Gamma correction (gamma = 2.2)
            inv_gamma = 1.0 / 2.2
            img = img.point(lambda p: 255.0 * ((p / 1023.0) ** inv_gamma) if isinstance(p, (int, float)) else 0)

            # Step 5: Downsample to 8-bit grayscale
            img = img.convert('L')

            # Step 6: Save to buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # Step 7: Encode to base64
            result_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Calculate execution time
        execution_time = (time.perf_counter() - start_time) * 1000

        return {
            "success": True,
            "image": result_b64,
            "execution_time_ms": round(execution_time, 2),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "image": "",
            "execution_time_ms": 0.0,
            "error": f"{str(e)}\n{traceback.format_exc()}"
        }