import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt

# Input the stock ticker symbol
stock = input("Enter a stock ticker symbol: ")

print(f"Fetching data for {stock}...")

# Define the start and end dates for historical data
start = dt.datetime(2000, 1, 1)
now = dt.datetime.now()

# Download historical data
df = yf.download(stock, start=start, end=now, auto_adjust=False)

# Calculate 3-day MA
df['3MA'] = df['Adj Close'].rolling(window=3).mean()

# Calculate 5-day moving average
df['5MA'] = df['Adj Close'].rolling(window=5).mean()

# Calculate 20-day moving average
df['20MA'] = df['Adj Close'].rolling(window=20).mean()

# Calculate 50-day MA
df['50MA'] = df['Adj Close'].rolling(window=50).mean()

# Calculate 200-day MA
df['200MA'] = df['Adj Close'].rolling(window=200).mean()

# Calculate daily turnover: Volume * Close Price (in millions)
df['Turnover (Millions)'] = (df['Volume'] * df['Close']) / 1_000_000

# Calculate Standard Deviation over 20 days
df['STD20'] = df['Adj Close'].rolling(window=20).std()

# Calculate Upper and Lower Bollinger Bands
df['UpperBand'] = df['20MA'] + 2 * df['STD20']
df['LowerBand'] = df['20MA'] - 2 * df['STD20'] 


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



print(df.tail(25))
