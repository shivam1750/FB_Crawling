# Facebook Page Crawler - Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Features](#features)
   - [Proxy Rotation](#proxy-rotation)
   - [Random Scrolling](#random-scrolling)
   - [Data Extraction](#data-extraction)
   - [Data Storage](#data-storage)
6. [Ethical and Legal Considerations](#ethical-and-legal-considerations)
7. [Limitations](#limitations)
8. [Troubleshooting](#troubleshooting)

## Project Overview

The Facebook Page Crawler is an AI agent designed to crawl public Facebook pages to collect posts, images, videos, and related metadata. The agent mimics human-like behavior by incorporating features such as proxy rotation and random scrolling speeds to reduce the chance of detection by anti-bot systems.

This tool is intended for research, data analysis, and monitoring purposes, and should be used in compliance with Facebook's terms of service and applicable laws regarding web scraping.

## Architecture

The Facebook Page Crawler is built with a modular architecture consisting of four main components:

1. **Proxy Rotation System**: Manages a pool of proxies and rotates them to avoid IP blocking.
2. **Human Behavior Simulator**: Implements variable scrolling speeds and random pauses to mimic human behavior.
3. **Data Extraction Module**: Extracts posts, images, videos, and metadata from Facebook pages.
4. **Data Storage Solution**: Stores extracted data in structured formats (JSON, CSV) and a SQLite database.

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Facebook Page Crawler                      │
└───────────────────────────────┬─────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼───────┐      ┌────────▼────────┐      ┌──────▼───────┐
│ Proxy Rotation │      │ Human Behavior  │      │     Data     │
│    System      │      │   Simulator     │      │  Extraction  │
└───────┬───────┘      └────────┬────────┘      └──────┬───────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                      ┌─────────▼─────────┐
                      │    Data Storage   │
                      │     Solution      │
                      └───────────────────┘
```

### File Structure

```
facebook_crawler/
├── proxy_rotation.py     # Proxy management and rotation
├── random_scrolling.py   # Human-like browsing behavior
├── data_extraction.py    # Facebook data extraction
├── data_storage.py       # Data storage and management
├── main.py               # Main application entry point
├── proxies.csv           # List of proxy servers
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
└── data/                 # Directory for stored data
    ├── pages/            # Page data
    ├── posts/            # Post data
    ├── images/           # Image metadata
    └── videos/           # Video metadata
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome or Firefox browser
- ChromeDriver or GeckoDriver (for Selenium)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/facebook-page-crawler.git
   cd facebook-page-crawler
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install browser drivers:
   ```bash
   # If using Playwright
   python -m playwright install
   
   # If using Selenium with Chrome
   # Download ChromeDriver from https://sites.google.com/chromium.org/driver/
   ```

5. Configure proxies:
   - Edit the `proxies.csv` file to add your proxy servers
   - Each line should contain one proxy in the format: `http://ip:port` or `https://username:password@ip:port`

## Usage

### Basic Usage

```python
from selenium import webdriver
from proxy_rotation import ProxyManager
from random_scrolling import HumanBehaviorSimulator
from data_extraction import FacebookExtractor
from data_storage import DataStorage

# Initialize components
driver = webdriver.Chrome()
proxy_manager = ProxyManager("proxies.csv")
simulator = HumanBehaviorSimulator(driver)
extractor = FacebookExtractor(driver)
storage = DataStorage()

# Target Facebook page
page_url = "https://www.facebook.com/example"

try:
    # Use proxy for the request
    response, proxy = proxy_manager.request_with_proxy_rotation(
        "https://www.facebook.com",
        rotation_strategy='sequential'
    )
    
    # Navigate to the page
    driver.get(page_url)
    
    # Simulate human browsing behavior
    simulator.browse_page_naturally(duration=60)  # Browse for 1 minute
    
    # Extract data
    data = extractor.extract_all_data(page_url, max_posts=10)
    
    # Store the data
    storage.store_page_data(data)
    
    # Export to CSV
    csv_files = storage.export_to_csv()
    print(f"Data exported to: {csv_files}")
    
finally:
    driver.quit()
```

### Command Line Interface

The crawler can also be run from the command line:

```bash
python main.py --url "https://www.facebook.com/example" --posts 10 --duration 60
```

Options:
- `--url`: Facebook page URL to crawl
- `--posts`: Maximum number of posts to extract (default: 10)
- `--duration`: Duration to browse the page in seconds (default: 60)
- `--proxy`: Proxy rotation strategy (sequential, random, performance)
- `--output`: Output format (json, csv, db, all)

## Features

### Proxy Rotation

The proxy rotation system helps maintain anonymity during crawling and reduces the chance of being blocked by Facebook's anti-bot systems.

#### Strategies

- **Sequential**: Rotates through proxies in order
- **Random**: Selects a random proxy for each request
- **Performance-based**: Selects proxies based on their success rate and response time

#### Implementation Details

The `ProxyManager` class handles proxy rotation with the following features:

- Loading proxies from a CSV file
- Formatting proxies for use with the requests library
- Handling proxy errors and timeouts
- Tracking proxy performance metrics
- Automatic retry with different proxies

```python
# Example: Using the proxy rotation system
proxy_manager = ProxyManager("proxies.csv")
response, proxy = proxy_manager.request_with_proxy_rotation(
    "https://www.facebook.com",
    rotation_strategy='random',
    max_retries=3
)
```

### Random Scrolling

The random scrolling behavior simulates natural user behavior, reducing the chance of detection by anti-bot systems.

#### Features

- Variable scrolling speeds
- Random pauses between actions
- Natural mouse movements
- Human-like interaction patterns (reading, hovering, clicking)

#### Implementation Details

The `HumanBehaviorSimulator` class provides sophisticated behavior simulation:

- Scrolling with random speeds and distances
- Adding random pauses before and after actions
- Simulating reading time based on content length
- Performing random mouse movements with natural curves
- Hovering over and clicking on non-critical elements

```python
# Example: Using the human behavior simulator
simulator = HumanBehaviorSimulator(driver)
simulator.browse_page_naturally(duration=60)  # Browse for 1 minute
```

### Data Extraction

The data extraction module scrapes essential data from Facebook pages, including text posts, images, video links, timestamps, and other relevant metadata.

#### Extracted Data

- Page information (name, URL, profile image, followers count, category)
- Posts (text content, timestamp, URL)
- Media (image URLs, video URLs)
- Metadata (likes, comments, shares)

#### Implementation Details

The `FacebookExtractor` class handles data extraction with the following features:

- Extracting page information
- Scrolling to load more posts
- Extracting post content and metadata
- Handling different types of media
- Error handling and logging

```python
# Example: Using the data extraction module
extractor = FacebookExtractor(driver)
data = extractor.extract_all_data("https://www.facebook.com/example", max_posts=10)
```

### Data Storage

The data storage solution securely stores the extracted data in structured formats (JSON, CSV) and a SQLite database.

#### Storage Formats

- **JSON**: Hierarchical storage of all data
- **CSV**: Tabular storage for easy analysis
- **SQLite**: Relational database for structured queries

#### Implementation Details

The `DataStorage` class handles data storage with the following features:

- Storing data in multiple formats
- Organizing data by type (pages, posts, images, videos)
- Database schema for structured storage
- Data validation and error handling
- Export functionality

```python
# Example: Using the data storage solution
storage = DataStorage()
storage.store_page_data(data)
csv_files = storage.export_to_csv()
```

## Ethical and Legal Considerations

### Legal Framework

While scraping public data is technically legal in many jurisdictions (per a 2022 Ninth Circuit Court ruling), Facebook actively opposes scraping and may take legal action against scrapers. Always consult with legal counsel before using this tool.

### Ethical Guidelines

1. **Respect Rate Limits**: Avoid excessive requests that could impact service performance.
2. **Focus on Public Data**: Only scrape publicly available information.
3. **Respect Privacy**: Do not collect or store personal information of users.
4. **Transparent Purpose**: Be clear about why you're collecting the data.
5. **Data Security**: Secure any collected data appropriately.

### Facebook's Terms of Service

Facebook's Terms of Service prohibit:
- Automated data collection without Facebook's express permission
- Using automated methods to access Facebook services
- Collecting users' content or information using automated means

## Limitations

1. **Detection Risk**: Despite anti-detection measures, Facebook may still detect and block the crawler.
2. **Dynamic Content**: Facebook's dynamic content loading may cause some content to be missed.
3. **Structure Changes**: Facebook frequently changes its page structure, which may break the extraction logic.
4. **Proxy Quality**: The effectiveness of proxy rotation depends on the quality of the proxies used.
5. **Legal Constraints**: Legal and terms of service restrictions limit the legitimate use cases.

## Troubleshooting

### Common Issues

1. **Proxy Connection Errors**
   - Ensure proxies in proxies.csv are valid and active
   - Check proxy format (http://ip:port or https://username:password@ip:port)
   - Try different proxy rotation strategies

2. **Extraction Failures**
   - Facebook may have changed its page structure
   - Check for updates to the extraction module
   - Try reducing the number of posts to extract

3. **Browser Driver Issues**
   - Ensure browser driver version matches your browser version
   - Update browser and driver to the latest versions

4. **Rate Limiting**
   - Increase pause durations in the human behavior simulator
   - Use more proxies and rotate them more frequently
   - Reduce the frequency of requests

### Logging

The crawler uses Python's logging module to log information, warnings, and errors:

- `facebook_extraction.log`: Logs from the data extraction module
- `facebook_storage.log`: Logs from the data storage module

Check these logs for detailed information about any issues encountered.
