import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://localhost:8003/reports/stream"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Read 3 messages
            for i in range(3):
                msg = await websocket.recv()
                data = json.loads(msg)
                print(f"Update {i+1}:")
                print(f"   CPU: {data['hardware']['cpu_usage']:.1f}%")
                print(f"   Neurons: {data['brain']['active_neurons']}")
                print("-" * 20)

    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
