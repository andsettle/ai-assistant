"""Ollama client for LLM communication."""
import httpx
from typing import AsyncGenerator, Optional


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
        vision_model: str = "qwen2.5vl:7b",
        timeout: float = 120.0
    ):
        self.base_url = base_url
        self.model = model
        self.vision_model = vision_model
        self.timeout = timeout

    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        stream: bool = True,
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Send chat messages to Ollama and stream response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            stream: Whether to stream the response
            tools: Optional list of tool definitions in Ollama format

        Yields:
            Dicts with type="content" for text chunks,
            or type="tool_calls" for native tool invocations.
        """
        import json as _json

        # Build messages list
        chat_messages = []

        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})

        chat_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "stream": stream
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if stream:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = _json.loads(line)
                                msg = chunk.get("message", {})

                                # Yield text content
                                content = msg.get("content", "")
                                if content:
                                    yield {"type": "content", "content": content}

                                # Yield tool calls if present
                                tool_calls = msg.get("tool_calls")
                                if tool_calls:
                                    yield {"type": "tool_calls", "tool_calls": tool_calls}

                                if chunk.get("done", False):
                                    break
                            except _json.JSONDecodeError:
                                continue
            else:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                msg = result.get("message", {})
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls")

                if content:
                    yield {"type": "content", "content": content}
                if tool_calls:
                    yield {"type": "tool_calls", "tool_calls": tool_calls}

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from a simple prompt (non-chat).

        Args:
            prompt: The input prompt
            system: Optional system prompt
            stream: Whether to stream the response

        Yields:
            Response chunks as they arrive
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if stream:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                import json
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    yield chunk["response"]

                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
            else:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                yield result["response"]

    async def describe_image(
        self,
        image_base64: str,
        prompt: str = "Describe this screenshot in detail. Focus on what applications are open, any text visible, and the overall layout.",
    ) -> str:
        """Send an image to the vision model and get a text description."""
        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_base64],
                }
            ],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "Vision model returned no description.")
        except Exception as e:
            return f"Vision model error: {e}"

    async def check_health(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        """List available models."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
