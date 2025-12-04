import json
import os
from datetime import datetime, timedelta

class RecommendationHistory:
    def __init__(self, history_file='recommendation_history.json'):
        """
        Manages recommendation history to prevent recommending the same stock within 60 days.
        """
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self):
        """Load recommendation history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_history(self):
        """Save recommendation history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def is_recently_recommended(self, ticker, days=60):
        """
        Check if a ticker was recommended within the last N days.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to check (default 60)
        
        Returns:
            True if recently recommended, False otherwise
        """
        if ticker not in self.history:
            return False
        
        last_recommended = datetime.fromisoformat(self.history[ticker]['date'])
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return last_recommended > cutoff_date
    
    def add_recommendation(self, ticker, score, price_delta):
        """
        Add a new recommendation to history.
        
        Args:
            ticker: Stock ticker symbol
            score: Smart money score
            price_delta: Price delta percentage from 52-week low
        """
        self.history[ticker] = {
            'date': datetime.now().isoformat(),
            'score': score,
            'price_delta': price_delta
        }
        self._save_history()
    
    def get_excluded_tickers(self, days=60):
        """
        Get list of tickers that should be excluded from recommendations.
        
        Args:
            days: Number of days to exclude (default 60)
        
        Returns:
            List of ticker symbols to exclude
        """
        excluded = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for ticker, data in self.history.items():
            last_recommended = datetime.fromisoformat(data['date'])
            if last_recommended > cutoff_date:
                excluded.append(ticker)
        
        return excluded
    
    def get_recommendation_info(self, ticker):
        """Get information about when a ticker was last recommended."""
        if ticker not in self.history:
            return None
        
        data = self.history[ticker]
        last_date = datetime.fromisoformat(data['date'])
        days_ago = (datetime.now() - last_date).days
        
        return {
            'last_recommended': last_date.strftime('%Y-%m-%d'),
            'days_ago': days_ago,
            'score': data.get('score', 'N/A'),
            'price_delta': data.get('price_delta', 'N/A')
        }
    
    def clean_old_entries(self, days=365):
        """Remove entries older than specified days to keep file size manageable."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        tickers_to_remove = []
        for ticker, data in self.history.items():
            last_recommended = datetime.fromisoformat(data['date'])
            if last_recommended < cutoff_date:
                tickers_to_remove.append(ticker)
        
        for ticker in tickers_to_remove:
            del self.history[ticker]
        
        if tickers_to_remove:
            self._save_history()
            print(f"Cleaned {len(tickers_to_remove)} old entries from history.")

if __name__ == "__main__":
    # Test the recommendation history
    history = RecommendationHistory()
    
    # Add a test recommendation
    history.add_recommendation("AAPL", 8.5, 15.2)
    
    # Check if recently recommended
    print(f"AAPL recently recommended: {history.is_recently_recommended('AAPL')}")
    print(f"MSFT recently recommended: {history.is_recently_recommended('MSFT')}")
    
    # Get excluded tickers
    excluded = history.get_excluded_tickers()
    print(f"Excluded tickers: {excluded}")
    
    # Get recommendation info
    info = history.get_recommendation_info("AAPL")
    if info:
        print(f"AAPL last recommended: {info['last_recommended']} ({info['days_ago']} days ago)")
