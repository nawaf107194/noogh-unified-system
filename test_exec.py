import asyncio
import logging
import time
from typing import Dict, Any

from unified_core.agent_daemon import AgentDaemon
from unified_core.orchestration.messages import MessageEnvelope, MessageType, RiskLevel
from unified_core.orchestration.agent_worker import get_message_bus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_exec")

async def test_direct_bus_execution():
    daemon = AgentDaemon()
    await daemon._register_core_components()
    await daemon.components.initialize_all()
    
    bus = get_message_bus()
    
    # 1. Listen for results
    results = []
    async def capture_result(msg: MessageEnvelope):
        if msg.type == MessageType.RESULT or msg.type == MessageType.ERROR:
            logger.info(f"Received reply from executor: {msg.payload}")
            import json
            with open("/tmp/noogh_test_result.json", "w") as f:
                json.dump(msg.payload, f, indent=2)
            results.append(msg)
            
    bus.subscribe("test:receiver", capture_result)
    
    # Start daemon loops
    daemon._running = True
    asyncio.create_task(daemon.run())
    
    # Wait for initialization
    await asyncio.sleep(5.0)
    
    logger.info("Injecting raw tool request onto MessageBus...")
    
    # 2. Build the exact payload AgentWorker.handle_message expects
    req_msg = MessageEnvelope(
        trace_id="test-1234",
        task_id="task-dir-exec-1",
        sender="test:receiver",
        receiver="agent:code_executor",
        type=MessageType.REQUEST,
        risk_level=RiskLevel.RESTRICTED,
        payload={
            "task": {
                "task_id": "test-task-001",
                "title": "Echo Test",
                "agent_role": "code_executor",
                "capabilities": ["EXECUTE_SHELL"],
                "isolation": "none",
                "risk_level": "RESTRICTED",
                "arguments": {
                    "command": "echo 'Direct Bus Execution Alive' > /tmp/noogh_bus_test.txt"
                }
            }
        }
    )
    
    await bus.publish(req_msg)
    
    logger.info("Waiting for agent to process...")
    # Allow background agent time to execute via process actuator
    await asyncio.sleep(15.0)
    logger.info("Shutdown timer reached.")
        
    # Graceful shutdown
    daemon._running = False
    
    logger.info("Test finished. Checking /tmp/noogh_bus_test.txt...")

if __name__ == "__main__":
    asyncio.run(test_direct_bus_execution())
