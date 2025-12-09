import json
import base64
import io
import time
import boto3
from botocore.exceptions import ClientError
from PIL import Image

# Global S3 client initialization
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    try:
        # Parse input event
        if isinstance(event, str):
            event = json.loads(event)

        image_b64 = event.get('image', '')
        params = event.get('params', {})

        if not image_b64:
            return {"success": False, "s3_url": "", "execution_time_ms": 0.0, "error": "Missing 'image' in input"}

        # Get parameters with defaults
        target_format = params.get('target_format', 'PNG').upper()
        bucket_name = params.get('bucket_name', 'test-bucket')
        s3_key = params.get('s3_key', 'output/test.png')

        # Content type mapping
        content_types = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'GIF': 'image/gif',
            'BMP': 'image/bmp'
        }
        content_type = content_types.get(target_format, f'image/{target_format.lower()}')

        # Start timing
        start_time = time.perf_counter()

        # Decode base64
        image_bytes = base64.b64decode(image_b64)

        # Process image
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Handle transparency for PNG
            if target_format == 'PNG' and img.mode in ('RGBA', 'LA'):
                background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                background.paste(img, img.split()[-1])
                img = background

            # Save to buffer in target format
            buffer = io.BytesIO()
            img.save(buffer, format=target_format)
            buffer.seek(0)

        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=buffer,
            ContentType=content_type
        )

        # Construct S3 URL
        region = s3_client.meta.region_name
        s3_url = f"https://s3.{region}.amazonaws.com/{bucket_name}/{s3_key}"

        # Calculate execution time
        execution_time = (time.perf_counter() - start_time) * 1000

        return {
            "success": True,
            "s3_url": s3_url,
            "execution_time_ms": round(execution_time, 2),
            "error": None
        }

    except ClientError as e:
        return {
            "success": False,
            "s3_url": "",
            "execution_time_ms": 0.0,
            "error": f"S3 Error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "s3_url": "",
            "execution_time_ms": 0.0,
            "error": str(e)
        }