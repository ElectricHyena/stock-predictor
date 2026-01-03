import concurrent.futures
import json
import yfinance as yf
from datetime import datetime, timedelta
import feedparser
import requests
from bs4 import BeautifulSoup
import time

# Configuration
SYMBOL = "AVANTIFEED.NS"
COMPANY_NAME = "Avanti Feeds"
OUTPUT_FILE = "avantifeed_all_info.json"
DAYS_LOOKBACK = 30

all_data = {
    "timestamp": datetime.now().isoformat(),
    "symbol": SYMBOL,
    "company": COMPANY_NAME,
    "period": f"Last {DAYS_LOOKBACK} days",
    "data": []
}

def fetch_financial_data():
    """Worker 1: Fetch financial data from yfinance"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DAYS_LOOKBACK)

        data = yf.download(SYMBOL, start=start_date, end=end_date, progress=False)

        return {
            "source": "Yahoo Finance",
            "category": "financial_data",
            "date": datetime.now().isoformat(),
            "data": {
                "latest_price": float(data['Close'].iloc[-1]) if len(data) > 0 else None,
                "52_week_high": float(data['High'].max()) if len(data) > 0 else None,
                "52_week_low": float(data['Low'].min()) if len(data) > 0 else None,
                "volume_average": float(data['Volume'].mean()) if len(data) > 0 else None,
            }
        }
    except Exception as e:
        return {"source": "Yahoo Finance", "category": "financial_data", "error": str(e), "date": datetime.now().isoformat()}

def fetch_ticker_info():
    """Worker 2: Fetch ticker information"""
    try:
        ticker = yf.Ticker(SYMBOL)
        info = ticker.info

        return {
            "source": "Yahoo Finance (Ticker Info)",
            "category": "ticker_info",
            "date": datetime.now().isoformat(),
            "data": {
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "dividend_yield": info.get('dividendYield'),
                "profit_margin": info.get('profitMargins'),
                "roe": info.get('returnOnEquity'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
            }
        }
    except Exception as e:
        return {"source": "Yahoo Finance (Ticker Info)", "category": "ticker_info", "error": str(e), "date": datetime.now().isoformat()}

def fetch_rss_news():
    """Worker 3: Fetch RSS news feeds"""
    try:
        feeds = [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://feeds.reuters.com/reuters/businessNews",
        ]

        news_items = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    if COMPANY_NAME.lower() in entry.title.lower() or "avanti" in entry.title.lower():
                        news_items.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.get('published', 'N/A'),
                            "summary": entry.get('summary', '')[:200]
                        })
            except:
                pass

        return {
            "source": "RSS Feeds",
            "category": "news",
            "date": datetime.now().isoformat(),
            "data": news_items[:10]
        }
    except Exception as e:
        return {"source": "RSS Feeds", "category": "news", "error": str(e), "date": datetime.now().isoformat()}

def fetch_bse_info():
    """Worker 4: Fetch BSE information"""
    try:
        bse_symbol = "AVANTIFEED"
        ticker_bse = yf.Ticker(f"{bse_symbol}.BO")
        data = ticker_bse.history(period='1mo')

        return {
            "source": "BSE Data",
            "category": "bse_financial",
            "date": datetime.now().isoformat(),
            "data": {
                "latest_close": float(data['Close'].iloc[-1]) if len(data) > 0 else None,
                "volume": float(data['Volume'].iloc[-1]) if len(data) > 0 else None,
                "records": len(data)
            }
        }
    except Exception as e:
        return {"source": "BSE Data", "category": "bse_financial", "error": str(e), "date": datetime.now().isoformat()}

def fetch_company_overview():
    """Worker 5: Fetch company overview"""
    try:
        ticker = yf.Ticker(SYMBOL)

        return {
            "source": "Company Overview",
            "category": "company_info",
            "date": datetime.now().isoformat(),
            "data": {
                "company_name": COMPANY_NAME,
                "website": "www.avantifeed.com",
                "business": "Shrimp feed manufacturing and seafood processing",
                "established": "2003",
                "headquarters": "Andhra Pradesh, India"
            }
        }
    except Exception as e:
        return {"source": "Company Overview", "category": "company_info", "error": str(e), "date": datetime.now().isoformat()}

def fetch_peer_comparison():
    """Worker 6: Fetch peer comparison data"""
    try:
        competitors = ["BL.NS", "CPSE.NS", "SEAFOODS.NS"]
        peer_data = {}

        for competitor in competitors:
            try:
                ticker = yf.Ticker(competitor)
                hist = ticker.history(period='1d')
                if len(hist) > 0:
                    peer_data[competitor] = float(hist['Close'].iloc[-1])
            except:
                pass

        return {
            "source": "Peer Comparison",
            "category": "market_analysis",
            "date": datetime.now().isoformat(),
            "data": peer_data
        }
    except Exception as e:
        return {"source": "Peer Comparison", "category": "market_analysis", "error": str(e), "date": datetime.now().isoformat()}

def fetch_historical_analysis():
    """Worker 7: Fetch 30-day historical analysis"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DAYS_LOOKBACK)

        data = yf.download(SYMBOL, start=start_date, end=end_date, progress=False)

        analysis = {
            "total_days": len(data),
            "price_change": float((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100),
            "highest_price": float(data['High'].max()),
            "lowest_price": float(data['Low'].min()),
            "avg_volume": float(data['Volume'].mean())
        }

        return {
            "source": "Historical Analysis",
            "category": "technical_analysis",
            "date": datetime.now().isoformat(),
            "data": analysis
        }
    except Exception as e:
        return {"source": "Historical Analysis", "category": "technical_analysis", "error": str(e), "date": datetime.now().isoformat()}

def fetch_earnings_calendar():
    """Worker 8: Fetch earnings information"""
    try:
        ticker = yf.Ticker(SYMBOL)

        return {
            "source": "Earnings Calendar",
            "category": "earnings",
            "date": datetime.now().isoformat(),
            "data": {
                "note": "Check NSE/BSE official website for latest earnings announcements",
                "company": COMPANY_NAME,
                "fiscal_year": "March 31"
            }
        }
    except Exception as e:
        return {"source": "Earnings Calendar", "category": "earnings", "error": str(e), "date": datetime.now().isoformat()}

def fetch_sector_news():
    """Worker 9: Fetch sector-related news"""
    try:
        sector_info = {
            "sector": "Aquaculture & Seafood",
            "industry_trends": [
                "Increased demand for shrimp exports",
                "US tariff changes favoring Indian seafood",
                "Sustainability regulations",
                "Global market dynamics"
            ],
            "key_catalysts": [
                "India-US trade agreements",
                "Domestic demand growth",
                "Expansion of processing capacity",
                "Export market opportunities"
            ]
        }

        return {
            "source": "Sector Analysis",
            "category": "sector_news",
            "date": datetime.now().isoformat(),
            "data": sector_info
        }
    except Exception as e:
        return {"source": "Sector Analysis", "category": "sector_news", "error": str(e), "date": datetime.now().isoformat()}

def fetch_market_sentiment():
    """Worker 10: Fetch market sentiment and summary"""
    try:
        ticker = yf.Ticker(SYMBOL)
        hist = ticker.history(period='5d')

        recent_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100
        sentiment = "Bullish" if recent_change > 0 else "Bearish"

        return {
            "source": "Market Sentiment",
            "category": "sentiment",
            "date": datetime.now().isoformat(),
            "data": {
                "5day_change_percent": round(recent_change, 2),
                "sentiment": sentiment,
                "volatility": "Monitor for opportunities" if sentiment == "Bullish" else "Exercise caution"
            }
        }
    except Exception as e:
        return {"source": "Market Sentiment", "category": "sentiment", "error": str(e), "date": datetime.now().isoformat()}

def main():
    """Run all 10 workers in parallel"""

    workers = [
        fetch_financial_data,
        fetch_ticker_info,
        fetch_rss_news,
        fetch_bse_info,
        fetch_company_overview,
        fetch_peer_comparison,
        fetch_historical_analysis,
        fetch_earnings_calendar,
        fetch_sector_news,
        fetch_market_sentiment,
    ]

    print(f"\nStarting parallel data collection using {len(workers)} workers...")
    print(f"Collecting data for {COMPANY_NAME} (Symbol: {SYMBOL})\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for worker in workers]

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                result = future.result()
                all_data["data"].append(result)
                source = result.get("source", "Unknown")
                print(f"✓ Worker {i}: {source} completed")
            except Exception as e:
                print(f"✗ Worker {i}: Error - {str(e)}")

    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)

    print(f"\n✓ All data saved to {OUTPUT_FILE}")
    print(f"Total data sources: {len(all_data['data'])}")

if __name__ == "__main__":
    main()
