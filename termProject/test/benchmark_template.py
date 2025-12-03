import boto3
import json
import base64
import time
import argparse
import csv
import statistics
from pathlib import Path
from datetime import datetime

# === Configuration Area ===
# Default configuration, can be overridden by command line arguments
# TODO: Teammates should update this default value with the actual bucket name
DEFAULT_BUCKET = ""
REGION = "us-east-2"

# Initialize Boto3
lambda_client = boto3.client('lambda', region_name=REGION)


def encode_image(image_path):
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Use pathlib to read bytes directly
    return base64.b64encode(path.read_bytes()).decode('utf-8')


def invoke_function(func_name, payload):
    """
    Invoke Lambda and return detailed performance metrics
    """
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
            return {
                "success": False,
                "error": response_payload.get("error", "Unknown Error"),
                "latency": round_trip_latency,
                "logic_time": 0
            }

        return {
            "success": True,
            "error": None,
            "latency": round_trip_latency,  # Client-side latency
            # Server-side logic time
            "logic_time": response_payload.get("execution_time_ms", 0),
            "payload": response_payload  # Return full data to extract output image or url
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "latency": 0,
            "logic_time": 0
        }


def run_benchmark(args):
    print(
        f"\n🚀 Starting Benchmark for Model: [{args.model.upper()}] | Arch: [{args.arch.upper()}]")
    print(f"🔄 Runs: {args.runs} | Warmup: {args.warmup} | Mode: {args.mode}")

    # Construct function name prefix (Naming convention: gpt_func1-x86, gemini_func1-arm, etc.)
    # Note: Assumes teammates also follow the {model}_func{N}-{arch} naming convention
    func_prefix = f"{args.model}_func"

    original_image = encode_image(args.image)

    # Prepare CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"results_{args.model}_{args.arch}_{timestamp}.csv"

    # CSV Header
    fieldnames = ['Run_ID', 'Type', 'Step', 'Function_Name',
                  'Logic_Time_ms', 'Round_Trip_ms', 'Success', 'Error']

    # Store data for final statistics
    stats_data = {
        "pipeline_total": [],
        "steps": {1: [], 2: [], 3: [], 4: [], 5: []}
    }

    # Using standard open() for CSV writing is fine, but we could also use Path(csv_filename).open(...)
    with open(csv_filename, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        total_iterations = args.warmup + args.runs

        for i in range(1, total_iterations + 1):
            is_warmup = i <= args.warmup
            run_type = "WARMUP" if is_warmup else "BENCHMARK"
            run_display_id = f"{i}/{total_iterations}"

            print(f"Running {run_type} [{run_display_id}]...", end='\r')

            # Initialize state
            current_image = original_image
            run_failed = False
            step_metrics = {}
            pipeline_start_time = time.time()

            # Define steps
            steps = [
                {"id": 1, "name": "Greyscale", "params": {}},
                {"id": 2, "name": "Resize",    "params": {
                    "width": 800, "height": 600}},
                {"id": 3, "name": "ColorDepth", "params": {"target_depth": 8}},
                {"id": 4, "name": "Rotate",    "params": {"angle": 90}},
                {"id": 5, "name": "Upload",    "params": {
                    "target_format": "PNG",
                    "bucket_name": args.bucket,
                    "s3_key": f"output/{args.model}_{args.arch}_{timestamp}_{i}.png"
                }}
            ]

            for step in steps:
                f_name = f"{func_prefix}{step['id']}-{args.arch}"

                # Mode logic
                payload_image = current_image if args.mode == 'pipeline' else original_image

                result = invoke_function(
                    f_name, {"image": payload_image, "params": step['params']})

                # Record data (Write to CSV)
                if not is_warmup:
                    writer.writerow({
                        'Run_ID': i - args.warmup,
                        'Type': run_type,
                        'Step': f"Step {step['id']} ({step['name']})",
                        'Function_Name': f_name,
                        'Logic_Time_ms': result['logic_time'],
                        'Round_Trip_ms': result['latency'],
                        'Success': result['success'],
                        'Error': result['error']
                    })

                if not result['success']:
                    run_failed = True
                    break  # Pipeline broken

                # Collect statistics (Non-Warmup only)
                if not is_warmup:
                    stats_data['steps'][step['id']].append(
                        result['logic_time'])

                # Pass data to the next step
                if args.mode == 'pipeline' and result['payload'].get('image'):
                    current_image = result['payload']['image']

            # Record Pipeline Total Time (Client Side)
            if not run_failed and not is_warmup and args.mode == 'pipeline':
                total_pipeline_time = (
                    time.time() - pipeline_start_time) * 1000
                stats_data['pipeline_total'].append(total_pipeline_time)
                # Write a summary row
                writer.writerow({
                    'Run_ID': i - args.warmup,
                    'Type': 'SUMMARY',
                    'Step': 'Pipeline_Total',
                    'Function_Name': 'ALL',
                    # Simply accumulate logic time
                    'Logic_Time_ms': sum(stats_data['steps'][s][-1] for s in range(1, 6)),
                    'Round_Trip_ms': total_pipeline_time,
                    'Success': True,
                    'Error': None
                })

    print(f"\n\n✅ Benchmark Complete. Data saved to: {csv_filename}")
    print_statistics(stats_data, args.mode)


def print_statistics(data, mode):
    print("\n" + "="*50)
    print("📊 PERFORMANCE REPORT")
    print("="*50)

    def calc_stats(values):
        if not values:
            return 0, 0, 0
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        cv = (stdev / mean) if mean > 0 else 0
        return mean, stdev, cv

    # 1. Pipeline Total Stats
    if mode == 'pipeline' and data['pipeline_total']:
        mean, sd, cv = calc_stats(data['pipeline_total'])
        print(f"\n🌍 End-to-End Pipeline Latency (Client-side):")
        print(f"   Avg: {mean:.2f} ms")
        print(f"   Std Dev: {sd:.2f} ms")
        print(f"   CV: {cv:.4f}")

    # 2. Per Function Stats (Logic Time)
    print(f"\n⚡ Per-Function Logic Execution Time (Server-side):")
    print(f"{'Step':<20} | {'Avg (ms)':<10} | {'StdDev':<10} | {'CV':<10}")
    print("-" * 60)

    for step_id in range(1, 6):
        values = data['steps'][step_id]
        if values:
            mean, sd, cv = calc_stats(values)
            step_name = f"Step {step_id}"
            print(f"{step_name:<20} | {mean:<10.2f} | {sd:<10.2f} | {cv:<10.4f}")

    print("="*50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TCSS 562 Benchmark Runner")

    # Core arguments
    parser.add_argument("--image", default="test.jpg", help="Input image path")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET,
                        help="S3 Bucket name")

    # Experiment variable arguments
    parser.add_argument("--model", required=True, choices=[
                        'gpt', 'gemini', 'deepseek'], default='gpt', help="Model name (used for function prefix)")
    parser.add_argument(
        "--arch", choices=['x86', 'arm'], default='x86', help="Architecture")
    parser.add_argument(
        "--mode", choices=['pipeline', 'standalone'], default='pipeline', help="Execution mode")

    # Statistics arguments
    parser.add_argument("--runs", type=int, default=10,
                        help="Number of benchmark runs (excluding warmup)")
    parser.add_argument("--warmup", type=int, default=2,
                        help="Number of warmup runs")

    args = parser.parse_args()

    run_benchmark(args)
