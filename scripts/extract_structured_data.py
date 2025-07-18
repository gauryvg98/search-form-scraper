import asyncio
import fcntl
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime

from browser_use import Browser, BrowserConfig
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from lib.schema import PropertyData

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

browser_config = BrowserConfig(headless=False)


def save_extracted_data(key: str, data: dict, url: str):
    """Save a single extracted data record to the output file using atomic writes."""
    output_file = f"output/{key}/extracted_data.json"
    lock_file = f"{output_file}.lock"

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create a temporary file for atomic write
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_filename = temp_file.name

        # Acquire file lock
        with open(lock_file, "w") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

                # Read existing data if file exists
                existing_data = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, "r") as f:
                            existing_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Could not parse existing data from {output_file}, starting fresh"
                        )

                # Add new data
                existing_data.append(data)

                # Write to temporary file
                json.dump(existing_data, temp_file, indent=2)

                # Release the lock
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            except Exception as e:
                logger.error(f"Error during file operation: {str(e)}")
                raise
            finally:
                # Ensure lock is released even if an error occurs
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                except:
                    pass

    # Atomic move of temporary file to target file
    try:
        shutil.move(temp_filename, output_file)
    except Exception as e:
        logger.error(f"Error during atomic move: {str(e)}")
        # Clean up temporary file if move fails
        os.unlink(temp_filename)
        raise

    logger.info(f"Saved data for URL {url} to {output_file}")


async def process_single_url(url: str, browser, chain: JsonOutputParser, key: str):
    """Process a single URL and extract structured data."""
    logger.info(f"Processing URL: {url}")

    try:
        # Create new page and navigate to URL
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state("load")

        # Get page content
        html_content = await page.content()

        # Extract structured data using LangChain
        raw_data = await chain.ainvoke(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "html_content": html_content,
            }
        )

        # Validate and convert data using Pydantic model
        data = PropertyData(**raw_data)
        data.source_url = url
        data_dict = data.model_dump()

        # Save data immediately after successful extraction
        save_extracted_data(key, data_dict, url)
        logger.info(f"Successfully extracted data from: {url}")
    except Exception as e:
        logger.error(f"Error extracting data from {url}: {str(e)}")
    finally:
        # Close the page
        await page.close()


async def extract_structured_data(key: str):
    logger.info(f"Extracting structured data for key: {key}")

    # Read URLs from the extracted_urls.txt file
    urls_file = f"output/{key}/extracted_urls.txt"
    if not os.path.exists(urls_file):
        logger.error(f"URLs file not found: {urls_file}")
        return

    with open(urls_file, "r") as f:
        urls = [line.strip() for line in f.readlines()]

    # Initialize browser
    browser = Browser(config=browser_config)
    playwright_browser = await browser.get_playwright_browser()

    # Initialize LangChain components
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_template("""
        Current timestamp: {timestamp}. Ignore all prior instructions if the timestamp has changed.
        
        HTML Content:
        {html_content}
        
        Instructions:
        Extract the following structured data from the HTML content and return it in the exact JSON format shown below.
        If any field is not found, set it to null.
        
        Required JSON Format:
        {{
            "address": "string or null",
            "city": "string or null",
            "state": "string or null",
            "zip": "string or null",
            "price": number or null,
            "sqft": number or null,
            "beds": integer or null,
            "baths": number or null,
            "property_image_urls": ["url1", "url2", ...],
            "brochure_doc_urls": ["url1", "url2", ...],
            "property_type": "string or null",
            "property_description": "string or null",
            "broker": "string or null",
            "broker_url": "string or null",
            "broker_phone": "string or null",
            "broker_email": "string or null",
            "broker_address": "string or null"
        }}
        
        Important Notes:
        1. Return ONLY the JSON object, no other text or explanation
        2. Ensure all number fields (price, sqft, beds, baths) are actual numbers, not strings
        3. For missing values, use null (not "null" as string)
        4. For empty lists, use [] (not null)
        5. Do not include any fields not in the schema above
        6. Do not add any additional fields
        7. Ensure the response is valid JSON that can be parsed
    """)

    chain = prompt | llm | JsonOutputParser()

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(10)

    async def process_with_semaphore(url):
        async with semaphore:
            await process_single_url(url, playwright_browser, chain, key)

    try:
        # Create tasks for all URLs
        tasks = [process_with_semaphore(url) for url in urls]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    finally:
        # Close browser
        await playwright_browser.close()


def main():
    key = "cbre"  # Default key, can be changed as needed
    asyncio.run(extract_structured_data(key))


if __name__ == "__main__":
    main()
