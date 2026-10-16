# Context Packet for GPT-5.2-Codex - AI Assistant Project

**Date**: February 8-9, 2026
**Previous AI**: Claude Sonnet 4.5 (Anthropic)
**Project Status**: 95% Complete - Tool calling implemented but needs verification in Tauri UI
**Urgency**: High - User needs fully functional standalone local AI assistant

---

## CRITICAL CONTEXT

### The Problem We're Solving
User (Drew) wants a **standalone local AI assistant** that:
- Runs 100% locally (no cloud dependencies)
- Has persistent memory across sessions
- Can read files and view screen **without manual intervention**
- Can maintain and fix itself
- Has a beautiful floating bubble UI (not a chatbot interface)

### Current Issue
The AI assistant currently responds with:
> "I don't have direct access to your screen or system files"

**This is UNACCEPTABLE** - defeats the entire purpose of having a local assistant.

### What Was Just Implemented (Last 2 Hours)
Claude Sonnet 4.5 implemented a **function calling system** that gives the AI real tools:
- `read_file()` - Read any file
- `list_files()` - List directory contents
- `capture_screen()` - Take screenshots
- `get_system_info()` - Check system status
- `search_files()` - Find files by pattern

**Testing Results:**
- ✅ Backend tool execution works perfectly (verified via test_tools.py)
- ❓ Tauri UI tool execution - NOT YET VERIFIED
- User is about to test via Tauri UI and will decide if Codex needs to take over

---

## SYSTEM ARCHITECTURE

```
Desktop Shortcuts (3 icons)
    ↓
start-assistant.bat (launches both services)
    ↓
┌─────────────────┬─────────────────┐
│   Backend       │    Frontend     │
│   (Python)      │    (Tauri)      │
│   Port 8000     │    WebSocket    │
└────────┬────────┴────────┬────────┘
         │                 │
    ┌────┴─────────────────┴────┐
    │   Ollama (Port 11434)     │
    │   Model: qwen2.5:14b      │
    │   Embedding: nomic-embed  │
    └────────┬──────────────────┘
             │
    ┌────────┴──────────────────┐
    │   Data Storage            │
    │   - SQLite (conversations)│
    │   - ChromaDB (embeddings) │
    └───────────────────────────┘
```

---

## HARDWARE & SOFTWARE ENVIRONMENT

### System Specs
- **OS**: Windows 11 Home (10.0.26200)
- **CPU**: AMD Ryzen 5 7600 (6-core)
- **RAM**: 31GB
- **GPU**: AMD Radeon RX 7900 XT (20GB VRAM)
- **Python**: 3.13.5
- **Node.js**: 22.17.0
- **Rust/Cargo**: 1.91.1

### Key Software
- **Ollama**: 0.15.6 (LLM runtime with ROCm for AMD GPU)
- **Model**: qwen2.5:14b (9GB, chosen for reasoning over speed)
- **FastAPI**: Backend framework
- **Tauri**: 2.0 (desktop UI framework)
- **ChromaDB**: Vector database for semantic memory
- **SQLite**: Conversation storage

### Important Notes
- User runs games, Discord, Chrome heavily - expect slower responses
- AMD GPU (not NVIDIA) - uses ROCm, not CUDA
- Windows console doesn't support emojis - avoid in Python code
- First Rust compile takes 5-10 minutes

---

## FILE STRUCTURE

