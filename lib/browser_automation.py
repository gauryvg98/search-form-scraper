import asyncio
import fcntl
import logging
import os
import random
from typing import Optional
from urllib.parse import urljoin

from playwright.async_api import Browser, ElementHandle, Page

from lib.schema import WebElement, WebSearchSchema

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TIMEOUT = 30000

FIVE_SECOND_WAIT = random.uniform(4, 6)


class BrowserAutomation:
    def __init__(
        self,
        browser: Browser,
        schema: WebSearchSchema,
        output_path: str,
    ):
        self.schema = schema
        self.browser = browser
        self.main_page = None
        self.output_path = output_path
        self.logger = logger

    async def execute(self):
        try:
            self.main_page = await self._create_new_page()

            await self.execute_search_and_save()
        finally:
            if self.main_page:
                await self.main_page.close()

    async def click_element(
        self, web_element: WebElement, current_page: Optional[Page] = None
    ):
        current_page = self._get_current_page(current_page)
        element = await self._attempt_to_find_element(web_element, current_page)
        if element is None:
            self.logger.error(
                f"Element not found for click: {web_element.element_description}"
            )
            raise Exception(
                f"Element not found for click: {web_element.element_description}"
            )

        await element.click()
        await current_page.wait_for_load_state("networkidle", timeout=TIMEOUT)

        self.logger.info(
            f"Clicked element {web_element.element_description or '[no description]'}"
        )

    async def execute_search(
        self,
        schema: WebSearchSchema,
    ):
        await self.main_page.goto(schema.search_page_url)
        await asyncio.sleep(FIVE_SECOND_WAIT)

        await self.click_element(schema.submit_button)

        self.logger.info(
            f"Search button clicked, Waiting for detail link: {schema.detail_page_link.xpath}"
        )
        await self.main_page.wait_for_selector(
            f"xpath={schema.detail_page_link.xpath}", timeout=TIMEOUT
        )
        self.logger.info("Detail links found")

    async def execute_search_and_save(
        self,
        limit: Optional[int] = None,
        start_page: Optional[int] = 1,
        max_concurrent: int = 10,  # Control concurrent processing
    ):
        search_schema = self.schema
        detail_xpath = search_schema.detail_page_link.xpath

        page = start_page
        total_processed = 0
        retry_count = 0
        previous_page_detail_link_hrefs = []
        # if search_schema.is_search_paginated and (
        #     search_schema.start_date and search_schema.end_date
        # ):
        await self.execute_search(
            schema=self.schema,
        )
        self.logger.info(f"Submitting search form for page {page}")
        if True:
            while limit is None or total_processed < limit:
                try:
                    self.logger.info(f"Waiting for detail links on page {page}")
                    await self.main_page.wait_for_selector(
                        f"xpath={detail_xpath}", timeout=TIMEOUT
                    )
                    detail_links = None
                    # Get all detail links on current page
                    detail_links = await self.main_page.query_selector_all(
                        f"xpath={detail_xpath}"
                    )
                    total_links = len(detail_links)
                    self.logger.info(f"Total links on page {page}: {total_links}")

                    if total_links == 0:
                        # Check for next page
                        next_button = await self._attempt_to_find_element(
                            search_schema.next_page_button
                        )

                        if not next_button or not await next_button.is_visible():
                            self.logger.info("Reached last page")
                            break
                        page += 1
                        await self.click_element(search_schema.next_page_button)
                        continue

                    # Process links concurrently in batches
                    for i in range(0, total_links, max_concurrent):
                        if limit and total_processed >= limit:
                            break

                        batch = detail_links[i : min(i + max_concurrent, total_links)]
                        tasks = []
                        for link in batch:
                            if limit and total_processed >= limit:
                                break

                            task = asyncio.create_task(
                                self.process_detail_link(
                                    link_element=link,
                                )
                            )
                            tasks.append(task)
                            total_processed += 1

                        # Wait for all tasks in the batch to complete
                        await asyncio.gather(*tasks)

                    # Move to next page
                    self.logger.info(f"Clicking next button on page {page}")
                    next_button = await self._attempt_to_find_element(
                        search_schema.next_page_button,
                    )
                    if next_button:
                        await self.click_element(search_schema.next_page_button)
                        self.logger.info(f"Page {page + 1} loaded")
                        page += 1
                    else:
                        self.logger.info("Reached last page")
                        break

                except Exception as e:
                    self.logger.error(f"Error processing page {page}: {e!s}")
                    retry_count += 1
                    if retry_count >= 10:
                        raise e
                    continue

    async def process_detail_link(
        self,
        link_element: ElementHandle,
    ):
        detail_page = None
        try:
            if await self._has_valid_href(link_element):
                detail_page = await self.open_detail_page_from_href(
                    link_element,
                )

        except Exception as e:
            self.logger.error(f"Error processing detail link: {e!s}")
        finally:
            if detail_page:
                await detail_page.close()

    async def open_detail_page_from_href(self, link_element: ElementHandle):
        detail_page = None
        try:
            # Get href attribute with error checking
            href = await link_element.get_attribute("href")
            if not href:
                raise ValueError("Link element has no href attribute")

            base_url = self.main_page.url
            full_url = urljoin(base_url, href)
            self._save_link(full_url)
        except Exception as e:
            self.logger.error(f"Error opening detail page: {e!s}")
            if detail_page:
                await detail_page.close()
            raise Exception(f"Failed to open detail page: {e!s}")

    def _get_current_page(self, current_page: Optional[Page] = None):
        return current_page if current_page else self.main_page

    async def _create_new_page(self) -> Page:
        """Create a new page with blocked resources"""

        context = await self.browser.new_context()
        new_page = await context.new_page()

        return new_page

    async def _attempt_to_find_element(
        self, web_element: WebElement, current_page: Optional[Page] = None
    ):
        """Attempts to find a web element using the provided selector."""
        self.logger.info(f"Attempting to find element: {web_element}")
        current_page = self._get_current_page(current_page)
        try:
            if web_element.xpath:
                element = await current_page.wait_for_selector(
                    f"xpath={web_element.xpath}", timeout=TIMEOUT, state="visible"
                )
            elif web_element.css_selector:
                element = await current_page.wait_for_selector(
                    web_element.css_selector, timeout=TIMEOUT, state="visible"
                )
            else:
                self.logger.error("No valid selector provided for element")
                return None

            if element:
                self.logger.info(f"Element found: {web_element.element_description}")
                return element
            return None
        except Exception as e:
            self.logger.error(
                f"Error finding element {web_element.element_description}: {e!s}"
            )
            return None

    async def _has_valid_href(self, link_element: ElementHandle) -> bool:
        # TODO: Check if this function requires refinement
        href = await link_element.get_attribute("href")
        if str(href).startswith("JSHandle@"):
            return False

        if not href or href.strip() == "":
            return False

        if href == "#" or href.startswith("javascript:"):
            return False

        return True

    def _save_link(self, url):
        file_path = os.path.join(
            self.output_path,
            "extracted_urls.txt",
        )
        with open(file_path, "a", encoding="utf-8") as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            file.write(f"{url} \n")
            fcntl.flock(file, fcntl.LOCK_UN)
        self.logger.info(f"Saved url -> {url} to file_path : {file_path}")
