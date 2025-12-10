import json
import base64
import io
import time
from PIL import Image, ImageResampling


def lambda_handler(event, context):
    try:
        # Parse input event
        if isinstance(event, str):
            event = json.loads(event)

        image_b64 = event.get('image', '')
        params = event.get('params', {})

        if not image_b64:
            return {"success": False, "image": "", "execution_time_ms": 0.0, "error": "Missing 'image' in input"}

        # Get dimensions with defaults
        width = int(params.get('width', 800))
        height = int(params.get('height', 600))

        # Start timing
        start_time = time.perf_counter()

        # Decode base64
        image_bytes = base64.b64decode(image_b64)

        # Process image
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Resize with high quality
            resized_img = img.resize((width, height), resample=ImageResampling.LANCZOS)

            # Save to buffer
            buffer = io.BytesIO()
            resized_img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # Encode result
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