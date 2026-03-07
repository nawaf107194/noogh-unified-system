"""
NOOGH Execution Plan JSON Schema

Strict schema for validated execution plans.

CRITICAL: All plans MUST pass this schema validation before execution.
"""

# JSON Schema for execution plans
PLAN_SCHEMA = {
    "type": "object",
    "required": ["plan_id", "summary", "overall_risk", "tasks"],
    "properties": {
        "plan_id": {
            "type": "string",
            "minLength": 1
        },
        "summary": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500
        },
        "overall_risk": {
            "type": "string",
            "enum": ["SAFE", "RESTRICTED", "DANGEROUS"]
        },
        "tasks": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,  # CRITICAL: Max 10 tasks per plan
            "items": {
                "type": "object",
                "required": [
                    "task_id",
                    "title",
                    "agent_role",
                    "capabilities",
                    "risk_level",
                    "isolation",
                    "dependencies",
                    "expected_output"
                ],
                "properties": {
                    "task_id": {
                        "type": "string",
                        "pattern": "^t[0-9]+$"  # Must be t1, t2, etc.
                    },
                    "title": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200
                    },
                    "agent_role": {
                        "type": "string",
                        "enum": [
                            "orchestrator",
                            "code_executor",
                            "security_auditor",
                            "research_analyst",
                            "file_manager",
                            "network_agent",
                            "memory_curator",
                            "system_monitor"
                        ]
                    },
                    "capabilities": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 5,  # Max 5 capabilities per task
                        "items": {
                            "type": "string",
                            "minLength": 1
                        }
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["SAFE", "RESTRICTED", "DANGEROUS"]
                    },
                    "isolation": {
                        "type": "string",
                        "enum": ["none", "sandbox", "lab_container"]
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": "^t[0-9]+$"
                        }
                    },
                    "expected_output": {
                        "type": "string",
                        "minLength": 1
                    }
                }
            }
        }
    }
}


# Allowed capabilities (abstract operations only)
ALLOWED_CAPABILITIES = {
    # Read operations
    "READ_FILE",
    "LIST_FILES",
    "SEARCH_CODE",
    "READ_DIRECTORY",
    
    # Analysis operations
    "ANALYZE_TEXT",
    "ANALYZE_CODE",
    "DETECT_MALICIOUS_CODE",
    "SCAN_CODE_FOR_VULNERABILITIES",
    "CLASSIFY_RISK",
    
    # Safe computation
    "COMPUTE_STATISTICS",
    "CALCULATE_METRICS",
    "GENERATE_REPORT",
    
    # Write operations (restricted)
    "WRITE_TEMP_FILE",
    "CREATE_PATCH",
    "GENERATE_CODE_PATCHES",
    
    # Execution (dangerous)
    "RUN_SAFE_CODE",
    "RUN_TESTS",
    "BUILD_PROJECT",
    
    # Network (dangerous)
    "FETCH_PUBLIC_DATA",
    "SEND_DATA",
    "VERIFY_URL",
    
    # Memory operations
    "SEARCH_MEMORY",
    "RECORD_INSIGHT",
    "RETRIEVE_CONTEXT",
    
    # System operations
    "GET_SYSTEM_INFO",
    "MONITOR_RESOURCES",
}


# Forbidden keywords in capabilities (tool names)
FORBIDDEN_KEYWORDS = [
    "exec", "run", "shell", "system", "subprocess",
    "os.", "eval", "compile",
    "fs.", "net.", "proc.", "code.exec",
    "http_get", "http_post",
    "delete", "remove", "rm"
]
