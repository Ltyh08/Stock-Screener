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

            i = 220
            while i < len(df) - holding_days:
                if strategy_func(df.iloc[:i + 1], ticker):
                    entry_date = df.loc[i, 'Date']
                    entry_price = df.loc[i, 'Close']
                    exit_index = i + holding_days

                    exit_date = df.loc[exit_index, 'Date']
                    exit_price = df.loc[exit_index, 'Close']
                    ret = (exit_price - entry_price) / entry_price * 100

                    

                    trade_log.append({
                        'Ticker': ticker,
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Exit Date': exit_date,
                        'Exit Price': exit_price,
                        'Return (%)': round(ret, 2)
                    })

                    i = exit_index
                else:
                    i += 1
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
        avg_return = results_df['Return (%)'].mean()
        win_rate = (results_df['Return (%)'] > 0).mean() * 100
        print(f"Average Return: {avg_return:.2f}%")
        print(f"Win Rate: {win_rate:.2f}%")

        # 🔄 ADDED: Average return by ticker
        avg_by_ticker = results_df.groupby('Ticker')['Return (%)'].mean().reset_index()
        avg_by_ticker.rename(columns={'Return (%)': 'Average Return (%)'}, inplace=True)

        print("\n📈 Average Return by Ticker:")
        for _, row in avg_by_ticker.iterrows():
            print(f"{row['Ticker']} Average Return: {row['Average Return (%)']:.2f}%")

        # 🔄 MODIFIED: Export results and summary
        output_dir = "backtest_results"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{args.strategy}.xlsx")

        # Create summary table
        summary_metrics = pd.DataFrame({
            'Metric': ['Total Trades', 'Average Return (%)', 'Win Rate (%)'],
            'Value': [len(results_df), round(avg_return, 2), round(win_rate, 2)]
        })

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Sheet 1: Individual trades
            results_df.to_excel(writer, sheet_name="Trades", index=False)

            # Sheet 2: Ticker performance and overall metrics
            avg_by_ticker.to_excel(writer, sheet_name="Summary", index=False, startrow=0)

            # Append summary metrics just below average return table
            summary_metrics.to_excel(writer, sheet_name="Summary", index=False, startrow=len(avg_by_ticker) + 3)

        print(f"✅ Results successfully saved to: {output_path}")
