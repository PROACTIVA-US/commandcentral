"""
Browser Service - Chrome for Testing Integration

Provides persistent browser automation for pipelines:
- Auto-starts Chrome for Testing on service init
- Manages browser lifecycle without authorization
- Captures screenshots, navigates pages
- Integrates with pipeline executor actions

Uses Chrome DevTools Protocol (CDP) for reliable automation.

Configuration from: skills/operations/chrome-for-testing-setup.md
Key requirements:
- Persistent profile (~/.chrome-for-testing-profile) for login/session state
- Claude extension loaded from regular Chrome installation
- Remote debugging port 9222 for auto-authorization
- Launch script: ~/.claude/launch-chrome-for-testing.sh
"""

import os
import asyncio
import subprocess
import json
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import httpx
import structlog

logger = structlog.get_logger(__name__)

# =============================================================================
# Chrome for Testing Configuration
# From: skills/operations/chrome-for-testing-setup.md
#
# Key requirements:
# - Use persistent profile for login/session state
# - Load Claude extension from regular Chrome
# - Enable remote debugging port 9222 for auto-authorization
# - Use Chrome for Testing (not regular Chrome)
# =============================================================================

# Chrome for Testing paths (ordered by preference)
CHROME_PATHS = [
    # Puppeteer-installed Chrome for Testing (preferred)
    os.path.expanduser("~/.cache/puppeteer/chrome/mac_arm-141.0.7390.54/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
    os.path.expanduser("~/.cache/puppeteer/chrome/mac_arm-*/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"),
    # Fallbacks
    "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
]

# Persistent profile directory (preserves logins across restarts)
PROFILE_DIR = os.path.expanduser("~/.chrome-for-testing-profile")

# Claude extension path (loaded from regular Chrome installation)
CLAUDE_EXTENSION_ID = "fcoeoabgfenejglbffodgkkbkcdhcgfn"
CLAUDE_EXTENSION_BASE = os.path.expanduser(
    f"~/Library/Application Support/Google/Chrome/Default/Extensions/{CLAUDE_EXTENSION_ID}"
)

# Screenshots directory
SCREENSHOTS_DIR = Path("/tmp/pipelzr-screenshots")


@dataclass
class BrowserContext:
    """Active browser context."""
    process: Optional[subprocess.Popen] = None
    debug_port: int = 9222
    ws_url: Optional[str] = None
    target_id: Optional[str] = None
    session_id: Optional[str] = None
    ready: bool = False


@dataclass
class Screenshot:
    """Captured screenshot."""
    path: str
    name: str
    url: str
    timestamp: str
    width: int
    height: int
    state: str = "default"


class BrowserService:
    """
    Persistent browser service for pipeline automation.

    Auto-starts on first use, stays running for pipeline lifetime.
    No authorization required - uses local Chrome instance.
    """

    def __init__(self):
        self.context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()
        self._message_id = 0
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def _find_chrome(self) -> Optional[str]:
        """Find Chrome for Testing executable."""
        import glob
        for pattern in CHROME_PATHS:
            if "*" in pattern:
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]
            elif os.path.exists(pattern):
                return pattern
        return None

    def _find_claude_extension(self) -> Optional[str]:
        """Find latest Claude extension version."""
        import glob
        if os.path.exists(CLAUDE_EXTENSION_BASE):
            versions = glob.glob(os.path.join(CLAUDE_EXTENSION_BASE, "*"))
            if versions:
                # Return the latest version
                return sorted(versions)[-1]
        return None

    async def ensure_browser(self) -> BrowserContext:
        """
        Ensure Chrome for Testing is running with proper configuration.

        Configuration from: skills/operations/chrome-for-testing-setup.md
        - Uses persistent profile for login/session state
        - Loads Claude extension for MCP integration
        - Enables remote debugging port 9222 for auto-authorization
        """
        async with self._lock:
            if self.context and self.context.ready:
                return self.context

            debug_port = 9222

            # Check if Chrome for Testing is already running on debug port
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:{debug_port}/json/version",
                        timeout=2.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        self.context = BrowserContext(
                            process=None,  # External process
                            debug_port=debug_port,
                            ws_url=data.get("webSocketDebuggerUrl"),
                            ready=True
                        )
                        logger.info(
                            "Connected to existing Chrome for Testing",
                            debug_port=debug_port
                        )
                        return self.context
            except Exception:
                pass  # Need to start browser

            # Find Chrome for Testing
            chrome_path = self._find_chrome()
            if not chrome_path:
                raise RuntimeError(
                    "Chrome for Testing not found. Install with: "
                    "npx @puppeteer/browsers install chrome@stable"
                )

            # Find Claude extension
            extension_path = self._find_claude_extension()

            # Ensure persistent profile directory exists
            os.makedirs(PROFILE_DIR, exist_ok=True)

            # Build Chrome arguments per skill requirements
            chrome_args = [
                chrome_path,
                f"--user-data-dir={PROFILE_DIR}",
                f"--remote-debugging-port={debug_port}",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1920,1080",
            ]

            # Load Claude extension if available
            if extension_path:
                chrome_args.extend([
                    f"--load-extension={extension_path}",
                    f"--disable-extensions-except={extension_path}",
                ])
                logger.info("Loading Claude extension", path=extension_path)
            else:
                chrome_args.append("--disable-extensions")
                logger.warning("Claude extension not found, running without it")

            chrome_args.append("about:blank")

            # Start Chrome for Testing
            logger.info("Starting Chrome for Testing", chrome=chrome_path)
            process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for Chrome to be ready
            self.context = BrowserContext(
                process=process,
                debug_port=debug_port
            )

            # Connect to CDP
            for _ in range(30):  # 30 second timeout
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"http://localhost:{debug_port}/json/version"
                        )
                        if response.status_code == 200:
                            data = response.json()
                            self.context.ws_url = data.get("webSocketDebuggerUrl")
                            self.context.ready = True
                            logger.info(
                                "Browser ready",
                                debug_port=debug_port,
                                ws_url=self.context.ws_url
                            )
                            return self.context
                except Exception:
                    pass
                await asyncio.sleep(1)

            raise RuntimeError("Failed to connect to Chrome DevTools")

    async def _send_cdp(self, method: str, params: Dict = None) -> Dict:
        """Send CDP command via HTTP."""
        if not self.context or not self.context.ready:
            await self.ensure_browser()

        self._message_id += 1

        async with httpx.AsyncClient() as client:
            # Get first page target
            response = await client.get(
                f"http://localhost:{self.context.debug_port}/json"
            )
            targets = response.json()

            # Find page target
            page_target = None
            for target in targets:
                if target.get("type") == "page":
                    page_target = target
                    break

            if not page_target:
                raise RuntimeError("No page target found")

            # Send command to target
            target_url = page_target.get("webSocketDebuggerUrl", "").replace(
                "ws://", "http://"
            ).replace("/devtools/page/", "/json/protocol/")

            # Use the simpler HTTP endpoint for CDP commands
            cmd_response = await client.post(
                f"http://localhost:{self.context.debug_port}/json/protocol",
                json={
                    "id": self._message_id,
                    "method": method,
                    "params": params or {}
                },
                timeout=30.0
            )

            return cmd_response.json() if cmd_response.status_code == 200 else {}

    async def navigate(self, url: str, wait_for: int = 3000) -> Dict[str, Any]:
        """Navigate to URL."""
        await self.ensure_browser()

        async with httpx.AsyncClient() as client:
            # Get page target
            response = await client.get(
                f"http://localhost:{self.context.debug_port}/json"
            )
            targets = response.json()

            for target in targets:
                if target.get("type") == "page":
                    target_id = target.get("id")

                    # Navigate using PUT to target
                    nav_response = await client.put(
                        f"http://localhost:{self.context.debug_port}/json/navigate",
                        params={"url": url, "id": target_id}
                    )

                    await asyncio.sleep(wait_for / 1000)

                    return {
                        "success": True,
                        "url": url,
                        "target_id": target_id
                    }

        return {"success": False, "error": "No page target"}

    async def screenshot(
        self,
        name: str,
        full_page: bool = False
    ) -> Screenshot:
        """Capture screenshot of current page."""
        await self.ensure_browser()

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename

        async with httpx.AsyncClient() as client:
            # Get page target
            response = await client.get(
                f"http://localhost:{self.context.debug_port}/json"
            )
            targets = response.json()

            for target in targets:
                if target.get("type") == "page":
                    # Use Page.captureScreenshot via websocket
                    import websockets
                    ws_url = target.get("webSocketDebuggerUrl")

                    async with websockets.connect(ws_url) as ws:
                        # Send screenshot command
                        self._message_id += 1
                        await ws.send(json.dumps({
                            "id": self._message_id,
                            "method": "Page.captureScreenshot",
                            "params": {
                                "format": "png",
                                "captureBeyondViewport": full_page
                            }
                        }))

                        result = json.loads(await ws.recv())

                        if "result" in result and "data" in result["result"]:
                            # Decode and save
                            img_data = base64.b64decode(result["result"]["data"])
                            filepath.write_bytes(img_data)

                            return Screenshot(
                                path=str(filepath),
                                name=name,
                                url=target.get("url", ""),
                                timestamp=timestamp,
                                width=1920,
                                height=1080
                            )

        raise RuntimeError("Failed to capture screenshot")

    async def capture_screens(
        self,
        base_url: str,
        screens: List[Dict[str, str]],
        viewport: Dict[str, int] = None
    ) -> List[Screenshot]:
        """Capture screenshots of multiple screens."""
        await self.ensure_browser()

        viewport = viewport or {"width": 1920, "height": 1080}
        screenshots = []

        for screen in screens:
            path = screen.get("path", "/")
            name = screen.get("name", path.replace("/", "_").strip("_") or "home")

            url = f"{base_url.rstrip('/')}{path}"

            try:
                await self.navigate(url)
                await asyncio.sleep(1)  # Wait for render

                screenshot = await self.screenshot(name)
                screenshots.append(screenshot)

                logger.info(f"Captured: {name}", url=url, path=screenshot.path)

            except Exception as e:
                logger.error(f"Failed to capture {name}: {e}")

        return screenshots

    async def close(self):
        """Close browser."""
        if self.context and self.context.process:
            self.context.process.terminate()
            try:
                self.context.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.context.process.kill()
            self.context = None


