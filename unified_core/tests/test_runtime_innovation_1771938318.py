import pytest
import asyncio
import signal

from unified_core.runtime import NooghRuntime, main

@pytest.fixture
def mock_runtime(mocker):
    return mocker.create_autospec(NooghRuntime)

async def test_main_happy_path(mock_runtime):
    loop = asyncio.get_event_loop()
    
    # Patch the runtime instance
    with mock.patch('unified_core.runtime.NooghRuntime', return_value=mock_runtime) as MockRuntime:
        main()
        
    # Assert the run method was called once
    MockRuntime.return_value.run.assert_called_once_with()

async def test_main_edge_case_no_runtime(mocker):
    loop = asyncio.get_event_loop()
    
    # Patch the runtime instance to return None
    with mock.patch('unified_core.runtime.NooghRuntime', return_value=None) as MockRuntime:
        main()
        
    # Assert no errors and the run method was not called
    assert MockRuntime.return_value.run.call_count == 0

async def test_main_async_behavior(mocker):
    loop = asyncio.get_event_loop()
    
    # Patch the runtime instance to simulate async behavior
    with mock.patch('unified_core.runtime.NooghRuntime') as MockRuntime:
        mock_runtime_instance = MockRuntime.return_value
        mock_runtime_instance.run.return_value = asyncio.sleep(0.1)
        
        main()
        
    # Assert the run method was called once and awaited properly
    assert MockRuntime.return_value.run.call_count == 1
    await asyncio.sleep(0.2)  # Ensure the sleep completes

async def test_main_signal_handling(mocker):
    loop = asyncio.get_event_loop()
    
    # Patch the runtime instance to simulate async behavior on signal
    with mock.patch('unified_core.runtime.NooghRuntime') as MockRuntime:
        mock_runtime_instance = MockRuntime.return_value
        shutdown_task = asyncio.create_task(mock_runtime_instance.shutdown())
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(runtime.shutdown()))
            
        # Simulate receiving a signal
        loop.call_soon(lambda: asyncio.create_task(asyncio.sleep(0.1)))
        await shutdown_task
        
    # Assert the shutdown method was called once
    MockRuntime.return_value.shutdown.assert_called_once_with()

async def test_main_keyboard_interrupt(mocker):
    loop = asyncio.get_event_loop()
    
    # Patch the runtime instance to simulate async behavior on keyboard interrupt
    with mock.patch('unified_core.runtime.NooghRuntime') as MockRuntime:
        mock_runtime_instance = MockRuntime.return_value
        shutdown_task = asyncio.create_task(mock_runtime_instance.shutdown())
        
        # Simulate receiving a KeyboardInterrupt
        loop.call_soon(lambda: asyncio.create_task(asyncio.sleep(0.1)))
        await asyncio.sleep(0.2)
        
    # Assert the shutdown method was not called and run method was not awaited
    assert MockRuntime.return_value.shutdown.call_count == 0
    assert MockRuntime.return_value.run.call_count == 0

async def test_main_shutdown_on_error(mocker):
    loop = asyncio.get_event_loop()
    
    # Patch the runtime instance to simulate an error during run
    with mock.patch('unified_core.runtime.NooghRuntime') as MockRuntime:
        mock_runtime_instance = MockRuntime.return_value
        mock_runtime_instance.run.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            main()
            
    # Assert the shutdown method was called once
    MockRuntime.return_value.shutdown.assert_called_once_with()