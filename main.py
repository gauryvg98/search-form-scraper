import asyncio
import os

from scripts.create_web_search_schema import generate_search_page_schema
from scripts.extract_urls import extract_urls


def main():
    key = "kensington"
    url = "https://kensington-international.com/en"
    if not os.path.exists(f"output/{key}/web_search_schema.json"):
        asyncio.run(generate_search_page_schema(key, url))
    asyncio.run(extract_urls(key))


if __name__ == "__main__":
    main()
