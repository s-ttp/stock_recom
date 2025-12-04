import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

def get_html_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_superinvestor_data(ticker):
    """
    Scrapes Dataroma for superinvestor activity.
    Returns a summary dictionary.
    """
    url = f"https://www.dataroma.com/m/stock.php?sym={ticker}"
    html = get_html_content(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the grid table
    table = soup.find('table', id='grid')
    if not table:
        # print(f"No superinvestor data found for {ticker}")
        return {'buys': 0, 'sells': 0, 'holds': 0, 'buyers': [], 'sellers': []}
    
    buys = 0
    sells = 0
    holds = 0
    
    buyers = []
    sellers = []
    
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 4:
            continue
        
        # Investor name is in the first column
        investor_name = cols[0].get_text().strip()
        activity_text = cols[3].get_text().strip().lower()
        
        if 'buy' in activity_text or 'add' in activity_text:
            buys += 1
            buyers.append(investor_name)
        elif 'sell' in activity_text or 'reduce' in activity_text:
            sells += 1
            sellers.append(investor_name)
        else:
            holds += 1
            
    return {
        'buys': buys,
        'sells': sells,
        'holds': holds,
        'buyers': buyers,
        'sellers': sellers,
        'total_activity': buys + sells + holds,
        'has_superinvestor_addition': buys > 0 # Simple proxy for "addition"
    }

def get_insider_data(ticker):
    """
    Scrapes OpenInsider for insider activity.
    Returns a summary dictionary.
    """
    url = f"http://openinsider.com/search?q={ticker}"
    html = get_html_content(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the tinytable
    table = soup.find('table', class_='tinytable')
    if not table:
        # print(f"No insider data found for {ticker}")
        return {'buys': 0, 'sells': 0, 'net_value': 0}
    
    buys = 0
    sells = 0
    net_value = 0.0
    
    rows = table.find('tbody').find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 12:
            continue
        
        trade_type = cols[6].get_text().strip()
        value_text = cols[11].get_text().strip().replace('$', '').replace(',', '')
        
        try:
            value = float(value_text)
        except:
            value = 0.0
            
        if 'Purchase' in trade_type:
            buys += 1
            net_value += value
        elif 'Sale' in trade_type:
            sells += 1
            net_value -= abs(value) # Ensure it's subtracted
            
    return {
        'buys': buys,
        'sells': sells,
        'net_value': net_value,
        'total_bought_value': net_value if net_value > 0 else 0 # Simplified, ideally sum of buys
    }

def analyze_stock(ticker):
    """
    Combines superinvestor and insider data.
    """
    superinvestor = get_superinvestor_data(ticker)
    # Be nice to servers
    time.sleep(random.uniform(0.5, 1.5)) 
    insider = get_insider_data(ticker)
    
    return {
        'ticker': ticker,
        'superinvestor': superinvestor,
        'insider': insider
    }

if __name__ == "__main__":
    # Test with AAPL
    print(analyze_stock("AAPL"))
