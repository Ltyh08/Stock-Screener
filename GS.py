import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt

# List of stock ticker symbols
stocks = ['NVDA', 'AMD', 'AAPL']

# Define the start and end dates for historical data
start = dt.datetime(2000, 1, 1)
now = dt.datetime.now()

for ticker in stocks:
    print(f"\nFetching data for {ticker}...")

    # Download historical data for each ticker
    df = yf.download(ticker, start=start, end=now, auto_adjust=False)

    if df.empty:
        print(f"No data found for {ticker}")
        continue

    # Moving Averages
    df['3MA'] = df['Adj Close'].rolling(window=3).mean()
    df['5MA'] = df['Adj Close'].rolling(window=5).mean()
    df['20MA'] = df['Adj Close'].rolling(window=20).mean()
    df['50MA'] = df['Adj Close'].rolling(window=50).mean()
    df['200MA'] = df['Adj Close'].rolling(window=200).mean()

    # Turnover (in millions)
    df['Turnover (Millions)'] = (df['Volume'] * df['Close']) / 1_000_000

    # Bollinger Bands
    df['STD20'] = df['Adj Close'].rolling(window=20).std()
    df['UpperBand'] = df['20MA'] + 2 * df['STD20']
    df['LowerBand'] = df['20MA'] - 2 * df['STD20']

    # Daily Return in %
    df['Daily_Return (%)'] = df['Adj Close'].pct_change() * 100

    # RSI (14-day)
    delta = df['Adj Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Volatility (20-day rolling std dev)
    df['Volatility_20D'] = df['Adj Close'].rolling(window=20).std()

    # MACD
    df['EMA12'] = df['Adj Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Adj Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Display last 25 rows
    print(df.tail(25))
