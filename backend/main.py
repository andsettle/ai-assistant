"""Main FastAPI server for the AI Assistant."""
import asyncio
import os
import json
import uuid
import re
import hashlib
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import DatabaseManager, Conversation
from memory_manager import MemoryManager
from ollama_client import OllamaClient
from screen_capture import ScreenCapture
from tools import ToolExecutor, get_ollama_tool_schemas
from telemetry import TelemetryMonitor

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/assistant.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:14b")
SENSITIVE_DATA_RETENTION_DAYS = int(os.getenv("SENSITIVE_DATA_RETENTION_DAYS", "90"))

# Global instances
db_manager: Optional[DatabaseManager] = None
memory_manager: Optional[MemoryManager] = None
ollama_client: Optional[OllamaClient] = None
screen_capture: Optional[ScreenCapture] = None
tool_executor: Optional[ToolExecutor] = None
ollama_tools: list[dict] = []
telemetry_monitor: Optional[TelemetryMonitor] = None
active_websockets: list[WebSocket] = []

async def broadcast_suggestion(suggestion: str):
    """Callback for when the telemetry monitor has a suggestion."""
    for ws in active_websockets:
        try:
            await ws.send_json({"type": "suggestion", "content": suggestion})
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global db_manager, memory_manager, ollama_client, screen_capture, tool_executor, ollama_tools, telemetry_monitor

    # Initialize
    db_manager = DatabaseManager(DATABASE_URL)
    await db_manager.init_db()

    memory_manager = MemoryManager(CHROMA_PATH, OLLAMA_BASE_URL)
    ollama_client = OllamaClient(OLLAMA_BASE_URL, MODEL_NAME)
    screen_capture = ScreenCapture()
    tool_executor = ToolExecutor(screen_capture)
    ollama_tools = get_ollama_tool_schemas()

    telemetry_monitor = TelemetryMonitor(
        ollama_url=OLLAMA_BASE_URL,
        evaluator_model="qwen2.5:0.5b",
        on_suggestion=broadcast_suggestion
    )
    telemetry_monitor.start()

    # Purge old sensitive data on startup
    await db_manager.purge_old_sensitive_data(SENSITIVE_DATA_RETENTION_DAYS)

    print(f"AI Assistant backend started!")
    print(f"Database: {DATABASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Sensitive data retention: {SENSITIVE_DATA_RETENTION_DAYS} days")
    print(f"Tools: {len(ollama_tools)} registered (native calling enabled)")
    print(f"Telemetry Monitor started with model: qwen2.5:0.5b")

    yield

    # Cleanup
    if telemetry_monitor:
        telemetry_monitor.stop()
    if screen_capture:
        screen_capture.close()


