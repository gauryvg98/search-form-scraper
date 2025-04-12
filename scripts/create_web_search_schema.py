import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Any, Dict

from browser_use import Agent, Browser, BrowserConfig, Controller
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from lib.file_utils import create_nested_directory
from lib.schema import WebSearchSchema

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
controller = Controller(
    # output_model=NavigationSchema,
)
browser_config = BrowserConfig(headless=False)


default_websearch_schema_prompt = """
        Your task is to follow instructions to the point to execute the search.
         - If there is no search form visible on the page, navigate to a search form page.
         - Click the submit search button to execute the search.
        Note the submit search_button and the exact url for the search_form_page.
        After the search results have loaded, validate whether the search results are paginated or is it the details page for a single property record.
        Steps to follow for paginated search:
         - Click the next page button on the bottom of the page to navigate to the next results page.
         - Click the next page button again
         - Click on a detail page link
         - Go back and click on a different detail page link
"""


async def generate_search_page_schema(key: str, url: str):
    logger.info(f"Creating websearch schema for : {url}")

    logger.info("Starting browser automation")
    websearch_schema_prompt = default_websearch_schema_prompt
    browser = Browser(config=browser_config)
    async with await browser.new_context() as browser_context:
        # Generate the navigation task description
        task = f"""
        url : {url}

        {websearch_schema_prompt}
        """

        # Initialize the Agent with browser context and LLM
        agent = Agent(
            task=task,
            llm=ChatAnthropic(
                model="claude-3-7-sonnet-latest", temperature=random.uniform(0, 0.2)
            ),
            browser_context=browser_context,
            controller=controller,
            generate_gif=False,
            use_vision=False,
            max_actions_per_step=10,
        )

        # Run the agent to get initial schema
        raw_schema = await agent.run()
        for result in raw_schema.history:
            result.state.screenshot = None

        # Create LangChain prompt template
        prompt = ChatPromptTemplate.from_template("""
        Current timestamp: {timestamp}. Ignore all prior instructions if the timestamp has changed.
        Here is a supplied action history for a browser automation agent using browser_use.

        Schema:
            {schema}

        Instructions:
            Generate a navigation schema in json format which returns a list of actions with their xpaths to be performed on the browser.
            Action Schema: 
                {traversal_path}
            Understand if the search results are paginated from the browser action history and set the is_search_paginated flag accordingly.
            Ensure the entire response is raw text format and only contains the action list.
            Only return the response of the supplied json schema, no comments/annotations/conversations etc.
            Also, do not format the response as json, just return the raw text.
        """)

        # Initialize LangChain components
        llm = ChatAnthropic(model="claude-3-7-sonnet-latest", temperature=0)
        chain = prompt | llm | JsonOutputParser()

        # Generate the navigation schema
        logger.info("Getting web search schema from LangChain")
        raw_web_search_schema = await chain.ainvoke(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "schema": raw_schema.model_dump_json(),
                "traversal_path": f"{get_simple_traversal_path()}",
            }
        )

        logger.info(f"Raw Web Search schema: {raw_web_search_schema}")
        web_search_schema = await clean_web_search_schema(raw_web_search_schema, llm)
        logger.info(f"Cleaned Web Search schema: {web_search_schema}")

        logger.info(f"Web Search schema created for {url}")

        # Create directory and save schema
        schema_path = os.path.join(f"output/{key}", "web_search_schema.json")
        with open(schema_path, "w") as f:
            f.write(web_search_schema.model_dump_json(indent=4))
        logger.info(f"Schema saved to {schema_path}")


