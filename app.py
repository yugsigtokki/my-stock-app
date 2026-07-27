import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. 페이지 레이아웃 및 디자인 설정 (다크 테마 스타일)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="고급 주식 시세 & 차트 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 다크 모드 감성의 고급스러운 커스텀 CSS 적용
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2B2F3A;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 - 종목 검색 및 설정 UI
# -----------------------------------------------------------------------------
st.sidebar.title("💎 Stock Dashboard")
st.sidebar.subheader("종목 검색 & 설정")

stock_input = st.sidebar.text_input(
    "종목 코드 / 티커 입력", 
    value="NVDA", 
    help="국내주식(예: 005930), 미국주식(예: NVDA, AAPL, TSLA)"
).strip().upper()

period = st.sidebar.selectbox(
    "조회 기간 선택",
    options=["1m", "3m", "6m", "1y", "2y"],
    index=2
)

# 입력받은 티커 처리 (한국 종목 자동 변환)
if stock_input.isdigit() and len(stock_input) == 6:
    ticker = f"{stock_input}.KS"
    currency = "KRW (원)"
else:
    ticker = stock_input
    currency = "USD ($)"

# -----------------------------------------------------------------------------
# 3. 데이터 수집 및 상단 요약 카드(Metrics) 표시
# -----------------------------------------------------------------------------
st.title(f"📊 {ticker} 실시간 분석 대시보드")

@st.cache_data(ttl=60)
def load_data(symbol, p):
    s = yf.Ticker(symbol)
    df = s.history(period=p)
    return s, df

try:
    stock_info, df = load_data(ticker, period)
    
    # 코스닥 처리 예외 구문
    if df.empty and stock_input.isdigit() and len(stock_input) == 6:
        ticker = f"{stock_input}.KQ"
        stock_info, df = load_data(ticker, period)

    if not df.empty:
        # 이동평균선 계산
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price_diff = latest['Close'] - prev['Close']
        pct_change = (price_diff / prev['Close']) * 100

        # 상단 핵심 데이터 카드 (3열 구성)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("현재가", f"{latest['Close']:,.2f}", f"{price_diff:+.2f} ({pct_change:+.2f}%)")
        col2.metric("당일 고가", f"{latest['High']:,.2f}")
        col3.metric("당일 저가", f"{latest['Low']:,.2f}")
        col4.metric("거래량", f"{int(latest['Volume']):,}")

        st.markdown("---")

        # -----------------------------------------------------------------------------
        # 4. 차트 레이아웃 구현 (Plotly 대시보드 스타일)
        # -----------------------------------------------------------------------------
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('캔들 차트 & 이동평균선', '거래량'),
            row_width=[0.25, 0.75]
        )

        # (1) 캔들 차트
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name='주가',
            increasing_line_color='#26a69a', # 프리미엄 녹색
            decreasing_line_color='#ef5350'  # 프리미엄 빨간색
        ), row=1, col=1)

        # (2) 이동평균선
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5일선', line=dict(color='#FFB74D', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20일선', line=dict(color='#AB47BC', width=1.5)), row=1, col=1)

        # (3) 거래량
        colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'],
            name='거래량', marker_color=colors
        ), row=2, col=1)

        # 다크 모드 스타일 레이아웃 최적화
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#1E222D',
            plot_bgcolor='#1E222D',
            height=650,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("종목 데이터를 불러올 수 없습니다. 종목 코드나 티커를 확인해 주세요.")

except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