```
C:\Users\drew\ai-assistant\
├── backend/                          # Python FastAPI backend
│   ├── main.py                       # FastAPI server with WebSocket chat
│   ├── database.py                   # SQLite schema (conversations, memories, settings)
│   ├── memory_manager.py             # ChromaDB semantic search
│   ├── ollama_client.py              # LLM communication with streaming
│   ├── screen_capture.py             # MSS library for screenshots
│   ├── tools.py                      # ⭐ NEW: Tool execution system
│   ├── test_client.py                # Test WebSocket connection
│   ├── test_tools.py                 # ⭐ Test tool calling
│   └── requirements.txt              # Python dependencies
│
├── frontend/                         # Tauri + React UI
│   ├── src/
│   │   ├── App.tsx                   # React component (floating bubble)
│   │   └── App.css                   # Bubble UI styling
│   └── src-tauri/                    # Rust backend for desktop app
│
├── data/                             # Created on first run
│   ├── assistant.db                  # SQLite database
│   └── chroma/                       # ChromaDB vector storage
│
├── Desktop Shortcuts (3)
│   ├── Start AI Assistant.lnk
│   ├── Restart AI Assistant.lnk
│   └── Test AI Assistant.lnk
│
├── Startup Scripts
│   ├── start-assistant.bat           # ⭐ Main launcher
│   ├── start-backend.bat             # Backend only (minimized window)
│   ├── start-frontend.bat            # Frontend only (minimized window)
│   ├── restart-assistant.bat         # Emergency restart
│   ├── quick-test.bat                # Health check
│   └── create-shortcuts.vbs          # Creates desktop shortcuts
│
└── Documentation
    ├── HANDOFF_CONTEXT.md            # Full system docs for AI
    ├── README.md                     # User quick start guide
    ├── IMPORTANT_TOOL_ACCESS.md      # Tool limitation explanation (outdated)
    ├── FINAL_STATUS.md               # Build status summary
    └── CODEX_HANDOFF.md              # This file
```

---

## WHAT WORKS PERFECTLY

### 1. Persistent Memory ✅
- **Technology**: SQLite + ChromaDB
- **Location**: `data/assistant.db` and `data/chroma/`
- **Features**:
  - Remembers ALL conversations across sessions
  - Semantic search via ChromaDB embeddings
  - 90-day auto-purge for sensitive data
  - Perfect recall verified in testing

### 2. Backend API ✅
- **Framework**: FastAPI with async/await
- **Port**: 8000
- **Endpoints**:
  - `GET /health` - System health check
  - `GET /models` - List Ollama models
  - `POST /capture` - Screenshot capture
  - `GET /monitors` - Monitor info
  - `WS /ws/chat` - WebSocket chat with streaming

### 3. LLM Integration ✅
- **Runtime**: Ollama on port 11434
- **Model**: qwen2.5:14b (9GB, 14 billion parameters)
- **Features**:
  - Streaming responses via WebSocket
  - OpenAI-compatible API
  - GPU acceleration (ROCm for AMD)
  - Response time: 10-30 seconds (acceptable given system load)

### 4. UI Design ✅
- **Framework**: Tauri 2.0 + React + TypeScript
- **Style**: Floating bubble (350px compact, 450px expanded)
- **Features**:
  - Semi-transparent background
  - Shows only current message
  - Expands on user input
  - Minimizes when idle
  - Status indicator (green = connected)

### 5. Tool Backend ✅
- **File**: `backend/tools.py`
- **Class**: `ToolExecutor`
- **Test Status**: Verified working via `test_tools.py`
- **Capabilities**:
  ```python
  read_file(filepath, max_lines=1000)
  list_files(directory=".", pattern="*")
  capture_screen(monitor=0)
  get_system_info()
  search_files(directory, pattern)
  ```

---

## WHAT NEEDS VERIFICATION/FIXING

### 1. Tool Calling in Tauri UI ⚠️
**Status**: Implemented but not yet verified by user

**How it should work:**
1. User asks: "Read the README file"
2. AI responds: `TOOL_CALL: read_file("C:\\Users\\drew\\ai-assistant\\README.md")`
3. Backend parses this, executes tool
4. Backend sends result back to AI
5. AI incorporates result and responds to user

**Current uncertainty:**
- Does the AI actually invoke tools in real conversation?
- Is the TOOL_CALL format clear enough in the system prompt?
- Does the WebSocket properly send tool execution notifications?

**Testing needed:**
Via Tauri UI, ask:
- "List files in the ai-assistant folder"
- "Read the HANDOFF_CONTEXT.md file"
- "Capture my screen"
- "What's my system info?"

