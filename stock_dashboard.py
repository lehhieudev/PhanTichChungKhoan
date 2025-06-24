import streamlit as st
import pandas as pd
import mplfinance as mpf
import ta
from datetime import datetime, timedelta
from vnstock import Vnstock
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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
    fig = go.Figure()

    # Vẽ biểu đồ nến
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlestick',
        hovertext=[
            f"Ngày: {x.strftime('%d-%m-%Y')}<br>Open: {o}<br>High: {h}<br>Low: {l}<br>Close: {c}"
            for x, o, h, l, c in zip(df.index, df['open'], df['high'], df['low'], df['close'])
        ],
        hoverinfo='text'  # Sử dụng text được định nghĩa ở hovertext
    ))
    # Vẽ các đường MA
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], mode='lines', name='MA5', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA10'], mode='lines', name='MA10', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50', line=dict(color='magenta')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], mode='lines', name='BB Upper', line=dict(color='grey', dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'], mode='lines', name='BB Middle', line=dict(color='black', dash='dot')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], mode='lines', name='BB Lower', line=dict(color='grey', dash='dash')))

    # Cấu hình giao diện
    fig.update_layout(
        title=f'Biểu đồ kỹ thuật: {symbol}',
        xaxis_title='Ngày',
        yaxis_title='Giá',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        autosize=True,
        height=700
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
            st.plotly_chart(fig, use_container_width=True)

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
