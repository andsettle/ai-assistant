"""Tool system for AI assistant to interact with the system."""
import os
import re
import json
from typing import Optional, Dict, Any
from screen_capture import ScreenCapture


class ToolExecutor:
    """Executes tools requested by the AI."""

    def __init__(self, screen_capture: ScreenCapture):
        self.screen_capture = screen_capture
        self._allowed_tools = {
            "read_file",
            "write_file",
            "list_files",
            "capture_screen",
            "get_system_info",
            "search_files",
            "run_shell_command",
        }

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse tool calls from AI response.

        Supported formats:
        - TOOL_CALL: tool_name(arg1, key=value)
        - TOOL_CALL: {"tool": "read_file", "kwargs": {"filepath": "..."}}
        - JSON tool calls inside code fences or raw JSON objects
        - OpenAI-style tool_calls/function objects (best-effort)
        """
        if not text:
            return None

        # 1) Explicit TOOL_CALL line
        line_match = re.search(r"TOOL_CALL:\s*(.+)", text)
        if line_match:
            call_text = line_match.group(1).strip()
            parsed = self._parse_json_tool(call_text) or self._parse_call_syntax(call_text)
            if parsed:
                return parsed

        # 2) JSON in fenced block
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            fence_body = fence_match.group(1).strip()
            parsed = self._parse_json_tool(fence_body)
            if parsed:
                return parsed

        # 3) Any JSON object in text
        for obj in self._extract_json_objects(text):
            parsed = self._parse_json_tool(obj)
            if parsed:
                return parsed

        # 4) Fallback to function-style call without TOOL_CALL prefix
        func_match = re.search(r"\b(\w+)\s*\((.*?)\)", text)
        if func_match:
            tool_name = func_match.group(1)
            if tool_name in self._allowed_tools:
                return self._parse_call_syntax(func_match.group(0))

        return None

    def _parse_call_syntax(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse: tool_name(arg1, arg2, key=value)"""
        pattern = r"^(\w+)\s*\((.*)\)$"
        match = re.match(pattern, text.strip())
        if not match:
            return None

        tool_name = match.group(1)
        if tool_name not in self._allowed_tools:
            return None

        args_str = match.group(2)
        args = []
        kwargs = {}

        if args_str.strip():
            # Split by comma, respecting quotes
            parts = re.findall(r'(?:[^,\"]|"(?:\\.|[^\"])*")+', args_str)

            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if "=" in part:
                    key, value = part.split("=", 1)
                    kwargs[key.strip()] = self._parse_value(value.strip())
                else:
                    args.append(self._parse_value(part))

        return {"tool": tool_name, "args": args, "kwargs": kwargs}

    def _parse_json_tool(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON tool calls with multiple common shapes."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Models often output Windows paths with single backslashes
            # which are invalid JSON. Escape them and retry.
            try:
                fixed = re.sub(r'(?<!\\)\\(?![\\"/bfnrtu])', r'\\\\', text)
                data = json.loads(fixed)
            except Exception:
                return None
        except Exception:
            return None

        # OpenAI-style tool_calls list
        if isinstance(data, dict) and "tool_calls" in data:
            calls = data.get("tool_calls") or []
            if calls and isinstance(calls, list):
                call = calls[0]
                fn = call.get("function", {}) if isinstance(call, dict) else {}
                name = fn.get("name")
                args = fn.get("arguments")
                kwargs = {}
                if isinstance(args, str):
                    try:
                        kwargs = json.loads(args)
                    except Exception:
                        kwargs = {}
                elif isinstance(args, dict):
                    kwargs = args
                if name in self._allowed_tools:
                    return {"tool": name, "args": [], "kwargs": kwargs}

        # Simple formats: {"tool": "read_file", "args": [...], "kwargs": {...}}
        if isinstance(data, dict):
            name = data.get("tool") or data.get("tool_name") or data.get("name")

            # OpenAI function object
            if not name and isinstance(data.get("function"), dict):
                name = data["function"].get("name")
                args = data["function"].get("arguments") or data["function"].get("parameters")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                if name in self._allowed_tools:
                    if isinstance(args, list):
                        return {"tool": name, "args": args, "kwargs": {}}
                    if isinstance(args, dict):
                        return {"tool": name, "args": [], "kwargs": args}
                    return {"tool": name, "args": [], "kwargs": {}}

            if name in self._allowed_tools:
                args = data.get("args", [])
                kwargs = data.get("kwargs", {})
                if isinstance(data.get("parameters"), dict):
                    kwargs = data.get("parameters")
                if isinstance(data.get("arguments"), dict):
                    kwargs = data.get("arguments")
                elif isinstance(data.get("arguments"), str):
                    try:
                        kwargs = json.loads(data["arguments"])
                    except Exception:
                        pass
                if isinstance(args, dict):
                    kwargs = args
                    args = []
                if not isinstance(args, list):
                    args = []
                if not isinstance(kwargs, dict):
                    kwargs = {}
                return {"tool": name, "args": args, "kwargs": kwargs}

        return None

    def _extract_json_objects(self, text: str) -> list[str]:
        """Best-effort extraction of JSON objects from text."""
        objects = []
        stack = []
        start = None

        for i, ch in enumerate(text):
            if ch == "{":
                if not stack:
                    start = i
                stack.append(ch)
            elif ch == "}":
                if stack:
                    stack.pop()
                    if not stack and start is not None:
                        obj = text[start : i + 1]
                        objects.append(obj)
                        start = None

        return objects

    def _parse_value(self, value: str) -> Any:
        """Parse a string value into appropriate Python type."""
        value = value.strip()

        # Remove quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]

        # Try to parse as number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        return value

    async def execute(self, tool_call: Dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        tool_name = tool_call["tool"]
        args = tool_call["args"]
        kwargs = tool_call["kwargs"]

        try:
            if tool_name == "read_file":
                return await self.read_file(*args, **kwargs)
            elif tool_name == "write_file":
                return await self.write_file(*args, **kwargs)
            elif tool_name == "list_files":
                return await self.list_files(*args, **kwargs)
            elif tool_name == "capture_screen":
                return await self.capture_screen(*args, **kwargs)
            elif tool_name == "get_system_info":
                return await self.get_system_info()
            elif tool_name == "search_files":
                return await self.search_files(*args, **kwargs)
            elif tool_name == "run_shell_command":
                return await self.run_shell_command(*args, **kwargs)
            else:
                return f"ERROR: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"ERROR: Tool execution failed: {str(e)}"

    async def read_file(self, filepath: str, max_lines: int = 1000) -> str:
        """Read a file and return its contents."""
        try:
            # Expand user path
            filepath = os.path.expanduser(filepath)

            # Security: Only allow reading from user directory
            user_dir = os.path.expanduser("~")
            abs_path = os.path.abspath(filepath)

            if not abs_path.startswith(user_dir):
                return f"ERROR: Can only read files in user directory ({user_dir})"

            if not os.path.exists(abs_path):
                return f"ERROR: File not found: {filepath}"

            # Read file
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Limit lines
            if len(lines) > max_lines:
                content = "".join(lines[:max_lines])
                content += f"\n\n[File truncated - showing first {max_lines} of {len(lines)} lines]"
            else:
                content = "".join(lines)

            return f"FILE: {filepath}\n\n{content}"

        except Exception as e:
            return f"ERROR reading file: {str(e)}"

    async def write_file(
        self,
        filepath: str,
        content: str,
        mode: str = "overwrite"
    ) -> str:
        """Write content to a file. mode: overwrite|append."""
        try:
            filepath = os.path.expanduser(filepath)
            user_dir = os.path.expanduser("~")
            abs_path = os.path.abspath(filepath)

            if not abs_path.startswith(user_dir):
                return f"ERROR: Can only write files in user directory ({user_dir})"

            dir_path = os.path.dirname(abs_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            if mode not in ("overwrite", "append"):
                return "ERROR: mode must be 'overwrite' or 'append'"

            file_mode = "w" if mode == "overwrite" else "a"
            with open(abs_path, file_mode, encoding="utf-8", errors="ignore") as f:
                f.write(content)

            return f"OK: Wrote {len(content)} chars to {filepath} (mode={mode})"

        except Exception as e:
            return f"ERROR writing file: {str(e)}"

    async def list_files(self, directory: str = ".", pattern: str = "*") -> str:
        """List files in a directory."""
        try:
            import glob

            # Expand user path
            directory = os.path.expanduser(directory)

            # Security: Only allow listing user directory
            user_dir = os.path.expanduser("~")
            abs_dir = os.path.abspath(directory)

            if not abs_dir.startswith(user_dir):
                return f"ERROR: Can only list files in user directory ({user_dir})"

            if not os.path.exists(abs_dir):
                return f"ERROR: Directory not found: {directory}"

            # List files
            search_pattern = os.path.join(abs_dir, pattern)
            files = glob.glob(search_pattern)

            # Format output
            result = f"DIRECTORY: {directory}\n\n"

            if not files:
                result += "No files found."
            else:
                # Separate directories and files
                dirs = [f for f in files if os.path.isdir(f)]
                files_only = [f for f in files if os.path.isfile(f)]

                if dirs:
                    result += "Directories:\n"
                    for d in sorted(dirs):
                        result += f"  [DIR] {os.path.basename(d)}/\n"

                if files_only:
                    result += "\nFiles:\n"
                    for f in sorted(files_only):
                        size = os.path.getsize(f)
                        size_str = self._format_size(size)
                        result += f"  [FILE] {os.path.basename(f)} ({size_str})\n"

                result += f"\nTotal: {len(dirs)} directories, {len(files_only)} files"

            return result

        except Exception as e:
            return f"ERROR listing files: {str(e)}"

    async def capture_screen(self, monitor: int = 0) -> str:
        """Capture a screenshot."""
        try:
            # Capture screenshot
            image_base64 = self.screen_capture.capture_as_base64(
                monitor_number=monitor,
                format="JPEG",
                quality=85
            )

            payload = {
                "type": "screenshot",
                "monitor": monitor,
                "format": "JPEG",
                "quality": 85,
                "image_base64": image_base64,
                "bytes": len(image_base64)
            }
            return json.dumps(payload)

        except Exception as e:
            return f"ERROR capturing screen: {str(e)}"

    async def get_system_info(self) -> str:
        """Get system information."""
        try:
            import platform
            import psutil

            info = f"""SYSTEM INFORMATION:

OS: {platform.system()} {platform.release()}
Machine: {platform.machine()}
Processor: {platform.processor()}
Python: {platform.python_version()}

CPU Cores: {psutil.cpu_count()}
CPU Usage: {psutil.cpu_percent(interval=1)}%
RAM Total: {self._format_size(psutil.virtual_memory().total)}
RAM Used: {self._format_size(psutil.virtual_memory().used)} ({psutil.virtual_memory().percent}%)
RAM Available: {self._format_size(psutil.virtual_memory().available)}

Disk Usage: {psutil.disk_usage('/').percent}%
"""
            return info

        except Exception as e:
            return f"ERROR getting system info: {str(e)}"

    async def search_files(self, directory: str, pattern: str) -> str:
        """Search for files matching a pattern."""
        try:
            import glob

            # Expand user path
            directory = os.path.expanduser(directory)

            # Security check
            user_dir = os.path.expanduser("~")
            abs_dir = os.path.abspath(directory)

            if not abs_dir.startswith(user_dir):
                return f"ERROR: Can only search in user directory ({user_dir})"

            # Search recursively
            search_pattern = os.path.join(abs_dir, "**", pattern)
            files = glob.glob(search_pattern, recursive=True)

            result = f"SEARCH RESULTS for '{pattern}' in {directory}:\n\n"

            if not files:
                result += "No files found."
            else:
                for f in sorted(files)[:50]:
                    rel_path = os.path.relpath(f, abs_dir)
                    result += f"  {rel_path}\n"

                if len(files) > 50:
                    result += f"\n[Showing first 50 of {len(files)} results]"

            return result

        except Exception as e:
            return f"ERROR searching files: {str(e)}"

    async def run_shell_command(self, command: str) -> str:
        """Execute a shell command via PowerShell."""
        import asyncio
        try:
            # We are on Windows (win32), use powershell
            process = await asyncio.create_subprocess_exec(
                "powershell.exe", "-NoProfile", "-Command", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='ignore').strip()
            error = stderr.decode('utf-8', errors='ignore').strip()
            
            result = f"Command: {command}\nExit Code: {process.returncode}\n"
            if output:
                result += f"STDOUT:\n{output}\n"
            if error:
                result += f"STDERR:\n{error}\n"
            
            if not output and not error:
                result += "Command executed successfully with no output."
                
            return result
        except Exception as e:
            return f"ERROR executing command '{command}': {str(e)}"

    def _format_size(self, bytes: int) -> str:
        """Format bytes into human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"


def get_ollama_tool_schemas() -> list[dict]:
    """Return tool definitions in Ollama's native function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file. Only files within C:\\Users\\drew\\ can be read.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Full Windows path to the file, e.g. C:\\Users\\drew\\file.txt"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum lines to read (default 1000)"
                        }
                    },
                    "required": ["filepath"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file. Only files within C:\\Users\\drew\\ can be written.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Full Windows path to the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["overwrite", "append"],
                            "description": "Write mode (default overwrite)"
                        }
                    },
                    "required": ["filepath", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files and directories at a given path. Only paths within C:\\Users\\drew\\ are allowed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Full Windows path to the directory"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to filter results (default *)"
                        }
                    },
                    "required": ["directory"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "capture_screen",
                "description": "Capture a screenshot. If the user has multiple monitors they will be prompted to select one. Do NOT pass a monitor number — just call with no arguments.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_system_info",
                "description": "Get system information including OS, CPU, RAM, and disk usage.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Recursively search for files matching a glob pattern. Only paths within C:\\Users\\drew\\ are allowed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Full Windows path to the starting directory"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match (e.g. *.txt, *.py)"
                        }
                    },
                    "required": ["directory", "pattern"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_shell_command",
                "description": "Execute a shell command via PowerShell. Can be used for installing packages, checking system state, running git commands, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The exact command to execute"
                        }
                    },
                    "required": ["command"]
                }
            }
        },
    ]


