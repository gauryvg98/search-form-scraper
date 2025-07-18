import asyncio
import json
import os

from lib.file_utils import create_nested_directory
from scripts.create_web_search_schema import generate_search_page_schema
from scripts.extract_urls import extract_urls


async def process_single_key(key, url):
    if not os.path.exists(f"output/{key}/web_search_schema.json"):
        create_nested_directory(f"output/{key}")
        await generate_search_page_schema(key, url)
    # await extract_urls(key)


async def extract_urls_in_parallel(urls, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_process(key):
        async with semaphore:
            await extract_urls(key)

    tasks = [bounded_process(obj["key"]) for obj in urls]
    await asyncio.gather(*tasks)


async def process_keys_in_parallel(urls, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_process(key, url):
        async with semaphore:
            await process_single_key(key, url)

    tasks = [bounded_process(obj["key"], obj["url"]) for obj in urls]
    await asyncio.gather(*tasks)


async def launch_schema_run_for_all_keys():
    with open("output/extracted_broker_websites.json", "r") as f:
        urls = json.load(f)
    await process_keys_in_parallel(urls)


async def launch_extract_run_for_all_keys():
    with open("output/extracted_broker_websites.json", "r") as f:
        urls = json.load(f)
    await extract_urls_in_parallel(urls)


def main():
    asyncio.run(launch_schema_run_for_all_keys())


if __name__ == "__main__":
    main()
