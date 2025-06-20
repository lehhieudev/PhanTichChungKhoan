import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import ta
from datetime import datetime, timedelta
from vnstock import Vnstock
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

def get_vietnam_stock_data(symbol: str, days_back: int = 180):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    try:
        stock_instance = Vnstock().stock(symbol=symbol)
        df = stock_instance.quote.history(start=start_date_str, end=end_date_str, interval='1D')

        if df is not None and not df.empty:
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df = df.set_index('time')
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            return df
        else:
            return None
    except:
        return None

def add_technical_indicators(df):
    df['MA5'] = ta.trend.sma_indicator(df['close'], window=5)
    df['MA10'] = ta.trend.sma_indicator(df['close'], window=10)
    df['MA50'] = ta.trend.sma_indicator(df['close'], window=50)
    bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BB_Middle'] = bb.bollinger_mavg()
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Lower'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    return df

def create_chart(df, symbol):
    addplots = [
        mpf.make_addplot(df['MA5'], color='blue'),
        mpf.make_addplot(df['MA10'], color='orange'),
        mpf.make_addplot(df['MA50'], color='magenta'),
        mpf.make_addplot(df['BB_Upper'], color='grey', linestyle='dashed'),
        mpf.make_addplot(df['BB_Middle'], color='black', linestyle='dotted'),
        mpf.make_addplot(df['BB_Lower'], color='grey', linestyle='dashed'),
        mpf.make_addplot(df['RSI'], panel=1, color='purple', ylabel='RSI')
    ]

    fig, _ = mpf.plot(
        df,
        type='candle',
        style='charles',
        title=f"Biểu đồ kỹ thuật: {symbol}",
        volume=True,
        addplot=addplots,
        figratio=(16, 9),
        figscale=1.2,
        panel_ratios=(6, 2),
        returnfig=True
    )
    return fig

def create_gui(symbols):
    root = tk.Tk()
    root.title("Biểu đồ cổ phiếu theo tab")
    notebook = ttk.Notebook(root)

    for symbol in symbols:
        df = get_vietnam_stock_data(symbol)
        if df is None:
            continue
        df = add_technical_indicators(df)
        fig = create_chart(df, symbol)

        frame = ttk.Frame(notebook)
        notebook.add(frame, text=symbol)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    notebook.pack(fill=tk.BOTH, expand=True)
    root.mainloop()

# --- CHẠY CHÍNH ---
if __name__ == "__main__":
    symbols = ['BID', 'HPG', 'CII', 'SSI', 'PDR']
    create_gui(symbols)
