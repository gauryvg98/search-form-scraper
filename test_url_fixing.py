#!/usr/bin/env python3
"""
Test script to verify URL fixing functionality
"""

from merge_to_csv import extract_base_url, fix_url, fix_url_list


def test_url_fixing():
    """Test the URL fixing functions with various scenarios"""

    print("Testing URL fixing functionality...\n")

    # Test base URL extraction
    test_urls = [
        "https://www.cbre.com/properties/some-property",
        "https://www.avisonyoung.us/properties/another-property",
        "http://example.com/path/to/page",
        "",
    ]

    print("1. Base URL extraction:")
    for url in test_urls:
        base = extract_base_url(url)
        print(f"   {url} -> {base}")

    print("\n2. URL fixing examples:")

    # Test URL fixing scenarios
    test_cases = [
        {
            "base": "https://www.cbre.com",
            "urls": [
                "/resources/fileassets/US-SMPL-178281/photo.jpg",
                "https://external.com/image.jpg",
                "//cdn.example.com/image.jpg",
                "relative/path/image.jpg",
                "",
            ],
        },
        {
            "base": "https://www.avisonyoung.us",
            "urls": [
                "/documents/brochure.pdf",
                "https://d3k1yame0apvip.cloudfront.net/image.jpg",
                "//static.example.com/doc.pdf",
            ],
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n   Test case {i} (base: {case['base']}):")
        for url in case["urls"]:
            fixed = fix_url(url, case["base"])
            print(f"     '{url}' -> '{fixed}'")

    print("\n3. URL list fixing:")
    url_list = [
        "/resources/image1.jpg",
        "https://external.com/image2.jpg",
        "/documents/brochure.pdf",
    ]
    base_url = "https://www.cbre.com"
    fixed_list = fix_url_list(url_list, base_url)

    print(f"   Original: {url_list}")
    print(f"   Fixed:    {fixed_list}")

    print("\n✅ URL fixing tests completed!")


if __name__ == "__main__":
    test_url_fixing()
