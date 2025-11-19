# TCSS 562 Term Project: System Architecture Specification
### Last Updated: 2025-11-18
### Status: Confirmed

## 1. High-Level Overview
- **Goal:** Benchmark LLM-generated code quality across CPU/IO tasks and Architectures.
- **Platform:** AWS Lambda (FaaS).
- **Runtime:** Python 3.14 (Amazon Linux 2023).
- **Architectures:** x86_64 (Intel) vs. arm64 (Graviton2).
- **Team Scale:** 3 Members, 1 LLM per member, 10 functions per member (Total 30 functions).

## 2. Data Flow & Constraints
- **Orchestration:** Client-side Benchmarking (Client manages the sequence).
- **Data Transport:** JSON / HTTP Body (Base64 Encoded Strings).
  - *Constraint:* Raw payload must stay under 6MB (AWS Hard Limit).
  - *Optimization:* Pass-by-Value for Steps 1-4 (Memory); Pass-by-Reference (S3) only for Step 5.
- **Test Data:**
  - Input images MUST be pre-validated to be < 3MB (approx) to prevent "413 Payload Too Large".
  - Recommended: Standardize on ~1080p JPEGs for raw input.

## 3. Pipeline Logic (Microservices)
1. **Client (Test Harness):** - Reads local image -> Encodes to Base64.
   - Sends Request to Function 1.
2. **Function 1 (Greyscale):**
   - Input: `{ "image": "base64...", "params": {} }`
   - Output: `{ "image": "base64_grey...", "time": ms }`
3. **Function 2 (Resize):**
   - Input: Output of Func 1.
   - Logic: Resize to fixed 800x600.
   - *Note:* Payload size decreases significantly here.
4. **Function 3 (Color Depth - CPU Intensive):**
   - Input: Output of Func 2 (800x600).
   - Logic: Bit-depth mapping (Pure CPU calc).
5. **Function 4 (Rotate):**
   - Input: Output of Func 3.
   - Logic: 90-degree rotation.
6. **Function 5 (Format Convert - I/O Intensive):**
   - Input: Output of Func 4 + Target S3 Bucket Name.
   - Logic: Convert format (e.g., PNG) -> Upload to S3.
   - Output: `{ "s3_url": "...", "time": ms }`

## 4. Infrastructure Requirements
- **Client Environment:** EC2 Instance (Same Region as Lambdas, e.g., us-west-2) to minimize network latency (RTT).
- **Dependencies:** - Common AWS Layer containing `Pillow` (compatible with Python 3.14 & x86/ARM).
  - *Action Item:* Verify/Build this Layer in Phase 1.

## 5. LLM Code Generation Rules
- **Interface Contract:** Strict JSON Schema for Input/Output.
- **Library Restriction:** Must utilize the pre-installed `Pillow` layer; NO `pip install` in code.
- **Error Handling:** Basic try-catch to return JSON error messages, not crash logs.