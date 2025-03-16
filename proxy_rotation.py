"""
Proxy Rotation System for Facebook Page Crawler

This module implements a proxy rotation system to avoid IP blocking and maintain
anonymity during the crawling process. It provides functionality to:
1. Load proxies from a CSV file
2. Rotate proxies based on different strategies (sequential, random)
3. Handle proxy errors and timeouts
4. Track proxy performance
"""

import csv
import random
import time
from typing import List, Dict, Optional, Tuple

import requests
from requests.exceptions import ProxyError, ReadTimeout, ConnectTimeout, RequestException


class ProxyManager:
    """
    Manages a pool of proxies and provides rotation functionality.
    """
    
    def __init__(self, proxy_file_path: str, timeout: int = 10):
        """
        Initialize the proxy manager.
        
        Args:
            proxy_file_path: Path to the CSV file containing proxies
            timeout: Default timeout for proxy requests in seconds
        """
        self.proxy_file_path = proxy_file_path
        self.timeout = timeout
        self.proxies = []
        self.current_index = 0
        self.proxy_stats = {}  # Track success/failure for each proxy
        
        # Load proxies from file
        self.load_proxies()
        
    def load_proxies(self) -> None:
        """Load proxies from the CSV file."""
        try:
            with open(self.proxy_file_path, 'r') as f:
                reader = csv.reader(f)
                self.proxies = [row[0].strip() for row in reader if row]
                
            if not self.proxies:
                print("Warning: No proxies found in the file.")
            else:
                print(f"Loaded {len(self.proxies)} proxies.")
                
            # Initialize stats for each proxy
            for proxy in self.proxies:
                self.proxy_stats[proxy] = {
                    'success': 0,
                    'failure': 0,
                    'last_used': None,
                    'avg_response_time': 0
                }
                
        except FileNotFoundError:
            print(f"Proxy file not found: {self.proxy_file_path}")
            # Create an empty file for future use
            with open(self.proxy_file_path, 'w') as f:
                f.write("# Add your proxies here, one per line in the format:\n")
                f.write("# http://ip:port\n")
                f.write("# https://username:password@ip:port\n")
            
    def get_proxy(self, rotation_strategy: str = 'sequential') -> Optional[str]:
        """
        Get the next proxy based on the rotation strategy.
        
        Args:
            rotation_strategy: Strategy for rotating proxies ('sequential', 'random', 'performance')
            
        Returns:
            A proxy string or None if no proxies are available
        """
        if not self.proxies:
            return None
            
        if rotation_strategy == 'random':
            proxy = random.choice(self.proxies)
        elif rotation_strategy == 'performance':
            # Get the proxy with the best success rate
            proxy = self._get_best_performing_proxy()
        else:  # sequential
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
        # Update last used timestamp
        self.proxy_stats[proxy]['last_used'] = time.time()
        return proxy
        
    def _get_best_performing_proxy(self) -> str:
        """Return the proxy with the best success rate."""
        best_proxy = self.proxies[0]
        best_score = -1
        
        for proxy, stats in self.proxy_stats.items():
            total = stats['success'] + stats['failure']
            if total == 0:
                # If never used, give it a chance
                score = 0
            else:
                score = stats['success'] / total
                
            if score > best_score:
                best_score = score
                best_proxy = proxy
                
        return best_proxy
        
    def update_proxy_stats(self, proxy: str, success: bool, response_time: float = None) -> None:
        """
        Update statistics for a proxy.
        
        Args:
            proxy: The proxy string
            success: Whether the request was successful
            response_time: The response time in seconds
        """
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {
                'success': 0,
                'failure': 0,
                'last_used': time.time(),
                'avg_response_time': 0
            }
            
        stats = self.proxy_stats[proxy]
        
        if success:
            stats['success'] += 1
            if response_time is not None:
                # Update average response time
                total = stats['success'] + stats['failure']
                stats['avg_response_time'] = (
                    (stats['avg_response_time'] * (total - 1) + response_time) / total
                )
        else:
            stats['failure'] += 1
            
    def format_proxy_for_requests(self, proxy: str) -> Dict[str, str]:
        """
        Format a proxy string for use with the requests library.
        
        Args:
            proxy: Proxy string (e.g., 'http://ip:port')
            
        Returns:
            Dictionary for use with requests.get(..., proxies=...)
        """
        # Extract the scheme (http or https)
        scheme = proxy.split('://')[0] if '://' in proxy else 'http'
        
        return {scheme: proxy}
        
    def request_with_proxy_rotation(
        self, 
        url: str, 
        rotation_strategy: str = 'sequential',
        max_retries: int = 3,
        **kwargs
    ) -> Tuple[Optional[requests.Response], Optional[str]]:
        """
        Make a request with automatic proxy rotation.
        
        Args:
            url: The URL to request
            rotation_strategy: Strategy for rotating proxies
            max_retries: Maximum number of retries before giving up
            **kwargs: Additional arguments to pass to requests.get()
            
        Returns:
            Tuple of (response, used_proxy) or (None, None) if all proxies failed
        """
        retries = 0
        
        while retries < max_retries:
            proxy = self.get_proxy(rotation_strategy)
            
            if not proxy:
                print("No proxies available.")
                return None, None
                
            proxies = self.format_proxy_for_requests(proxy)
            
            try:
                start_time = time.time()
                response = requests.get(
                    url, 
                    proxies=proxies, 
                    timeout=self.timeout,
                    **kwargs
                )
                response_time = time.time() - start_time
                
                # Update stats
                self.update_proxy_stats(proxy, True, response_time)
                
                return response, proxy
                
            except (ProxyError, ReadTimeout, ConnectTimeout, RequestException) as e:
                print(f"Proxy error with {proxy}: {str(e)}")
                self.update_proxy_stats(proxy, False)
                retries += 1
                
        print(f"Failed after {max_retries} retries.")
        return None, None


# Example usage
if __name__ == "__main__":
    # Create a proxy manager
    proxy_manager = ProxyManager("proxies.csv")
    
    # Test with a sample URL
    response, proxy = proxy_manager.request_with_proxy_rotation(
        "https://ip.oxylabs.io/location",
        rotation_strategy='sequential'
    )
    
    if response:
        print(f"Success with proxy {proxy}")
        print(f"Response: {response.text}")
    else:
        print("All proxies failed.")
