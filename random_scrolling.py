"""
Random Scrolling Behavior for Facebook Page Crawler

This module implements variable scrolling speeds to simulate natural user behavior,
reducing the chance of detection by anti-bot systems. It provides functionality to:
1. Scroll with random speeds
2. Add random pauses between scrolling actions
3. Implement human-like interaction patterns
"""

import random
import time
from typing import Tuple, Optional, List, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class HumanBehaviorSimulator:
    """
    Simulates human-like browsing behavior with variable scrolling speeds,
    random pauses, and natural interaction patterns.
    """
    
    def __init__(self, driver: webdriver.Chrome):
        """
        Initialize the human behavior simulator.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        
        # Default configuration for human-like behavior
        self.config = {
            # Scrolling parameters
            'scroll_min_pixels': 100,
            'scroll_max_pixels': 800,
            'scroll_min_speed': 300,  # pixels per second
            'scroll_max_speed': 1200,  # pixels per second
            
            # Pause parameters
            'min_pause_before_scroll': 0.5,  # seconds
            'max_pause_before_scroll': 3.0,  # seconds
            'min_pause_after_scroll': 1.0,   # seconds
            'max_pause_after_scroll': 5.0,   # seconds
            
            # Session parameters
            'session_min_duration': 30,  # seconds
            'session_max_duration': 300, # seconds
            
            # Interaction parameters
            'mouse_movement_probability': 0.3,
            'click_probability': 0.1,
            'hover_probability': 0.2
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update the behavior configuration.
        
        Args:
            new_config: Dictionary with configuration parameters to update
        """
        self.config.update(new_config)
    
    def random_pause(self, min_time: float, max_time: float) -> None:
        """
        Pause for a random amount of time.
        
        Args:
            min_time: Minimum pause time in seconds
            max_time: Maximum pause time in seconds
        """
        pause_time = random.uniform(min_time, max_time)
        time.sleep(pause_time)
    
    def scroll_with_random_speed(self, direction: str = 'down', distance: Optional[int] = None) -> None:
        """
        Scroll with a random speed in the specified direction.
        
        Args:
            direction: Scroll direction ('up' or 'down')
            distance: Scroll distance in pixels, random if None
        """
        # Random pause before scrolling
        self.random_pause(
            self.config['min_pause_before_scroll'],
            self.config['max_pause_before_scroll']
        )
        
        # Determine scroll distance
        if distance is None:
            distance = random.randint(
                self.config['scroll_min_pixels'],
                self.config['scroll_max_pixels']
            )
        
        # Adjust distance for direction
        if direction == 'up':
            distance = -distance
        
        # Calculate scroll duration based on random speed
        speed = random.uniform(
            self.config['scroll_min_speed'],
            self.config['scroll_max_speed']
        )
        duration = abs(distance) / speed
        
        # Perform the scroll with the calculated duration
        script = f"""
        var start = window.pageYOffset;
        var distance = {distance};
        var duration = {duration * 1000}; // Convert to milliseconds
        var startTime = null;
        
        function animate(currentTime) {{
            if (startTime === null) startTime = currentTime;
            var timeElapsed = currentTime - startTime;
            var progress = Math.min(timeElapsed / duration, 1);
            
            // Easing function to make scrolling more natural
            progress = 0.5 - 0.5 * Math.cos(progress * Math.PI);
            
            window.scrollTo(0, start + distance * progress);
            
            if (timeElapsed < duration) {{
                requestAnimationFrame(animate);
            }}
        }}
        
        requestAnimationFrame(animate);
        """
        self.driver.execute_script(script)
        
        # Wait for scroll animation to complete
        time.sleep(duration + 0.1)
        
        # Random pause after scrolling
        self.random_pause(
            self.config['min_pause_after_scroll'],
            self.config['max_pause_after_scroll']
        )
    
    def move_mouse_randomly(self) -> None:
        """Move the mouse cursor to a random position on the page."""
        # Get viewport dimensions
        viewport_width = self.driver.execute_script("return window.innerWidth;")
        viewport_height = self.driver.execute_script("return window.innerHeight;")
        
        # Generate random coordinates within the viewport
        x = random.randint(0, viewport_width)
        y = random.randint(0, viewport_height)
        
        # Move the mouse
        actions = ActionChains(self.driver)
        actions.move_by_offset(x, y).perform()
    
    def random_mouse_movement(self) -> None:
        """Perform random mouse movements with natural curves."""
        # Get viewport dimensions
        viewport_width = self.driver.execute_script("return window.innerWidth;")
        viewport_height = self.driver.execute_script("return window.innerHeight;")
        
        # Generate random start and end points
        start_x = random.randint(0, viewport_width)
        start_y = random.randint(0, viewport_height)
        end_x = random.randint(0, viewport_width)
        end_y = random.randint(0, viewport_height)
        
        # Generate a random control point for a quadratic curve
        control_x = (start_x + end_x) / 2 + random.randint(-100, 100)
        control_y = (start_y + end_y) / 2 + random.randint(-100, 100)
        
        # Create a sequence of points along the curve
        points = []
        steps = random.randint(10, 20)
        
        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bezier curve formula
            x = (1 - t) * (1 - t) * start_x + 2 * (1 - t) * t * control_x + t * t * end_x
            y = (1 - t) * (1 - t) * start_y + 2 * (1 - t) * t * control_y + t * t * end_y
            points.append((int(x), int(y)))
        
        # Move the mouse along the curve with varying speeds
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(self.driver.find_element(By.TAG_NAME, 'body'), start_x, start_y)
        actions.perform()
        
        for point in points:
            actions = ActionChains(self.driver)
            actions.move_by_offset(point[0] - start_x, point[1] - start_y)
            actions.perform()
            start_x, start_y = point
            time.sleep(random.uniform(0.01, 0.05))
    
    def random_hover(self) -> None:
        """Randomly hover over a clickable element."""
        try:
            # Find all clickable elements
            elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'a, button, input[type="button"], input[type="submit"], .clickable')
            
            if elements:
                # Choose a random element
                element = random.choice(elements)
                
                # Hover over the element
                actions = ActionChains(self.driver)
                actions.move_to_element(element).perform()
                
                # Pause for a random duration
                self.random_pause(0.5, 2.0)
        except Exception as e:
            print(f"Error during random hover: {str(e)}")
    
    def random_click(self) -> None:
        """Randomly click on a non-critical element (like expanding comments)."""
        try:
            # Find potential safe elements to click (expand comments, like buttons, etc.)
            # This is Facebook-specific and should be customized based on the page structure
            safe_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                '.see-more, .UFIPagerLink, .UFICommentLink, .UFILikeLink')
            
            if safe_elements:
                # Choose a random element
                element = random.choice(safe_elements)
                
                # Click the element
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                
                # Pause for a random duration
                self.random_pause(1.0, 3.0)
        except Exception as e:
            print(f"Error during random click: {str(e)}")
    
    def simulate_reading(self, duration: Optional[float] = None) -> None:
        """
        Simulate a user reading the content by pausing.
        
        Args:
            duration: Reading duration in seconds, random if None
        """
        if duration is None:
            # Calculate reading time based on content length
            content_length = len(self.driver.find_element(By.TAG_NAME, 'body').text)
            # Average reading speed: ~200-300 words per minute
            # Assuming average word length of 5 characters
            words = content_length / 5
            duration = words / random.uniform(200, 300) * 60
            # Cap the duration to a reasonable range
            duration = min(max(duration, 2.0), 30.0)
        
        time.sleep(duration)
    
    def perform_random_action(self) -> None:
        """Perform a random action based on configured probabilities."""
        rand = random.random()
        
        if rand < self.config['mouse_movement_probability']:
            self.random_mouse_movement()
        elif rand < self.config['mouse_movement_probability'] + self.config['hover_probability']:
            self.random_hover()
        elif rand < self.config['mouse_movement_probability'] + self.config['hover_probability'] + self.config['click_probability']:
            self.random_click()
        else:
            # Just pause as if reading
            self.simulate_reading(random.uniform(1.0, 5.0))
    
    def scroll_page(self, direction: str = 'down', num_scrolls: int = 5) -> None:
        """
        Scroll the page multiple times with random behavior.
        
        Args:
            direction: Scroll direction ('up' or 'down')
            num_scrolls: Number of scroll actions to perform
        """
        for _ in range(num_scrolls):
            # Perform random action before scrolling
            if random.random() < 0.7:  # 70% chance to perform a random action
                self.perform_random_action()
            
            # Scroll with random speed and distance
            self.scroll_with_random_speed(direction)
            
            # Perform random action after scrolling
            if random.random() < 0.5:  # 50% chance to perform a random action
                self.perform_random_action()
    
    def browse_page_naturally(self, duration: Optional[float] = None) -> None:
        """
        Browse a page naturally for a specified duration.
        
        Args:
            duration: Browsing duration in seconds, random if None
        """
        if duration is None:
            duration = random.uniform(
                self.config['session_min_duration'],
                self.config['session_max_duration']
            )
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            action = random.choice([
                'scroll_down',
                'scroll_up',
                'random_action',
                'read'
            ])
            
            if action == 'scroll_down':
                self.scroll_with_random_speed('down')
            elif action == 'scroll_up':
                self.scroll_with_random_speed('up')
            elif action == 'random_action':
                self.perform_random_action()
            elif action == 'read':
                self.simulate_reading()


# Example usage
if __name__ == "__main__":
    # Initialize a WebDriver
    driver = webdriver.Chrome()
    
    try:
        # Navigate to a Facebook page
        driver.get("https://www.facebook.com/example")
        
        # Create a human behavior simulator
        simulator = HumanBehaviorSimulator(driver)
        
        # Browse the page naturally
        simulator.browse_page_naturally(duration=60)  # 1 minute
        
    finally:
        # Clean up
        driver.quit()
