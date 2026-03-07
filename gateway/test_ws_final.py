import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://localhost:8005/reports/stream"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Read 5 messages
            for i in range(5):
                msg = await websocket.recv()
                data = json.loads(msg)

                if data.get("type") == "handshake":
                    print("🤝 Handshake received!")
                    continue

                print(f"Update {i}:")
                print(f"   CPU: {data['hardware']['cpu_usage']:.1f}%")
                print(f"   Neurons: {data['brain']['active_neurons']}")
                print("-" * 20)

    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
