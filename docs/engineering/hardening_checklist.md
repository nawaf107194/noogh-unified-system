# Architecture Hardening Checklist

## A) Boundaries & Data Flow

- [ ] **Control-Plane Separation**: Ensure flags like `use_reasoning`, `temperature`, `max_tokens`, `trace_id` are NEVER injected into the text prompt.
- [ ] **Unified Prompt Builder**: Implement `PromptBuilder.build(user_text, system_text, tools_schema)` that returns structured `messages`, not raw strings.
- [ ] **Input Sanitization**: Strictly escape or reject user input containing reserved keywords like "Observation:", "Action:", or "System:".
- [ ] **Secure Logging**: Redact sensitive prompt data in production logs.

## B) Resilience (Timeouts / Retries / Circuit Breakers)

- [ ] **Layered Timeouts**:
  - Gateway: 30s
  - Orchestrator: 28s
  - Inference: 25s
- [ ] **Smart Retry Policy**: STOP retries on GPU OOM errors. Do not hammer a dying GPU.
- [ ] **Circuit Breaker**: If the inference engine is unhealthy, fast-fail at the Gateway. DO NOT fallback to local loading.
- [ ] **Backpressure**: Implement a Semaphore to limit concurrent GPU requests (e.g., max 1 active generation).

## C) GPU Safety & Ownership

- [ ] **Single Model Host**: ONE process owns the GPU. No other process may load `AutoModel`.
- [ ] **No Double-Load**: Use filesystem locks or process-level mutexes to prevent accidental multi-process model loading.
- [ ] **Memory Headroom**: Reserve 10-15% VRAM to prevent fragmentation crashes.
- [ ] **OOM Recovery Strategy**: On OOM -> Clear KV Cache -> Evict Sessions -> Retry ONCE with reduced context -> Fail.

## D) Generation Correctness

- [ ] **Token-Based Stopping**: Use `eos_token_id` or token-id based criteria. BAN string matching for stopping.
- [ ] **Mandatory Tokenizer**: Every generation request MUST have access to the tokenizer.
- [ ] **Strict Kwargs Validation**: Whitelist only: `max_new_tokens`, `temperature`, `top_p`, `do_sample`, `seed`.
- [ ] **Deterministic Testing**: Use fixed seeds for reasoning loop verification.

## E) Observability

- [ ] **Correlation IDs**: Trace `request_id` from Gateway -> Orchestrator -> Inference.
- [ ] **Critical Metrics**:
  - GPU Memory (Allocated vs Reserved)
  - Tokens/sec
  - Queue Depth
  - Error Rates (by specific class: OOM, Timeout, Validation)
