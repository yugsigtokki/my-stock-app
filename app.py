import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. 토스증권 스타일 페이지 설정 및 디자인 (토스 RED: #F04452 / BLUE: #3182F6)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="토스증권 스타일 실시간 단타 대시보드",
    page_icon="📈",
    layout="wide"
)

# 토스증권 앱 느낌의 커스텀 CSS (모바일 최적화)
st.markdown("""
    <style>
    /* 토스 어두운 배경 */
    .stApp { background-color: #101012; color: #FFFFFF; }
    
    /* 카드 디자인 */
    .toss-card {
        background-color: #1C1C1E;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #2C2C2E;
        margin-bottom: 12px;
    }
    
    /* 텍스트 & 색상 */
    .toss-sub { font-size: 13px; color: #8E8E93; font-weight: 500; }
    .toss-up { color: #F04452; font-weight: 700; }   /* 한국/토스 기준 상승: 빨강 */
    .toss-down { color: #3182F6; font-weight: 700; } /* 한국/토스 기준 하락: 파랑 */
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] { background-color: #18181A; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 - 설정 & 실시간 초단위 설정
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ 단타 대시보드")

# 5초 간격 자동 새로고침 (HTML 이용)
auto_refresh = st.sidebar.checkbox("🔄 5초 자동 시세 갱신", value=True)
if auto_refresh:
    st.markdown("<meta http-equiv='refresh' content='5'>", unsafe_allow_html=True)

stock_input = st.sidebar.text_input("종목 입력 (티커)", value="TSLL").strip().upper()

timeframe = st.sidebar.selectbox(
    "차트 주기",
    options=["1분봉 (1일)", "5분봉 (1일)", "15분봉 (5일)", "1일봉 (6개월)"],
    index=0
)

tf_map = {
    "1분봉 (1일)": ("1m", "1d"),
    "5분봉 (1일)": ("5m", "1d"),
    "15분봉 (5일)": ("15m", "5d"),
    "1일봉 (6개월)": ("1d", "6m")
}
interval, period = tf_map[timeframe]

ticker = f"{stock_input}.KS" if stock_input.isdigit() and len(stock_input) == 6 else stock_input

# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 복합 단타 지표 계산 (5/20/60/120 이평선, RSI, MACD, 볼린저밴드)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=2) # 2초 캐시로 시세 빠르게 수집
def get_stock_data(symbol, p, i):
    return yf.download(symbol, period=p, interval=i)

try:
    df = get_stock_data(ticker, period, interval)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if not df.empty and len(df) > 20:
        # 1) 이평선 (5, 20, 60, 120일선)
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        df['MA120'] = df['Close'].rolling(120).mean()

        # 2) RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 3) 볼린저 밴드
        df['STD20'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD20'] * 2)
        df['Lower'] = df['MA20'] - (df['STD20'] * 2)

        # 4) MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        curr_price = float(latest['Close'])
        prev_price = float(prev['Close'])
        price_diff = curr_price - prev_price
        pct_change = (price_diff / prev_price) * 100

        # -----------------------------------------------------------------------------
        # 4. 토스증권 상단 메인 헤더
        # -----------------------------------------------------------------------------
        color_cls = "toss-up" if price_diff >= 0 else "toss-down"
        sign = "+" if price_diff >= 0 else ""

        st.markdown(f"""
            <div style="padding: 10px 0px;">
                <div style="font-size: 22px; font-weight: 700; color: #FFFFFF;">{stock_input}</div>
                <div style="margin-top: 4px;">
                    <span style="font-size: 38px; font-weight: 800; color: #FFFFFF;">${curr_price:,.2f}</span>
                    <span style="font-size: 18px; margin-left: 8px;" class="{color_cls}">{sign}${price_diff:,.2f} ({sign}{pct_change:.2f}%)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # 5. 🔥 단타 다중 알고리즘 AI 매매 진단 (복합 지표)
        # -----------------------------------------------------------------------------
        buy_signals = 0
        sell_signals = 0

        # 신호 1: 골든/데드크로스
        if float(latest['MA5']) > float(latest['MA20']): buy_signals += 1
        else: sell_signals += 1

        # 신호 2: RSI
        rsi_val = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
        if rsi_val <= 30: buy_signals += 1.5
        elif rsi_val >= 70: sell_signals += 1.5

        # 신호 3: 볼린저밴드
        if curr_price <= float(latest['Lower']): buy_signals += 1
        elif curr_price >= float(latest['Upper']): sell_signals += 1

        # 신호 4: MACD
        if float(latest['MACD']) > float(latest['Signal']): buy_signals += 1
        else: sell_signals += 1

        # 종합 진단
        if buy_signals >= 3:
            signal_text = "🔴 **강력 매수 신호** (단기 저점 / 반등 가능성 높음)"
            bg_color = "rgba(240, 68, 82, 0.15)"
            border_color = "#F04452"
        elif sell_signals >= 3:
            signal_text = "🔵 **강력 매도 / 관망 신호** (단기 고점 / 하락 추세)"
            bg_color = "rgba(49, 130, 246, 0.15)"
            border_color = "#3182F6"
        else:
            signal_text = "⚪ **중립 / 횡보 구간** (명확한 방향성 없음)"
            bg_color = "#1C1C1E"
            border_color = "#2C2C2E"

        st.markdown(f"""
            <div class="toss-card" style="background-color: {bg_color}; border-color: {border_color};">
                <div class="toss-sub">⚡ AI 단타 복합 분석 결과 (MA + RSI + MACD + Bollinger)</div>
                <div style="font-size: 17px; font-weight: 700; margin-top: 4px;">{signal_text}</div>
            </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # 6. 토스증권 느낌의 고화질 캔들 차트 (이평선 5/20/60/120 포함)
        # -----------------------------------------------------------------------------
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_width=[0.2, 0.8]
        )

        # 캔들 차트 (토스 컬러: 상승 빨강 #F04452, 하락 파랑 #3182F6)
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='주가',
            increasing_line_color='#F04452', decreasing_line_color='#3182F6',
            increasing_fillcolor='#F04452', decreasing_fillcolor='#3182F6'
        ), row=1, col=1)

        # 토스 스타일 이평선 4개 (5일-빨강, 20일-초록, 60일-주황, 120일-보라)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5선', line=dict(color='#FF5252', width=1.2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20선', line=dict(color='#00E676', width=1.2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='60선', line=dict(color='#FFB300', width=1.2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA120'], name='120선', line=dict(color='#E040FB', width=1.2)), row=1, col=1)

        # 거래량 차트
        colors = ['#F04452' if c >= o else '#3182F6' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량', marker_color=colors), row=2, col=1)

        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#101012', plot_bgcolor='#101012',
            height=520, margin=dict(l=0, r=0, t=10, b=0),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("데이터를 불러올 수 없거나 데이터 수가 부족합니다.")

except Exception as e:
    st.error(f"오류 발생: {e}")
