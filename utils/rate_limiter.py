"""
Rate Limiter Utility
Prevents too frequent requests to avoid blocking
"""

import time
import random
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Implements rate limiting between requests
    """
    
    def __init__(self, min_delay: float = 3, max_delay: float = 5):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self):
        """Wait before next request"""
        elapsed = time.time() - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def reset(self):
        """Reset the rate limiter"""
        self.last_request_time = 0


if __name__ == "__main__":
    limiter = RateLimiter(min_delay=2, max_delay=4)
    
    for i in range(3):
        print(f"Request {i+1}")
        limiter.wait()
        print(f"Made request at {time.time()}")
