"""
Data Storage Module for Facebook Page Crawler

This module implements functionality to store extracted Facebook data securely
in structured formats (CSV, JSON) and provides data validation and error handling.
"""

import os
import csv
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("facebook_storage.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("facebook_storage")


class DataStorage:
    """
    Handles storage of extracted Facebook data in various formats.
    """
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize the data storage.
        
        Args:
            output_dir: Directory to store output files
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create subdirectories for different data types
        self.pages_dir = os.path.join(output_dir, "pages")
        self.posts_dir = os.path.join(output_dir, "posts")
        self.images_dir = os.path.join(output_dir, "images")
        self.videos_dir = os.path.join(output_dir, "videos")
        
        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        
        # Initialize SQLite database
        self.db_path = os.path.join(output_dir, "facebook_data.db")
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create pages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id TEXT,
                page_name TEXT,
                page_url TEXT UNIQUE,
                profile_image_url TEXT,
                followers_count TEXT,
                category TEXT,
                extraction_time TEXT,
                raw_data TEXT
            )
            ''')
            
            # Create posts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                page_id INTEGER,
                post_url TEXT UNIQUE,
                timestamp TEXT,
                text_content TEXT,
                likes INTEGER,
                comments INTEGER,
                shares INTEGER,
                extraction_time TEXT,
                raw_data TEXT,
                FOREIGN KEY (page_id) REFERENCES pages (id)
            )
            ''')
            
            # Create media table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                media_type TEXT,
                media_url TEXT,
                local_path TEXT,
                extraction_time TEXT,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def save_to_json(self, data: Dict[str, Any], filename: str) -> str:
        """
        Save data to a JSON file.
        
        Args:
            data: Data to save
            filename: Output filename (without extension)
            
        Returns:
            Path to the saved file
        """
        try:
            # Add timestamp to filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"{filename}_{timestamp}.json")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Data saved to JSON: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")
            return ""
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Save data to a CSV file.
        
        Args:
            data: List of dictionaries to save
            filename: Output filename (without extension)
            
        Returns:
            Path to the saved file
        """
        try:
            # Add timestamp to filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"{filename}_{timestamp}.csv")
            
            # Convert to DataFrame for easier CSV handling
            df = pd.DataFrame(data)
            
            # Handle nested dictionaries by converting them to strings
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                    df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
            
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Data saved to CSV: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return ""
    
    def store_page_data(self, page_data: Dict[str, Any]) -> str:
        """
        Store Facebook page data.
        
        Args:
            page_data: Dictionary containing page information
            
        Returns:
            Path to the saved file
        """
        try:
            # Extract page name for filename
            page_name = page_data.get("page_info", {}).get("page_name", "unknown_page")
            page_name = self._sanitize_filename(page_name)
            
            # Save to JSON
            output_path = os.path.join(self.pages_dir, f"{page_name}")
            json_path = self.save_to_json(page_data, output_path)
            
            # Store in database
            self._store_page_in_db(page_data)
            
            return json_path
            
        except Exception as e:
            logger.error(f"Error storing page data: {str(e)}")
            return ""
    
    def _store_page_in_db(self, page_data: Dict[str, Any]) -> int:
        """
        Store page data in SQLite database.
        
        Args:
            page_data: Dictionary containing page information
            
        Returns:
            Page ID in the database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            page_info = page_data.get("page_info", {})
            
            # Check if page already exists
            cursor.execute("SELECT id FROM pages WHERE page_url = ?", (page_info.get("page_url", ""),))
            result = cursor.fetchone()
            
            if result:
                page_id = result[0]
                logger.info(f"Page already exists in database with ID: {page_id}")
            else:
                # Insert new page
                cursor.execute('''
                INSERT INTO pages (
                    page_id, page_name, page_url, profile_image_url, 
                    followers_count, category, extraction_time, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    "", # page_id (not available in our extraction)
                    page_info.get("page_name", ""),
                    page_info.get("page_url", ""),
                    page_info.get("profile_image_url", ""),
                    page_info.get("followers_count", ""),
                    page_info.get("category", ""),
                    page_info.get("extraction_time", datetime.now().isoformat()),
                    json.dumps(page_info)
                ))
                
                page_id = cursor.lastrowid
                logger.info(f"Inserted new page with ID: {page_id}")
            
            # Store posts
            posts = page_data.get("posts", [])
            for post in posts:
                self._store_post_in_db(post, page_id, conn)
            
            conn.commit()
            conn.close()
            
            return page_id
            
        except Exception as e:
            logger.error(f"Error storing page in database: {str(e)}")
            return -1
    
    def _store_post_in_db(self, post: Dict[str, Any], page_id: int, conn: sqlite3.Connection) -> int:
        """
        Store post data in SQLite database.
        
        Args:
            post: Dictionary containing post information
            page_id: ID of the parent page in the database
            conn: SQLite connection
            
        Returns:
            Post ID in the database
        """
        try:
            cursor = conn.cursor()
            
            # Check if post already exists
            cursor.execute("SELECT id FROM posts WHERE post_url = ?", (post.get("post_url", ""),))
            result = cursor.fetchone()
            
            if result:
                post_id = result[0]
                logger.info(f"Post already exists in database with ID: {post_id}")
            else:
                # Get reaction counts
                reactions = post.get("reactions", {})
                
                # Insert new post
                cursor.execute('''
                INSERT INTO posts (
                    post_id, page_id, post_url, timestamp, text_content,
                    likes, comments, shares, extraction_time, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.get("post_id", ""),
                    page_id,
                    post.get("post_url", ""),
                    post.get("timestamp", ""),
                    post.get("text_content", ""),
                    reactions.get("likes", 0),
                    reactions.get("comments", 0),
                    reactions.get("shares", 0),
                    post.get("extraction_time", datetime.now().isoformat()),
                    json.dumps(post)
                ))
                
                post_id = cursor.lastrowid
                logger.info(f"Inserted new post with ID: {post_id}")
                
                # Store media
                image_urls = post.get("image_urls", [])
                for url in image_urls:
                    self._store_media_in_db(post_id, "image", url, conn)
                    
                video_urls = post.get("video_urls", [])
                for url in video_urls:
                    self._store_media_in_db(post_id, "video", url, conn)
            
            return post_id
            
        except Exception as e:
            logger.error(f"Error storing post in database: {str(e)}")
            return -1
    
    def _store_media_in_db(self, post_id: int, media_type: str, media_url: str, conn: sqlite3.Connection) -> int:
        """
        Store media data in SQLite database.
        
        Args:
            post_id: ID of the parent post in the database
            media_type: Type of media ('image' or 'video')
            media_url: URL of the media
            conn: SQLite connection
            
        Returns:
            Media ID in the database
        """
        try:
            cursor = conn.cursor()
            
            # Check if media already exists
            cursor.execute("SELECT id FROM media WHERE post_id = ? AND media_url = ?", (post_id, media_url))
            result = cursor.fetchone()
            
            if result:
                media_id = result[0]
                logger.info(f"Media already exists in database with ID: {media_id}")
            else:
                # Insert new media
                cursor.execute('''
                INSERT INTO media (
                    post_id, media_type, media_url, local_path, extraction_time
                ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    post_id,
                    media_type,
                    media_url,
                    "",  # local_path (to be filled when media is downloaded)
                    datetime.now().isoformat()
                ))
                
                media_id = cursor.lastrowid
                logger.info(f"Inserted new media with ID: {media_id}")
            
            return media_id
            
        except Exception as e:
            logger.error(f"Error storing media in database: {str(e)}")
            return -1
    
    def export_to_csv(self) -> Dict[str, str]:
        """
        Export all database data to CSV files.
        
        Returns:
            Dictionary with paths to the exported CSV files
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Export pages
            pages_df = pd.read_sql_query("SELECT * FROM pages", conn)
            pages_csv = os.path.join(self.output_dir, f"pages_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            pages_df.to_csv(pages_csv, index=False)
            
            # Export posts
            posts_df = pd.read_sql_query("SELECT * FROM posts", conn)
            posts_csv = os.path.join(self.output_dir, f"posts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            posts_df.to_csv(posts_csv, index=False)
            
            # Export media
            media_df = pd.read_sql_query("SELECT * FROM media", conn)
            media_csv = os.path.join(self.output_dir, f"media_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            media_df.to_csv(media_csv, index=False)
            
            conn.close()
            
            logger.info(f"Data exported to CSV files")
            return {
                "pages": pages_csv,
                "posts": posts_csv,
                "media": media_csv
            }
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return {}
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 50:
            filename = filename[:50]
            
        return filename


# Example usage
if __name__ == "__main__":
    # Create a data storage instance
    storage = DataStorage()
    
    # Example data
    example_data = {
        "page_info": {
            "page_name": "Example Page",
            "page_url": "https://www.facebook.com/example",
            "profile_image_url": "https://example.com/image.jpg",
            "followers_count": "1.2K followers",
            "category": "Technology",
            "extraction_time": datetime.now().isoformat()
        },
        "posts": [
            {
                "post_id": "123456789",
                "post_url": "https://www.facebook.com/example/posts/123456789",
                "timestamp": "2023-01-01 12:00:00",
                "text_<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>