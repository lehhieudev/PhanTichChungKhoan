
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import ta
from datetime import datetime, timedelta
from vnstock import Vnstock
import requests
from io import BytesIO
import os

plt.rcParams['font.family'] = 'DejaVu Sans'

# Cấu hình Telegram
TELEGRAM_BOT_TOKEN = "7231869368:AAEOHsusD-BVugJ-p3npA_UYCnqQZ2ENWE8"
TELEGRAM_CHAT_ID = "7481101547"

def send_photo_to_telegram(photo_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("chart.png", photo_bytes)}
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
    resp = requests.post(url, files=files, data=data)
    if resp.status_code != 200:
        print(f"[ERROR] Gửi ảnh Telegram lỗi: {resp.text}")

def get_vietnam_stock_data(symbol: str, days_back: int = 180):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"\nLấy dữ liệu cho mã {symbol} từ {start_date_str} đến {end_date_str}...")

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
            print(f"Không có dữ liệu cho mã {symbol}.")
            return None
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu {symbol}: {e}")
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


    addplots = [
        mpf.make_addplot(df['MA5'], color='blue'),
        mpf.make_addplot(df['MA10'], color='orange'),
        mpf.make_addplot(df['MA50'], color='magenta'),
        mpf.make_addplot(df['BB_Upper'], color='grey', linestyle='dashed'),
        mpf.make_addplot(df['BB_Middle'], color='black', linestyle='dotted'),
        mpf.make_addplot(df['BB_Lower'], color='grey', linestyle='dashed'),
    ]
    
    # Tạo buffer ảnh
    buf = BytesIO()
    mpf.plot(
        df,
        type='candle',
        style='charles',
        title=f"Biểu đồ nến + chỉ báo kỹ thuật: {symbol}",
        volume=True,
        addplot=addplots,
        figratio=(16,9),
        figscale=1.2,
        mav=(5, 10, 50),
        savefig=buf
    )
    buf.seek(0)
    return buf
def plot_candlestick_with_indicators(df, symbol):
    import matplotlib.pyplot as plt

    # Các đường kỹ thuật cần vẽ
    addplots = [
        mpf.make_addplot(df['MA5'], color='blue', width=1.0, linestyle='-'),
        mpf.make_addplot(df['MA10'], color='orange', width=1.0, linestyle='-'),
        mpf.make_addplot(df['MA50'], color='magenta', width=1.0, linestyle='-'),
        mpf.make_addplot(df['BB_Upper'], color='grey', linestyle='dashed'),
        mpf.make_addplot(df['BB_Middle'], color='black', linestyle='dotted'),
        mpf.make_addplot(df['BB_Lower'], color='grey', linestyle='dashed'),
        # Nếu bạn muốn thêm RSI ở panel phụ:
        # mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI')
    ]

    fig, axlist = mpf.plot(
        df,
        type='candle',
        style='charles',
        title=f"Biểu đồ nến + chỉ báo kỹ thuật: {symbol}",
        volume=True,
        addplot=addplots,
        figratio=(16, 9),
        figscale=1.2,
        mav=(5, 10, 50),
        returnfig=True
    )

    # Lấy trục chính (candlestick)
    ax = axlist[0]

    # Tạo chú thích (legend) thủ công vì mpf.plot không tự thêm legend cho addplot
    # Tên chú thích và màu tương ứng
    legend_labels = [
        ("MA5 (Trung bình 5 ngày)", 'blue'),
        ("MA10 (Trung bình 10 ngày)", 'orange'),
        ("MA50 (Trung bình 50 ngày)", 'magenta'),
        ("BB Upper (Dải Bollinger trên)", 'grey'),
        ("BB Middle (Trung bình Bollinger)", 'black'),
        ("BB Lower (Dải Bollinger dưới)", 'grey')
    ]

    # Tạo các Line2D giả để vẽ legend
    import matplotlib.lines as mlines
    legend_lines = [
        mlines.Line2D([], [], color=color, linestyle='-' if 'MA' in label else ('dashed' if 'Upper' in label or 'Lower' in label else 'dotted'), linewidth=2)
        for label, color in legend_labels
    ]

    ax.legend(legend_lines, [label for label, _ in legend_labels], loc='upper left')

    # Hiển thị biểu đồ (nếu cần)
    # plt.show()

    # Trả về đối tượng figure để lưu hoặc xử lý tiếp
    return fig

if __name__ == "__main__":
    stock_symbols = ['FPT', 'BID', 'SSI']  # Thay list này tùy ý
    for symbol in stock_symbols:
        df = get_vietnam_stock_data(symbol)
        if df is not None:
            df = add_technical_indicators(df)
            img_buf = plot_candlestick_with_indicators(df, symbol)
            if img_buf:
                caption = f"Biểu đồ kỹ thuật {symbol} cập nhật lúc {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                print(f"Gửi biểu đồ {symbol} lên Telegram...")
                send_photo_to_telegram(img_buf, caption)
