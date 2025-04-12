# Web Search Schema Generator

A powerful tool for generating and managing web search schemas, designed to automate and standardize web search interactions across different websites.

## Overview

This project provides a framework for:
- Generating structured schemas for web search interactions
- Automating browser-based search operations
- Extracting and processing search results
- Managing pagination and detail page navigation
- Extracting URLs from search results

### Tech Stack
- Python 3.x
- Playwright for browser automation
- LangChain for LLM integration
- Pydantic for data validation
- Anthropic's Claude for schema generation

## Project Structure
```
.
├── create_web_search_schema.py  # Main schema generation script
├── extract_urls.py             # URL extraction utilities
├── lib/                        # Core library components
│   ├── browser_automation.py   # Browser automation logic
│   ├── file_utils.py          # File management utilities
│   ├── playwright_browser_manager.py  # Browser management
│   └── schema.py              # Schema definitions
├── output/                     # Generated schemas and outputs
├── requirements.txt            # Python dependencies
└── .env                        # Environment configuration
```

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

## Usage

### Generating Search Schemas

1. Run the schema generator:
```bash
python create_web_search_schema.py
```

2. The script will:
   - Launch a browser session
   - Navigate to specified URLs
   - Generate and validate search schemas
   - Save schemas to the output directory

### Output Structure

The generated schemas are stored in the `output/` directory with the following structure:
```
output/
├── schemas/           # Generated search schemas
├── logs/             # Operation logs
└── validation/       # Schema validation results
```

### Manual Schema Management

To manually create or modify schemas:

1. Navigate to the `output/schemas/` directory
2. Create a new JSON file following the schema structure:
```json
{
    "submit_button": {
        "id": "submit_button",
        "xpath": "//*[@id='openimmo-quick-search-form']/div[2]/div[5]/div/button",
        "css_selector": "-",
        "index": 0,
        "element_description": "Submit button for the search form"
    },
    "next_page_button": {
        "id": "next_page_button",
        "xpath": "//a[contains(@class, 'page-link') and contains(@aria-label, 'Nächste')]",
        "css_selector": "a.page-link[aria-label='Nächste Immobilien Seite']",
        "index": 0,
        "element_description": "Next page button"
    },
    "detail_page_link": {
        "id": "detail_page_link",
        "xpath": "//a[@title='details' and contains(@href, '/en/expose/') and not(.//img) and normalize-space()]",
        "css_selector": "//a[@title='details' and contains(@href, '/en/expose/) and not(.//img) and normalize-space()]",
        "index": 0,
        "element_description": "Property detail link"
    },
    "search_page_url": "https://kensington-international.com/en"
}
```

3. Validate the schema using the built-in validation tools

### URL Extraction

The `extract_urls.py` script is used to extract URLs from search results using a generated schema. It works in conjunction with the schema generator to:

1. Load a previously generated web search schema
2. Automate browser navigation using the schema
3. Extract URLs from search results
4. Save extracted URLs to the output directory

#### Usage

1. First, ensure you have a generated schema in the output directory
2. Run the URL extraction script:
```bash
python extract_urls.py
```

The script will:
- Load the schema for the specified key (default: "kensington")
- Navigate through search results
- Extract URLs from detail pages
- Save results to `output/{key}/urls.json`

#### Output Structure

URL extraction results are stored in the following structure:
```
output/
├── {key}/
│   ├── web_search_schema.json  # Generated schema
│   ├── urls.json              # Extracted URLs
│   └── logs/                  # Operation logs
```

## Development

### Key Components

1. **Browser Automation**
   - Uses Playwright for reliable browser control
   - Handles dynamic content and JavaScript
   - Manages multiple browser contexts

2. **Schema Generation**
   - LLM-powered schema creation
   - Automatic validation and cleaning
   - Support for complex search patterns

3. **Data Processing**
   - Structured data extraction
   - Pagination handling
   - Error recovery and retry mechanisms
