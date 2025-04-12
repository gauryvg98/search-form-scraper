import asyncio
import logging
import os
from typing import Optional

from playwright.async_api import Browser, async_playwright

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PlaywrightBrowserManager:
    async def setup_browser(
        self,
        headless=False,
    ) -> Browser:
        """Initialize and return a configured Playwright Browser."""
        try:
            playwright = await async_playwright().start()
            browser_options = self._get_browser_options()

            browser = await playwright.chromium.launch(
                **browser_options,
                headless=headless,
                # proxy=self._create_proxy_dict(proxy_config),
                timeout=60000,
            )

            logger.info("Playwright browser initialized successfully")

            return browser

        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {e!s}")

            await self._log_debug_info()

            raise RuntimeError(f"Playwright browser initialization failed: {e!s}")

    def _get_browser_options(self) -> dict:
        """Configure Playwright browser options."""
        browser_options = {
            "args": [
                # "--disable-gpu",
                # "--no-sandbox",
                # "--disable-dev-shm-usage",
                # "--disable-background-networking",
                # "--disable-background-timer-throttling",
                # "--disable-backgrounding-occluded-windows",
                # "--disable-breakpad",
                # "--disable-client-side-phishing-detection",
                # "--disable-default-apps",
                # "--disable-extensions",
                # "--disable-sync",
                # "--disable-translate",
                # "--metrics-recording-only",
                # "--no-first-run",
                # "--ignore-certificate-errors",
            ]
        }

        return browser_options

    async def _log_debug_info(self) -> None:
        """Log debug information about system state."""
        try:
            # Check Chrome process
            chrome_process = await self._run_command(
                ["ps", "aux", "|", "grep", "chrome"]
            )
            logger.info(f"Chrome processes: {chrome_process}")

            # Check temp directory
            if os.path.exists("/tmp"):
                tmp_contents = await self._run_command(["ls", "-la", "/tmp"])
                logger.info(f"Temp directory contents: {tmp_contents}")
        except Exception as e:
            logger.error(f"Failed to gather debug information: {e!s}")

    async def _run_command(self, command: list[str]) -> str:
        """Run a shell command asynchronously."""
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        return stdout.decode("utf-8")

    async def _resource_cleanup(self, browser: Optional[Browser]) -> None:
        """Safely clean up the Playwright browser resource."""
        if browser:
            try:
                await browser.close()
                # Kill any remaining browser processes
                await self._run_command(["pkill", "-f", "chrome"])
            except Exception as e:
                print(f"Warning: Failed to cleanup browser: {e!s}")
