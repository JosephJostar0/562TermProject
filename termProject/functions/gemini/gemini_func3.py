import json
import base64
import io
import time
import traceback
from PIL import Image

def lambda_handler(event, context):
    """
    AWS Lambda handler to perform CPU-intensive Color Depth Map simulation.
    Runtime: Python 3.14
    """
    success = False
    output_image = ""
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
            raise ValueError("Missing 'image' key in input payload.")

        # Extract params (parsing only, as logic is hardcoded per specifications)
        params = payload.get('params', {})
        if not isinstance(params, dict):
            params = {}
        target_depth = params.get('target_depth', 8)

        # 2. Start Timer (Base64 Decode -> Processing -> Base64 Encode)
        start_time = time.perf_counter()

        # 3. Processing Pipeline
        try:
            # Step 1: Base64 Decode
            input_b64 = payload['image']
            image_data = base64.b64decode(input_b64)
            
            with Image.open(io.BytesIO(image_data)) as img:
                # Step 2: Force Upscaling to Mode "I" (32-bit signed integer)
                # This ensures we don't overflow 8-bit channels during math
                work_img = img.convert("I")

                # Step 3: Simulate 10-bit Sensor Data (0-255 -> 0-1020)
                # Guard against Pillow's internal type check
                work_img = work_img.point(
                    lambda p: p * 4 if isinstance(p, (int, float)) else 0
                )

                # Step 4: CPU-Heavy Gamma Correction (Gamma = 2.2)
                # Formula: NewPixel = 255 * ((OldPixel / 1023.0) ** (1 / 2.2))
                inv_gamma = 1.0 / 2.2
                
                # We perform floating point math per pixel.
                # Must check isinstance to prevent crash when Pillow passes ImagePointTransform
                work_img = work_img.point(
                    lambda p: int(255.0 * ((p / 1023.0) ** inv_gamma)) 
                    if isinstance(p, (int, float)) else 0
                )

                # Step 5: Downsampling to Grayscale (Mode "L")
                final_img = work_img.convert("L")

                # Step 6: Save to Buffer as JPEG
                output_buffer = io.BytesIO()
                final_img.save(output_buffer, format="JPEG", quality=85)
                
                # Step 7: Base64 Encode
                output_data = output_buffer.getvalue()
                output_b64_bytes = base64.b64encode(output_data)
                output_image = output_b64_bytes.decode('utf-8')

        except Exception as process_error:
            # Capture traceback for debugging in the error field
            raise RuntimeError(f"Processing failed: {str(process_error)} | Trace: {traceback.format_exc()}")

        # 4. Stop Timer
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        success = True

    except Exception as e:
        error_message = str(e)
        success = False
        # execution_time_ms remains 0.0 or partial if failed mid-process

    # 5. Return JSON Response
    return {
        "success": success,
        "image": output_image,
        "execution_time_ms": round(execution_time_ms, 4),
        "error": error_message
    }