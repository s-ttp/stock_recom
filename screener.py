import pandas as pd
import ssl

# Bypass SSL verification for legacy systems/macOS specific issues
ssl._create_default_https_context = ssl._create_unverified_context

import requests
from io import StringIO
import config
import time
import random
import random
from rate_limiter import alpha_vantage_limiter

def get_html_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return StringIO(response.text)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_fundamental_data(ticker):
    """
    Fetches fundamental data: Market Cap, Free Cash Flow, Debt/Equity.
    Uses Alpha Vantage for reliable data.
    """
    data = {
        'market_cap': None,
        'free_cash_flow': None,
        'debt_to_equity': None
    }
    
    try:
        from alpha_vantage.fundamentaldata import FundamentalData
        
        # Rate limit: Wait if needed to stay under 75 calls/minute
        alpha_vantage_limiter.wait_if_needed()
        
        fd = FundamentalData(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
        
        # Get company overview
        overview, _ = fd.get_company_overview(ticker)
        
        if overview:
            # Market Cap
            mc = overview.get('MarketCapitalization')
            data['market_cap'] = int(mc) if mc and mc != 'None' else None
            
            # Debt to Equity (Total Debt / Total Equity)
            de = overview.get('DebtToEquity')
            data['debt_to_equity'] = float(de) if de and de != 'None' else None
            
            # Net Income (TTM)
            ni = overview.get('EBITDA') # Alpha Vantage Overview has EBITDA, ProfitMargin, etc. 
            # Let's check if NetIncomeTTM exists. It usually does.
            # If not, we can use ProfitMargin * RevenueTTM?
            # Let's try to get 'RevenueTTM' and 'ProfitMargin' to calculate or just use 'EBITDA' as proxy?
            # No, user asked for Net Income.
            # Alpha Vantage Overview usually has 'RevenueTTM', 'ProfitMargin', 'OperatingMarginTTM', 'ReturnOnAssetsTTM', 'ReturnOnEquityTTM', 'RevenuePerShareTTM', 'QuarterlyRevenueGrowthYOY', 'GrossProfitTTM', 'DilutedEPSTTM', 'QuarterlyEarningsGrowthYOY'.
            # It might not have NetIncomeTTM directly in Overview.
            # But we have get_quarterly_financials in research.py now!
            # We can use that? Or just fetch it here.
            # Let's check if Overview has it. Documentation says it has 'EBITDA', 'PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'DividendYield', 'EPS', 'RevenuePerShareTTM', 'ProfitMargin', 'OperatingMarginTTM', 'ReturnOnAssetsTTM', 'ReturnOnEquityTTM', 'RevenueTTM', 'GrossProfitTTM', 'DilutedEPSTTM', 'QuarterlyEarningsGrowthYOY', 'QuarterlyRevenueGrowthYOY', 'AnalystTargetPrice', 'TrailingPE', 'ForwardPE', 'PriceToSalesRatioTTM', 'PriceToBookRatio', 'EVToRevenue', 'EVToEBITDA', 'Beta', '52WeekHigh', '52WeekLow', '50DayMovingAverage', '200DayMovingAverage', 'SharesOutstanding', 'DividendDate', 'ExDividendDate'.
            # It doesn't seem to have NetIncomeTTM directly.
            # But Net Income = Revenue * Profit Margin.
            # Let's calculate it.
            
            rev = overview.get('RevenueTTM')
            margin = overview.get('ProfitMargin')
            
            if rev and margin and rev != 'None' and margin != 'None':
                data['net_income'] = float(rev) * float(margin)
            else:
                data['net_income'] = None
            
        # Get cash flow statement for FCF
        try:
            # Rate limit: Wait if needed
            alpha_vantage_limiter.wait_if_needed()
            
            cashflow, _ = fd.get_cash_flow_annual(ticker)
            if cashflow and 'annualReports' in cashflow:
                latest = cashflow['annualReports'][0] if cashflow['annualReports'] else {}
                ocf = latest.get('operatingCashflow')
                capex = latest.get('capitalExpenditures')
                
                if ocf and capex:
                    # FCF = Operating Cash Flow - Capital Expenditures
                    data['free_cash_flow'] = int(ocf) - abs(int(capex))
        except:
            pass
            
    except Exception as e:
        print(f"Alpha Vantage failed for {ticker}: {e}")
        pass
        
    return data

def get_sp500_tickers():
    """Fetches S&P 500 tickers from Wikipedia."""
    try:
        html = get_html_content('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        tables = pd.read_html(html, header=0)
        
        # Try to find the right table by looking for Symbol/Ticker column
        for df in tables:
            # Check for various possible column names
            if 'Symbol' in df.columns:
                tickers = df['Symbol'].tolist()
                return [t.replace('.', '-') for t in tickers if isinstance(t, str)]
            elif 'Ticker symbol' in df.columns:
                tickers = df['Ticker symbol'].tolist()
                return [t.replace('.', '-') for t in tickers if isinstance(t, str)]
            elif 'Ticker' in df.columns:
                tickers = df['Ticker'].tolist()
                return [t.replace('.', '-') for t in tickers if isinstance(t, str)]
        
        # If no table found with expected columns, print debug info
        print(f"S&P 500 table not found. Found {len(tables)} tables.")
        if tables:
            print(f"First table columns: {tables[0].columns.tolist()[:5]}")
        return []
            
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_nasdaq100_tickers():
    """Fetches NASDAQ 100 tickers from Wikipedia."""
    try:
        html = get_html_content('https://en.wikipedia.org/wiki/NASDAQ-100')
        table = pd.read_html(html, header=0)
        # The table index might vary, usually it's the 4th table (index 3) or similar.
        for df in table:
            if 'Ticker' in df.columns:
                return [t.replace('.', '-') for t in df['Ticker'].tolist()]
            if 'Symbol' in df.columns:
                return [t.replace('.', '-') for t in df['Symbol'].tolist()]
        print("Could not find NASDAQ 100 table.")
        return []
    except Exception as e:
        print(f"Error fetching NASDAQ 100 tickers: {e}")
        return []

def get_dow_tickers():
    """Fetches Dow Jones Industrial Average tickers from Wikipedia."""
    try:
        html = get_html_content('https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average')
        table = pd.read_html(html, header=0)
        
        for df in table:
            # print("Checking table columns:", df.columns)
            if 'Symbol' in df.columns:
                return [t.replace('.', '-') for t in df['Symbol'].tolist()]
            if 'Ticker' in df.columns:
                return [t.replace('.', '-') for t in df['Ticker'].tolist()]
        
        print("Could not find Dow Jones table.")
        return []
    except Exception as e:
        print(f"Error fetching Dow Jones tickers: {e}")
        return []

def get_all_tickers():
    """Combines tickers from all three indices."""
    sp500 = set(get_sp500_tickers())
    nasdaq = set(get_nasdaq100_tickers())
    dow = set(get_dow_tickers())
    
    all_tickers = list(sp500.union(nasdaq).union(dow))
    return sorted(all_tickers)


def filter_stocks(tickers):
    """
    Filters stocks that are within 30% of their 52-week low.
    Returns a list of dictionaries with stock info.
    """
    shortlist = []
    print(f"Screening {len(tickers)} stocks using Stooq...")
    
    
    for ticker_symbol in tickers:
        try:
            print(f"Checking {ticker_symbol}...")
            
            # 1. Price Check (Use Alpha Vantage for reliability)
            try:
                from alpha_vantage.timeseries import TimeSeries
                
                # Rate limit: Wait if needed
                alpha_vantage_limiter.wait_if_needed()
                
                ts = TimeSeries(key=config.ALPHA_VANTAGE_API_KEY, output_format='pandas')
                df, _ = ts.get_daily(symbol=ticker_symbol, outputsize='full')
                
                # Filter for last year
                start_date = pd.Timestamp.now() - pd.Timedelta(days=365)
                df = df[df.index > start_date]
                
                if df.empty:
                    print(f"  Skipping {ticker_symbol}: No price data found")
                    continue
                
                # Alpha Vantage returns data with most recent first? No, pandas format usually index sorted?
                # Let's sort just in case
                df = df.sort_index()
                
                current_price = df['4. close'].iloc[-1]
                low_52w = df['4. close'].min()
                high_52w = df['4. close'].max()
            except Exception as e:
                print(f"  Error fetching price for {ticker_symbol}: {e}")
                continue
            
            if pd.isna(current_price) or pd.isna(low_52w) or low_52w == 0:
                print(f"  Skipping {ticker_symbol}: Invalid price data")
                continue
            
            # Check if dropped significantly from 52-week high
            # We want stocks that are at least X% below their high
            drop_pct = (high_52w - current_price) / high_52w
            
            if drop_pct < config.MIN_DROP_FROM_HIGH_PCT:
                print(f"  Skipping {ticker_symbol}: Only dropped {drop_pct*100:.1f}% from high (Target: >{config.MIN_DROP_FROM_HIGH_PCT*100:.0f}%)")
                continue
                
            # 2. Fundamental Checks
            # Fetch data (Market Cap, FCF, D/E, Net Income)
            fund_data = get_fundamental_data(ticker_symbol)
            
            # Market Cap > $1 Billion (config.MIN_MARKET_CAP)
            mc = fund_data.get('market_cap')
            if mc is None or mc < config.MIN_MARKET_CAP:
                print(f"  Skipping {ticker_symbol}: Market Cap too low (${mc:,.0f} if available)")
                continue
            
            # Net Income > 0
            ni = fund_data.get('net_income')
            if ni is None or ni <= 0:
                print(f"  Skipping {ticker_symbol}: Negative or missing Net Income")
                continue
                
            # REMOVED: FCF and Debt/Equity filters as per request
            # But we still need the data for the report/scoring
            fcf = fund_data.get('free_cash_flow')
            de = fund_data.get('debt_to_equity')
            
            print(f"  Passed! Adding {ticker_symbol} to shortlist.")
            
            diff_pct = (current_price - low_52w) / low_52w * 100
            shortlist.append({
                'Ticker': ticker_symbol,
                'Current_Price': round(current_price, 2),
                '52_Week_Low': round(low_52w, 2),
                '52_Week_High': round(high_52w, 2),
                'Above_Low_Pct': round(diff_pct, 2),
                'Drop_From_High_Pct': round(drop_pct * 100, 2),
                'Market_Cap': mc,
                'FCF': fcf,
                'Debt_Equity': de
            })
            
            # Be nice to APIs
            time.sleep(0.1)
                
        except Exception as e:
            # print(f"Error processing {ticker_symbol}: {e}")
            continue
            
    return shortlist

if __name__ == "__main__":
    # Test fetching
    print("Fetching tickers...")
    tickers = get_all_tickers()
    print(f"Found {len(tickers)} unique tickers.")
    
    # Test filtering with a small subset
    print("Testing filter with first 10 tickers...")
    filtered = filter_stocks(tickers[:10])
    print("Filtered results:", filtered)