**Expected behavior:**
- AI should use tools WITHOUT saying "I can't do that"
- Frontend should show `[Executed: tool_name]` messages
- AI should respond with actual file contents/results

**If AI still says "I don't have access":**
→ Problem is either:
  a) System prompt not clear enough
  b) Tool calling format wrong for Qwen model
  c) WebSocket loop not working correctly

### 2. Potential Issues to Check

#### Issue A: Model Not Understanding Tool Format
**Symptom**: AI responds normally but never writes TOOL_CALL

**Diagnosis**: Check if Qwen2.5:14b supports this tool calling format

**Solution Options:**
1. Switch to explicit function calling (JSON format):
   ```python
   tools = [{"name": "read_file", "parameters": {...}}]
   ```
2. Use Llama 3.1 which has native function calling
3. Add examples to system prompt showing exact TOOL_CALL format

#### Issue B: Tool Results Not Being Injected
**Symptom**: AI executes tool but doesn't use results in response

**Diagnosis**: Check WebSocket message handling in `main.py:253-285`

**Solution**: Verify tool result is properly added to message history

#### Issue C: Frontend Not Showing Tool Execution
**Symptom**: Tools execute but user doesn't know

**Diagnosis**: Check if frontend handles `tool_execution` message type

**Solution**: Update `App.tsx` to display tool notifications

---

## DETAILED TECHNICAL IMPLEMENTATION

### Tool Calling System (How It Works)

**File**: `backend/main.py` lines 253-285

**Flow**:
```python
1. User sends message via WebSocket
2. Backend adds to conversation history
3. Backend retrieves relevant memories (ChromaDB)
4. Backend builds context with recent conversations
5. Backend sends to Ollama with system prompt containing tool descriptions
6. Ollama streams response
7. Backend parses each chunk for "TOOL_CALL: tool_name(...)"
8. If found:
   a. Execute tool via ToolExecutor
   b. Add tool result to messages
   c. Continue conversation loop (max 5 iterations)
9. If no tool call, finish and save response
```

**System Prompt** (main.py lines 100-127):
```python
SYSTEM_PROMPT = """You are a personal AI assistant...

YOU HAVE ACCESS TO THE FOLLOWING TOOLS:

1. read_file(filepath, max_lines=1000)
   - Example: TOOL_CALL: read_file("C:\\Users\\drew\\file.txt")

2. list_files(directory=".", pattern="*")
   - Example: TOOL_CALL: list_files("C:\\Users\\drew")

...

TO USE A TOOL:
1. Write "TOOL_CALL: " followed by the tool name and arguments
2. The tool will execute and return results
3. You will receive the results and can continue the conversation

CRITICAL:
When Drew asks you to look at files or screen, USE YOUR TOOLS immediately.
"""
```

**Tool Parser** (tools.py lines 17-54):
```python
def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
    """Parse: TOOL_CALL: tool_name(arg1, arg2, key=value)"""
    pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
    match = re.search(pattern, text)

    if match:
        tool_name = match.group(1)
        args_str = match.group(2)
        # Parse arguments...
        return {"tool": tool_name, "args": [...], "kwargs": {...}}
    return None
```

**Tool Executor** (tools.py lines 56-95):
```python
async def execute(self, tool_call: Dict[str, Any]) -> str:
    """Execute a tool and return the result."""
    tool_name = tool_call["tool"]

    if tool_name == "read_file":
        return await self.read_file(*args, **kwargs)
    elif tool_name == "list_files":
        return await self.list_files(*args, **kwargs)
    # ... etc
```

---

## DATABASE SCHEMA

### SQLite Tables (database.py)

**conversations**:
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_sensitive BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_session ON conversations(session_id);
CREATE INDEX idx_timestamp ON conversations(timestamp);
```

**memories**:
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    embedding_id VARCHAR(100),  -- ChromaDB ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    tags VARCHAR(500),
    is_sensitive BOOLEAN DEFAULT FALSE
);
```

