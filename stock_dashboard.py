import streamlit as st
import pandas as pd
import mplfinance as mpf
import ta
from datetime import datetime, timedelta
from vnstock import Vnstock
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

def get_vietnam_stock_data(symbol: str, days_back: int = 180):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    try:
        stock_instance = Vnstock().stock(symbol=symbol)
        df = stock_instance.quote.history(start=start_date_str, end=end_date_str, interval='1D')
        if df is not None and not df.empty:
            df['time'] = pd.to_datetime(df.get('time', df.get('date')))
            df = df.set_index('time')
            return df
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {e}")
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

def plot_chart(df, symbol):
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

def get_company_profile(symbol):
    try:
        company = Vnstock().stock(symbol=symbol).company
        profile = company.overview()
        leaders = company.officers(filter_by='working')
        shareholders = company.shareholders()
        return profile, leaders, shareholders
    except Exception as e:
        st.warning(f"Lỗi khi lấy thông tin công ty {symbol}: {e}")
        return None, None, None

# --- Giao diện Streamlit ---
st.title("📈 Biểu đồ kỹ thuật & Thông tin doanh nghiệp")

symbol_input = st.text_input("Nhập mã cổ phiếu (ngăn cách bởi dấu phẩy):", "BID, HPG, SSI")
symbols = [sym.strip().upper() for sym in symbol_input.split(",") if sym.strip()]
days_back = st.slider("Số ngày gần đây:", min_value=30, max_value=365, value=180)

if symbols:
    for symbol in symbols:
        st.subheader(f"🔍 Mã: {symbol}")
        df = get_vietnam_stock_data(symbol, days_back)
        if df is not None:
            df = add_technical_indicators(df)
            fig = plot_chart(df, symbol)
            st.pyplot(fig)

            # --- Thông tin doanh nghiệp ---
            st.markdown("### 🏢 Thông tin doanh nghiệp")
            profile, leaders, shareholders = get_company_profile(symbol)

            if profile is not None and not profile.empty:
                st.dataframe(profile.T)  # transpose để dễ đọc

            st.markdown("### 👨‍💼 Ban lãnh đạo")
            if leaders is not None and not leaders.empty:
                st.dataframe(leaders)

            st.markdown("### 🏦 Cổ đông lớn")
            if shareholders is not None and not shareholders.empty:
                st.dataframe(shareholders)
        else:
            st.warning(f"Không có dữ liệu cho mã {symbol}.")
