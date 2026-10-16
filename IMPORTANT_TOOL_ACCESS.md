# IMPORTANT: AI Tool Access Clarification

## The Current Limitation

**The AI assistant in the Tauri UI does NOT have direct file/screen access yet.**

Here's why:
- The Tauri UI connects to Qwen2.5:14b via Ollama
- Qwen is just a language model - it has NO tools
- It can only chat, remember conversations, and reason

**What this means:**
- The AI can't read files on its own
- The AI can't take screenshots on its own
- The AI can't run commands on its own

## Two Ways to Use the Assistant

### Option 1: Through Tauri UI (Current - Limited)
**What works:**
- ✅ Chat conversations
- ✅ Persistent memory across sessions
- ✅ Intelligent responses
- ✅ Context retention

**What doesn't work:**
- ❌ Automatic file reading
- ❌ Automatic screen capture
- ❌ Command execution

**Workaround:**
You need to manually provide information:
- Copy/paste file contents into chat
- Share screenshots manually
- Tell it what you see on your screen

### Option 2: Through Claude Code (Full Access)
If you open this project in Claude Code:
- ✅ Full file system access (Read, Edit, Write tools)
- ✅ Terminal access (Bash tool)
- ✅ Screen capture capability
- ✅ Can maintain itself

**This is how you should interact with it for maintenance tasks.**

## The Solution (To Be Implemented)

To give the Tauri UI assistant real tool access, we need to add **function calling**:

```python
# In main.py, add tool definitions:
TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the system",
        "parameters": {"path": "string"}
    },
    {
        "name": "capture_screen",
        "description": "Take a screenshot",
        "parameters": {"monitor": "int"}
    },
    {
        "name": "run_command",
        "description": "Execute a system command",
        "parameters": {"command": "string"}
    }
]

# Then implement tool calling in the WebSocket handler
# When the AI wants to use a tool, intercept and execute it
```

## Quick Fix: Command System

Until function calling is implemented, you can use text commands:

Add to the chat logic:
- `!read <filepath>` - Read a file
- `!screenshot` - Take screenshot
- `!help` - Show available commands

## Recommended Usage Right Now

**For chatting and brainstorming:**
→ Use the Tauri UI (it's beautiful and remembers everything)

**For system maintenance and file operations:**
→ Use Claude Code to talk to the assistant
→ The AI can read HANDOFF_CONTEXT.md and maintain itself

## Example Interaction (Current State)

**What WON'T work:**
```
You: "Look at my screen and tell me what you see"
AI: "I don't have direct screen access yet..."
```

**What WILL work:**
```
You: "I'm looking at VS Code with errors. Let me paste them..."
[paste error text]
AI: "Those errors are caused by..."
```

**Or use Claude Code:**
```
You (in Claude Code): "Read the backend logs and check for errors"
AI: *Uses Read tool to open logs*
"I see the following errors in backend/logs/..."
```

## Next Steps

1. **Short term**: Use the Tauri UI for conversations, Claude Code for maintenance
2. **Medium term**: Implement command system (!read, !screenshot)
3. **Long term**: Add full function calling support to give the UI assistant real tools

## Why This Matters

You wanted the AI to:
- ✅ Remember conversations - **WORKS**
- ❌ View your screen - **NEEDS IMPLEMENTATION**
- ❌ Access files - **NEEDS IMPLEMENTATION**
- ✅ Self-maintain - **WORKS through Claude Code**

The memory and conversation parts are perfect. The tool access needs more work.

## Immediate Action Items

1. **For daily use**: Chat in Tauri UI, manually share context
2. **For maintenance**: Use Claude Code to interact with the assistant
3. **To improve**: Implement function calling (see backend/main.py)

---

**TL;DR**: The AI assistant works great for conversations and remembers everything. For file/screen access, either manually share info OR use Claude Code to give it full access to tools.
