# Project Check-in Information

  * **Project Title/Topic:** A Case Study on the Performance, Cost, and Architectural Implications of LLM-Generated Serverless Image Processing Pipelines
  * **Group Members:** Bohan Xiong, Xu Zhu, Xiaoling Wei

## GROUP PLANNING

**1. How has the group decided to divide the project work?**
There are three LLMs (GPT, Gemini, DeepSeek) to be evaluated in this project. Each group member is responsible for one LLM and the corresponding image processing pipeline implementation, testing, and evaluation.

**2. What technologies and/or aspects is each group member responsible for?**

  - **Bohan Xiong:** GPT-based image processing pipeline implementation and evaluation (10 Lambda functions for 5 stages × 2 CPU architectures). Also responsible for project coordination, repository management, and documentation.
  - **Xiaoling Wei:** Gemini-based image processing pipeline implementation and evaluation (10 Lambda functions for 5 stages × 2 CPU architectures).
  - **Xu Zhu:** DeepSeek-based image processing pipeline implementation and evaluation (10 Lambda functions for 5 stages × 2 CPU architectures).

**3. What aspects of the project have a shared responsibility?**
Project planning, documentation, data collection, and final report writing are shared responsibilities among all group members.

## PROGRESS UPDATE: CODE

**4. What code has been developed/generated/created (e.g. lists of Lambda functions, classes, shared libraries with short descriptions)?**
We have generated and deployed 30 AWS Lambda functions (5 pipeline stages × 3 LLMs × 2 CPU Architectures). The functions perform: Greyscale, Resize, Color Depth Map, Rotate, and Format Conversion.

**5. What languages are being used?**
Python 3.14

**6. To date, what is the size of the code (lines of code, size in KB)?**

  - Prompts for LLMs: 345 lines and 14 KB
  - Lambda functions: \~1400 lines and 60 KB
  - Bash scripts for deployment and testing: \~140 lines and 5 KB
  - Python scripts for testing and evaluation: \~440 lines and 25 KB
  - **In total:** \~2325 lines and 104 KB

**7. Is there a shared GitHub repository? If so, please share a URL.**
Yes, the repository URL is: [https://github.com/JosephJostar0/562TermProject](https://github.com/JosephJostar0/562TermProject)

## PROGRESS UPDATE: DATA

**8. What data sources have been identified or tested to support the project? (kaggle.com is an excellent source)**
We are using 3 different images representing real-world scenarios: a high-resolution photograph (4k), a medium-resolution photograph (1080p), and a low-resolution photograph (512x512).

**9. How large are the data sets that the team has been using/testing?**
The data sets consist of three images with different resolutions:

  - High-resolution photograph (4k): 1354 KB
  - Medium-resolution photograph (1080p): 882 KB
  - Low-resolution photograph (512x512): 68 KB

**10. What type of information does the data set describe (e.g. sales data, medical data, other, ..)?**
Image files (JPEG) used for benchmarking image processing algorithms.

**11. What cloud services are being used to store data --OR--, what services is the group planning to use?**
AWS S3 (for object storage) and AWS Lambda (for serverless compute).

## EVALUATION/COMPARISON

**12. Provide a brief summary of the status of the case study comparison work. What progress has been made?**
We have successfully implemented and deployed the image processing pipelines using three different LLMs (GPT, Gemini, DeepSeek) on AWS Lambda with both x86\_64 and ARM64 architectures. Each pipeline consists of five stages: Greyscale, Resize, Color Depth Map, Rotate, and Format Conversion. We have also set up automated testing scripts to measure performance metrics such as execution time and cost. Initial "smoke tests" (N=10 runs) have been conducted to validate the pipeline stability and gather preliminary data.

**13. Describe any initial performance results.**
Initial profiling of the GPT-generated pipeline reveals interesting architectural differences. While I/O-bound tasks like **Greyscale** (\~422ms) and **Upload** (\~126ms) show similar performance across architectures, the ARM64 architecture demonstrates a clear advantage in compute-intensive tasks. Specifically, for the **Resize** stage, ARM64 (\~407ms) was approximately **27% faster** than x86\_64 (\~561ms). This suggests that for our specific image processing workload, ARM64 may offer superior performance-per-dollar. Further testing is required to see if this trend holds for Gemini and DeepSeek generated code.

**14. Describe any profiling data. (for example, have you completed test runs to estimate average runtime)**
Yes, we have completed initial benchmarking runs. Below is the average **Logic Runtime** (compute duration excluding network latency) for the GPT-based pipeline (averaged over 60 data points):

| Pipeline Stage | Function | ARM64 Avg Runtime (ms) | x86\_64 Avg Runtime (ms) | Delta (x86 vs ARM) |
| :--- | :--- | :--- | :--- | :--- |
| Step 1 | Greyscale | 422.83 ms | 421.39 ms | \~0% |
| Step 2 | Resize | **407.08 ms** | 561.18 ms | **ARM is \~27% Faster** |
| Step 3 | Color Depth | 22.91 ms | 24.32 ms | ARM is \~6% Faster |
| Step 4 | Rotate | 2.36 ms | 4.28 ms | ARM is \~45% Faster |
| Step 5 | Format Convert | 125.78 ms | 126.86 ms | \~0% |
| **Total** | **Pipeline Logic** | **980.97 ms** | **1138.03 ms** | **ARM is \~14% Faster Overall** |

*(Note: Data derived from initial GPT-5.1 generated code tests.)*

## ROADBLOCKS / QUESTIONS / CHANGES

**15. Describe any project road blocks or questions you may have.**
The default Python runtime in AWS Lambda does not contain the `Pillow` (PIL) library, which is essential for image processing. We had to create a custom Lambda Layer to include this dependency. This added complexity, particularly with cross-architecture compatibility (building ARM64 layers on AMD64 dev machines). We resolved this by using Docker to build the layers in a target-specific environment.

**16. Describe any changes that your group needs to make to the original project proposal.**

1.  **Architecture:** As detailed in Proposal v0.2, we shifted from a monolithic S3 trigger-based architecture to a decoupled microservices design to allow for more precise individual function benchmarking.
2.  **Tech Stack:** We updated the target runtime to **Python 3.14** (utilizing custom layers/runtimes where necessary) and updated the LLM versions to the latest available (GPT-5.1, Gemini 3.0 Pro) to ensure the study remains relevant to state-of-the-art capabilities.