# Tool descriptions for the AI (fallback for text-pattern mode)
TOOL_DESCRIPTIONS = """
YOU HAVE ACCESS TO THE FOLLOWING TOOLS:

1. read_file(filepath, max_lines=1000)
   - Read contents of a file
   - Example: TOOL_CALL: read_file("C:\\Users\\drew\\ai-assistant\\README.md")

2. write_file(filepath, content, mode="overwrite")
   - Write content to a file (mode: overwrite|append)
   - Example: TOOL_CALL: write_file("C:\\Users\\drew\\Desktop\\hello.txt", "Hello World", mode="overwrite")

3. list_files(directory=".", pattern="*")
   - List files in a directory
   - Example: TOOL_CALL: list_files("C:\\Users\\drew\\ai-assistant")

4. capture_screen(monitor=0)
   - Capture a screenshot
   - Example: TOOL_CALL: capture_screen(monitor=0)

5. get_system_info()
   - Get system information (CPU, RAM, disk)
   - Example: TOOL_CALL: get_system_info()

6. search_files(directory, pattern)
   - Search for files matching a pattern
   - Example: TOOL_CALL: search_files("C:\\Users\\drew", "*.txt")

7. run_shell_command(command)
   - Execute a shell command via PowerShell
   - Example: TOOL_CALL: run_shell_command("pip install requests")

TO USE A TOOL:
1. When a tool is needed, respond ONLY with the tool call line.
2. Do not add explanations, code fences, or extra text.
3. The tool will execute and return results, then you can answer normally.

IMPORTANT:
- Use tools proactively when user asks about files, screen, or system
- Always use full Windows paths with double backslashes (\\)
- Do not say you lack access when a tool applies
"""

