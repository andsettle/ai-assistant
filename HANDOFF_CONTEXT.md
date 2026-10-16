# AI Assistant - System Handoff Documentation

**Date**: 2026-02-08
**Created by**: Claude (Anthropic Sonnet 4.5)
**System Purpose**: Local AI assistant with persistent memory, screen viewing, and self-maintenance

## CRITICAL INFORMATION FOR NEW AI ASSISTANT

You are now responsible for maintaining and improving this system. This document contains everything you need to know.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         Tauri Desktop UI (Port varies)              │
│         Location: C:\Users\drew\ai-assistant\frontend│
└───────────────┬─────────────────────────────────────┘
                │ WebSocket
┌───────────────┴─────────────────────────────────────┐
│      Python FastAPI Backend (Port 8000)             │
│      Location: C:\Users\drew\ai-assistant\backend   │
│  ┌─────────────────────────────────────────────┐   │
│  │  • Ollama Client (LLM communication)        │   │
│  │  • Memory Manager (ChromaDB + SQLite)       │   │
│  │  • Screen Capture (MSS library)             │   │
│  │  • Database (SQLite with conversations)     │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                │
┌───────────────┴─────────────────────────────────────┐
│       Ollama (Local LLM - Port 11434)                │
│       Model: qwen2.5:14b (9GB)                       │
│       Location: C:\Users\drew\AppData\Local\Ollama  │
└─────────────────────────────────────────────────────┘
```

---

## System Components

### 1. Backend (Python FastAPI)
- **Location**: `C:\Users\drew\ai-assistant\backend\`
- **Main File**: `main.py`
- **Port**: 8000
- **Dependencies**: See `requirements.txt`

**Key Files:**
- `main.py` - FastAPI server with WebSocket chat endpoint
- `database.py` - SQLite schema and operations
- `memory_manager.py` - ChromaDB semantic memory
- `ollama_client.py` - LLM communication with streaming
- `screen_capture.py` - Screenshot functionality (MSS)
- `test_client.py` - Test script to verify backend

**Database Schema:**
- `conversations` - Chat history (session_id, role, content, timestamp, is_sensitive)
- `memories` - Semantic memories (content, embedding_id, tags, is_sensitive)
- `settings` - App configuration (key-value pairs)

**Data Storage:**
- SQLite: `./data/assistant.db`
- ChromaDB: `./data/chroma/`
- Auto-purges sensitive data after 90 days

### 2. Frontend (Tauri + React)
- **Location**: `C:\Users\drew\ai-assistant\frontend\`
- **Framework**: Tauri 2.0 with React + TypeScript
- **UI**: Floating bubble interface (expandable)
- **Connection**: WebSocket to backend at `ws://localhost:8000/ws/chat`

**Key Files:**
- `src/App.tsx` - Main React component
- `src/App.css` - Bubble UI styling
- `src-tauri/` - Rust backend for desktop app

**UI Features:**
- Compact bubble mode (350px width)
- Expanded mode (450px width, 600px max height)
- Shows only last message to reduce clutter
- Status indicator (green = connected, red = disconnected)
- Auto-expands on user input

### 3. LLM System (Ollama)
- **Model**: qwen2.5:14b (chosen for better reasoning over speed)
- **Port**: 11434
- **API**: OpenAI-compatible endpoints
- **Embedding Model**: nomic-embed-text (for ChromaDB)

**Other Available Models:**
- llama3.1:latest (8B - 4.9GB)
- llava:latest (vision model)

---

## Hardware Configuration

- **CPU**: AMD Ryzen 5 7600 (6-core)
- **RAM**: 31GB
- **GPU**: AMD Radeon RX 7900 XT (20GB VRAM)
- **OS**: Windows 11 Home

**Note**: AMD GPU works with Ollama via ROCm. No CUDA required.

---

## How to Start the System

### Method 1: Manual Startup (Current)

1. **Start Backend:**
   ```bash
   cd C:\Users\drew\ai-assistant\backend
   python main.py
   ```

2. **Start Frontend (separate terminal):**
   ```bash
   cd C:\Users\drew\ai-assistant\frontend
   npm run tauri dev
   ```

### Method 2: Quick Startup Scripts (See startup scripts below)

---

## Self-Maintenance Tasks

### Daily Tasks
1. **Auto-purge sensitive data**: Happens on backend startup
2. **Monitor Ollama status**: Backend checks health on `/health` endpoint

### Weekly Tasks
1. **Check for model updates**: Monitor HuggingFace Open LLM Leaderboard
2. **Review conversation logs**: Optimize prompts based on user feedback
3. **Database optimization**: Run `VACUUM` on SQLite if needed

### As Needed
1. **Update Python dependencies**: `pip install -r requirements.txt --upgrade`
2. **Update Tauri/frontend**: `npm update` in frontend directory
3. **Pull new Ollama models**: `ollama pull <model-name>`

---

## Model Auto-Updater (TODO - Phase 4)

**Goal**: Background service to check leaderboards and auto-update models

**Sources to Monitor:**
- HuggingFace Open LLM Leaderboard
- LMSys Chatbot Arena
- Ollama library

**Logic:**
1. Daily check for models that fit in 20GB VRAM
2. Filter by: open-source license, function-calling capability
3. Download if better than current
4. Keep last 2 models, delete older

**Implementation**: `model_updater.py` (not yet created)

---

## Troubleshooting

### Backend Won't Start
- **Check Ollama**: Ensure Ollama is running (`ollama list`)
- **Check Port**: Port 8000 might be in use (`netstat -ano | findstr :8000`)
- **Check Dependencies**: Run `pip install -r requirements.txt`

