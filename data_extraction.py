"""
Data Extraction Module for Facebook Page Crawler

This module implements functionality to extract various types of data from Facebook pages,
including posts, images, videos, and related metadata. It provides:
1. Post content extraction
2. Image and video link extraction
3. Metadata extraction (timestamps, reactions, etc.)
4. Structured data output
"""

import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("facebook_extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("facebook_extractor")


class FacebookExtractor:
    """
    Extracts data from Facebook pages including posts, images, videos, and metadata.
    """
    
    def __init__(self, driver: webdriver.Chrome):
        """
        Initialize the Facebook extractor.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    def extract_page_info(self) -> Dict[str, Any]:
        """
        Extract basic information about the Facebook page.
        
        Returns:
            Dictionary containing page information
        """
        logger.info("Extracting page information")
        
        try:
            # Wait for the page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            
            # Get page HTML
            page_html = self.driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Extract page name (usually in the h1 tag)
            page_name = ""
            name_element = soup.find('h1')
            if name_element:
                page_name = name_element.text.strip()
            
            # Extract page URL
            page_url = self.driver.current_url
            
            # Extract page profile image (Facebook usually has a profile image with role="img")
            profile_image = ""
            img_elements = soup.find_all(attrs={"role": "img"})
            for img in img_elements:
                if img.has_attr('src') and 'profile' in img['src'].lower():
                    profile_image = img['src']
                    break
            
            # Extract page likes/followers count
            followers_count = ""
            followers_elements = soup.find_all(string=re.compile(r'(followers|likes)'))
            if followers_elements:
                for element in followers_elements:
                    if re.search(r'\d+', element):
                        followers_count = element.strip()
                        break
            
            # Extract page category
            category = ""
            category_elements = soup.find_all('span')
            for span in category_elements:
                if span.parent and span.parent.name == 'div' and 'category' in str(span.parent).lower():
                    category = span.text.strip()
                    break
            
            return {
                "page_name": page_name,
                "page_url": page_url,
                "profile_image_url": profile_image,
                "followers_count": followers_count,
                "category": category,
                "extraction_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting page info: {str(e)}")
            return {
                "page_url": self.driver.current_url,
                "extraction_time": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def extract_posts(self, max_posts: int = 10) -> List[Dict[str, Any]]:
        """
        Extract posts from the Facebook page.
        
        Args:
            max_posts: Maximum number of posts to extract
            
        Returns:
            List of dictionaries containing post data
        """
        logger.info(f"Extracting up to {max_posts} posts")
        
        posts = []
        post_elements = []
        
        try:
            # Wait for posts to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']")))
            
            # Get initial post elements
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
            
            # Scroll to load more posts if needed
            current_posts_count = len(post_elements)
            while current_posts_count < max_posts:
                # Scroll down to load more posts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for new posts to load
                
                # Get updated post elements
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
                
                # Check if we've loaded new posts
                if len(post_elements) <= current_posts_count:
                    # No new posts loaded, break the loop
                    break
                    
                current_posts_count = len(post_elements)
                
                # Avoid infinite loops
                if current_posts_count >= max_posts or current_posts_count > 100:
                    break
            
            # Process each post
            for i, post_element in enumerate(post_elements[:max_posts]):
                try:
                    post_data = self._extract_post_data(post_element)
                    posts.append(post_data)
                except Exception as e:
                    logger.error(f"Error extracting post {i}: {str(e)}")
            
            return posts
            
        except Exception as e:
            logger.error(f"Error extracting posts: {str(e)}")
            return posts
    
    def _extract_post_data(self, post_element) -> Dict[str, Any]:
        """
        Extract data from a single post element.
        
        Args:
            post_element: WebElement representing a post
            
        Returns:
            Dictionary containing post data
        """
        # Get post HTML
        post_html = post_element.get_attribute('outerHTML')
        soup = BeautifulSoup(post_html, 'html.parser')
        
        # Extract post ID (usually in data attributes)
        post_id = ""
        if post_element.get_attribute('id'):
            post_id = post_element.get_attribute('id')
        
        # Extract post URL
        post_url = ""
        link_elements = soup.find_all('a')
        for link in link_elements:
            href = link.get('href', '')
            if 'posts' in href or 'permalink' in href:
                post_url = f"https://www.facebook.com{href}" if href.startswith('/') else href
                break
        
        # Extract post timestamp
        timestamp = ""
        time_elements = soup.find_all(['abbr', 'span'])
        for element in time_elements:
            if element.has_attr('title') or element.has_attr('data-utime'):
                timestamp = element.get('title', element.text.strip())
                break
        
        # Extract post text content
        text_content = ""
        content_elements = soup.find_all(['p', 'span', 'div'])
        for element in content_elements:
            if len(element.text) > 50:  # Likely to be the main content
                text_content = element.text.strip()
                break
        
        # Extract image URLs
        image_urls = []
        img_elements = soup.find_all('img')
        for img in img_elements:
            if img.has_attr('src') and not 'profile' in img['src'].lower():
                image_urls.append(img['src'])
        
        # Extract video URLs
        video_urls = []
        video_elements = soup.find_all(['video', 'div'])
        for element in video_elements:
            if element.has_attr('data-video-id') or element.has_attr('data-video'):
                video_id = element.get('data-video-id', element.get('data-video', ''))
                if video_id:
                    video_urls.append(f"https://www.facebook.com/watch/?v={video_id}")
        
        # Extract reaction counts
        reactions = {
            "likes": 0,
            "comments": 0,
            "shares": 0
        }
        
        reaction_elements = soup.find_all(['span', 'div'])
        for element in reaction_elements:
            text = element.text.lower()
            if 'like' in text and re.search(r'\d+', text):
                reactions["likes"] = self._extract_count(text)
            elif 'comment' in text and re.search(r'\d+', text):
                reactions["comments"] = self._extract_count(text)
            elif 'share' in text and re.search(r'\d+', text):
                reactions["shares"] = self._extract_count(text)
        
        return {
            "post_id": post_id,
            "post_url": post_url,
            "timestamp": timestamp,
            "text_content": text_content,
            "image_urls": image_urls,
            "video_urls": video_urls,
            "reactions": reactions,
            "extraction_time": datetime.now().isoformat()
        }
    
    def _extract_count(self, text: str) -> int:
        """
        Extract numeric count from text.
        
        Args:
            text: Text containing a count (e.g., "5 likes", "1.2K comments")
            
        Returns:
            Numeric count
        """
        # Remove non-numeric characters except for K, M, and decimal points
        clean_text = re.sub(r'[^0-9KkMm.]', '', text)
        
        # Extract the numeric part
        match = re.search(r'(\d+(\.\d+)?[KkMm]?)', clean_text)
        if not match:
            return 0
            
        count_str = match.group(1)
        
        # Convert K/M suffixes to actual numbers
        if 'k' in count_str.lower():
            return int(float(count_str.lower().replace('k', '')) * 1000)
        elif 'm' in count_str.lower():
            return int(float(count_str.lower().replace('m', '')) * 1000000)
        else:
            return int(float(count_str))
    
    def extract_comments(self, post_element, max_comments: int = 5) -> List[Dict[str, Any]]:
        """
        Extract comments from a post.
        
        Args:
            post_element: WebElement representing a post
            max_comments: Maximum number of comments to extract
            
        Returns:
            List of dictionaries containing comment data
        """
        comments = []
        
        try:
            # Try to expand comments if they're collapsed
            try:
                view_comments_links = post_element.find_elements(By.XPATH, 
                    ".//span[contains(text(), 'View') and contains(text(), 'comment')]")
                if view_comments_links:
                    view_comments_links[0].click()
                    time.sleep(2)  # Wait for comments to load
            except Exception as e:
                logger.warning(f"Could not expand comments: {str(e)}")
            
            # Find comment elements
            comment_elements = post_element.find_elements(By.CSS_SELECTOR, "div[role='article'][aria-label*='Comment']")
            
            # Process each comment
            for i, comment_element in enumerate(comment_elements[:max_comments]):
                try:
                    comment_html = comment_element.get_attribute('outerHTML')
                    soup = BeautifulSoup(comment_html, 'html.parser')
                    
                    # Extract commenter name
                    commenter_name = ""
                    name_elements = soup.find_all('a')
                    for element in name_elements:
                        if element.has_attr('href') and '/user/' in element.get('href', ''):
                            commenter_name = element.text.strip()
                            break
                    
                    # Extract comment text
                    comment_text = ""
                    text_elements = soup.find_all(['span', 'div'])
                    for element in text_elements:
                        if len(element.text) > 5 and not element.find_parent('a'):
                            comment_text = element.text.strip()
                            break
                    
                    # Extract timestamp
                    timestamp = ""
                    time_elements = soup.find_all(['abbr', 'span'])
                    for element in time_elements:
                        if element.has_attr('title') or 'ago' in element.text.lower():
                            timestamp = element.get('title', element.text.strip())
                            break
                    
                    comments.append({
                        "commenter_name": commenter_name,
                        "comment_text": comment_text,
                        "timestamp": timestamp
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting comment {i}: {str(e)}")
            
            return comments
            
        except Exception as e:
            logger.error(f"Error extracting comments: {str(e)}")
            return comments
    
    def extract_all_data(self, page_url: str, max_posts: int = 10) -> Dict[str, Any]:
        """
        Extract all data from a Facebook page.
        
        Args:
            page_url: URL of the Facebook page
            max_posts: Maximum number of posts to extract
            
        Returns:
            Dictionary containing all extracted data
        """
        logger.info(f"Extracting all data from {page_url}")
        
        try:
            # Navigate to the page
            self.driver.get(page_url)
            time.sleep(5)  # Wait for page to load
            
            # Extract page info
            page_info = self.extract_page_info()
            
            # Extract posts
            posts = self.extract_posts(max_posts)
            
            # Combine all data
            all_data = {
                "page_info": page_info,
                "posts": posts,
                "extraction_time": datetime.now().isoformat()
            }
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error extracting all data: {str(e)}")
            return {
                "page_url": page_url,
                "error": str(e),
                "extraction_time": datetime.now().isoformat()
            }


# Example usage
if __name__ == "__main__":
    # Initialize a WebDriver
    driver = webdriver.Chrome()
    
    try:
        # Create a Facebook extractor
        extractor = FacebookExtractor(driver)
        
        # Extract data from a Facebook page
        data = extractor.extract_all_data("https://www.facebook.com/example", max_posts=5)
        
        # Print the extracted data
        print(json.dumps(data, indent=2))
        
    finally:
        # Clean up
        driver.quit()
