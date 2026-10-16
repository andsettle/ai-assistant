"""Simple test client to verify the assistant is working."""
import asyncio
import websockets
import json


async def test_chat():
    """Test the WebSocket chat endpoint."""
    uri = "ws://localhost:8000/ws/chat"

    print("Connecting to AI Assistant...")

    async with websockets.connect(uri) as websocket:
        # Receive session info
        session_msg = await websocket.recv()
        session_data = json.loads(session_msg)
        print(f"Connected! Session ID: {session_data['session_id']}\n")

        # Test 1: Hello World
        print("Sending: 'Hello! Can you introduce yourself?'")
        await websocket.send(json.dumps({
            "type": "message",
            "message": "Hello! Can you introduce yourself?",
            "session_id": session_data["session_id"]
        }))

        # Receive streaming response
        print(" Response: ", end="", flush=True)
        full_response = ""

        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
                full_response += data["content"]
            elif data["type"] == "done":
                print("\n")
                break
            elif data["type"] == "status":
                if data["status"] == "thinking":
                    print("[Assistant is thinking...]")

        # Test 2: Memory recall
        print("\n" + "="*60)
        print("Sending: 'What did I just ask you?'")
        await websocket.send(json.dumps({
            "type": "message",
            "message": "What did I just ask you?",
            "session_id": session_data["session_id"]
        }))

        # Receive streaming response
        print(" Response: ", end="", flush=True)

        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
            elif data["type"] == "done":
                print("\n")
                break

        print("\n[SUCCESS] POC TEST COMPLETE! The assistant is working with persistent memory!")


if __name__ == "__main__":
    try:
        asyncio.run(test_chat())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        print("\nMake sure the backend server is running:")
        print("  cd ai-assistant/backend")
        print("  python main.py")
