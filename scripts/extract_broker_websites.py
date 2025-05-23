import asyncio
import json
import logging
import random
from datetime import datetime

from browser_use import Agent, Browser, BrowserConfig, Controller
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
controller = Controller(
    # output_model=NavigationSchema,
)
browser_config = BrowserConfig(headless=False)

async def extract_broker_websites(url: str):
    logger.info(f"Extracting broker websites for : {url}")

    logger.info("Starting browser automation")
    browser = Browser(config=browser_config)
    playwright_browser = await browser.get_playwright_browser()
    page = await playwright_browser.new_page()
    await page.goto(url)
    
    raw_html = await page.content()
        
    prompt = ChatPromptTemplate.from_template("""
        Current timestamp: {timestamp}. Ignore all prior instructions if the timestamp has changed.
        Here is a supplied action history for a browser automation agent using browser_use.

        HTML File:
            {html_file}

        Instructions:
            Return a list of broker websites from the page.
            Expected Schema:  
            [{{"url":"https://www.brokerwebsite1.com", "key":"brokerwebsite1"}}, {{"url":"https://www.brokerwebsite2.com", "key":"brokerwebsite2"}}, {{"url":"https://www.brokerwebsite3.com", "key":"brokerwebsite3"}}]
            
            Ensure the entire response is raw text format and only contains the action list.
            Only return the response of the supplied json schema, no comments/annotations/conversations etc.
            Also, do not format the response as json, just return the raw text.
        """)

    # Initialize LangChain components
    llm = ChatAnthropic(model="claude-3-7-sonnet-latest", temperature=0)
    chain = prompt | llm | JsonOutputParser()

        # Generate the navigation schema
    logger.info("Getting web search schema from LangChain")
    raw_broker_website_list = await chain.ainvoke(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "html_file": raw_html,
            }
        )

    logger.info(f"Raw broker website list: {raw_broker_website_list}")

    save_broker_website_list(raw_broker_website_list)

def save_broker_website_list(raw_broker_website_list):
    with open("output/extracted_broker_websites.json", "w") as f:
        json.dump(raw_broker_website_list, f)

def main():
    url = "https://www.50pros.com/top-50/real-estate-commercial"
    asyncio.run(extract_broker_websites(url))


if __name__ == "__main__":
    main()
