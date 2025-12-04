import os

# API Keys (User should set these in environment variables or replace here)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-key")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "your-kimi-api-key")
KIMI_MODEL_NAME = "kimi-k2-thinking"
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "your-alpha-vantage-key")

# Screener Configuration
MIN_MARKET_CAP = 1_000_000_000  # $1 Billion
MAX_DEBT_TO_EQUITY = 2.0
MIN_DROP_FROM_HIGH_PCT = 0.25  # 25% or more below 52-week high

# Analysis Configuration
MIN_INSIDER_BUY_VALUE = 100_000  # $100k
INSIDER_LOOKBACK_DAYS = 180  # 6 months
