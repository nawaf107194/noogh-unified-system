"""
Integration Test: Matrix Operations & High-Performance Computing
Ensures the system can handle deterministic math via Built-in Actuators.
"""
import pytest
import asyncio
from unified_core.core.actuators import MathActuator
from gateway.app.core.auth import FULL_ADMIN_AUTH

@pytest.mark.asyncio
async def test_matrix_multiplication_performance():
    """Test that MathActuator correctly performs and profiles matrices."""
    actuator = MathActuator()
    
    # Test sizes: 32x32 and 64x64
    for size in [32, 64]:
        result = await actuator.matrix_multiply(size=size, auth=FULL_ADMIN_AUTH)
        
        assert result.result.value == "success"
        data = result.result_data
        
        assert data["size"] == f"{size}x{size}"
        assert "duration_ms" in data
        assert "gflops" in data
        assert isinstance(data["mean_result"], float)
        
        print(f"\n✅ Size {size}x{size}: {data['duration_ms']}ms, {data['gflops']} GFLOPS")

if __name__ == "__main__":
    # Logic for manual run
    actuator = MathActuator()
    loop = asyncio.get_event_loop()
    print("Running Matrix Performance Audit...")
    loop.run_until_complete(test_matrix_multiplication_performance())
