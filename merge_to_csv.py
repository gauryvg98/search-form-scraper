#!/usr/bin/env python3
"""
Script to merge all extracted_data.json files into one large CSV.
Handles URL prefixing for relative URLs using the source_url domain.
"""

import csv
import glob
import json
import os
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse


def extract_base_url(source_url: str) -> str:
    """
    Extract the base URL (scheme + netloc) from a source URL.

    Args:
        source_url: The full source URL

    Returns:
        Base URL with scheme and domain (e.g., 'https://www.example.com')
    """
    if not source_url:
        return ""

    parsed = urlparse(source_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fix_url(url: str, base_url: str) -> str:
    """
    Fix a URL by adding the base domain if it's relative.

    Args:
        url: The URL to fix
        base_url: The base URL to use for relative URLs

    Returns:
        Fixed absolute URL
    """
    if not url:
        return url

    # If URL already has a scheme, return as-is
    if url.startswith(("http://", "https://")):
        return url

    # If URL starts with //, add scheme from base_url
    if url.startswith("//"):
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}:{url}"

    # If URL starts with /, it's a relative path
    if url.startswith("/"):
        return urljoin(base_url, url)

    # For other relative URLs, join with base
    return urljoin(base_url, url)


def fix_url_list(url_list: List[str], base_url: str) -> List[str]:
    """
    Fix a list of URLs by adding the base domain for relative URLs.

    Args:
        url_list: List of URLs to fix
        base_url: The base URL to use for relative URLs

    Returns:
        List of fixed absolute URLs
    """
    if not url_list:
        return url_list

    return [fix_url(url, base_url) for url in url_list]


def process_record(record: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Process a single record to fix URLs and prepare for CSV output.
    Returns None if the record should be discarded.

    Args:
        record: The record dictionary

    Returns:
        Processed record with fixed URLs, or None to discard
    """
    # Discard if address is null or empty
    if not record.get("address"):
        return None

    # Create a copy to avoid modifying the original
    processed = record.copy()

    # Extract base URL from source_url
    source_url = record.get("source_url", "")
    base_url = extract_base_url(source_url)

    # Fix image URLs
    if "property_image_urls" in processed:
        processed["property_image_urls"] = fix_url_list(
            processed["property_image_urls"], base_url
        )

    # Fix brochure URLs
    if "brochure_doc_urls" in processed:
        processed["brochure_doc_urls"] = fix_url_list(
            processed["brochure_doc_urls"], base_url
        )

    # Convert lists to pipe-separated strings for CSV
    if isinstance(processed.get("property_image_urls"), list):
        processed["property_image_urls"] = "\n".join(processed["property_image_urls"])

    if isinstance(processed.get("brochure_doc_urls"), list):
        processed["brochure_doc_urls"] = "\n".join(processed["brochure_doc_urls"])

    return processed


def find_json_files(output_dir: str = "output") -> List[str]:
    """
    Find all extracted_data.json files in the output directory.

    Args:
        output_dir: The output directory to search

    Returns:
        List of paths to extracted_data.json files
    """
    pattern = os.path.join(output_dir, "*", "extracted_data.json")
    return glob.glob(pattern)


def merge_json_to_csv(output_file: str = "merged_properties.csv"):
    """
    Merge all extracted_data.json files into a single CSV file.

    Args:
        output_file: The output CSV file path
    """
    json_files = find_json_files()

    if not json_files:
        print("No extracted_data.json files found in the output directory.")
        return

    print(f"Found {len(json_files)} JSON files to merge:")
    for file_path in json_files:
        print(f"  - {file_path}")

    all_records = []
    total_processed = 0

    # Process each JSON file
    for json_file in json_files:
        print(f"\nProcessing {json_file}...")

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"Warning: {json_file} does not contain a list. Skipping.")
                continue

            # Process each record in the file
            file_records = 0
            for record in data:
                if isinstance(record, dict):
                    processed_record = process_record(record)
                    if processed_record:
                        all_records.append(processed_record)
                        file_records += 1

            print(
                f"  Processed {file_records} records (after discarding null addresses)"
            )
            total_processed += file_records

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue

    if not all_records:
        print("No valid records found to write to CSV.")
        return

    # Get all unique field names
    all_fields = set()
    for record in all_records:
        all_fields.update(record.keys())

    # Sort fields for consistent column order
    fieldnames = sorted(all_fields)

    # Write to CSV
    print(f"\nWriting {len(all_records)} records to {output_file}...")

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)

        print(f"Successfully created {output_file} with {len(all_records)} records")
        print(f"Columns: {', '.join(fieldnames)}")

    except Exception as e:
        print(f"Error writing CSV file: {e}")


if __name__ == "__main__":
    merge_json_to_csv()
