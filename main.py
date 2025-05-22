import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from vnstock import Vnstock


def get_vietnam_stock_data(symbol: str, days_back: int = 30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"\n\u0110ang l\u1ea5y d\u1eef li\u1ec7u cho m\u00e3 {symbol} t\u1eeb {start_date_str} \u0111\u1ebfn {end_date_str}...")

    try:
        stock_instance = Vnstock().stock(symbol=symbol)
        df = stock_instance.quote.history(start=start_date_str, end=end_date_str, interval='1D')

        if df is not None and not df.empty:
            print(f"\u0110\u00e3 l\u1ea5y th\u00e0nh c\u00f4ng {len(df)} d\u00f2ng d\u1eef li\u1ec7u cho {symbol}.")
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df = df.set_index('time')
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            return df
        else:
            print(f"Kh\u00f4ng t\u00ecm th\u1ea5y d\u1eef li\u1ec7u ho\u1eb7c d\u1eef li\u1ec7u r\u1ed7ng cho m\u00e3 {symbol}.")
            return None
    except Exception as e:
        print(f"L\u1ed7i khi l\u1ea5y d\u1eef li\u1ec7u cho m\u00e3 {symbol}: {e}")
        return None


def analyze_and_plot(df: pd.DataFrame, symbol: str):
    if df is None or df.empty:
        print(f"Kh\u00f4ng c\u00f3 d\u1eef li\u1ec7u \u0111\u1ec3 v\u1ebd cho {symbol}.")
        return

    df['signal'] = 'HOLD'
    df['close_shift'] = df['close'].shift(1)

    df.loc[df['close'] > df['close_shift'] * 1.02, 'signal'] = 'BUY'
    df.loc[df['close'] < df['close_shift'] * 0.98, 'signal'] = 'SELL'

    buy_signals = df[df['signal'] == 'BUY']
    sell_signals = df[df['signal'] == 'SELL']

    plt.figure(figsize=(14, 6))
    plt.plot(df.index, df['close'], label='Close Price', color='blue')
    plt.scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', label='Buy Signal', s=100)
    plt.scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', label='Sell Signal', s=100)

    plt.title(f"T\u00edn hi\u1ec7u MUA/B\u00c1N cho m\u00e3 {symbol}")
    plt.xlabel("Th\u1eddi gian")
    plt.ylabel("Gi\u00e1 \u0111\u00f3ng c\u1ee1a (VND)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    stock_symbols = ['BID', 'CII', 'SSI', 'PDR', 'FPT', 'HPG']

    for symbol in stock_symbols:
        df = get_vietnam_stock_data(symbol, days_back=180)
        analyze_and_plot(df, symbol)
