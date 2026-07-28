import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. 레이아웃 & CSS 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PRO AI 실시간 트레이딩",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #FFFFFF; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; }
    
    .card-buy { background-color: rgba(240, 68, 82, 0.15); border: 2px solid #F04452; padding: 15px; border-radius: 14px; margin-bottom: 10px; }
    .card-weak-buy { background-color: rgba(255, 126, 54, 0.15); border: 2px solid #FF7E36; padding: 15px; border-radius: 14px; margin-bottom: 10px; }
    .card-sell { background-color: rgba(49, 130, 246, 0.15); border: 2px solid #3182F6; padding: 15px; border-radius: 14px; margin-bottom: 10px; }
    .card-hold { background-color: #12161c; border: 1px solid #2a2e39; padding: 15px; border-radius: 14px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화 및 입력 패널
# -----------------------------------------------------------------------------
if "symbol" not in st.session_state:
    st.session_state["symbol"] = "TSLA"

col_input, col_time = st.columns([1.5, 3])

with col_input:
    user_symbol = st.text_input("미국 티커 입력 (예: TSLA, NVDA, AAPL, SOXL)", value=st.session_state["symbol"]).strip().upper()
    if user_symbol:
        st.session_state["symbol"] = user_symbol

with col_time:
    timeframe_mode = st.radio(
        "실시간 차트 주기", 
        ["1분봉", "5분봉", "1시간봉", "일봉"], 
        horizontal=True
    )

target_ticker = st.session_state["symbol"]
tv_symbol = f"BATS:{target_ticker}"

if "1분봉" in timeframe_mode:
    yf_interval, yf_period, tv_interval = "1m", "1d", "1"
elif "5분봉" in timeframe_mode:
    yf_interval, yf_period, tv_interval = "5m", "5d", "5"
elif "1시간봉" in timeframe_mode:
    yf_interval, yf_period, tv_interval = "60m", "1mo", "60"
else:
    yf_interval, yf_period, tv_interval = "1d", "1y", "D"

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. AI 실시간 시그널 분석 엔진 (백그라운드 계산)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def get_ai_signal(symbol, interval, period):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 20:
            return None
        
        # 지표 계산
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        latest = df.iloc[-1]
        curr_price = float(latest['Close'])
        curr_vwap = float(latest['VWAP'])
        curr_rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
        curr_macd = float(latest['MACD_Hist'])

        score = 0
        reasons = []

        if curr_price > curr_vwap: score += 2; reasons.append("VWAP 수급선 상회 (매수 우위)")
        else: score -= 2; reasons.append("VWAP 수급선 하회 (매도 우위)")

        if latest['EMA9'] > latest['EMA21']: score += 2; reasons.append("단기 이평선 정배열 (상승세)")
        else: score -= 2; reasons.append("단기 이평선 역배열 (하락세)")

        if curr_macd > 0: score += 2; reasons.append("MACD 모멘텀 강세")
        else: score -= 2; reasons.append("MACD 모멘텀 약세")

        if curr_rsi <= 35: score += 1; reasons.append(f"RSI 과매도 구간 ({curr_rsi:.1f})")
        elif curr_rsi >= 75: score -= 1; reasons.append(f"RSI 과열 구간 ({curr_rsi:.1f})")

        return {"price": curr_price, "score": score, "reasons": reasons}
    except:
        return None

analysis = get_ai_signal(target_ticker, yf_interval, yf_period)

if analysis:
    score = analysis['score']
    reasons_html = " | ".join([f"• {r}" for r in analysis['reasons']])
    
    if score >= 3:
        st.markdown(f'<div class="card-buy"><span style="color: #F04452; font-weight: 700;">🔥 AI 추천: 강력 매수 (+{score}점)</span><span style="float: right; font-weight: 800; color: #F04452;">기준가: ${analysis["price"]:,.2f}</span><div style="font-size: 12px; color: #ccc; margin-top: 5px;">{reasons_html}</div></div>', unsafe_allow_html=True)
    elif 1 <= score < 3:
        st.markdown(f'<div class="card-weak-buy"><span style="color: #FF7E36; font-weight: 700;">📈 AI 추천: 분할 접근 (+{score}점)</span><span style="float: right; font-weight: 800; color: #FF7E36;">기준가: ${analysis["price"]:,.2f}</span><div style="font-size: 12px; color: #ccc; margin-top: 5px;">{reasons_html}</div></div>', unsafe_allow_html=True)
    elif score <= -3:
        st.markdown(f'<div class="card-sell"><span style="color: #3182F6; font-weight: 700;">🚨 AI 추천: 매도 / 하락 우위 ({score}점)</span><span style="float: right; font-weight: 800; color: #3182F6;">기준가: ${analysis["price"]:,.2f}</span><div style="font-size: 12px; color: #ccc; margin-top: 5px;">{reasons_html}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="card-hold"><span style="color: #8E8E93; font-weight: 700;">⚪ AI 추천: 관망 (중립 {score}점)</span><span style="float: right; font-weight: 800;">기준가: ${analysis["price"]:,.2f}</span><div style="font-size: 12px; color: #aaa; margin-top: 5px;">{reasons_html}</div></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 트레이딩뷰 실시간 차트 위젯 (툴바 제거 완료)
# -----------------------------------------------------------------------------
tradingview_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body, html {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background-color: #0b0e11;
      overflow: hidden;
    }}
  </style>
</head>
<body>
  <div class="tradingview-widget-container" style="height:100%;width:100%;">
    <div id="tradingview_realtime_chart" style="height:100%;width:100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "{tv_interval}",
      "timezone": "Asia/Seoul",
      "theme": "dark",
      "style": "1",
      "locale": "kr",
      "toolbar_bg": "#12161c",
      "enable_publishing": false,
      "hide_side_toolbar": true,
      "allow_symbol_change": false,
      "details": false,
      "hotlist": false,
      "calendar": false,
      "studies": [
        "MASimple@tv-basicstudies",
        "RSI@tv-basicstudies",
        "Volume@tv-basicstudies",
        "MACD@tv-basicstudies"
      ],
      "container_id": "tradingview_realtime_chart"
    }});
    </script>
  </div>
</body>
</html>
"""

components.html(tradingview_html, height=620)


components.html(tradingview_html, height=720)
