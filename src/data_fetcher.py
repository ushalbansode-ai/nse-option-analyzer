"""
NSE Data Fetcher Module
Handles all data fetching operations from NSE
"""

import requests
import time
import random
import logging
from typing import Dict, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import NSEConfig
from utils.nse_bypass import NSEBypass
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class NSEDataFetcher:
    """
    Fetches option chain data from NSE with anti-blocking measures
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.bypass = NSEBypass(self.session)
        self.rate_limiter = RateLimiter(
            min_delay=NSEConfig.MIN_REQUEST_DELAY,
            max_delay=NSEConfig.MAX_REQUEST_DELAY
        )
        self.cookies = None
        
    def fetch_option_chain(self, symbol: str = 'NIFTY') -> Optional[Dict]:
        """
        Fetch option chain data from NSE
        
        Args:
            symbol: Index symbol (NIFTY, BANKNIFTY, etc.)
            
        Returns:
            Option chain data as dictionary or None
        """
        # Apply rate limiting
        self.rate_limiter.wait()
        
        # Get fresh cookies if not available
        if not self.cookies:
            if not self.bypass.get_cookies():
                return None
            self.cookies = self.session.cookies
            time.sleep(1)
        
        try:
            url = f"{NSEConfig.OPTION_CHAIN_URL}?symbol={symbol}"
            
            response = self.session.get(
                url,
                cookies=self.cookies,
                timeout=NSEConfig.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Successfully fetched option chain for {symbol}")
                return data
            elif response.status_code == 401:
                # Unauthorized - refresh cookies
                logger.warning("Unauthorized - refreshing cookies")
                self.cookies = None
                return self.fetch_option_chain(symbol)
            else:
                logger.error(f"Failed to fetch data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option chain: {str(e)}")
            return None
    
    def get_spot_price(self, data: Dict) -> float:
        """Extract current spot price from option chain data"""
        try:
            return float(data.get('records', {}).get('underlyingValue', 0))
        except:
            return 0.0
    
    def get_expiry_dates(self, data: Dict) -> list:
        """Extract all expiry dates from option chain data"""
        try:
            return data.get('records', {}).get('expiryDates', [])
        except:
            return []


if __name__ == "__main__":
    # Test the fetcher
    logging.basicConfig(level=logging.INFO)
    
    fetcher = NSEDataFetcher()
    data = fetcher.fetch_option_chain('NIFTY')
    
    if data:
        print(f"✓ Data fetched successfully")
        print(f"Spot Price: {fetcher.get_spot_price(data)}")
        print(f"Expiry Dates: {fetcher.get_expiry_dates(data)}")
    else:
        print("✗ Failed to fetch data")
