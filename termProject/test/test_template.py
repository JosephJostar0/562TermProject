# COPY THIS FILE TO 'test.py' AND FILL IN YOUR CONFIG
# DO NOT COMMIT 'test.py'
import boto3
import json
import base64
import time
import argparse
from pathlib import Path

# === Configuration Section ===
# Your S3 Bucket Name
# IMPORTANT: Please fill in your actual bucket name below
BUCKET_NAME = ""  # TODO: Fill in your actual bucket name here
REGION = "us-east-2"

# Basic function name mapping
# E.g., if your function format is: deepseek_func{N}-{ARCH}
FUNC_PREFIX = "deepseek_func"

RESULT_DIR = Path("image_results")

# Initialize Boto3
lambda_client = boto3.client('lambda', region_name=REGION)

# Initialize timestamp
timestamp = int(time.time())


def encode_image(image_path):
    """Read local image and convert to Base64."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Use pathlib to read bytes directly
    return base64.b64encode(path.read_bytes()).decode('utf-8')


def save_image(base64_str, step_name, arch):
    """Save Base64 string as an image file."""
    try:
        # Clean up step name for use as filename (e.g., "Step 1 (Greyscale)" -> "step1_greyscale")
        clean_name = step_name.lower().replace(
            " ", "_").replace("(", "").replace(")", "")

        # Create directory: image_results/<timestamp>/
        # parents=True creates intermediate directories if needed (mkdir -p)
        target_dir = RESULT_DIR / str(timestamp)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Define output filename
        file_path = target_dir / f"out_{clean_name}_{arch}.jpg"

        # Write bytes directly using pathlib
        file_path.write_bytes(base64.b64decode(base64_str))
        print(f"     💾 Saved output to: {file_path}")
    except Exception as e:
        print(f"     ⚠️ Failed to save image: {e}")


def invoke_function(func_name, payload, step_name):
    """Generic Lambda invocation function."""
    print(f"  👉 Invoking {step_name} ({func_name})...")

    try:
        start_time = time.time()
        response = lambda_client.invoke(
            FunctionName=func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        end_time = time.time()

        # Parse response
        response_payload = json.loads(response['Payload'].read())
        round_trip_latency = (end_time - start_time) * 1000

        if not response_payload.get("success"):
            print(f"  ❌ Error in {step_name}: {response_payload.get('error')}")
            return None

        execution_time = response_payload.get("execution_time_ms", 0)
        print(
            f"     ✅ Success! Logic: {execution_time:.2f}ms | Round-Trip: {round_trip_latency:.2f}ms")

        return response_payload

    except Exception as e:
        print(f"  ❌ Invocation Exception: {str(e)}")
        return None


def run_pipeline(image_path, arch, save_output, mode):
    """
    Execute the test.
    mode: 'pipeline' (serial) or 'standalone' (parallel/independent)
    """
    print(
        f"\n🚀 Starting Test | Arch: [{arch.upper()}] | Mode: [{mode.upper()}]")
    print(f"📄 Input Image: {image_path}")

    # Read original image
    original_image = encode_image(image_path)

    # Initialize current_image as the original image
    current_image = original_image

    total_start = time.time()

    # Define step list to reduce code duplication
    # Note: Func 5 is handled separately
    steps = [
        {"id": 1, "name": "Step 1 (Greyscale)", "params": {}},
        {"id": 2, "name": "Step 2 (Resize)",    "params": {
            "width": 800, "height": 600}},
        {"id": 3, "name": "Step 3 (ColorDepth)", "params": {
            "target_depth": 8}},
        {"id": 4, "name": "Step 4 (Rotate)",    "params": {"angle": 90}}
    ]

    # === Execute the first 4 steps (Image Processing) ===
    for step in steps:
        func_name = f"{FUNC_PREFIX}{step['id']}-{arch}"

        # Determine input image: use previous output for pipeline mode, original for standalone mode
        payload_image = current_image if mode == 'pipeline' else original_image

        res = invoke_function(
            func_name, {"image": payload_image, "params": step['params']}, step['name'])

        if not res:
            if mode == 'pipeline':
                print("⛔ Pipeline broken due to error.")
                return
            else:
                continue  # In standalone mode, one failure doesn't affect the next step

        # If saving is required and image data is returned
        if save_output and res.get("image"):
            save_image(res['image'], step['name'], arch)

        # Only update current_image to the output of the current step in pipeline mode
        if mode == 'pipeline' and res.get("image"):
            current_image = res['image']

    # === Step 5: Upload (I/O Intensive) ===
    # This step is special; it returns a URL instead of base64 data
    f5_name = f"{FUNC_PREFIX}5-{arch}"
    output_filename = f"output/result_{arch}_{mode}_{int(time.time())}.png"

    params5 = {
        "target_format": "PNG",
        "bucket_name": BUCKET_NAME,
        "s3_key": output_filename
    }

    # Determine input source similarly
    payload_image_5 = current_image if mode == 'pipeline' else original_image

    res5 = invoke_function(
        f5_name, {"image": payload_image_5, "params": params5}, "Step 5 (Upload)")

    total_end = time.time()
    print("-" * 50)

    if res5 and res5.get("success"):
        print(f"🎉 Process Completed Successfully!")
        print(f"🌍 S3 URL: {res5.get('s3_url')}")

    if mode == 'pipeline':
        print(
            f"⏱️ Total End-to-End Latency: {(total_end - total_start):.2f} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run LLM-generated Serverless Pipeline")
    parser.add_argument("image", nargs='?',
                        default="test.jpg", help="Path to input image")
    parser.add_argument(
        "--arch", choices=['x86', 'arm'], default='x86', help="CPU architecture")

    # New arguments
    parser.add_argument("--save", action="store_true",
                        help="Save intermediate images to local disk")
    parser.add_argument("--mode", choices=['pipeline', 'standalone'], default='standalone',
                        help="pipeline: output->input chain; standalone: original image -> each function")

    args = parser.parse_args()

    run_pipeline(args.image, args.arch, args.save, args.mode)
