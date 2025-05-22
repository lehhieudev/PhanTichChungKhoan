import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
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

def send_telegram_photo_with_caption(photo_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {'photo': ('chart.png', photo_bytes)}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
    resp = requests.post(url, files=files, data=data)
    if resp.status_code != 200:
        print(f"Lỗi gửi Telegram: {resp.text}")
    else:
        print("Đã gửi ảnh qua Telegram thành công.")

def send_telegram_document(file_path, caption=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': (os.path.basename(file_path), f)}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        if caption:
            data['caption'] = caption
            data['parse_mode'] = 'Markdown'
        response = requests.post(url, files=files, data=data)
        if response.status_code != 200:
            print(f"Lỗi gửi file Telegram: {response.text}")
        else:
            print(f"Đã gửi file {file_path} qua Telegram.")

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
        stock = Vnstock().stock(symbol=symbol, source='VCI')

        bs = stock.finance.balance_sheet(period=period, lang=lang, dropna=True)
        inc = stock.finance.income_statement(period=period, lang=lang, dropna=True)
        cf = stock.finance.cash_flow(period=period, dropna=True)
        ratio = stock.finance.ratio(period=period, lang=lang, dropna=True)

        def df_to_summary(df, n=3):
            if df is None or df.empty:
                return "Không có dữ liệu."
            df = df.fillna('')
            lines = []
            cols = df.columns[1:n+1]  # bỏ cột đầu nếu là ticker
            for col in cols:
                lines.append(f"*{col}*")
                for idx, val in df[col].items():
                    lines.append(f"  - {idx}: {val}")
                lines.append("")
            return "\n".join(lines)

        # Tóm tắt caption
        short_summary = f"📊 *{symbol}* - Tổng quan tài chính ({period}):\n"
        if not ratio.empty:
            latest_col = ratio.columns[-1]
            try:
                roe = ratio.loc['ROE', latest_col]
                eps = ratio.loc['EPS', latest_col]
                pe = ratio.loc['P/E', latest_col]
                short_summary += f"ROE: {roe} | EPS: {eps} | P/E: {pe}"
            except:
                short_summary += "Không có chỉ số ROE, EPS, P/E"

        # Nội dung lưu file
        full_text = f"📊 *BÁO CÁO TÀI CHÍNH {symbol}* ({period})\n\n"
        full_text += "*Bảng cân đối kế toán:*\n" + df_to_summary(bs) + "\n"
        full_text += "*Kết quả hoạt động kinh doanh:*\n" + df_to_summary(inc) + "\n"
        full_text += "*Lưu chuyển tiền tệ:*\n" + df_to_summary(cf) + "\n"
        full_text += "*Chỉ số tài chính:*\n" + df_to_summary(ratio) + "\n"

        with open(f"{symbol}_report.txt", "w", encoding="utf-8") as f:
            f.write(full_text)

        return short_summary
    except Exception as e:
        return f"Lỗi khi lấy báo cáo tài chính {symbol}: {e}"

# --- CHẠY CHÍNH ---
if __name__ == "__main__":
    symbols = ['BID', 'HPG', 'CII','SSI','PDR']

    for symbol in symbols:
        df = get_vietnam_stock_data(symbol)
        if df is None:
            continue
        df = add_technical_indicators(df)
        img_buf = plot_candlestick_with_indicators(df, symbol)

        # Lấy báo cáo và caption
        report_caption = get_financial_report_text(symbol, period='year', lang='vi')

        # Gửi ảnh biểu đồ
        send_telegram_photo_with_caption(img_buf, report_caption)

        # Gửi file báo cáo tài chính
        txt_file_path = f"{symbol}_report.txt"
        if os.path.exists(txt_file_path):
            send_telegram_document(txt_file_path)
