import asyncio
import json
import logging

from lib.browser_automation import BrowserAutomation
from lib.file_utils import create_nested_directory
from lib.playwright_browser_manager import PlaywrightBrowserManager
from lib.schema import WebSearchSchema

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def extract_urls(key: str):
    web_search_schema = json.load(open(f"output/{key}/web_search_schema.json"))
    web_search_schema = WebSearchSchema(**web_search_schema)
    logger.info(f"web_search_schema : {web_search_schema}")

    try:
        automation = BrowserAutomation(
            browser=await PlaywrightBrowserManager().setup_browser(
                headless=False,
            ),
            schema=web_search_schema,
            output_path=f"output/{key}",
        )
        await automation.execute()

        return {
            "status": "success",
            "metadata": {
                "status": "success",
            },
        }
    except Exception as e:
        logger.error(f"Error in building permits detail extraction: {e}")
        logger.error(f"Exception details: {e!s}", exc_info=True)
        return {
            "status": "error",
            "metadata": {
                "status": "error",
                "error": str(e),
            },
        }
    finally:
        logger.info("Extraction completed")


def main():
    key = "transwestern"
    create_nested_directory(f"output/{key}")
    asyncio.run(extract_urls(key))


if __name__ == "__main__":
    main()
