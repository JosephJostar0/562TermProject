import json
import base64
import io
import time
import boto3
from PIL import Image
from botocore.exceptions import ClientError

# Global initialization to leverage execution context reuse (optimization)
try:
    s3_client = boto3.client('s3')
except Exception as e:
    # If client fails to initialize, the handler will catch the error when trying to use it
    s3_client = None

def lambda_handler(event, context):
    """
    AWS Lambda handler to convert image format and upload to S3.
    Runtime: Python 3.14
    """
    success = False
    s3_url = None
    execution_time_ms = 0.0
    error_message = None

    # Default Parameters
    DEFAULT_FORMAT = "PNG"
    DEFAULT_BUCKET = "test-bucket"
    DEFAULT_KEY = "output/test.png"

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

        # Extract Parameters
        params = payload.get('params', {})
        if not isinstance(params, dict):
            params = {}

        target_format = params.get('target_format', DEFAULT_FORMAT).upper()
        bucket_name = params.get('bucket_name', DEFAULT_BUCKET)
        s3_key = params.get('s3_key', DEFAULT_KEY)

        # Validate S3 Client availability
        if s3_client is None:
            raise RuntimeError("AWS S3 Client failed to initialize globally.")

        # 2. Start Timer (Decode -> Convert -> Upload)
        start_time = time.perf_counter()

        try:
            # 3. Image Processing (Format Conversion)
            input_b64 = payload['image']
            image_data = base64.b64decode(input_b64)
            
            with Image.open(io.BytesIO(image_data)) as img:
                # Handle Alpha channel for JPEG (convert to RGB if needed)
                if target_format in ['JPEG', 'JPG'] and img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                output_buffer = io.BytesIO()
                img.save(output_buffer, format=target_format)
                output_buffer.seek(0) # Rewind buffer for reading
                
                # Determine Content-Type
                content_type = f"image/{target_format.lower()}"
                if target_format == 'JPG': 
                    content_type = 'image/jpeg'

                # 4. S3 Upload (I/O Intensive)
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=output_buffer,
                    ContentType=content_type
                )
                
                # Construct S3 URL
                # Attempt to get region, default to us-east-1 if not configured in session
                region = s3_client.meta.region_name or 'us-east-1'
                s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"

        except ClientError as s3_err:
            raise RuntimeError(f"S3 Upload Error: {str(s3_err)}")
        except Exception as process_err:
            raise RuntimeError(f"Processing Error: {str(process_err)}")

        # 5. Stop Timer
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        success = True

    except Exception as e:
        error_message = str(e)
        success = False
        # execution_time_ms remains 0.0 or partial

    # 6. Return JSON Response
    return {
        "success": success,
        "s3_url": s3_url,
        "execution_time_ms": round(execution_time_ms, 4),
        "error": error_message
    }