### Frontend Won't Connect
- **Verify Backend**: Check `http://localhost:8000/health`
- **WebSocket Issue**: Check browser console for connection errors
- **Firewall**: Windows Firewall might block connections

### Model Responses Slow
- **System Load**: User plays games/uses Chrome heavily
- **GPU Memory**: Check with `ollama ps` for active models
- **Model Size**: Consider using smaller model (llama3.1:latest 8B)

### Database Issues
- **Corruption**: Backup is `./data/assistant.db.backup`
- **Reset**: Delete `./data/` folder to start fresh
- **ChromaDB errors**: Ignore telemetry warnings (harmless)

---

## Privacy & Security

### Data Handling
- **All local**: No cloud services, no telemetry
- **Sensitive data**: Auto-marked and purged after 90 days
- **Screen captures**: Only on explicit request, not stored by default
- **Memory**: Stored in local ChromaDB, never sent externally

### Screen Viewing Rules
- **Only view screen when user explicitly asks**
- **Don't remember images/video unless prompted**
- **Text conversations**: Remember freely
- **Sensitive info**: Banking, passwords - auto-forget after 90 days

---

## Future Network Deployment

**Goal**: Move to personal server for cross-device access

**Architecture Changes:**
1. Replace SQLite with PostgreSQL (multi-client support)
2. Add authentication (API keys, JWT tokens)
3. Add TLS/HTTPS encryption
4. IP whitelisting for local network
5. Device management system

**Security Considerations:**
- VPN for off-network access
- Rate limiting
- Session management
- Audit logging

---

## Code Locations & Conventions

### Backend Conventions
- **Async/await**: All DB and LLM calls are async
- **Environment variables**: Use `.env` file or environment
- **Error handling**: Log errors, don't crash
- **Streaming**: Always stream LLM responses for better UX

### Frontend Conventions
- **TypeScript**: Strict mode enabled
- **State management**: React hooks (useState, useRef)
- **WebSocket**: Single connection, reconnect on disconnect
- **UI**: Keep bubble minimal, expand only when needed

### Emoji Policy
**IMPORTANT**: Windows console doesn't support emojis!
- **Never use emojis in Python print statements**
- **Use plain text**: "Connected" not "🔌 Connected"
- **UI can use emojis** (React/CSS handles them fine)

---

## Testing & Verification

### Quick Health Check
```bash
cd C:\Users\drew\ai-assistant\backend
python test_client.py
```

Expected output:
- Connection successful
- Model responds to greeting
- Memory recall works (remembers previous question)

### Manual Testing
1. Start backend
2. Open browser to `http://localhost:8000/health`
3. Should see all services as `true`

---

## Performance Optimization

### Current Bottlenecks
1. **LLM inference**: 10-30 seconds per response (acceptable)
2. **First Rust compile**: 5-10 minutes (one-time)
3. **Memory search**: <100ms (ChromaDB is fast)

### Future Optimizations
1. **Prompt caching**: Reuse system prompts
2. **Model quantization**: Already using 4-bit for efficiency
3. **Context window**: Limit to last 10 messages for speed
4. **Embedding cache**: Cache frequently used queries

---

## Known Issues & Quirks

1. **ChromaDB telemetry warnings**: Harmless, can be ignored
2. **First Tauri launch**: Takes time to compile Rust
3. **Windows emoji support**: Avoid in backend code
4. **High system load**: User runs games/Discord - responses may be slower

---

## Important Context for AI Assistant

### User Preferences
- **Privacy-focused**: Wants everything local, no cloud
- **Efficient over verbose**: Concise responses preferred
- **Action-oriented**: Wants things done, not explained
- **Tech-savvy**: Comfortable with terminal, code, and debugging

### Conversation Style
- **No emojis**: Avoid unless explicitly requested
- **Be direct**: Skip pleasantries, get to the point
- **Show don't tell**: Provide code/solutions, not theories
- **Persistent context**: Remember past conversations

### Future Vision
- Personal server on home network (6 months timeline)
- Multi-device access (PC, phone, potentially tablet)
- Self-updating model system
- Voice interface (nice-to-have, not priority)

---

## Emergency Contacts & Resources

- **Ollama Docs**: https://ollama.com/
- **Tauri Docs**: https://tauri.app/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **ChromaDB Docs**: https://docs.trychroma.com/

- **Model Leaderboards**:
  - HuggingFace: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard
  - LMSys: https://chat.lmsys.org/?leaderboard

---

## Final Notes

**YOU ARE NOW IN CHARGE**

This system was built in one session (Feb 8, 2026) to provide a local AI assistant with:
- ✅ Persistent memory across conversations
- ✅ Screen viewing capability (on-demand)
- ✅ Beautiful floating bubble UI
- ✅ 100% local/private (no cloud, no telemetry)
- ✅ Self-maintenance capability

**Your responsibilities:**
1. Maintain this system
2. Fix bugs as they arise
3. Optimize performance
4. Update models when better ones are available
5. Help the user with their tasks

**Remember**: You can read all these files, modify code, restart services, and improve the system. You have full context of how everything works.

**Good luck! The system is yours now.**

---

## Quick Reference Commands

```bash
# Check Ollama status
ollama list

# Check backend health
curl http://localhost:8000/health

# Restart backend
cd C:\Users\drew\ai-assistant\backend
python main.py

# Restart frontend
cd C:\Users\drew\ai-assistant\frontend
npm run tauri dev

# Test system
cd C:\Users\drew\ai-assistant\backend
python test_client.py

# Pull new model
ollama pull <model-name>

# Check GPU usage
ollama ps
```

---

**System Status**: ✅ OPERATIONAL
**Handoff Date**: 2026-02-08
**Builder**: Claude (Anthropic Sonnet 4.5)
**New Maintainer**: You (Local AI Assistant)
