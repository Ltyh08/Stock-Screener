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
def backtest_strategy(strategy_func, starting_cash, risk_pct, stop_loss_pct, take_profit_pct):
    xls = pd.ExcelFile(file_path)
    tickers = xls.sheet_names
    trade_log = []
    cash = starting_cash

    for ticker in tickers:
        try:
            df = pd.read_excel(file_path, sheet_name=ticker)
            df.columns = df.columns.str.strip()
            df.dropna(subset=['Close'], inplace=True)
            df.reset_index(drop=True, inplace=True)

            i = 220  # Lookback window
            while i < len(df) - 1:
                if strategy_func(df.iloc[:i + 1], ticker):
                    entry_date = df.loc[i, 'Date']
                    entry_price = df.loc[i, 'Close']

                    max_risk_cash = (cash * risk_pct) / 100
                    num_shares = max_risk_cash // entry_price

                    if num_shares == 0:
                        i += 1
                        continue

                    invested_amount = num_shares * entry_price
                    stop_price = entry_price * (1 - stop_loss_pct / 100)
                    target_price = entry_price * (1 + take_profit_pct / 100)

                    exit_price = None
                    exit_date = None

                    for j in range(i + 1, len(df)):
                        price = df.loc[j, 'Close']
                        if price <= stop_price:
                            exit_price = price
                            exit_date = df.loc[j, 'Date']
                            break
                        elif price >= target_price:
                            exit_price = price
                            exit_date = df.loc[j, 'Date']
                            break

                    if exit_price is None:
                        i += 1
                        continue

                    ret_pct = (exit_price - entry_price) / entry_price * 100
                    cash += num_shares * (exit_price - entry_price)

                    trade_log.append({
                        'Ticker': ticker,
                        'Entry Date': entry_date,
                        'Entry Price': entry_price,
                        'Shares': int(num_shares),
                        'Exit Date': exit_date,
                        'Exit Price': exit_price,
                        'Return (%)': round(ret_pct, 2),
                        'Profit/Loss': round(num_shares * (exit_price - entry_price), 2),
                        'Cash After Trade': round(cash, 2)
                    })

                    i = j  # skip to after exit
                else:
                    i += 1
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")

    return pd.DataFrame(trade_log), cash

# =====================
# ▶️ Run Backtest
# =====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backtest stock strategy with risk management")
    parser.add_argument("--strategy", type=str, required=True, help="Name of the strategy module (e.g. minervini)")
    parser.add_argument("--starting_cash", type=float, default=10000, help="Initial capital")
    parser.add_argument("--risk_pct", type=float, default=10, help="Capital % to allocate per trade")
    parser.add_argument("--stop_loss", type=float, default=5, help="Stop loss %")
    parser.add_argument("--take_profit", type=float, default=10, help="Take profit %")
    args = parser.parse_args()

    print(f"\n📌 Using strategy: {args.strategy}")
    strategy_func = load_strategy(args.strategy)

    results_df, final_cash = backtest_strategy(
        strategy_func,
        starting_cash=args.starting_cash,
        risk_pct=args.risk_pct,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit
    )

    if results_df.empty:
        print("⚠ No trades met the strategy criteria.")
    else:
        print("\n✅ Backtest Results:")
        print(results_df)

        print("\n📊 Summary:")
        total_trades = len(results_df)
        avg_return = results_df['Return (%)'].mean()
        win_rate = (results_df['Return (%)'] > 0).mean() * 100
        total_profit = results_df['Profit/Loss'].sum()

        print(f"Total Trades: {total_trades}")
        print(f"Average Return: {avg_return:.2f}%")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Final Cash: ${final_cash:,.2f}")
        print(f"Total Profit: ${total_profit:,.2f}")

        # Grouped summary by ticker
        avg_by_ticker = results_df.groupby('Ticker')['Return (%)'].mean().reset_index()
        avg_by_ticker.rename(columns={'Return (%)': 'Average Return (%)'}, inplace=True)

        print("\n📈 Average Return by Ticker:")
        for _, row in avg_by_ticker.iterrows():
            print(f"{row['Ticker']} Average Return: {row['Average Return (%)']:.2f}%")

        # Export to Excel
        output_dir = "backtest_results"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{args.strategy}.xlsx")

        summary_metrics = pd.DataFrame({
            'Metric': ['Total Trades', 'Average Return (%)', 'Win Rate (%)', 'Final Cash', 'Total Profit'],
            'Value': [total_trades, round(avg_return, 2), round(win_rate, 2), round(final_cash, 2), round(total_profit, 2)]
        })

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            results_df.to_excel(writer, sheet_name="Trades", index=False)
            avg_by_ticker.to_excel(writer, sheet_name="Summary", index=False, startrow=0)
            summary_metrics.to_excel(writer, sheet_name="Summary", index=False, startrow=len(avg_by_ticker) + 3)

        print(f"✅ Results successfully saved to: {output_path}")
