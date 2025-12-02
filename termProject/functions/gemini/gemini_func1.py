import json
import base64
import io
import time
from PIL import Image

def lambda_handler(event, context):
    """
    AWS Lambda handler to convert a Base64 encoded image to Greyscale.
    Runtime: Python 3.14
    """
    # Initialize response variables
    success = False
    output_image = None
    execution_time_ms = 0.0
    error_message = None

    try:
        # 1. Parse Input Payload
        # Handle cases where event is from API Gateway (has 'body') or direct invocation
        payload = event
        if 'body' in event:
            if isinstance(event['body'], str):
                try:
                    payload = json.loads(event['body'])
                except json.JSONDecodeError:
                    raise ValueError("Event body is not valid JSON.")
            else:
                payload = event['body']
        
        # Validate 'image' key existence
        if not payload or 'image' not in payload:
            raise ValueError("Missing 'image' key in input payload.")

        input_b64 = payload['image']
        
        # 2. Start Timer (Immediately before decoding)
        start_time = time.perf_counter()

        # 3. Image Processing
        try:
            # Decode Base64 string to bytes
            image_data = base64.b64decode(input_b64)
            
            # Open image from bytes
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to Greyscale (Mode 'L')
                grey_img = img.convert('L')
                
                # Save to buffer as JPEG with quality 85 to optimize size
                output_buffer = io.BytesIO()
                grey_img.save(output_buffer, format="JPEG", quality=85)
                
                # Encode result back to Base64
                output_data = output_buffer.getvalue()
                output_b64_bytes = base64.b64encode(output_data)
                
                # Convert bytes to string for JSON response
                output_image = output_b64_bytes.decode('utf-8')

        except Exception as process_error:
            # Re-raise specific processing errors to be caught by the outer block
            raise RuntimeError(f"Image processing failed: {str(process_error)}")

        # 4. Stop Timer (Immediately after encoding)
        end_time = time.perf_counter()
        
        # Calculate execution time in milliseconds
        execution_time_ms = (end_time - start_time) * 1000
        success = True

    except Exception as e:
        # Global Exception Handler to ensure the function never crashes
        error_message = str(e)
        success = False
        # execution_time_ms remains 0.0 or whatever was calculated if failure occurred after timing started (unlikely here due to flow)

    # 5. Return JSON Response
    return {
        "success": success,
        "image": output_image,
        "execution_time_ms": round(execution_time_ms, 4),
        "error": error_message
    }