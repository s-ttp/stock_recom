import time
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """
    Rate limiter to ensure API calls don't exceed specified limits.
    Uses a sliding window approach to track calls.
    """
    def __init__(self, max_calls, time_window_seconds):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window_seconds: Time window in seconds (e.g., 60 for per minute)
        """
        self.max_calls = max_calls
        self.time_window = timedelta(seconds=time_window_seconds)
        self.calls = deque()
    
    def wait_if_needed(self):
        """
        Wait if necessary to stay within rate limits.
        Automatically removes old calls outside the time window.
        """
        now = datetime.now()
        
        # Remove calls outside the time window
        while self.calls and (now - self.calls[0]) > self.time_window:
            self.calls.popleft()
        
        # If at limit, wait until oldest call expires
        if len(self.calls) >= self.max_calls:
            oldest_call = self.calls[0]
            wait_until = oldest_call + self.time_window
            wait_seconds = (wait_until - now).total_seconds()
            
            if wait_seconds > 0:
                print(f"Rate limit reached. Waiting {wait_seconds:.1f} seconds...")
                time.sleep(wait_seconds + 0.1)  # Add small buffer
                
                # Clean up again after waiting
                now = datetime.now()
                while self.calls and (now - self.calls[0]) > self.time_window:
                    self.calls.popleft()
        
        # Record this call
        self.calls.append(now)
    
    def get_current_usage(self):
        """Get current number of calls in the time window."""
        now = datetime.now()
        
        # Remove old calls
        while self.calls and (now - self.calls[0]) > self.time_window:
            self.calls.popleft()
        
        return len(self.calls)
    
    def reset(self):
        """Reset the rate limiter."""
        self.calls.clear()

# Global rate limiter for Alpha Vantage (75 calls per minute)
alpha_vantage_limiter = RateLimiter(max_calls=75, time_window_seconds=60)

if __name__ == "__main__":
    # Test the rate limiter
    limiter = RateLimiter(max_calls=5, time_window_seconds=10)
    
    print("Testing rate limiter (5 calls per 10 seconds)...")
    for i in range(8):
        limiter.wait_if_needed()
        print(f"Call {i+1} at {datetime.now().strftime('%H:%M:%S')} - Usage: {limiter.get_current_usage()}/5")
        time.sleep(0.5)
