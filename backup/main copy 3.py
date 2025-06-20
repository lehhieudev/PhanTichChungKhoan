import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import ta
from datetime import datetime, timedelta
from vnstock import Vnstock
import requests
from io import BytesIO

plt.rcParams['font.family'] = 'DejaVu Sans'

# Cấu hình Telegram
TELEGRAM_BOT_TOKEN = "7231869368:AAEOHsusD-BVugJ-p3npA_UYCnqQZ2ENWE8"
TELEGRAM_CHAT_ID = "7481101547"
def send_telegram_photo_with_caption(photo_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {'photo': ('chart.png', photo_bytes)}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
    resp = requests.post(url, files=files, data=data)
    if resp.status_code != 200:
        print(f"Lỗi gửi Telegram: {resp.text}")
    else:
        print("Đã gửi báo cáo qua Telegram thành công.")

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
        print(f"Lỗi khi lấy dữ liệu: {e}")
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

def plot_candlestick_with_indicators(df, symbol):
    addplots = [
        mpf.make_addplot(df['MA5'], color='blue', panel=0, ylabel='MA5'),
        mpf.make_addplot(df['MA10'], color='orange', panel=0, ylabel='MA10'),
        mpf.make_addplot(df['MA50'], color='magenta', panel=0, ylabel='MA50'),
        mpf.make_addplot(df['BB_Upper'], color='grey', linestyle='dashed', panel=0),
        mpf.make_addplot(df['BB_Middle'], color='black', linestyle='dotted', panel=0),
        mpf.make_addplot(df['BB_Lower'], color='grey', linestyle='dashed', panel=0),
        mpf.make_addplot(df['RSI'], panel=1, color='purple', ylabel='RSI')
    ]

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
        panel_ratios=(6,2),
        savefig=buf
    )
    buf.seek(0)
    return buf

def get_financial_report_text(symbol, period='year', lang='vi'):
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')# Chỉ có nguồn dữ liệu từ VCI, TCBS, MSN được hỗ trợ.

        bs = stock.finance.balance_sheet(period=period, lang=lang, dropna=True)
        inc = stock.finance.income_statement(period=period, lang=lang, dropna=True)
        cf = stock.finance.cash_flow(period=period, dropna=True)
        ratio = stock.finance.ratio(period=period, lang=lang, dropna=True)

        def df_to_summary(df, n=3):
            if df is None or df.empty:
                return "Không có dữ liệu."
            df = df.fillna('')
            lines = []
            cols = df.columns[:n]
            for col in cols:
                lines.append(f"*{col}*")
                for idx, val in df[col].items():
                    lines.append(f"  - {idx}: {val}")
                lines.append("")
            return "\n".join(lines)

        text = f"📊 *Báo cáo tài chính {symbol}* ({period}):\n\n"
        text += "*Bảng cân đối kế toán:*\n" + df_to_summary(bs) + "\n"
        text += "*Kết quả hoạt động kinh doanh:*\n" + df_to_summary(inc) + "\n"
        text += "*Lưu chuyển tiền tệ:*\n" + df_to_summary(cf) + "\n"
        text += "*Chỉ số tài chính:*\n" + df_to_summary(ratio) + "\n"

        return text
    except Exception as e:
        return f"Lỗi khi lấy báo cáo tài chính {symbol}: {e}"

if __name__ == "__main__":
    symbols = ['FPT', 'BID', 'SSI']  # danh sách mã cần gửi

    for symbol in symbols:
        df = get_vietnam_stock_data(symbol)
        if df is None:
            continue
        df = add_technical_indicators(df)
        img_buf = plot_candlestick_with_indicators(df, symbol)

        report_text = get_financial_report_text(symbol, period='year', lang='vi')

        send_telegram_photo_with_caption(img_buf, report_text)
