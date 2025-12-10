import json
import base64
import io
import time
from PIL import Image

def lambda_handler(event, context):
    """
    AWS Lambda handler to resize a Base64 encoded image.
    Runtime: Python 3.14
    """
    success = False
    output_image = None
    execution_time_ms = 0.0
    error_message = None

    try:
        # 1. Parse Input Payload
        # Handle API Gateway (string body) vs Direct Invocation (dict body)
        payload = event
        if 'body' in event:
            if isinstance(event['body'], str):
                try:
                    payload = json.loads(event['body'])
                except json.JSONDecodeError:
                    raise ValueError("Event body is not valid JSON.")
            else:
                payload = event['body']

        if 'image' not in payload:
            raise ValueError("Missing 'image' key in payload.")

        # 2. Extract Parameters (Defaults: 800x600)
        params = payload.get('params', {})
        # Ensure params is a dict, otherwise fallback to empty dict
        if not isinstance(params, dict):
            params = {}
            
        try:
            target_width = int(params.get('width', 800))
            target_height = int(params.get('height', 600))
        except (ValueError, TypeError):
            # Fallback to defaults if non-integers provided
            target_width = 800
            target_height = 600

        # 3. Start Timer (Covers Decode -> Resize -> Encode)
        start_time = time.perf_counter()

        # 4. Processing
        try:
            # Decode
            image_data = base64.b64decode(payload['image'])
            
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB to ensure compatibility with JPEG (removes Alpha channel if present)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGB')

                # Resize using modern PIL syntax (LANCZOS)
                resized_img = img.resize(
                    (target_width, target_height), 
                    resample=Image.Resampling.LANCZOS
                )

                # Save to Buffer
                output_buffer = io.BytesIO()
                resized_img.save(output_buffer, format="JPEG", quality=85)
                
                # Encode
                output_b64_bytes = base64.b64encode(output_buffer.getvalue())
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