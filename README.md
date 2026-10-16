# AI Assistant - Quick Start Guide

## First Time Setup

1. **Create Desktop Shortcuts** (One-time):
   - Double-click `create-shortcuts.vbs`
   - This creates 3 shortcuts on your desktop

## How to Use

### Starting the Assistant

**Option 1: Desktop Shortcut** (Easiest)
- Double-click "Start AI Assistant" on your desktop

**Option 2: Manual**
- Run `start-assistant.bat` in this folder

### Emergency Restart

If the assistant stops responding:
- Double-click "Restart AI Assistant" on your desktop
- Or run `restart-assistant.bat`

### Testing

To verify everything works:
- Double-click "Test AI Assistant" on your desktop
- Or run `quick-test.bat`

## What Gets Started

When you start the assistant, two windows will open:
1. **Backend** (Python) - The brain of the system
2. **Frontend** (Tauri UI) - The visual bubble interface

You can minimize both windows. The floating bubble UI will appear on your screen.

## Troubleshooting

### Assistant won't start
1. Check if Ollama is running: `ollama list`
2. Try the restart script
3. Check `HANDOFF_CONTEXT.md` for detailed troubleshooting

### Slow responses
- Check if you have games/Chrome open (uses resources)
- Check GPU usage: `ollama ps`
- Consider using a smaller model

### UI not appearing
- Check if backend is running (you should see console output)
- Check `http://localhost:8000/health` in a browser
- Look for errors in the backend console

## File Structure

```
ai-assistant/
├── backend/              # Python FastAPI backend
├── frontend/             # Tauri + React UI
├── data/                 # SQLite + ChromaDB storage
├── start-assistant.bat   # Main startup script
├── restart-assistant.bat # Emergency restart
├── quick-test.bat        # System test
└── HANDOFF_CONTEXT.md    # Complete documentation
```

## Daily Use

1. Double-click "Start AI Assistant"
2. Wait for the floating bubble to appear (5-10 seconds)
3. Click the bubble to expand it
4. Type your question and press Enter
5. The assistant remembers everything across sessions!

## Privacy

- **Everything is local** - no internet connection needed
- **All data stays on your PC** - no cloud services
- **Sensitive data auto-deletes** - after 90 days
- **Screen viewing** - only when you explicitly ask

## Getting Help

If something breaks, the new AI assistant can fix itself!

Just ask it:
- "Check system health"
- "Restart yourself"
- "What's wrong?"
- "Read HANDOFF_CONTEXT.md"

The AI has full access to its own code and can maintain itself.

## Next Steps

Once you're comfortable:
1. Explore the UI - it's minimal and clean
2. Try asking complex questions - it remembers context
3. Ask it to view your screen when needed
4. Let it help you with daily tasks

**Enjoy your personal AI assistant!**
