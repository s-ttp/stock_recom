import requests
import xml.etree.ElementTree as ET
import ssl
import time
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.timeseries import TimeSeries
import config
from rate_limiter import alpha_vantage_limiter

def safe_float(val):
    """Safely converts a value to float, handling None and '-'."""
    if val is None:
        return None
    if isinstance(val, str):
        if val.strip() == '-' or val.strip().lower() == 'none':
            return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

# Bypass SSL verification for legacy systems/macOS specific issues
ssl._create_default_https_context = ssl._create_unverified_context

def get_news(ticker):
    """
    Fetches news from Google News RSS.
    Returns a list of dictionaries with title, link, and pubDate.
    """
    url = f"https://news.google.com/rss/search?q={ticker}+stock"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        news_items = []
        
        for item in root.findall('./channel/item')[:5]: # Top 5 news
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            
            news_items.append({
                'title': title,
                'link': link,
                'pubDate': pub_date
            })
            
        return news_items
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

def get_company_info(ticker):
    """
    Fetches company info using Alpha Vantage.
    Much more reliable than Yahoo Finance.
    """
    try:
        # Rate limit: Wait if needed to stay under 75 calls/minute
        alpha_vantage_limiter.wait_if_needed()
        
        fd = FundamentalData(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
        
        # Get company overview
        data, meta_data = fd.get_company_overview(ticker)
        
        if not data:
            return {
                'summary': 'No summary available.',
                'sector': 'Unknown',
                'industry': 'Unknown',
                'marketCap': None,
                'forwardPE': None,
                'targetMeanPrice': None,
                'recommendationKey': 'Unknown'
            }
        
        return {
            'summary': data.get('Description', 'No summary available.'),
            'sector': data.get('Sector', 'Unknown'),
            'industry': data.get('Industry', 'Unknown'),
            'marketCap': int(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') and data.get('MarketCapitalization') != 'None' else None,
            'forwardPE': safe_float(data.get('ForwardPE')),
            'targetMeanPrice': safe_float(data.get('AnalystTargetPrice')),
            'recommendationKey': 'Unknown',
            'name': data.get('Name', ticker),
            'exchange': data.get('Exchange', 'Unknown'),
            'currency': data.get('Currency', 'USD'),
            'country': data.get('Country', 'Unknown'),
            # Valuation Metrics
            'PERatio': safe_float(data.get('PERatio')),
            'PriceToBookRatio': safe_float(data.get('PriceToBookRatio')),
            'DividendYield': safe_float(data.get('DividendYield')),
            'ReturnOnEquityTTM': safe_float(data.get('ReturnOnEquityTTM')),
            'ProfitMargin': safe_float(data.get('ProfitMargin'))
        }
        
    except Exception as e:
        print(f"Error fetching company info for {ticker}: {e}")
        return {
            'Summary': "Information not available.",
            'Sector': "N/A",
            'Industry': "N/A",
            'Employees': "N/A",
            'City': "N/A",
            'State': "N/A",
            'Country': "N/A",
            'Website': "N/A"
        }

def get_quarterly_financials(ticker):
    """
    Fetches quarterly financial data (Revenue, Net Income, EPS) for the last 8 quarters.
    """
    try:
        # Rate limit: Wait if needed
        alpha_vantage_limiter.wait_if_needed()
        
        fd = FundamentalData(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
        
        # Get income statement
        income_stmt, _ = fd.get_income_statement_annual(ticker) # Using annual method but it returns quarterly too usually? 
        # Wait, get_income_statement_annual returns (data, meta_data). 
        # Actually Alpha Vantage library has get_income_statement_quarterly?
        # Let's check the library or use the generic get_income_statement which returns both.
        
        # The library method get_income_statement_annual actually calls the API with function=INCOME_STATEMENT
        # and returns annual reports.
        # There isn't a get_income_statement_quarterly in some versions, but let's try get_income_statement() if available
        # or check what get_income_statement_annual returns.
        # Usually the API returns both annual and quarterly in the JSON.
        # The python library might parse it.
        
        # Let's use requests directly to be sure, or check if library supports it.
        # Using requests is safer for specific structure.
        
        url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={config.ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if 'quarterlyReports' not in data:
            return []
            
        quarterly_data = []
        for report in data['quarterlyReports'][:8]: # Last 8 quarters
            quarterly_data.append({
                'fiscalDateEnding': report.get('fiscalDateEnding', 'N/A'),
                'totalRevenue': float(report.get('totalRevenue', 0)),
                'netIncome': float(report.get('netIncome', 0)),
                'reportedEPS': float(report.get('reportedEPS', 0)) if report.get('reportedEPS') != 'None' else 0.0
            })
            
        return quarterly_data
        
    except Exception as e:
        print(f"Error fetching quarterly financials for {ticker}: {e}")
        return []

def get_earnings_history(ticker):
    """
    Fetches historical quarterly EPS data.
    """
    try:
        # Rate limit: Wait if needed
        alpha_vantage_limiter.wait_if_needed()
        
        url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={config.ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if 'quarterlyEarnings' not in data:
            return []
            
        return data['quarterlyEarnings']
        
    except Exception as e:
        print(f"Error fetching earnings history for {ticker}: {e}")
        return []

def get_context_for_ai(ticker):
    """
    Aggregates news and company info into a single string for AI context.
    """
    info = get_company_info(ticker)
    news = get_news(ticker)
    
    context = f"Company: {ticker}\n"
    context += f"Name: {info.get('name', ticker)}\n"
    context += f"Sector: {info['sector']}\n"
    context += f"Industry: {info['industry']}\n"
    context += f"Summary: {info['summary']}\n\n"
    
    context += "Recent News:\n"
    for n in news:
        context += f"- {n['title']} ({n['pubDate']})\n"
        
    return context

if __name__ == "__main__":
    print("Testing news fetch for AAPL...")
    news = get_news("AAPL")
    for n in news:
        print(f"- {n['title']}")
        
    print("\nTesting info fetch for AAPL...")
    info = get_company_info("AAPL")
    print(f"Name: {info.get('name', 'N/A')}")
    print(f"Sector: {info['sector']}")
    print(f"Market Cap: ${info['marketCap']:,}" if info['marketCap'] else "Market Cap: N/A")
    print(f"Summary: {info['summary'][:100]}...")
