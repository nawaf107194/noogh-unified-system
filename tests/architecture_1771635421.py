# tests/__init__.py
from .test_phase8_signing import *
from .test_model_integration import *
from .test_deletion_survival import *
from .async_tests import test_async_base_test, test_minimal_test
from .system_tests import test_start_full_system
from .security_tests import test_cf_security, test_memory_isolation
from .ai_tests import test_ai_core
from .debugging_tests import debug_init, debug_reason
from .sovereign_agent_tests import test_sovereign_agent
from .thinking_engine_tests import test_thinking_engine

# tests/async_tests.py
import asyncio
from .test_model_integration import *
from .minimal_test import *

async def run_all_async_tests():
    await asyncio.gather(
        test_model_integration(),
        test_minimal_test(),
    )

if __name__ == '__main__':
    asyncio.run(run_all_async_tests())

# tests/system_tests.py
from .test_start_full_system import *

def run_all_system_tests():
    test_start_full_system()

if __name__ == '__main__':
    run_all_system_tests()

# tests/security_tests.py
from .test_cf_security import *
from .test_memory_isolation import *

def run_all_security_tests():
    test_cf_security()
    test_memory_isolation()

if __name__ == '__main__':
    run_all_security_tests()

# tests/ai_tests.py
from .test_ai_core import *

def run_all_ai_tests():
    test_ai_core()

if __name__ == '__main__':
    run_all_ai_tests()

# tests/debugging_tests.py
from .debug_init import *
from .debug_reason import *

def run_all_debugging_tests():
    debug_init()
    debug_reason()

if __name__ == '__main__':
    run_all_debugging_tests()

# tests/sovereign_agent_tests.py
from .test_sovereign_agent import *

def run_all_sovereign_agent_tests():
    test_sovereign_agent()

if __name__ == '__main__':
    run_all_sovereign_agent_tests()

# tests/thinking_engine_tests.py
from .test_thinking_engine import *

def run_all_thinking_engine_tests():
    test_thinking_engine()

if __name__ == '__main__':
    run_all_thinking_engine_tests()