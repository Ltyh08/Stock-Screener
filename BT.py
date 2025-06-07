import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import importlib

# =====================
# 🔧 Load Excel Path
# =====================
load_dotenv()
file_path = os.getenv("EXCEL_OUTPUT_PATH")
if not file_path or not os.path.exists(file_path):
    raise FileNotFoundError("Excel file not found or EXCEL_OUTPUT_PATH not set.")

# =====================
# 🧠 Load Strategy
# =====================
def load_strategy(strategy_name):
    try:
        strategy_module = importlib.import_module(strategy_name)
        return strategy_module.meets_criteria
    except Exception as e:
        raise ImportError(f"⚠ Failed to import strategy '{strategy_name}': {e}")

# =====================
# ♻️ Backtest Function
# =====================
def backtest_strategy(strategy_func, holding_days=30):
    xls = pd.ExcelFile(file_path)
    tickers = xls.sheet_names
    trade_log = []

    for ticker in tickers:
        try:
            df = pd.read_excel(file_path, sheet_name=ticker)
            df.columns = df.columns.str.strip()
            df.dropna(subset=['Close'], inplace=True)

            i = 220  # start after enough data for moving averages
            while i < len(df) - holding_days:
                if strategy_func(df.iloc[:i + 1], ticker):
                    entry_date = df.loc[i, 'Date']
                    entry_price = df.loc[i, 'Close']
                    exit_index = i + holding_days

                    exit_date = df.loc[exit_index, 'Date']
                    exit_price = df.loc[exit_index, 'Close']
                    ret = (exit_price - entry_price) / entry_price * 100

                    print(f"✅ Signal found for {ticker} on {entry_date} @ {entry_price:.2f}")

                    trade_log.append({
                        'Ticker': ticker,
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': exit_date,
                        'Exit Price': exit_price,
                        'Return (%)': round(ret, 2)
                    })

                    i = exit_index  # Skip ahead after holding period
                else:
                    i += 1  # No signal, move forward
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")

    return pd.DataFrame(trade_log)


# =====================
# ▶️ Run Backtest
# =====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backtest stock strategy")
    parser.add_argument("--strategy", type=str, required=True, help="Name of the strategy module (e.g. minervini)")
    parser.add_argument("--holding_days", type=int, default=30, help="Holding period after entry")
    args = parser.parse_args()

    print(f"\n📌 Using strategy: {args.strategy}")
    strategy_func = load_strategy(args.strategy)

    results_df = backtest_strategy(strategy_func, holding_days=args.holding_days)

    if results_df.empty:
        print("⚠ No trades met the strategy criteria.")
    else:
        print("\n✅ Backtest Results:")
        print(results_df)

        print("\n📊 Summary:")
        print(f"Total Trades: {len(results_df)}")
        print(f"Average Return: {results_df['Return (%)'].mean():.2f}%")
        print(f"Win Rate: {(results_df['Return (%)'] > 0).mean() * 100:.2f}%")

        # Save results using strategy name
        output_dir = "backtest_results"
        os.makedirs(output_dir, exist_ok=True)

        # Construct file path based on strategy name
        output_path = os.path.join(output_dir, f"{args.strategy}.xlsx")

        # Export to Excel
        results_df.to_excel(output_path, index=False, engine="openpyxl")
        print(f"✅ Results successfully saved to: {output_path}")