async def clean_web_search_schema(
    json_data: Dict[str, Any],
    llm: ChatAnthropic,
) -> WebSearchSchema:
    try_count = 0
    while try_count < 10:
        # Create LangChain prompt template
        prompt = ChatPromptTemplate.from_template("""
        Here is a supplied action history for a browser automation agent using browser_use.

        Schema: 
            {schema}

        Instructions:
            Generate a WebSearchSchema in json format which returns an object with major interactable elements pertaining to a search form and its results.
            Ensure to club all the search form submission steps into a single WebSearchSchema with all fields populated.
            Search form submission steps include : 
                - Click search button
                - Click next page button
                - Click detail link (ensure to extract the relative xpath and make it generic)

                Note : If any of the input fields are not present, do not include them in the execute_search_schema object.
                Link Helper Points
                    1. Link might not be in the anchor tag if not then do not add anchor tag in the xpath
                    2. Link can also be in the text format you have to find out where is the link of a row.
                    3. Find out where is the link in the anchor tag or in the text of a element.
                    4. Give xpath of the elements, not the value or an attribute.
                    5. The xpath must be generic to match to all the row links in the table
                    6. Use contains() function in the xpath to match all the row links in the table

                Next Button Helper Points
                    1. It must navigate to next page not next item
                    2. There can be '>' text in the next button 'next' text in the next button but not both
                    3. '>' text has a priority
                    4. If there are multiple next button xpath must get only the last one.
                    5. Find actual next button from the provided html file and make its xpath.
                       
            Also, ensure to capture the search page url as search_page_url in `WebSearchSchema`.
            Ensure the xpaths and css selectors are relative and not absolute.
            Sample WebSearchSchema:
                {get_sample_web_search_example}
            
            Ensure the response adheres to the supplied schema, for `WebSearchSchema`.

            Ensure the entire response is raw text format and only contains the WebSearchSchema in json.
            Only return the response of the supplied json schema, no comments/annotations/conversations etc.
            Also, do not format the response as json, just return the raw text.
        """)

        # Initialize LangChain chain
        chain = prompt | llm | JsonOutputParser()

        # Generate cleaned schema
        response = await chain.ainvoke(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "schema": json_data,
                "get_sample_web_search_example": f"{get_sample_web_search_example()}",
            }
        )

        try:
            return WebSearchSchema(**response)
        except Exception as e:
            logger.error(
                f"Error cleaning and parsing navigation schema: \n response : {response} \n {e}"
            )
            try_count += 1
            continue
    raise Exception("Failed to clean and parse web_search_schema")


def get_simple_traversal_path():
    return """
		{   
            "is_search_paginated": "boolean ; whether the search results are paginated",
		    "data":
                [
                    {
                        "step_description":"string (example : Navigate to the building permit page, Input start date, Input end date, Input parcel number, Click search button, Click next page button, Click detail link, Click additional information buttons, Extract data from the detail page)",
                        "step_type":"enum in [navigate, click, input, extract]",
                        "element_type":"enum in [text, button, input, link]",
                        "is_search_step": "boolean ; whether the step is a search step (detail link clicks and next page pagination clicks are also considered search steps along with date inputs, parcel inputs and search button clicks.)",
                        "url":"string ; url on which the action is to be performed (capture the search page url ; url on which the search button is pressed)",
                        "id":"string ; id of the element interacted with",
                        "xpath":"string ; not required for navigate",
                        "css_selector":"string ; not required for navigate",
                        "index":"int ; index of the element interacted with",
                        "element_description":"string (start date input field, end date input field, parcel number input field, search button, search result link etc.)",
                    },
                    ...
                ]
		}
		"""


def get_sample_web_search_example():
    return """
            {
                "submit_button": {
                    "id": "submit_button",
                    "xpath": "//button[@type='submit']",
                    "css_selector": "button[type='submit']",
                    "index": 0,
                    "element_description": "Submit button for the search form"
                },
                "next_page_button": {
                    "id": "next_page_button",
                    "xpath": "//button[@aria-label='Next']",
                    "css_selector": "button[aria-label='Next']",
                    "index": 0,
                    "element_description": "Next page button"
                },
                "detail_page_link": {
                    "id": "detail_page_link",
                    "xpath": "//a[@title='details' and contains(@href, '/en/expose/')]",
                    "index": 0,
                    "element_description": "Detail page links. There can be multiple detail page links in the search results page. Use contains() function in the xpath to match all the row links in the table."
                },
                "search_page_url": "https://property-search.example.com/search",
            }

    Here are pydantic models for the schema:

    class WebElement(BaseModel):
        id: Optional[str] = Field(default=None, description="ID of the element")
        xpath: str = Field(
            description="XPath selector to find element"
        )
        css_selector: Optional[str] = Field(
            default=None, description="CSS selector to find element"
        )
        index: Optional[int] = Field(
            default=None, description="Index if multiple elements match"
        )
        element_description: Optional[str] = Field(
            default=None, description="Description of the element being interacted with"
        )


    class WebSearchSchema(BaseModel):
        detail_page_link: WebElement
        submit_button: WebElement
        next_page_button: WebElement
        search_page_url: str
    """


def main():
    key = "kensington"
    url = "https://kensington-international.com/en"
    create_nested_directory(f"output/{key}")
    asyncio.run(generate_search_page_schema(key, url))


if __name__ == "__main__":
    main()
