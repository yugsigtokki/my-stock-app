import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd

# -----------------------------------------------------------------------------
# 1. 토스/트레이딩뷰 스타일 다크 테마
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PRO 실시간 단타 대시보드",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp { background-color: #101012; color: #FFFFFF; }
    .toss-card {
        background-color: #1C1C1E;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #2C2C2E;
        margin-bottom: 12px;
    }
    .toss-title { font-size: 13px; color: #8E8E93; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 - 종목 검색
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ PRO 단타 대시보드")

stock_input = st.sidebar.text_input("종목 입력 (예: TSLL, NVDA, AAPL)", value="TSLL").strip().upper()

# 트레이딩뷰 심볼 매핑
if stock_input.isdigit() and len(stock_input) == 6:
    tv_symbol = f"KRX:{stock_input}"
    yf_symbol = f"{stock_input}.KS"
else:
    tv_symbol = stock_input
    yf_symbol = stock_input

# -----------------------------------------------------------------------------
# 3. 🔥 핵심: 깜빡임이 전혀 없는 TradingView 실시간 라이브 차트
# -----------------------------------------------------------------------------
st.markdown(f"## **{stock_input}** 실시간 프로 차트")

# 트레이딩뷰 위젯 HTML (증권사급 캔들/이평선/실시간 틱 반영)
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div id="tradingview_chart" style="height:550px;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "1",
    "timezone": "Asia/Seoul",
    "theme": "dark",
    "style": "1",
    "locale": "kr",
    "toolbar_bg": "#101012",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "studies": [
      "MASimple@tv-basicstudies",
      "RSI@tv-basicstudies",
      "MACD@tv-basicstudies",
      "BB@tv-basicstudies"
    ],
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""

# HTML을 직접 주입하여 화면 깜빡임 완벽 제거
components.html(tradingview_html, height=560)

# -----------------------------------------------------------------------------
# 4. AI 실시간 기술적 복합 분석 (실시간 보조)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10)
def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

df = analyze_stock(yf_symbol)

if not df.empty and len(df) > 15:
    # 지표 계산
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]
    curr_rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
    ma5_val = float(latest['MA5'])
    ma20_val = float(latest['MA20'])

    # 점수화 분석
    score = 50
    if ma5_val > ma20_val: score += 25
    else: score -= 25

    if curr_rsi <= 30: score += 25
    elif curr_rsi >= 70: score -= 25

    if score >= 75:
        signal = "🔴 **단기 적극 매수** (5선 우상향 + 과매도 반등)"
    elif score <= 25:
        signal = "🔵 **단기 매도/관망** (5선 이탈 + 과열)"
    else:
        signal = "⚪ **횡보/중립** (선별적 대응 필요)"

    st.markdown(f"""
        <div class="toss-card">
            <div class="toss-title">🤖 1분봉 AI 보조 알고리즘 진단</div>
            <div style="font-size: 18px; font-weight: 700; margin-top: 6px;">{signal}</div>
            <div style="color: #A1A1A6; font-size: 13px; margin-top: 4px;">
                RSI: {curr_rsi:.1f} | 5일 이평: {ma5_val:,.2f} | 20일 이평: {ma20_val:,.2f}
            </div>
        </div>
    """, unsafe_allow_html=True)
