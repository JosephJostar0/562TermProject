import base64
import io
import time
import boto3
from botocore.exceptions import ClientError
from PIL import Image, UnidentifiedImageError

# Global S3 client to leverage execution context reuse
s3_client = boto3.client("s3")


def _guess_content_type(format_name: str) -> str:
    fmt = (format_name or "").strip().upper()
    mapping = {
        "PNG": "image/png",
        "JPG": "image/jpeg",
        "JPEG": "image/jpeg",
        "WEBP": "image/webp",
        "GIF": "image/gif",
        "TIFF": "image/tiff",
        "BMP": "image/bmp",
        "ICO": "image/x-icon",
    }
    return mapping.get(fmt, "application/octet-stream")


def _normalize_base64(b64_str: str) -> str:
    # Remove data URI prefix if present
    if "," in b64_str and b64_str.startswith("data:"):
        return b64_str.split(",", 1)[1]
    return b64_str


def lambda_handler(event, context):
    result = {
        "success": False,
        "s3_url": None,
        "execution_time_ms": 0.0,
        "error": None,
    }

    # Defaults
    params = event.get("params", {}) or {}
    target_format = (params.get("target_format") or "PNG").strip().upper()
    bucket_name = params.get("bucket_name") or "test-bucket"
    s3_key = params.get("s3_key") or "output/test.png"

    b64_image = event.get("image")
    if not b64_image:
        result["error"] = "No 'image' field in event payload"
        return result

    try:
        start = time.perf_counter()

        # Decode base64
        b64_norm = _normalize_base64(b64_image)
        try:
            image_bytes = base64.b64decode(b64_norm, validate=True)
        except Exception:
            # fallback to permissive decode (some payloads may not be strictly padded)
            image_bytes = base64.b64decode(b64_norm + "===")

        # Open image with Pillow
        buf_in = io.BytesIO(image_bytes)
        try:
            img = Image.open(buf_in)
            img.load()
        except UnidentifiedImageError as e:
            raise UnidentifiedImageError(f"Unable to identify image file: {e}")

        # Convert mode if necessary (e.g., to RGB for JPEG)
        if target_format in ("JPEG", "JPG") and img.mode in ("RGBA", "LA", "P"):
            # Convert with white background to avoid black where alpha existed
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img.convert("RGBA"),
                             mask=img.convert("RGBA").split()[-1])
            img = background
        elif target_format == "PNG" and img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode == "CMYK" and target_format in ("PNG", "JPEG", "WEBP"):
            img = img.convert("RGB")

        # Save converted image to memory buffer
        buf_out = io.BytesIO()
        save_kwargs = {}
        # For JPEG, set quality to a value to influence size (we intentionally increase processing)
        if target_format in ("JPEG", "JPG"):
            save_kwargs["quality"] = 95
            save_kwargs["optimize"] = True
            save_kwargs["progressive"] = True

        # Pillow expects format names like "PNG", "JPEG"
        try:
            img.save(buf_out, format=target_format, **save_kwargs)
        except ValueError:
            # Some user-supplied format strings might be lowercase or synonyms; try common mapping
            alt_format = {"JPG": "JPEG"}.get(target_format, target_format)
            img.save(buf_out, format=alt_format, **save_kwargs)

        buf_out.seek(0)

        # Upload to S3
        content_type = _guess_content_type(target_format)
        # Collect bytes for put_object
        body = buf_out.getvalue()

        s3_client.put_object(Bucket=bucket_name, Key=s3_key,
                             Body=body, ContentType=content_type)

        end = time.perf_counter()

        # Attempt to determine region for URL construction
        region = None
        try:
            region = s3_client.meta.region_name
        except Exception:
            region = None
        if not region:
            try:
                session = boto3.session.Session()
                region = session.region_name or "us-east-1"
            except Exception:
                region = "us-east-1"

        # Standard virtual-hosted–style URL
        if region == "us-east-1":
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        else:
            s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"

        result["success"] = True
        result["s3_url"] = s3_url
        result["execution_time_ms"] = (end - start) * 1000.0
        result["error"] = None
        return result

    except ClientError as ce:
        result["error"] = f"S3 ClientError: {str(ce)}"
        result["success"] = False
        return result
    except UnidentifiedImageError as ue:
        result["error"] = f"Image error: {str(ue)}"
        result["success"] = False
        return result
    except Exception as e:
        result["error"] = f"Unhandled error: {str(e)}"
        result["success"] = False
        return result
