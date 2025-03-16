"""
Main application entry point for the Facebook Page Crawler

This script provides a command-line interface to run the Facebook page crawler
with various options for proxy rotation, scrolling behavior, data extraction,
and storage.
"""

import os
import sys
import time
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from proxy_rotation import ProxyManager
from random_scrolling import HumanBehaviorSimulator
from data_extraction import FacebookExtractor
from data_storage import DataStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("facebook_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("facebook_crawler")


def setup_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Set up and configure the Chrome WebDriver.
    
    Args:
        headless: Whether to run in headless mode
        
    Returns:
        Configured Chrome WebDriver instance
    """
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    # Add additional options to avoid detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Set user agent to a common one
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Initialize the WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Execute CDP commands to avoid detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    })
    
    return driver


def take_screenshots(driver: webdriver.Chrome, output_dir: str = "screenshots") -> Dict[str, str]:
    """
    Take screenshots of the Facebook page crawler in action.
    
    Args:
        driver: Chrome WebDriver instance
        output_dir: Directory to save screenshots
        
    Returns:
        Dictionary mapping screenshot names to file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    screenshots = {}
    
    # Take a screenshot of the initial page
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    initial_screenshot = os.path.join(output_dir, f"initial_page_{timestamp}.png")
    driver.save_screenshot(initial_screenshot)
    screenshots["initial_page"] = initial_screenshot
    
    # Scroll down and take another screenshot
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(1)
    scrolled_screenshot = os.path.join(output_dir, f"scrolled_page_{timestamp}.png")
    driver.save_screenshot(scrolled_screenshot)
    screenshots["scrolled_page"] = scrolled_screenshot
    
    # Take a screenshot of a post if available
    try:
        post_elements = driver.find_elements_by_css_selector("div[role='article']")
        if post_elements:
            post_elements[0].screenshot(os.path.join(output_dir, f"post_{timestamp}.png"))
            screenshots["post"] = os.path.join(output_dir, f"post_{timestamp}.png")
    except Exception as e:
        logger.warning(f"Could not take post screenshot: {str(e)}")
    
    return screenshots


def run_crawler(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run the Facebook page crawler with the specified arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Dictionary containing results and metadata
    """
    logger.info(f"Starting Facebook page crawler for {args.url}")
    
    # Initialize components
    driver = setup_driver(args.headless)
    proxy_manager = ProxyManager(args.proxy_file)
    simulator = HumanBehaviorSimulator(driver)
    extractor = FacebookExtractor(driver)
    storage = DataStorage(args.output_dir)
    
    screenshots = {}
    extracted_data = None
    storage_paths = {}
    
    try:
        # Navigate to the page
        logger.info(f"Navigating to {args.url}")
        driver.get(args.url)
        time.sleep(5)  # Wait for page to load
        
        # Take initial screenshots
        if args.screenshots:
            logger.info("Taking screenshots")
            screenshots = take_screenshots(driver)
        
        # Simulate human browsing behavior
        logger.info(f"Simulating human browsing behavior for {args.duration} seconds")
        simulator.browse_page_naturally(duration=args.duration)
        
        # Take more screenshots after browsing
        if args.screenshots:
            logger.info("Taking additional screenshots after browsing")
            browsed_screenshots = take_screenshots(driver, "screenshots_after_browsing")
            screenshots.update(browsed_screenshots)
        
        # Extract data
        logger.info(f"Extracting data (max {args.posts} posts)")
        extracted_data = extractor.extract_all_data(args.url, max_posts=args.posts)
        
        # Store the data
        logger.info("Storing extracted data")
        json_path = storage.store_page_data(extracted_data)
        storage_paths["json"] = json_path
        
        # Export to CSV if requested
        if args.format in ["csv", "all"]:
            logger.info("Exporting data to CSV")
            csv_files = storage.export_to_csv()
            storage_paths["csv"] = csv_files
        
        logger.info("Crawler completed successfully")
        
        return {
            "status": "success",
            "url": args.url,
            "extracted_data": extracted_data,
            "storage_paths": storage_paths,
            "screenshots": screenshots
        }
        
    except Exception as e:
        logger.error(f"Error running crawler: {str(e)}")
        return {
            "status": "error",
            "url": args.url,
            "error": str(e),
            "screenshots": screenshots
        }
        
    finally:
        # Clean up
        driver.quit()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Facebook Page Crawler")
    
    parser.add_argument("--url", required=True, help="Facebook page URL to crawl")
    parser.add_argument("--posts", type=int, default=10, help="Maximum number of posts to extract")
    parser.add_argument("--duration", type=int, default=60, help="Duration to browse the page in seconds")
    parser.add_argument("--proxy-file", default="proxies.csv", help="Path to proxy list CSV file")
    parser.add_argument("--proxy-strategy", choices=["sequential", "random", "performance"], default="sequential", help="Proxy rotation strategy")
    parser.add_argument("--format", choices=["json", "csv", "db", "all"], default="all", help="Output format")
    parser.add_argument("--output-dir", default="data", help="Output directory for extracted data")
    parser.add_argument("--screenshots", action="store_true", help="Take screenshots during crawling")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    return parser.parse_args()


def main():
    """Main entry point for the Facebook page crawler."""
    args = parse_arguments()
    results = run_crawler(args)
    
    # Print results summary
    if results["status"] == "success":
        print("\n=== Facebook Page Crawler Results ===")
        print(f"URL: {results['url']}")
        
        if "page_info" in results["extracted_data"]:
            page_info = results["extracted_data"]["page_info"]
            print(f"Page Name: {page_info.get('page_name', 'Unknown')}")
            print(f"Followers: {page_info.get('followers_count', 'Unknown')}")
        
        posts = results["extracted_data"].get("posts", [])
        print(f"Posts Extracted: {len(posts)}")
        
        print("\nStorage Paths:")
        for format_type, path in results["storage_paths"].items():
            print(f"  - {format_type}: {path}")
        
        print("\nScreenshots:")
        for name, path in results["screenshots"].items():
            print(f"  - {name}: {path}")
    else:
        print("\n=== Facebook Page Crawler Error ===")
        print(f"URL: {results['url']}")
        print(f"Error: {results['error']}")


if __name__ == "__main__":
    main()