**settings**:
```sql
CREATE TABLE settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### ChromaDB Collection

**Name**: `assistant_memories`
**Distance**: Cosine similarity
**Embedding Model**: nomic-embed-text (via Ollama)

**Storage**:
- Documents: Raw conversation text
- Embeddings: 768-dimensional vectors
- Metadata: {"session_id": "...", ...}

---

## DEPENDENCIES

### Backend (requirements.txt)
```
fastapi==0.115.0
uvicorn[standard]==0.32.1
python-multipart==0.0.17
websockets==14.1
httpx==0.28.1
chromadb==0.5.23
mss==9.0.2
pillow==11.1.0
pydantic==2.10.5
pydantic-settings==2.7.0
sqlalchemy==2.0.36
aiosqlite==0.20.0
psutil==6.1.1
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@tauri-apps/api": "^2.3.0",
    "@tauri-apps/cli": "^2.3.0",
    "typescript": "^5.6.2",
    "vite": "^7.3.1"
  }
}
```

---

## TESTING PROCEDURES

### 1. Backend Health Check
```bash
curl http://localhost:8000/health
```
**Expected**:
```json
{
  "ollama": true,
  "database": true,
  "memory": true,
  "screen_capture": true
}
```

### 2. Tool Execution Test
```bash
cd C:\Users\drew\ai-assistant\backend
python test_tools.py
```
**Expected**: Two successful tool executions (list_files, read_file)

### 3. Basic Conversation Test
```bash
cd C:\Users\drew\ai-assistant\backend
python test_client.py
```
**Expected**: AI responds and remembers previous question

### 4. Full UI Test (via Tauri)
**Steps**:
1. Double-click "Start AI Assistant" on desktop
2. Wait for bubble UI to appear
3. Type: "List all files in the ai-assistant folder"
4. Verify: AI executes tool and shows results (not "I can't do that")

---

## COMMON ISSUES & SOLUTIONS

### Issue: Port 8000 Already in Use
**Symptom**: Backend won't start, error about port binding

**Solution**:
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill specific process (replace PID)
powershell.exe "Stop-Process -Id <PID> -Force"
```

### Issue: ChromaDB Telemetry Warnings
**Symptom**: Console shows telemetry errors

**Solution**: Ignore - these are harmless and don't affect functionality

### Issue: Ollama Not Running
**Symptom**: Backend health check shows ollama: false

**Solution**:
```bash
ollama list  # This starts Ollama if not running
```

### Issue: Windows Kills Python Process
**Symptom**: Backend randomly stops

**Solution**: Don't use `taskkill /F /IM python.exe` - it kills ALL Python including Claude. Use specific PID instead.

### Issue: Emoji Encoding Errors
**Symptom**: UnicodeEncodeError with emojis

