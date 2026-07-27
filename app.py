import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. 페이지 레이아웃 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="실시간 주식 차트 & 매매 신호 대시보드",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #1E222D; padding: 12px; border-radius: 8px; border: 1px solid #2B2F3A; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 - 설정 메뉴 (새로고침 & 분봉/일봉 선택)
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ 실시간 주식 대시보드")

# 시세 즉시 갱신 버튼
if st.sidebar.button("🔄 실시간 시세 새로고침", use_container_width=True):
    st.cache_data.clear()

stock_input = st.sidebar.text_input("종목 티커 입력", value="TSLL").strip().upper()

# 분봉 / 일봉 / 주봉 선택 기능
timeframe = st.sidebar.selectbox(
    "차트 주기 선택",
    options=["1분봉 (1일)", "5분봉 (1일)", "15분봉 (5일)", "1일봉 (6개월)", "1주봉 (2년)"],
    index=1
)

tf_map = {
    "1분봉 (1일)": ("1m", "1d"),
    "5분봉 (1일)": ("5m", "1d"),
    "15분봉 (5일)": ("15m", "5d"),
    "1일봉 (6개월)": ("1d", "6m"),
    "1주봉 (2년)": ("1wk", "2y")
}
interval, period = tf_map[timeframe]

# 한국 주식 처리
if stock_input.isdigit() and len(stock_input) == 6:
    ticker = f"{stock_input}.KS"
else:
    ticker = stock_input

# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 보조지표 계산
# -----------------------------------------------------------------------------
st.title(f"📊 [{ticker}] {timeframe} 차트 & 분석")

@st.cache_data(ttl=5) # 5초 캐시로 빠르게 반영
def get_data(symbol, p, i):
    df_data = yf.download(symbol, period=p, interval=i)
    return df_data

try:
    df = get_data(ticker, period, interval)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if not df.empty:
        # 이평선 계산
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()

        # RSI 계산 (매매 타이밍 보조지표)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # -----------------------------------------------------------------------------
        # 4. 🔥 매수 / 매도 타이밍 분석
        # -----------------------------------------------------------------------------
        ma5_curr, ma20_curr = float(latest['MA5']), float(latest['MA20'])
        ma5_prev, ma20_prev = float(prev['MA5']), float(prev['MA20'])
        rsi_curr = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0

        st.subheader("💡 AI 매매 타이밍 신호")
        col_signal1, col_signal2 = st.columns(2)

        # 골든크로스 / 데드크로스 판단
        if ma5_prev <= ma20_prev and ma5_curr > ma20_curr:
            col_signal1.success("🔴 **[골든크로스]** 단기 상승 추세 전환! **(매수 추천)**")
        elif ma5_prev >= ma20_prev and ma5_curr < ma20_curr:
            col_signal1.error("🔵 **[데드크로스]** 단기 하락 추세 전환! **(매도/관망 추천)**")
        else:
            col_signal1.info("⚪ **[추세 유지]** 5일선과 20일선이 평행 이동 중입니다.")

        # RSI 과매수 / 과매도 판단
        if rsi_curr >= 70:
            col_signal2.warning(f"⚠️ **[RSI {rsi_curr:.1f}]** 과매수 구간! (매도 고려)")
        elif rsi_curr <= 30:
            col_signal2.success(f"🎯 **[RSI {rsi_curr:.1f}]** 과매도 구간! (저점 매수 고려)")
        else:
            col_signal2.metric("RSI 수치 (30이하: 매수 / 70이상: 매도)", f"{rsi_curr:.1f}")

        st.markdown("---")

        # -----------------------------------------------------------------------------
        # 5. 차트 그리기 (캔들 + 거래량 + RSI)
        # -----------------------------------------------------------------------------
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('캔들 차트 (5일선/20일선)', '거래량', 'RSI 지표'),
            row_width=[0.2, 0.2, 0.6]
        )

        # 캔들차트
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='주가', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5일선', line=dict(color='#FFB74D', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20일선', line=dict(color='#AB47BC', width=1.5)), row=1, col=1)

        # 거래량
        colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량', marker_color=colors), row=2, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#29b6f6', width=1.5)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#1E222D', plot_bgcolor='#1E222D',
            height=750, margin=dict(l=10, r=10, t=30, b=10),
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("데이터를 불러올 수 없습니다.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