# Singleton instance - persists across pipeline runs
browser_service = BrowserService()


# Action handlers for pipeline executor
async def action_browser_launch(
    input_data: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    """Launch browser and navigate to app URL."""
    project_path = input_data.get("project_path", "")
    app_url = input_data.get("app_url", "http://localhost:3000")

    await browser_service.ensure_browser()

    # Navigate to app URL
    result = await browser_service.navigate(app_url)

    return {
        "context_id": "browser-1",
        "tab_id": 1,
        "app_url": app_url,
        "ready": result.get("success", False)
    }


async def action_browser_screenshots(
    input_data: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    """Capture screenshots of screens."""
    base_url = input_data.get("base_url", "http://localhost:3000")
    raw_screens = input_data.get("screens")
    viewport = input_data.get("viewport", {"width": 1920, "height": 1080})

    # Handle various input formats for screens
    screens = []
    if isinstance(raw_screens, list):
        for s in raw_screens:
            if isinstance(s, dict) and "path" in s:
                screens.append(s)
            elif isinstance(s, str):
                screens.append({"path": s, "name": s.replace("/", "_").strip("_") or "home"})
    elif isinstance(raw_screens, str):
        # If it's a string, try to parse common paths
        screens = [{"path": "/", "name": "home"}]

    # Default to home if no valid screens
    if not screens:
        screens = [{"path": "/", "name": "home"}]

    screenshots = await browser_service.capture_screens(
        base_url=base_url,
        screens=screens,
        viewport=viewport
    )

    return {
        "screenshots": [
            {
                "path": s.path,
                "name": s.name,
                "url": s.url,
                "timestamp": s.timestamp
            }
            for s in screenshots
        ],
        "paths": [s.path for s in screenshots],
        "count": len(screenshots)
    }
