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

import yfinance as yf

def get_company_info(ticker):
    """
    Fetches company info using Alpha Vantage and Yahoo Finance.
    Merges data to get the most comprehensive metrics.
    """
    info = {
        'summary': 'No summary available.',
        'sector': 'Unknown',
        'industry': 'Unknown',
        'marketCap': None,
        'forwardPE': None,
        'targetMeanPrice': None,
        'recommendationKey': 'Unknown',
        'name': ticker,
        'exchange': 'Unknown',
        'currency': 'USD',
        'country': 'Unknown',
        '52WeekHigh': None,
        '52WeekLow': None,
        # Valuation Metrics
        'PERatio': None,
        'PriceToBookRatio': None,
        'DividendYield': None,
        'ReturnOnEquityTTM': None,
        'ProfitMargin': None,
        'EVToEBITDA': None,
        'PriceToSalesRatioTTM': None,
        'Beta': None,
        'PEGRatio': None
    }

    # 1. Try Alpha Vantage first (for consistency with existing flow)
    try:
        # Rate limit: Wait if needed
        alpha_vantage_limiter.wait_if_needed()
        fd = FundamentalData(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
        data, _ = fd.get_company_overview(ticker)
        
        if data:
            info.update({
                'summary': data.get('Description', info['summary']),
                'sector': data.get('Sector', info['sector']),
                'industry': data.get('Industry', info['industry']),
                'marketCap': int(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') and data.get('MarketCapitalization') != 'None' else None,
                'forwardPE': safe_float(data.get('ForwardPE')),
                'targetMeanPrice': safe_float(data.get('AnalystTargetPrice')),
                'name': data.get('Name', ticker),
                'exchange': data.get('Exchange', info['exchange']),
                'currency': data.get('Currency', info['currency']),
                'country': data.get('Country', info['country']),
                '52WeekHigh': safe_float(data.get('52WeekHigh')),
                '52WeekLow': safe_float(data.get('52WeekLow')),
                'PERatio': safe_float(data.get('PERatio')),
                'PriceToBookRatio': safe_float(data.get('PriceToBookRatio')),
                'DividendYield': safe_float(data.get('DividendYield')),
                'ReturnOnEquityTTM': safe_float(data.get('ReturnOnEquityTTM')),
                'ProfitMargin': safe_float(data.get('ProfitMargin')),
                'EVToEBITDA': safe_float(data.get('EVToEBITDA')),
                'PriceToSalesRatioTTM': safe_float(data.get('PriceToSalesRatioTTM')),
                'Beta': safe_float(data.get('Beta')),
                'PEGRatio': safe_float(data.get('PEGRatio'))
            })
    except Exception as e:
        print(f"Alpha Vantage fetch failed for {ticker}: {e}")

    # 2. Enhance/Fallback with Yahoo Finance - REMOVED due to instability
    # try:
    #     yf_ticker = yf.Ticker(ticker)
    #     yf_info = yf_ticker.info
    #     ...
    # except Exception as e:
    #     print(f"Yahoo Finance fetch failed for {ticker}: {e}")
        
    return info

def get_balance_sheet(ticker):
    """
    Fetches the latest annual balance sheet using Alpha Vantage.
    Returns a dictionary of key balance sheet items.
    """
    try:
        # Rate limit: Wait if needed
        alpha_vantage_limiter.wait_if_needed()
        
        fd = FundamentalData(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
        bs, _ = fd.get_balance_sheet_annual(ticker)
        
        latest = None
        if isinstance(bs, dict) and 'annualReports' in bs and bs.get('annualReports'):
            latest = bs['annualReports'][0]
        elif hasattr(bs, 'iloc') and not bs.empty: # Handle DataFrame
            latest = bs.iloc[0].to_dict()
        
        if not latest:
            return None
            
        # Convert to dictionary with safe access and float conversion
        def get_val(key):
            val = latest.get(key)
            return float(val) if val and val != 'None' else 0

        return {
            "Total Assets": get_val("totalAssets"),
            "Total Liabilities": get_val("totalLiabilities"),
            "Total Equity": get_val("totalShareholderEquity"),
            "Cash And Cash Equivalents": get_val("cashAndCashEquivalentsAtCarryingValue"),
            "Total Debt": get_val("shortTermDebt") + get_val("longTermDebt"), # Approximation
            "Working Capital": get_val("totalCurrentAssets") - get_val("totalCurrentLiabilities"),
            "Date": latest.get("fiscalDateEnding", "N/A")
        }
        
    except Exception as e:
        print(f"Error fetching balance sheet for {ticker}: {e}")
        return None

def get_cash_flow(ticker):
    """
    Fetches the latest annual cash flow statement using Alpha Vantage.
    Returns a dictionary of key cash flow items.
    """
    try:
        # Rate limit: Wait if needed
        alpha_vantage_limiter.wait_if_needed()
        
        fd = FundamentalData(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
        cf, _ = fd.get_cash_flow_annual(ticker)
        
        latest = None
        if isinstance(cf, dict) and 'annualReports' in cf and cf.get('annualReports'):
            latest = cf['annualReports'][0]
        elif hasattr(cf, 'iloc') and not cf.empty: # Handle DataFrame
            latest = cf.iloc[0].to_dict()
            
        if not latest:
            return None
            
        # Convert to dictionary with safe access and float conversion
        def get_val(key):
            val = latest.get(key)
            return float(val) if val and val != 'None' else 0

        return {
            "Operating Cash Flow": get_val("operatingCashflow"),
            "Investing Cash Flow": get_val("cashflowFromInvestment"),
            "Financing Cash Flow": get_val("cashflowFromFinancing"),
            "Capital Expenditure": get_val("capitalExpenditures"),
            "Free Cash Flow": get_val("operatingCashflow") - abs(get_val("capitalExpenditures")),
            "Date": latest.get("fiscalDateEnding", "N/A")
        }
        
    except Exception as e:
        print(f"Error fetching cash flow for {ticker}: {e}")
        return None

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
            # Safe EPS parsing - use None for missing data instead of 0.0
            eps_raw = report.get('reportedEPS')
            if eps_raw and eps_raw != 'None':
                try:
                    eps = float(eps_raw)
                except (ValueError, TypeError):
                    eps = None
            else:
                eps = None
            
            quarterly_data.append({
                'fiscalDateEnding': report.get('fiscalDateEnding', 'N/A'),
                'totalRevenue': float(report.get('totalRevenue', 0)),
                'netIncome': float(report.get('netIncome', 0)),
                'reportedEPS': eps
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