**Solution**: Remove all emojis from Python print statements (Windows console doesn't support them)

---

## WHAT CODEX NEEDS TO DO (If Tools Don't Work)

### Priority 1: Verify Tool Calling Works in UI

**Test**:
1. Start the Tauri UI
2. Ask: "Read the README.md file"
3. Check if AI uses TOOL_CALL or says "I can't"

**If AI says "I can't":**

#### Option A: Improve System Prompt
Make the tool calling format more explicit:

```python
SYSTEM_PROMPT = """...

EXAMPLE CONVERSATION:
User: "Read the README file"
You: TOOL_CALL: read_file("C:\\Users\\drew\\ai-assistant\\README.md")
[System executes tool and provides result]
You: "Based on the README, here's a summary..."

YOU MUST USE TOOLS WHEN ASKED ABOUT FILES OR SCREEN.
DO NOT SAY "I can't access files" - YOU CAN WITH TOOLS.
"""
```

#### Option B: Switch to JSON Function Calling
Qwen2.5 might prefer JSON format:

```python
# In ollama_client.py, add tools parameter
{
    "model": "qwen2.5:14b",
    "messages": [...],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"}
                    }
                }
            }
        }
    ]
}
```

#### Option C: Use a Different Model
Llama 3.1 has native function calling:

```bash
ollama pull llama3.1:8b
```

Update `main.py`:
```python
MODEL_NAME = "llama3.1:8b"
```

### Priority 2: Add Visual Feedback in UI

**Problem**: User can't tell if tools are executing

**Solution**: Update `frontend/src/App.tsx`:

```typescript
// Add to message types
interface Message {
  role: "user" | "assistant" | "tool";
  content: string;
  tool?: string;
}

// In WebSocket handler
else if (data.type === "tool_execution") {
  setMessages((prev) => [...prev, {
    role: "tool",
    content: `Executing ${data.tool}...`,
    tool: data.tool
  }]);
}

// In CSS
.message.tool {
  color: #22c55e;
  font-style: italic;
  font-size: 12px;
}
```

### Priority 3: Add Command System (Fallback)

If tool calling doesn't work, add simple command parsing:

```python
# In main.py WebSocket handler
if user_message.startswith("!"):
    # Parse command
    if user_message.startswith("!read "):
        filepath = user_message[6:].strip()
        result = await tool_executor.read_file(filepath)
        await websocket.send_json({
            "type": "chunk",
            "content": result
        })
        continue
    elif user_message == "!help":
        await websocket.send_json({
            "type": "chunk",
            "content": TOOL_DESCRIPTIONS
        })
        continue
```

Users can then use:
- `!read C:\path\to\file.txt`
- `!list C:\path\to\directory`
- `!screenshot`

---

## USER PREFERENCES & CONSTRAINTS

### User (Drew) Characteristics
- **Tech-savvy**: Comfortable with code, terminal, debugging
- **Direct communication**: Hates fluff, wants action not talk
- **Privacy-focused**: Everything must be local, no cloud
- **Heavy multitasker**: Runs games, Discord, Chrome simultaneously
- **Impatient**: Wants things working NOW

### Communication Style Expected
- ❌ "Let me explain how this works..."
- ✅ "Done. Test it."
- ❌ "We could try several approaches..."
- ✅ "Implementing solution X."
- ❌ Emojis everywhere
- ✅ Clean, professional output

### Project Requirements
1. **Must be standalone** - Cannot depend on Claude Code or any external AI service
2. **Must have real tools** - File access, screen capture, etc.
3. **Must be beautiful** - Floating bubble UI, not a terminal
4. **Must be private** - 100% local, no telemetry
5. **Must remember everything** - Persistent memory across sessions
6. **Must be fast to start** - <10 seconds from desktop click

---

## CRITICAL FILES TO REVIEW

If taking over, read these in order:

1. **backend/main.py** (lines 100-127, 253-285)
   - System prompt
   - Tool calling loop

2. **backend/tools.py** (entire file)
   - Tool implementations
   - Tool parser

3. **frontend/src/App.tsx** (lines 20-100)
   - WebSocket message handling
   - Could need updates for tool feedback

4. **HANDOFF_CONTEXT.md**
   - Full context for the AI assistant itself
   - What it should know about itself

5. **test_tools.py**
   - Working example of tool execution
   - Use as reference

---

## DEBUGGING CHECKLIST

If user reports tools still don't work:

- [ ] Backend logs show "Tools: Enabled" on startup
- [ ] `test_tools.py` executes successfully
- [ ] Ollama is running (`ollama list`)
- [ ] Backend is running on port 8000 (`netstat -ano | findstr :8000`)
- [ ] Tauri UI connects (green status dot)
- [ ] System prompt includes TOOL_DESCRIPTIONS
- [ ] Tool calling loop is in WebSocket handler (main.py:253-285)
- [ ] ToolExecutor is initialized in lifespan
- [ ] AI response contains "TOOL_CALL:" somewhere
- [ ] Tool parser successfully extracts tool calls
- [ ] Tool execution returns valid results

---

## FALLBACK PLAN

If all else fails and tools absolutely won't work:

### Option 1: Use LangChain Agent
```bash
pip install langchain langchain-community
```

```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import Ollama

tools = [
    Tool(
        name="ReadFile",
        func=tool_executor.read_file,
        description="Read a file..."
    ),
    # ... etc
]

agent = initialize_agent(tools, Ollama(model="qwen2.5:14b"))
```

### Option 2: Use Llama 3.1 with Native Function Calling
```bash
ollama pull llama3.1:8b
```

Update MODEL_NAME in main.py and use Ollama's native function calling API.

### Option 3: Prompt Engineering
Add more explicit examples to system prompt showing EXACT format:

```python
SYSTEM_PROMPT += """

CRITICAL EXAMPLES - COPY THESE EXACTLY:

Example 1:
User: "What files are in the backend folder?"
You: TOOL_CALL: list_files("C:\\Users\\drew\\ai-assistant\\backend")

Example 2:
User: "Read the README"
You: TOOL_CALL: read_file("C:\\Users\\drew\\ai-assistant\\README.md")

Example 3:
User: "Show me my screen"
You: TOOL_CALL: capture_screen(0)

NEVER say "I don't have access" - YOU DO HAVE ACCESS VIA TOOLS.
"""
```

---

## PERFORMANCE EXPECTATIONS

### Response Times
- **First message**: 20-40 seconds (model loading into VRAM)
- **Subsequent messages**: 10-20 seconds
- **With tool execution**: +5-10 seconds per tool

### Memory Usage
- Backend: ~500MB RAM
- Frontend: ~200MB RAM
- Ollama: ~10GB VRAM (model cached)
- Total system: ~15GB with everything running

### Storage
- Model: 9GB (qwen2.5:14b)
- Database: <100MB (grows over time)
- ChromaDB: <500MB (grows over time)

---

## SUCCESS CRITERIA

The project is considered COMPLETE when:

1. ✅ User can start assistant from desktop shortcut
2. ✅ Floating bubble UI appears and connects
3. ✅ User asks "Read the README file"
4. ✅ AI responds with actual file contents (not "I can't access")
5. ✅ User asks "Capture my screen"
6. ✅ AI responds "Screenshot captured" and has image data
7. ✅ Memory persists across restarts
8. ✅ User can restart assistant if it crashes
9. ✅ No dependencies on external AI services

---

## HANDOFF CHECKLIST

Before declaring victory:

- [ ] Backend starts successfully with "Tools: Enabled"
- [ ] Frontend connects (green status indicator)
- [ ] `test_tools.py` passes both tests
- [ ] User tests "Read README" in Tauri UI - AI actually reads it
- [ ] User tests "List files" in Tauri UI - AI actually lists them
- [ ] User tests "Capture screen" in Tauri UI - AI actually captures
- [ ] Memory persists (restart and ask "what did we talk about?")
- [ ] Desktop shortcuts work
- [ ] Restart script works
- [ ] User is satisfied

---

## CONTACT INFORMATION FOR CODEX

**User**: Drew
**Project Location**: C:\Users\drew\ai-assistant\
**Communication Style**: Direct, no-nonsense
**Priority**: GET TOOLS WORKING IN UI
**Deadline**: ASAP (user is testing now)

**If you (Codex) need to take over:**
1. Read this entire document
2. Review backend/main.py lines 100-127 and 253-285
3. Review backend/tools.py entirely
4. Run test_tools.py to verify backend works
5. Focus on making Tauri UI actually use the tools
6. User will test by asking "Read the README file"
7. If AI says "I can't" - you need to fix tool calling
8. If AI uses tools - mission accomplished

**Key insight**: The backend tool system WORKS (verified). The question is whether the AI in the Tauri UI will actually INVOKE the tools when asked.

---

## FINAL NOTES

This is a **passion project** for the user. They want:
- Independence from cloud AI services
- A personal assistant that truly helps
- Beautiful, minimal UI
- Real capabilities, not chatbot limitations

The tools are implemented. The architecture is sound. The last 5% is making sure the AI in the Tauri UI knows it has tools and uses them.

**Good luck, Codex. The baton is yours if needed.**

---

**Document prepared by**: Claude Sonnet 4.5 (Anthropic)
**Date**: February 9, 2026, 2:40 AM
**Status**: Tools implemented, awaiting user verification
**Next step**: User tests Tauri UI, decides if Codex takes over
