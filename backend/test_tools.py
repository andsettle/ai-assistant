"""Test client to verify tool calling works."""
import sys
import asyncio
import websockets
import json

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def test_tools():
    """Test tool calling functionality."""
    uri = "ws://localhost:8000/ws/chat"

    print("Connecting to AI Assistant...")

    async with websockets.connect(uri) as websocket:
        # Receive session info
        session_msg = await websocket.recv()
        session_data = json.loads(session_msg)
        print(f"Connected! Session ID: {session_data['session_id']}\n")

        # Test 1: Ask AI to list files (should trigger tool)
        print("="*60)
        print("TEST 1: Asking AI to list files in ai-assistant folder")
        print("="*60)
        await websocket.send(json.dumps({
            "type": "message",
            "message": "List all files in the C:\\Users\\drew\\ai-assistant directory",
            "session_id": session_data["session_id"]
        }))

        print("Response: ", end="", flush=True)
        tool_executed = False

        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
            elif data["type"] == "tool_execution":
                print(f"\n[TOOL EXECUTED: {data['tool']}]", flush=True)
                tool_executed = True
            elif data["type"] == "done":
                print("\n")
                break

        if tool_executed:
            print("[SUCCESS] Tool was executed!")
        else:
            print("[FAILED] No tool was executed - AI didn't use tools")

        # Test 2: Ask AI to read README
        print("\n" + "="*60)
        print("TEST 2: Asking AI to read README.md")
        print("="*60)
        await websocket.send(json.dumps({
            "type": "message",
            "message": "Read the README.md file and summarize it",
            "session_id": session_data["session_id"]
        }))

        print("Response: ", end="", flush=True)
        tool_executed = False

        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
            elif data["type"] == "tool_execution":
                print(f"\n[TOOL EXECUTED: {data['tool']}]", flush=True)
                tool_executed = True
            elif data["type"] == "done":
                print("\n")
                break

        if tool_executed:
            print("[SUCCESS] Tool was executed!")
        else:
            print("[FAILED] No tool was executed - AI didn't use tools")

        print("\n" + "="*60)
        print("TOOL TESTING COMPLETE")
        print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(test_tools())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        print("\nMake sure the backend server is running:")
        print("  cd ai-assistant/backend")
        print("  python main.py")
