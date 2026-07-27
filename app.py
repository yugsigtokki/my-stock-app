import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. 레이아웃 & CSS 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PRO AI 트레이딩 대시보드",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #101012; color: #FFFFFF; }
    .block-container {
        padding-top: 2rem !important;
        max-width: 100% !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1C1C1E !important;
    }
    
    .card-buy { background-color: rgba(240, 68, 82, 0.15); border: 2px solid #F04452; padding: 20px; border-radius: 16px; margin-bottom: 15px; }
    .card-weak-buy { background-color: rgba(255, 126, 54, 0.15); border: 2px solid #FF7E36; padding: 20px; border-radius: 16px; margin-bottom: 15px; }
    .card-hold { background-color: #1C1C1E; border: 1px solid #2C2C2E; padding: 20px; border-radius: 16px; margin-bottom: 15px; }
    .card-sell { background-color: rgba(49, 130, 246, 0.15); border: 2px solid #3182F6; padding: 20px; border-radius: 16px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 수집 및 AI 분석 엔진
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10)
def fetch_data(symbol, interval, period):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

def get_ai_analysis(df, mode):
    if df.empty or len(df) < 50:
        return None
    
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['SMA200'] = df['Close'].rolling(200).mean()
    
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    curr_price = float(latest['Close'])
    curr_vwap = float(latest['VWAP'])
    curr_rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
    curr_macd_hist = float(latest['MACD_Hist'])
    prev_macd_hist = float(prev['MACD_Hist'])
    sma50 = float(latest['SMA50'])
    sma200 = float(latest['SMA200'])

    score = 0
    reasons = []

    if "중장기" in mode or "스윙" in mode:
        if not pd.isna(sma200) and sma50 > sma200: score += 3; reasons.append("정배열 (50일선 > 200일선)")
        else: score -= 3; reasons.append("역배열 (50일선 < 200일선)")
        if curr_price > sma50: score += 2; reasons.append("50일 지지선 상회")
        else: score -= 2; reasons.append("50일 지지선 이탈")
        if curr_macd_hist > 0: score += 2; reasons.append("MACD 모멘텀 강세")
        else: score -= 2; reasons.append("MACD 모멘텀 약세")
        if curr_rsi <= 40: score += 1; reasons.append(f"RSI 과매도 ({curr_rsi:.1f})")
        elif curr_rsi >= 70: score -= 2; reasons.append(f"RSI 과열 ({curr_rsi:.1f})")
    else:
        if curr_price > curr_vwap: score += 2; reasons.append("VWAP 수급선 상회")
        else: score -= 2; reasons.append("VWAP 수급선 하회")
        if latest['EMA9'] > latest['EMA21']: score += 2; reasons.append("단기 이평 정배열")
        else: score -= 2; reasons.append("단기 이평 역배열")
        if curr_macd_hist > 0 and curr_macd_hist > prev_macd_hist: score += 2; reasons.append("MACD 강한 매수세")
        elif curr_macd_hist < 0 and curr_macd_hist < prev_macd_hist: score -= 2; reasons.append("MACD 매도세")
        if curr_rsi <= 35: score += 1; reasons.append(f"RSI 과매도 ({curr_rsi:.1f})")
        elif curr_rsi >= 75: score -= 1; reasons.append(f"RSI 과열 ({curr_rsi:.1f})")

    return {"price": curr_price, "score": score, "reasons": reasons}

# -----------------------------------------------------------------------------
# 3. 사이드바 메뉴 (페이지 라우터)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🤖 메뉴")
    page = st.radio("이동할 창을 선택하세요:", ["🏠 홈 (AI 실시간 추천)", "🔍 개별 종목 검색"])
    st.markdown("---")

# -----------------------------------------------------------------------------
# 4. [페이지 1] AI 실시간 추천 홈
# -----------------------------------------------------------------------------
if page == "🏠 홈 (AI 실시간 추천)":
    st.title("🔥 AI 실시간 매매 시그널 보드")
    
    home_mode = st.radio("타임프레임 기준", ["⚡ 단타 (5분봉)", "📅 스윙 (일봉)"], horizontal=True)
    interval = "5m" if "단타" in home_mode else "1d"
    period = "5d" if "단타" in home_mode else "6mo"
    
    # 미국 주식 및 인기 레버리지 ETF 리스트
    target_stocks = {
        "NVDA": "엔비디아", "TSLA": "테슬라", "AAPL": "애플", "MSFT": "마이크로소프트",
        "AMZN": "아마존", "GOOGL": "구글", "META": "메타", "AMD": "AMD",
        "SOXL": "반도체 3X", "TQQQ": "나스닥 3X", "TSLL": "테슬라 2X"
    }
    
    st.markdown("### 🏆 현재 추천 매수 종목")
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    col_idx = 0
    no_buy_signals = True
    
    for ticker, name in target_stocks.items():
        df = fetch_data(ticker, interval, period)
        analysis = get_ai_analysis(df, home_mode)
        
        if analysis:
            score = analysis['score']
            if score >= 1:
                no_buy_signals = False
                with cols[col_idx % 3]:
                    if score >= 4:
                        st.markdown(f"""
                            <div class="card-buy">
                                <h3 style="margin:0; color:#F04452;">{name} ({ticker})</h3>
                                <h2 style="margin:5px 0 0 0;">${analysis['price']:,.2f}</h2>
                                <p style="color:#F04452; font-weight:bold; margin:5px 0;">🔥 강력 매수 (+{score}점)</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="card-weak-buy">
                                <h3 style="margin:0; color:#FF7E36;">{name} ({ticker})</h3>
                                <h2 style="margin:5px 0 0 0;">${analysis['price']:,.2f}</h2>
                                <p style="color:#FF7E36; font-weight:bold; margin:5px 0;">📈 분할 매수 (+{score}점)</p>
                            </div>
                        """, unsafe_allow_html=True)
                col_idx += 1
                
    if no_buy_signals:
        st.info("현재 뚜렷한 매수 신호가 포착된 종목이 없습니다.")

# -----------------------------------------------------------------------------
# 5. [페이지 2] 개별 종목 검색 및 차트 분석
# -----------------------------------------------------------------------------
elif page == "🔍 개별 종목 검색":
    st.markdown("### 🔍 개별 종목 정밀 분석")

    if "current_symbol" not in st.session_state:
        st.session_state["current_symbol"] = "TSLA"

    col_search, col_mode = st.columns([1.5, 2])
    with col_search:
        user_input = st.text_input("미국 티커 입력 (예: NVDA, TSLA, SOXL)", value=st.session_state["current_symbol"]).strip().upper()
        if user_input: st.session_state["current_symbol"] = user_input
    with col_mode:
        trade_mode = st.radio("🎯 매매 전략 모드", ["⚡ 초단타 (1분봉)", "🚀 추세 스윙 (5분봉)", "📅 중장기 예측 (일봉)"], horizontal=True)

    stock_input = st.session_state["current_symbol"]
    tv_symbol = f"BATS:{stock_input}"
    yf_symbol = stock_input

    st.markdown("---")

    if "초단타" in trade_mode: target_interval, target_period, tv_interval = "1m", "5d", "1"
    elif "추세" in trade_mode: target_interval, target_period, tv_interval = "5m", "1mo", "5"
    else: target_interval, target_period, tv_interval = "1d", "1y", "D"

    df = fetch_data(yf_symbol, target_interval, target_period)
    analysis = get_ai_analysis(df, trade_mode)

    if analysis:
        score = analysis['score']
        reasons_html = "<br>".join([f"• {r}" for r in analysis['reasons']])

        if score >= 4:
            st.markdown(f'<div class="card-buy"><div style="color: #F04452; font-weight: 700;">🔥 종합점수: +{score}점 [강세 및 매수 추천]</div><div style="font-size: 24px; font-weight: 800; color: #F04452;">현재가: ${analysis["price"]:,.2f}</div><div style="font-size: 14px; margin-top: 10px;">{reasons_html}</div></div>', unsafe_allow_html=True)
        elif 1 <= score < 4:
            st.markdown(f'<div class="card-weak-buy"><div style="color: #FF7E36; font-weight: 700;">📈 종합점수: +{score}점 [약세 속 반등 / 분할 접근]</div><div style="font-size: 24px; font-weight: 800; color: #FF7E36;">현재가: ${analysis["price"]:,.2f}</div><div style="font-size: 14px; margin-top: 10px;">{reasons_html}</div></div>', unsafe_allow_html=True)
        elif score <= -4:
            st.markdown(f'<div class="card-sell"><div style="color: #3182F6; font-weight: 700;">🚨 종합점수: {score}점 [강력 매도 / 하락 추세]</div><div style="font-size: 24px; font-weight: 800; color: #3182F6;">현재가: ${analysis["price"]:,.2f}</div><div style="font-size: 14px; margin-top: 10px;">{reasons_html}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card-hold"><div style="color: #8E8E93; font-weight: 700;">⚪ 종합점수: {score}점 [관망 및 비중 축소]</div><div style="font-size: 24px; font-weight: 800;">현재가: ${analysis["price"]:,.2f}</div><div style="font-size: 14px; color: #8E8E93; margin-top: 10px;">{reasons_html}</div></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 트레이딩뷰 위젯 (미국 주식 전용 깔끔한 캔들 차트)
    # -------------------------------------------------------------------------
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%;">
      <div id="tradingview_chart" style="height:650px;width:100%;"></div>
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
        "toolbar_bg": "#101012",
        "enable_publishing": false,
        "hide_side_toolbar": true,
        "allow_symbol_change": true,
        "studies": ["MASimple@tv-basicstudies", "RSI@tv-basicstudies", "Volume@tv-basicstudies", "MACD@tv-basicstudies"],
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tradingview_html, height=660)
