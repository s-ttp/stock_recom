# Stock Recommendation Application

A smart money-driven stock screener that identifies undervalued stocks with strong insider and superinvestor backing.

## Overview

This application uses a 3-phase approach to recommend stocks:

1. **Screening**: Filters S&P 500, NASDAQ 100, and Dow Jones stocks trading near 52-week lows
2. **Smart Money Analysis**: Analyzes insider trading and superinvestor activity from Dataroma and OpenInsider
3. **AI-Powered Research**: Uses OpenAI GPT to generate comprehensive investment thesis

## Features

- **Fundamental Screening**: Market cap > $1B, profitable companies, low debt
- **Smart Money Tracking**: Prioritizes stocks with superinvestor additions and insider buying
- **AI Analysis**: Management quality, business sustainability, and growth outlook
- **PDF Reports**: Professional investment reports with charts and analysis
- **Recommendation History**: 60-day cooldown to avoid repeat recommendations

## Prerequisites

### Python Packages

```bash
pip install pandas yfinance requests beautifulsoup4 lxml html5lib pandas-datareader matplotlib reportlab openai
```

### API Keys

Set the following environment variables or update `config.py`:

- `OPENAI_API_KEY` - Required for AI analysis (get from https://platform.openai.com)
- `ALPHA_VANTAGE_API_KEY` - Required for fundamental data (get from https://www.alphavantage.co)

Optional:
- `GEMINI_API_KEY`
- `KIMI_API_KEY`
- `ANTHROPIC_API_KEY`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/s-ttp/stock_recom.git
cd stock_recom
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys:
```bash
export OPENAI_API_KEY="your-key-here"
export ALPHA_VANTAGE_API_KEY="your-key-here"
```

## Usage

Run the main application:

```bash
python3 main.py
```

## Output

The application generates:
- **Console Output**: Real-time progress and stock rankings
- **PDF Report**: Saved to `~/Desktop/Screener Reports/investment_thesis_{TICKER}.pdf`
- **Recommendation History**: Tracked in `recommendation_history.json`

## Scoring System

Stocks are scored on a 22-point scale:

- **Smart Money (0-10 pts)**: Insider buying + Superinvestor activity
- **AI Analysis (0-10 pts)**: Management quality + Business sustainability
- **Quantitative (0-2 pts)**: Low debt + Price near 52-week low

## Configuration

Edit `config.py` to customize:

- `MIN_MARKET_CAP`: Minimum market capitalization (default: $1B)
- `MIN_DROP_FROM_HIGH_PCT`: Minimum drop from 52-week high (default: 25%)
- `MIN_INSIDER_BUY_VALUE`: Minimum insider purchase value (default: $100k)

## Data Sources

- **Stock Data**: Yahoo Finance (via yfinance)
- **Superinvestor Activity**: Dataroma.com
- **Insider Trading**: OpenInsider.com
- **Fundamental Data**: Alpha Vantage API

## License

MIT License

## Disclaimer

This tool is for educational and research purposes only. Not financial advice. Always do your own research before investing.
