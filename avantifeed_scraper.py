import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Stock symbol for Avanti Feeds on NSE
symbol = "AVANTIFEED.NS"

# Get last 30 days of data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Download data
df = yf.download(symbol, start=start_date, end=end_date, progress=False)

# Display the data
print(f"\n{symbol} - Last 30 Days\n")
print(f"{'Date':<12} {'High':<10} {'Low':<10} {'Change%':<10}")
print("-" * 42)

for i, (date, row) in enumerate(df.iterrows()):
    date_str = date.strftime('%d-%b')
    high = f"{float(row['High']):.2f}"
    low = f"{float(row['Low']):.2f}"

    if i == 0:
        change_pct = 0.0
    else:
        prev_close = float(df.iloc[i-1]['Close'])
        curr_close = float(row['Close'])
        change_pct = ((curr_close - prev_close) / prev_close) * 100

    change_str = f"{change_pct:+.2f}%"
    print(f"{date_str:<12} {high:<10} {low:<10} {change_str:<10}")

# Optional: Save to CSV
df.to_csv('avantifeed_30days.csv')
print(f"\nData saved to avantifeed_30days.csv")
