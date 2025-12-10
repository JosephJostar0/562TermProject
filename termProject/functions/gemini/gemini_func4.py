import json
import base64
import io
import time
from PIL import Image

def lambda_handler(event, context):
    """
    AWS Lambda handler to rotate a Base64 encoded image.
    Runtime: Python 3.14
    """
    success = False
    output_image = None
    execution_time_ms = 0.0
    error_message = None

    try:
        # 1. Parse Input Payload
        payload = event
        if 'body' in event:
            if isinstance(event['body'], str):
                try:
                    payload = json.loads(event['body'])
                except json.JSONDecodeError:
                    raise ValueError("Event body is not valid JSON.")
            else:
                payload = event['body']

        if not payload or 'image' not in payload:
            raise ValueError("Missing 'image' key in payload.")

        # 2. Extract Parameters (Default angle: 90)
        params = payload.get('params', {})
        if not isinstance(params, dict):
            params = {}
            
        try:
            angle = float(params.get('angle', 90))
        except (ValueError, TypeError):
            angle = 90.0

        # 3. Start Timer (Decode -> Rotate -> Encode)
        start_time = time.perf_counter()

        # 4. Processing
        try:
            # Decode
            input_b64 = payload['image']
            image_data = base64.b64decode(input_b64)
            
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB to ensure compatibility with JPEG (removes Alpha/transparency)
                # We do this before rotation or saving to prevent "cannot write mode RGBA as JPEG" errors.
                # Note: Default fill color for rotation on RGB images is black (0, 0, 0).
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Rotate with expand=True to resize canvas and prevent cropping
                rotated_img = img.rotate(angle, expand=True)

                # Save to Buffer
                output_buffer = io.BytesIO()
                rotated_img.save(output_buffer, format="JPEG", quality=85)
                
                # Encode
                output_data = output_buffer.getvalue()
                output_b64_bytes = base64.b64encode(output_data)
                output_image = output_b64_bytes.decode('utf-8')

        except Exception as process_err:
            raise RuntimeError(f"Image processing failed: {str(process_err)}")

        # 5. Stop Timer
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        success = True

    except Exception as e:
        error_message = str(e)
        success = False

    # 6. Return Response
    return {
        "success": success,
        "image": output_image,
        "execution_time_ms": round(execution_time_ms, 4),
        "error": error_message
    }