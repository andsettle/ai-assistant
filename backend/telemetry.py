import asyncio
import ctypes
import json
import time
from typing import Callable, Optional
import httpx

user32 = ctypes.windll.user32

def get_active_window_title() -> str:
    """Get the title of the currently active (foreground) window."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

class TelemetryMonitor:
    def __init__(self, ollama_url: str, evaluator_model: str, on_suggestion: Callable):
        self.ollama_url = ollama_url
        self.evaluator_model = evaluator_model
        self.on_suggestion = on_suggestion
        self.history = []
        self.running = False
        self._task = None

    def start(self):
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    async def _monitor_loop(self):
        last_title = ""
        while self.running:
            try:
                current_title = get_active_window_title()
                # Ignore self and empty
                if current_title and current_title != last_title and "Navi" not in current_title:
                    self.history.append({"time": time.time(), "title": current_title})
                    last_title = current_title
                    
                    if len(self.history) > 10:
                        self.history.pop(0)

                # Evaluate every 20 seconds if we have sufficient context
                if len(self.history) >= 3:
                    await self._evaluate_context()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Telemetry loop error: {e}")
            
            await asyncio.sleep(20)

    async def _evaluate_context(self):
        history_text = "\n".join([f"- {item['title']}" for item in self.history])
        
        system_prompt = (
            "You are Navi's background monitor evaluator. You watch the user's active window titles. "
            "Your job is to decide if the user could use help (e.g., debugging an error, coding, stuck on a problem). "
            "If the user is just browsing casually, playing a game, or chatting, ignore it. "
            'If they need help, output a JSON object: {"help_needed": true, "suggestion": "A short, friendly 1-sentence offer to help"}. '
            'If no help is needed, output: {"help_needed": false}. '
            "IMPORTANT: Output ONLY valid JSON, nothing else."
        )

        prompt = f"User's recent windows:\n{history_text}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.evaluator_model,
                        "system": system_prompt,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result_text = data.get("response", "{}")
                    try:
                        result = json.loads(result_text)
                        if result.get("help_needed") and result.get("suggestion"):
                            await self.on_suggestion(result["suggestion"])
                            # Clear history so we don't spam
                            self.history.clear()
                    except json.JSONDecodeError:
                        pass
        except Exception:
            # Silently fail if ollama is busy/unavailable
            pass
