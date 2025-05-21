import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt
import os
from dotenv import load_dotenv

# Load .env file and get the Excel output path
load_dotenv()
file_path = os.getenv("EXCEL_OUTPUT_PATH")
if not file_path:
    raise ValueError("EXCEL_OUTPUT_PATH not set in .env file.")

# List of stock ticker symbols
stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD']

# Define the start and end dates
start = dt.datetime(2000, 1, 1)
now = dt.datetime.now()

# Ensure the file exists before appending to it
if not os.path.exists(file_path):
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        pass  # Create an empty Excel file

# Loop through each stock ticker and fetch data
for ticker in stocks:
    print(f"\nFetching data for {ticker}...")
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

    #High Lows
    df['52W_High'] = df['Adj Close'].rolling(window=252).max()
    df['52W_Low'] = df['Adj Close'].rolling(window=252).min()

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

    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))


    # Volatility (20-day)
    df['Volatility_20D'] = df['Adj Close'].rolling(window=20).std()

    # MACD
    df['EMA12'] = df['Adj Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Adj Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    #ATR
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR_14'] = df['TR'].rolling(window=14).mean()


    # Save to Excel sheet named after the ticker, replacing the sheet but preserving workbook
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=ticker)

print(f"\n✅ All data written to {file_path} without overwriting formatting.")
