import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. 레이아웃 & 최적화 CSS 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PRO REALTIME TRADING DESK",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #FFFFFF; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; }
    
    .live-price-box {
        background: #12161c;
        border: 2px solid #2a2e39;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .card-buy { background-color: rgba(240, 68, 82, 0.15); border: 2px solid #F04452; padding: 15px; border-radius: 14px; margin-bottom: 12px; }
    .card-weak-buy { background-color: rgba(255, 126, 54, 0.15); border: 2px solid #FF7E36; padding: 15px; border-radius: 14px; margin-bottom: 12px; }
    .card-sell { background-color: rgba(49, 130, 246, 0.15); border: 2px solid #3182F6; padding: 15px; border-radius: 14px; margin-bottom: 12px; }
    .card-hold { background-color: #12161c; border: 1px solid #2a2e39; padding: 15px; border-radius: 14px; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태 및 입력 컨트롤
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
# 3. 실시간 시세 및 AI 분석 엔진 (ttl=2초로 즉각 반영)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=2)
def get_live_market_data(symbol, interval, period):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 10:
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
        prev = df.iloc[-2]
        
        curr_price = float(latest['Close'])
        prev_price = float(prev['Close'])
        price_change = curr_price - prev_price
        pct_change = (price_change / prev_price) * 100
        
        curr_vwap = float(latest['VWAP'])
        curr_rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
        curr_macd = float(latest['MACD_Hist'])

        score = 0
        reasons = []

        if curr_price > curr_vwap: score += 2; reasons.append("VWAP 수급선 상회")
        else: score -= 2; reasons.append("VWAP 수급선 하회")

        if latest['EMA9'] > latest['EMA21']: score += 2; reasons.append("단기 이평선 정배열")
        else: score -= 2; reasons.append("단기 이평선 역배열")

        if curr_macd > 0: score += 2; reasons.append("MACD 모멘텀 강세")
        else: score -= 2; reasons.append("MACD 모멘텀 약세")

        if curr_rsi <= 35: score += 1; reasons.append(f"RSI 과매도 ({curr_rsi:.1f})")
        elif curr_rsi >= 75: score -= 1; reasons.append(f"RSI 과열 ({curr_rsi:.1f})")

        return {
            "price": curr_price, 
            "change": price_change, 
            "pct": pct_change, 
            "score": score, 
            "reasons": reasons
        }
    except:
        return None

market_data = get_live_market_data(target_ticker, yf_interval, yf_period)

if market_data:
    p = market_data["price"]
    ch = market_data["change"]
    pct = market_data["pct"]
    score = market_data["score"]
    reasons_str = " | ".join([f"• {r}" for r in market_data["reasons"]])
    
    # 등락 색상 설정
    ch_color = "#F04452" if ch >= 0 else "#3182F6"
    ch_sign = "+" if ch >= 0 else ""

    # 1. 실시간 시세 대형 카드 출력
    st.markdown(f"""
        <div class="live-price-box">
            <div>
                <h4 style="margin:0; color:#848e9c; font-size:14px;">{target_ticker} 실시간 현재가</h4>
                <h1 style="margin:5px 0 0 0; font-size:36px; font-weight:800;">${p:,.2f}</h1>
            </div>
            <div style="text-align: right;">
                <h4 style="margin:0; color:#848e9c; font-size:14px;">변동폭</h4>
                <h2 style="margin:5px 0 0 0; color:{ch_color}; font-size:24px; font-weight:700;">{ch_sign}${ch:,.2f} ({ch_sign}{pct:.2f}%)</h2>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. AI 매수/매도 추천 카드 출력
    if score >= 3:
        st.markdown(f'<div class="card-buy"><span style="color: #F04452; font-weight: 700; font-size: 16px;">🔥 [강력 매수 추천] (+{score}점)</span><div style="font-size: 13px; color: #ddd; margin-top: 6px;">{reasons_str}</div></div>', unsafe_allow_html=True)
    elif 1 <= score < 3:
        st.markdown(f'<div class="card-weak-buy"><span style="color: #FF7E36; font-weight: 700; font-size: 16px;">📈 [분할 매수 접근] (+{score}점)</span><div style="font-size: 13px; color: #ddd; margin-top: 6px;">{reasons_str}</div></div>', unsafe_allow_html=True)
    elif score <= -3:
        st.markdown(f'<div class="card-sell"><span style="color: #3182F6; font-weight: 700; font-size: 16px;">🚨 [매도 / 하락 우위] ({score}점)</span><div style="font-size: 13px; color: #ddd; margin-top: 6px;">{reasons_str}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="card-hold"><span style="color: #8E8E93; font-weight: 700; font-size: 16px;">⚪ [관망 중] (중립 {score}점)</span><div style="font-size: 13px; color: #aaa; margin-top: 6px;">{reasons_str}</div></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 트레이딩뷰 차트 (툴바 완전 제거)
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

components.html(tradingview_html, height=560)
