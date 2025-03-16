# Demo Script for Facebook Page Crawler

This script demonstrates the Facebook Page Crawler in action, showing how it can extract data from public Facebook pages while mimicking human-like behavior.

## Prerequisites

Before running this demo, ensure you have:

1. Installed all required dependencies (`pip install -r requirements.txt`)
2. Added proxy servers to `proxies.csv` (if using proxy rotation)
3. Chrome or Firefox browser installed
4. ChromeDriver or GeckoDriver installed and in your PATH

## Demo Steps

### 1. Basic Crawling Demo

```bash
# Run a basic crawl of a public Facebook page
python main.py --url "https://www.facebook.com/NASA" --posts 5 --duration 30 --screenshots
```

This command will:
- Navigate to NASA's Facebook page
- Browse the page for 30 seconds with human-like behavior
- Extract up to 5 posts with their content and metadata
- Take screenshots during the process
- Save all data to the data/ directory

### 2. Advanced Features Demo

```bash
# Run with proxy rotation and all output formats
python main.py --url "https://www.facebook.com/NASA" --posts 10 --duration 60 --proxy-strategy random --format all --screenshots
```

This command demonstrates:
- Random proxy rotation strategy
- Longer browsing duration (60 seconds)
- Extracting more posts (10)
- Saving data in all available formats (JSON, CSV, SQLite)

### 3. Headless Mode Demo

```bash
# Run in headless mode for server environments
python main.py --url "https://www.facebook.com/NASA" --posts 5 --headless --output-dir "server_data"
```

This command demonstrates:
- Running in headless mode (no visible browser)
- Saving output to a custom directory

## Expected Output

After running the demo, you should see:

1. Terminal output showing the crawling progress
2. Screenshots in the screenshots/ directory
3. Extracted data in the data/ directory (or your custom output directory)
4. A summary of the results including:
   - Number of posts extracted
   - Storage paths for the data
   - Paths to the screenshots

## Sample Output Files

- `data/pages/NASA_20250314_083511.json` - Complete page data in JSON format
- `data/posts_export_20250314_083511.csv` - Posts data in CSV format
- `data/facebook_data.db` - SQLite database with all extracted data
- `screenshots/initial_page_20250314_083511.png` - Screenshot of the initial page
- `screenshots/scrolled_page_20250314_083511.png` - Screenshot after scrolling
- `screenshots/post_20250314_083511.png` - Screenshot of an individual post

## Troubleshooting

If you encounter issues during the demo:

1. Check the `facebook_crawler.log` file for detailed error messages
2. Ensure your internet connection is stable
3. Verify that your proxy servers are working (if using proxy rotation)
4. Make sure the Facebook page URL is correct and publicly accessible
5. Try increasing the duration to allow more time for page loading
