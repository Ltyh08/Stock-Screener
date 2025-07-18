# Mark Minervini Trend

def meets_criteria(df, ticker=None):
    if len(df) < 220:
        return False  # Not enough data to evaluate 200MA slope

    latest = df.iloc[-1]
    ma_200_now = df['200MA'].iloc[-1]
    ma_200_past = df['200MA'].iloc[-21]  # ~1 month ago

    conditions = [
        latest['Close'] > latest['50MA'] > latest['150MA'] > latest['200MA'],
        latest['Close'] >= 1.3 * latest['52W_Low'],
        latest['Close'] >= 0.75 * latest['52W_High'],
        ma_200_now > ma_200_past,
        latest['RSI'] > 50
    ]

    return all(conditions)

 # python BT.py --strategy MMSS --starting_cash 10000 --risk_pct 10 --stop_loss 20 --take_profit 30

