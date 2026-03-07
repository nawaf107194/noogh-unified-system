# GPU Resource Governance Design

## Objective
Prevent "Split-Brain" processing and OOM crashes by enforcing a strict **Single Model Host** architecture with a lease-based access mechanism.

## 1. Core Architecture

### Components
1.  **Gateway (Stateless Proxy)**: 
    - Function: Routes requests only. 
    - Constraint: **FORBIDDEN** from loading `torch` or `transformers`.
2.  **Neural Engine / Orchestrator**: 
    - Function: Manages logic and pipelines.
    - Constraint: Does not hold GPU handle directly, delegates to Model Host.
3.  **Model Host (The Sentinel)**: 
    - Function: The **ONLY** process allowed to call `model.to("cuda")`. 
    - Responsibility: Memory mgmt, KV-Caching, Batching.
4.  **Lease Manager**:
    - Function: Gatekeeper for GPU time. 

## 2. Request Flow (The Lease Protocol)

1.  **Request**: Orchestrator sends job -> Model Host.
    - Payload: `messages`, `params`, `request_id`.
2.  **Admission Control (Model Host)**:
    - Check `active_leases`. If full -> **429 Too Many Requests**.
    - Estimate Memory: `VRAM_Needed = (PromptTokens + MaxNewTokens) * KV_Factor`.
    - If `VRAM_Needed > Available_Headroom` -> **Reject (OOM risk)**.
3.  **Lease Acquisition**:
    - Host grants `LeaseToken {id, ttl_ms, max_tokens}`.
4.  **Execution**:
    - Generation runs.
    - If `Time > TTL` -> **Preempt/Cancel**.
5.  **Release**:
    - Result returned.
    - Lease destroyed. Memory marked available.

## 3. Failure & Recovery Modes

### OOM During Generation
- **Action**: Immediate `torch.cuda.empty_cache()`.
- **Policy**: Mark Lease as FAILED (Do not retry automatically).
- **Report**: Return `ERR_GPU_OOM` to Orchestrator.

### Host Unresponsive
- **Action**: Gateway Circuit Breaker opens.
- **Fallback**: 
    - **Tier 1 (Warm)**: Smaller CPU quantized model (if resident in separate process).
    - **Tier 2 (Cold)**: Static "System Offline" response.
    - **NEVER**: Load model in Gateway.

## 4. Implementation Requirements
- **Mutex**: `flock` on `/var/lock/noogh_gpu.lock` to prevent 2nd Model Host startup.
- **Isolation**: Model Host runs in separate process group or container.
