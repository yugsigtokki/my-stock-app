import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. 레이아웃 & 실시간 풀스크린 CSS 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="REALTIME PRO TRADING",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #FFFFFF; }
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important;
        max-width: 100% !important; 
    }
    [data-testid="stSidebar"] { background-color: #12161c !important; }
    
    .header-box {
        background: linear-gradient(135deg, #1e222d 0%, #12161c 100%);
        border: 1px solid #2a2e39;
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화
# -----------------------------------------------------------------------------
if "symbol" not in st.session_state:
    st.session_state["symbol"] = "TSLA"

# -----------------------------------------------------------------------------
# 3. 상단 컨트롤 패널
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="header-box">
        <h4 style="margin:0; color:#00ffcc;">⚡ ULTRA REALTIME TRADING DESK</h4>
        <span style="color:#848e9c; font-size:13px;">실시간 엔진 연동 완료</span>
    </div>
""", unsafe_allow_html=True)

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

# 타임프레임 매핑
if "1분봉" in timeframe_mode:
    tv_interval = "1"
elif "5분봉" in timeframe_mode:
    tv_interval = "5"
elif "1시간봉" in timeframe_mode:
    tv_interval = "60"
else:
    tv_interval = "D"

target_ticker = st.session_state["symbol"]
tv_symbol = f"BATS:{target_ticker}"

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 트레이딩뷰 위젯 (왼쪽 선 긋기 툴바 완전 숨김 처리 적용)
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
      "hide_side_toolbar": true,      // <-- 이 옵션이 왼쪽 선 긋기 툴바를 완전히 숨깁니다!
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

components.html(tradingview_html, height=720)
