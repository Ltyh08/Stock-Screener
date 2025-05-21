import pandas as pd
import os
from dotenv import load_dotenv

# Load Excel file path from .env
load_dotenv()
file_path = os.getenv("EXCEL_OUTPUT_PATH")
if not file_path or not os.path.exists(file_path):
    raise FileNotFoundError("Excel file not found or path not set in .env")

# Get all sheet names (tickers) from the Excel file
xls = pd.ExcelFile(file_path)
stocks = xls.sheet_names

# Screening results
screened_stocks = []

# Screening function based on Minervini's template
def meets_minervini_criteria(df, ticker):
    latest = df.iloc[-1]

    if len(df) < 220:
        print(f"⚠ {ticker}: Not enough data to evaluate 200MA slope.")
        return False

    ma_200_now = df['200MA'].iloc[-1]
    ma_200_past = df['200MA'].iloc[-21]

    # Condition 1
    if not (latest['Close'] > latest['50MA'] > latest['150MA'] > latest['200MA']):
        print(f"❌ {ticker}: Price/MA hierarchy not satisfied (Close: {latest['Close']}, 50MA: {latest['50MA']}, 150MA: {latest['150MA']}, 200MA: {latest['200MA']})")
        return False

    # Condition 2
    if not (latest['Close'] >= 1.3 * latest['52W_Low']):
        print(f"❌ {ticker}: Close < 1.3 * 52W_Low (Close: {latest['Close']}, 52W_Low: {latest['52W_Low']})")
        return False

    # Condition 3
    if not (latest['Close'] >= 0.75 * latest['52W_High']):
        print(f"❌ {ticker}: Close < 0.75 * 52W_High (Close: {latest['Close']}, 52W_High: {latest['52W_High']})")
        return False

    # Condition 4
    if not (ma_200_now > ma_200_past):
        print(f"❌ {ticker}: 200MA not trending up (Now: {ma_200_now}, 21 days ago: {ma_200_past})")
        return False

    # Condition 5 (Optional RSI)
    if not (latest['RSI'] > 70):
        print(f"❌ {ticker}: RSI ≤ 70 (RSI: {latest['RSI']})")
        return False

    return True

# Loop through tickers and apply screener
for ticker in stocks:
    try:
        df = pd.read_excel(file_path, sheet_name=ticker)
        df.dropna(subset=['50MA', '150MA', '200MA', '52W_Low', '52W_High', 'RSI'], inplace=True)

        if not df.empty and meets_minervini_criteria(df, ticker):
            screened_stocks.append(ticker)
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")

# Display results
print("\n✅ Stocks meeting Minervini's trend template:")
for stock in screened_stocks:
    print(f"✔ {stock}")

if not screened_stocks:
    print("⚠ No stocks met the criteria.")
