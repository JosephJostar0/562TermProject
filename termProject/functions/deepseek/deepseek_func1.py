import json
import base64
import io
import time
from PIL import Image


def lambda_handler(event, context):
    try:
        # Parse event body
        if isinstance(event, str):
            event = json.loads(event)

        image_b64 = event.get('image', '')
        if not image_b64:
            return {"success": False, "image": "", "execution_time_ms": 0.0, "error": "Missing 'image' in input"}

        # Start timing
        start_time = time.perf_counter()

        # Decode base64
        image_bytes = base64.b64decode(image_b64)

        # Open and process image
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert to greyscale
            grey_img = img.convert('L')

            # Save to buffer
            buffer = io.BytesIO()
            grey_img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # Encode to base64
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
            "error": str(e)
        }