# Create app
app = FastAPI(
    title="AI Assistant API",
    version="0.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For POC, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    is_sensitive: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str


class ScreenCaptureRequest(BaseModel):
    monitor_number: int = 0
    format: str = "JPEG"
    quality: int = 85


class ScreenCaptureResponse(BaseModel):
    image_base64: str
    monitor_count: int


# System prompt — tools are described via native function-calling API,
# so only personality, grounding, and limits go here.
SYSTEM_PROMPT = """You are Drew's private, local personal assistant.

PERSONALITY:
- Warm, direct, and grounded. You speak like a real person, not a chatbot.
- You are confident but never pretend to see things you cannot.
- You keep responses concise unless Drew asks for detail.
- You use clear, concrete language and avoid hedging.

GROUNDING RULES:
- Never claim you saw the screen unless a tool result contains SCREENSHOT_AVAILABLE.
- SCREENSHOT_AVAILABLE means the image was captured and sent to the UI only. You cannot see it.
- If a tool fails or returns no data, say so plainly.
- When unsure, ask a short, specific question.

LIMITS:
- You can read and write files within the user directory (C:\\Users\\drew\\).
- If Drew asks for something that requires missing tools, say so and ask if he wants that tool added.

YOUR CAPABILITIES (use your tools for these):
- Read, write, list, and search files on this PC
- Capture screenshots of any monitor
- Get system information (CPU, RAM, disk)
- Execute shell commands (PowerShell) for package management, running scripts, and automating tasks
- Persistent memory across conversations (automatic)

TOOL USAGE:
- When a question involves files, the screen, system info, or running code, USE a tool. Do not guess.
- You have tools available; call them directly when needed.
- Always use full Windows paths (e.g. C:\\Users\\drew\\...).
"""


# REST Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Assistant API is running"}


@app.get("/health")
async def health_check():
    """Check if all services are healthy."""
    ollama_healthy = await ollama_client.check_health()

    return {
        "ollama": ollama_healthy,
        "database": db_manager is not None,
        "memory": memory_manager is not None,
        "screen_capture": screen_capture is not None
    }


@app.get("/models")
async def list_models():
    """List available Ollama models."""
    models = await ollama_client.list_models()
    return {"models": models}


@app.post("/capture", response_model=ScreenCaptureResponse)
async def capture_screen(request: ScreenCaptureRequest):
    """Capture a screenshot."""
    try:
        image_base64 = screen_capture.capture_as_base64(
            monitor_number=request.monitor_number,
            format=request.format,
            quality=request.quality
        )
        monitor_count = screen_capture.get_monitor_count()

        return ScreenCaptureResponse(
            image_base64=image_base64,
            monitor_count=monitor_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitors")
async def get_monitors():
    """Get information about available monitors."""
    return {"monitors": screen_capture.get_monitor_info()}


async def _prompt_monitor_select(websocket: WebSocket) -> Optional[int]:
    """If multiple monitors exist, prompt the user to pick one.

    Returns the chosen monitor id, or None if only one monitor exists
    (caller should use the default).
    """
    monitor_count = screen_capture.get_monitor_count()
    if monitor_count <= 1:
        return None

    monitors = screen_capture.get_monitor_info()
    request_id = str(uuid.uuid4())

    await websocket.send_json({
        "type": "monitor_select",
        "monitors": monitors,
        "request_id": request_id,
    })

    # Wait for the user's selection with a timeout so we don't hang forever
    try:
        selection = await asyncio.wait_for(websocket.receive_json(), timeout=15.0)
        if selection.get("type") == "monitor_select_response":
            return int(selection.get("monitor", 1))
    except asyncio.TimeoutError:
        print("Monitor selection timed out — defaulting to monitor 1")

    # Fallback — timeout or unexpected message, use monitor 1
    return 1


async def _handle_screenshot_result(tool_result: str) -> tuple[str, Optional[dict]]:
    """Process a capture_screen tool result.

    Sends the image to the vision model (LLaVA) for description,
    then returns that description as the tool result for the main LLM.

    Returns (result_for_llm, ws_payload_or_None).
    """
    try:
        parsed = json.loads(tool_result)
        if isinstance(parsed, dict) and parsed.get("type") == "screenshot":
            image_b64 = parsed.get("image_base64", "")
            ws_payload = {
                "type": "tool_result",
                "tool": "capture_screen",
                "image_base64": image_b64,
                "bytes": parsed.get("bytes", 0),
            }

            # Send to vision model for description
            if image_b64:
                print(f"Sending screenshot to vision model ({ollama_client.vision_model})...")
                description = await ollama_client.describe_image(image_b64)
                llm_text = f"SCREENSHOT DESCRIPTION (from vision model):\n{description}"
            else:
                llm_text = "Screenshot captured but image data was empty."

            return llm_text, ws_payload
    except Exception as e:
        print(f"Screenshot handling error: {e}")
    return tool_result, None


# WebSocket for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    active_websockets.append(websocket)

    # Generate or receive session ID
    session_id = str(uuid.uuid4())
    await websocket.send_json({"type": "session", "session_id": session_id})

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            message_type = data.get("type", "message")

            if message_type == "message":
                user_message = data.get("message", "")
                is_sensitive = data.get("is_sensitive", False)
                session_id = data.get("session_id", session_id)

                if not user_message.strip():
                    continue

                # Save user message
                await db_manager.add_conversation(
                    session_id=session_id,
                    role="user",
                    content=user_message,
                    is_sensitive=is_sensitive
                )

                # Get recent conversations
                recent_convs = await db_manager.get_recent_conversations(
                    session_id=session_id,
                    limit=10
                )

                # Format for memory manager
                recent_convs_dict = [
                    {"role": conv.role, "content": conv.content}
                    for conv in recent_convs[:-1]  # Exclude the message we just added
                ]

                # Build context with memories
                context = await memory_manager.build_context(
                    query=user_message,
                    recent_conversations=recent_convs_dict,
                    max_memories=3
                )

                # Prepare messages for LLM
                messages = []
                for conv in recent_convs[-5:]:  # Last 5 messages for chat history
                    messages.append({"role": conv.role, "content": conv.content})

                # Add context if available
                full_system_prompt = SYSTEM_PROMPT
                if context:
                    full_system_prompt += f"\n\n{context}"

                # Send "thinking" status
                await websocket.send_json({"type": "status", "status": "thinking"})

                # Tool calling loop
                max_tool_iterations = 3
                iteration = 0
                full_conversation = ""
                last_call_sig = None
                consecutive_same = 0

                while iteration < max_tool_iterations:
                    response_chunks = []
                    native_tool_calls = None

                    # Buffer chunks; only flush to frontend after
                    # confirming there are no native tool calls.
                    buffered_chunks: list[str] = []

                    try:
                        async for item in ollama_client.chat(
                            messages=messages,
                            system_prompt=full_system_prompt,
                            stream=True,
                            tools=ollama_tools,
                        ):
                            if item["type"] == "content":
                                response_chunks.append(item["content"])
                                buffered_chunks.append(item["content"])
                            elif item["type"] == "tool_calls":
                                native_tool_calls = item["tool_calls"]
                    except Exception as exc:
                        print(f"Ollama error: {exc}")
                        await websocket.send_json({
                            "type": "chunk",
                            "content": (
                                "I couldn't reach the local model (Ollama). "
                                "Please make sure Ollama is running, then try again."
                            )
                        })
                        await websocket.send_json({"type": "done"})
                        break

                    full_response = "".join(response_chunks)

                    # --- Priority 1: Native tool calls from Ollama ---
                    if native_tool_calls:
                        tc = native_tool_calls[0]
                        func = tc.get("function", {})
                        tool_name = func.get("name", "")
                        tool_kwargs = func.get("arguments", {})

                        if isinstance(tool_kwargs, str):
                            try:
                                tool_kwargs = json.loads(tool_kwargs)
                            except Exception:
                                tool_kwargs = {}

                        if tool_name in tool_executor._allowed_tools:
                            # Detect looping: same tool+args called repeatedly
                            call_sig = hashlib.md5(
                                f"{tool_name}:{json.dumps(tool_kwargs, sort_keys=True)}".encode()
                            ).hexdigest()
                            if call_sig == last_call_sig:
                                consecutive_same += 1
                            else:
                                consecutive_same = 0
                            last_call_sig = call_sig

                            if consecutive_same >= 2:
                                # Model is stuck in a loop — break out
                                fallback = (
                                    f"I tried to use {tool_name} multiple times "
                                    "but couldn't complete the action. "
                                    "Could you rephrase what you'd like me to do?"
                                )
                                await websocket.send_json({
                                    "type": "chunk",
                                    "content": fallback,
                                })
                                full_conversation += fallback
                                break

                            # If capturing screen with multiple monitors, ask user first
                            if tool_name == "capture_screen":
                                selected = await _prompt_monitor_select(websocket)
                                if selected is not None:
                                    if isinstance(tool_kwargs, dict):
                                        tool_kwargs["monitor"] = selected
                                    else:
                                        tool_kwargs = {"monitor": selected}

                            await websocket.send_json({
                                "type": "tool_execution",
                                "tool": tool_name,
                            })

                            tool_call_dict = {
                                "tool": tool_name,
                                "args": [],
                                "kwargs": tool_kwargs if isinstance(tool_kwargs, dict) else {},
                            }
                            tool_result = await tool_executor.execute(tool_call_dict)
                            tool_result_for_llm = tool_result

                            # Handle screenshot specially
                            if tool_name == "capture_screen":
                                tool_result_for_llm, ws_payload = await _handle_screenshot_result(tool_result)
                                if ws_payload:
                                    await websocket.send_json(ws_payload)

                            # Append assistant turn WITH tool_calls so
                            # Ollama can reconstruct the conversation.
                            messages.append({
                                "role": "assistant",
                                "content": "",
                                "tool_calls": native_tool_calls,
                            })

                            # Append tool result (Ollama expects role="tool")
                            messages.append({
                                "role": "tool",
                                "content": tool_result_for_llm,
                            })

                            iteration += 1
                            continue

                    # --- Priority 2: Text-pattern fallback ---
                    tool_call = tool_executor.parse_tool_call(full_response)
                    if tool_call:
                        tp_name = tool_call["tool"]
                        tp_kwargs = tool_call.get("kwargs", {})
                        call_sig = hashlib.md5(
                            f"{tp_name}:{json.dumps(tp_kwargs, sort_keys=True)}".encode()
                        ).hexdigest()
                        if call_sig == last_call_sig:
                            consecutive_same += 1
                        else:
                            consecutive_same = 0
                        last_call_sig = call_sig

                        if consecutive_same >= 2:
                            fallback = (
                                f"I tried to use {tp_name} multiple times "
                                "but couldn't complete the action. "
                                "Could you rephrase what you'd like me to do?"
                            )
                            await websocket.send_json({
                                "type": "chunk",
                                "content": fallback,
                            })
                            full_conversation += fallback
                            break

                        # If capturing screen with multiple monitors, ask user first
                        if tool_call["tool"] == "capture_screen":
                            selected = await _prompt_monitor_select(websocket)
                            if selected is not None:
                                tool_call["kwargs"]["monitor"] = selected

                        await websocket.send_json({
                            "type": "tool_execution",
                            "tool": tool_call["tool"],
                        })

                        tool_result = await tool_executor.execute(tool_call)
                        tool_result_for_llm = tool_result

                        if tool_call["tool"] == "capture_screen":
                            tool_result_for_llm, ws_payload = await _handle_screenshot_result(tool_result)
                            if ws_payload:
                                await websocket.send_json(ws_payload)

                        messages.append({
                            "role": "assistant",
                            "content": full_response,
                        })
                        messages.append({
                            "role": "tool",
                            "content": tool_result_for_llm,
                        })

                        iteration += 1
                        continue

                    # No tool calls at all — flush buffered chunks
                    # to the frontend now.
                    for chunk_text in buffered_chunks:
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk_text,
                        })

                    # This is the final response
                    full_conversation += full_response
                    break

                # If the loop exhausted without producing text, send fallback
                if not full_conversation.strip() and iteration >= max_tool_iterations:
                    fallback = (
                        "I used all my tool attempts without reaching a conclusion. "
                        "Could you try asking in a different way?"
                    )
                    await websocket.send_json({
                        "type": "chunk",
                        "content": fallback,
                    })
                    full_conversation = fallback

                # Save final assistant response
                if full_conversation.strip():
                    await db_manager.add_conversation(
                        session_id=session_id,
                        role="assistant",
                        content=full_conversation,
                        is_sensitive=False,
                    )

                    # Add to memory if meaningful
                    if len(full_conversation) > 50:
                        await memory_manager.add_memory(
                            content=f"User: {user_message}\nAssistant: {full_conversation}",
                            metadata={"session_id": session_id},
                        )

                # Send done signal
                await websocket.send_json({"type": "done"})

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
