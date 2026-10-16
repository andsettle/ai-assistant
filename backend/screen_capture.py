"""Screen capture functionality using MSS."""
import mss
import mss.tools
from PIL import Image
from io import BytesIO
import base64
from typing import Optional


class ScreenCapture:
    """Handles screen capture operations."""

    def __init__(self):
        self.sct = mss.mss()

    def capture_screen(self, monitor_number: int = 0) -> Image.Image:
        """
        Capture a screenshot of the specified monitor.

        Args:
            monitor_number: Monitor to capture (0 = all monitors, 1+ = specific monitor)

        Returns:
            PIL Image object
        """
        # Get monitor
        if monitor_number == 0:
            monitor = self.sct.monitors[0]  # All monitors
        else:
            monitor = self.sct.monitors[monitor_number]

        # Capture screenshot
        screenshot = self.sct.grab(monitor)

        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

        return img

    def capture_as_base64(
        self,
        monitor_number: int = 0,
        format: str = "JPEG",
        quality: int = 85
    ) -> str:
        """
        Capture screenshot and return as base64-encoded string.

        Args:
            monitor_number: Monitor to capture
            format: Image format (JPEG, PNG)
            quality: JPEG quality (1-100)

        Returns:
            Base64-encoded image string
        """
        img = self.capture_screen(monitor_number)

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format=format, quality=quality)
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_base64

    def capture_and_save(
        self,
        filepath: str,
        monitor_number: int = 0,
        format: str = "PNG"
    ) -> str:
        """
        Capture screenshot and save to file.

        Args:
            filepath: Path to save the image
            monitor_number: Monitor to capture
            format: Image format

        Returns:
            Path to saved file
        """
        img = self.capture_screen(monitor_number)
        img.save(filepath, format=format)
        return filepath

    def get_monitor_count(self) -> int:
        """Get number of available monitors."""
        return len(self.sct.monitors) - 1  # Subtract 1 for the "all monitors" entry

    def get_monitor_info(self) -> list[dict]:
        """Get information about all monitors."""
        monitors = []
        for i, monitor in enumerate(self.sct.monitors):
            if i == 0:
                continue  # Skip "all monitors" entry
            monitors.append({
                "id": i,
                "width": monitor["width"],
                "height": monitor["height"],
                "left": monitor["left"],
                "top": monitor["top"]
            })
        return monitors

    def close(self):
        """Close the screen capture object."""
        self.sct.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
