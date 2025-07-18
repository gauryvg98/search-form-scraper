# JSON to CSV Merger Script

This script merges all `extracted_data.json` files from the output directory into a single CSV file with proper URL handling.

## Features

- **Automatic JSON Discovery**: Finds all `extracted_data.json` files in subdirectories of the `output` folder
- **URL Fixing**: Automatically converts relative URLs to absolute URLs using the `source_url` domain
- **CSV Export**: Converts JSON data to CSV format with pipe-separated lists for multiple URLs
- **Error Handling**: Gracefully handles malformed JSON files and missing data

## URL Fixing Logic

The script handles various URL formats:

1. **Absolute URLs** (already have http/https): Left unchanged
   - `https://example.com/image.jpg` → `https://example.com/image.jpg`

2. **Protocol-relative URLs** (start with //): Adds protocol from source URL
   - `//cdn.example.com/image.jpg` → `https://cdn.example.com/image.jpg`

3. **Root-relative URLs** (start with /): Adds domain from source URL
   - `/resources/image.jpg` → `https://www.cbre.com/resources/image.jpg`

4. **Relative URLs**: Joins with base URL
   - `images/photo.jpg` → `https://www.cbre.com/images/photo.jpg`

## Usage

### Basic Usage

```bash
python merge_to_csv.py
```

This will:
- Find all `extracted_data.json` files in `output/*/`
- Process and fix URLs
- Create `merged_properties.csv` in the current directory

### Custom Output File

```python
from merge_to_csv import merge_json_to_csv

# Specify custom output filename
merge_json_to_csv('my_custom_output.csv')
```

## Output Format

The CSV file contains all unique fields from all JSON files, with:
- **Multiple URLs**: Converted to comma-separated strings (`url1,url2,url3`)
- **Fixed URLs**: All relative URLs converted to absolute URLs
- **Sorted Columns**: Consistent column ordering across runs

## Example

### Input JSON (excerpt):
```json
{
  "property_image_urls": [
    "/resources/fileassets/US-SMPL-178281/photo.jpg",
    "https://external.com/image.jpg"
  ],
  "brochure_doc_urls": [
    "/documents/brochure.pdf"
  ],
  "source_url": "https://www.cbre.com/properties/some-property"
}
```

### Output CSV:
```csv
property_image_urls,brochure_doc_urls,source_url
"https://www.cbre.com/resources/fileassets/US-SMPL-178281/photo.jpg,https://external.com/image.jpg","https://www.cbre.com/documents/brochure.pdf","https://www.cbre.com/properties/some-property"
```

## Statistics from Last Run

- **Files Processed**: 4 JSON files
- **Total Records**: 26,213 properties
- **Output Size**: 29MB CSV file
- **Sources**: cbcworldwide, transwestern, avisonyoung, cbre

## Testing

Run the test script to verify URL fixing functionality:

```bash
python test_url_fixing.py
```

## Requirements

- Python 3.6+
- Standard library modules: `json`, `csv`, `os`, `glob`, `urllib.parse`, `typing`

## File Structure

```
output/
├── cbcworldwide/
│   └── extracted_data.json
├── transwestern/
│   └── extracted_data.json
├── avisonyoung/
│   └── extracted_data.json
└── cbre/
    └── extracted_data.json
```

## Error Handling

The script handles:
- Missing or empty JSON files
- Malformed JSON data
- Missing URL fields
- Empty or invalid source URLs
- File permission issues

**Note**: Entries with a null or empty `address` field will be discarded and not included in the final CSV.

Errors are logged to console but don't stop the overall process. 