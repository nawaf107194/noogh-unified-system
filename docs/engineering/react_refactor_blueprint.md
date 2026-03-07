# ReAct Loop Refactor Blueprint

## Objective
Transform the ReAct loop from a fragile text-parsing loop into a structured **Finite State Machine (FSM)**. Eliminate "Observation:" injections by enforcing strict message structuration.

## 1. Core Principles

### A. State Machine (The Brain)
Processing moves through explicit states:
1.  `THINK`: Model reasons about the user request.
2.  `ACT`: Model (or System) decides to call a tool.
3.  `OBSERVE`: System feeds back tool result.
4.  `FINAL`: Model formulates answer to user.

### B. Structured History
**OLD (Fragile):**
```text
User: Hi
Assistant: I will search.
Action: search
Observation: results...
```

**NEW (Robust):**
```json
[
  {"role": "user", "content": "Hi"},
  {"role": "assistant", "content": "{\"type\": \"thought\", \"text\": \"I need to search\"}"},
  {"role": "assistant", "content": "{\"type\": \"call\", \"tool\": \"search\", \"args\": {}}"},
  {"role": "tool", "content": "{\"result\": \"...\"}"}
]
```

## 2. Implementation Logic

### The Loop (Pseudocode)

```python
history = [system_msg, user_msg]

for i in range(MAX_STEPS):
    # 1. Generate formatted step
    response_payload = model_host.generate(
        messages=history, 
        schema=StepSchema # Enforce JSON output if model supports it
    )
    
    # 2. Parse & Validate
    try:
        step = parse_json(response_payload)
    except JsonError:
        history.append(system_correction("Output must be valid JSON"))
        continue

    # 3. State Handling
    if step.type == "final":
        return step.content

    if step.type == "action":
        # Execute Tool (Sandbox)
        result = tool_registry.execute(step.tool, step.args)
        
        # Append structured history
        history.append(AssistantMessage(content=response_payload))
        history.append(ToolMessage(content=json.dumps(result)))
    
    elif step.type == "thought":
        # Just update history
        history.append(AssistantMessage(content=response_payload))

return FallbackError("Max iterations reached")
```

## 3. Safety Guards

### Anti-Injection
- **User Content Delimiters**: Wrap user content in `<user_input>` tags if the model is weak instruction follower.
- **Strict Role Enforcement**: The parser MUST ignore any text that looks like a tool call if it appears inside a `user` message block.

### Stop Conditions
- **Hard Limit**: `MAX_STEPS` (e.g., 5).
- **Stuck Loop Detection**: If `step.tool` and `step.args` are identical to `history[-2]`, break loop (Model is looping).
