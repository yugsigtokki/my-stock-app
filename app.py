import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# 1. 레이아웃 & 가로 여백 완전히 제거 (화면 꽉 채우기)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PRO 실시간 단타 대시보드",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #101012; color: #FFFFFF; }
    
    .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-top: 1rem !important;
        max-width: 100% !important;
    }
    
    /* 5단계 신호 카드 스타일 */
    .signal-card-strong-buy {
        background-color: rgba(240, 68, 82, 0.25);
        border: 2px solid #F04452;
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    .signal-card-buy {
        background-color: rgba(255, 126, 54, 0.2);
        border: 2px solid #FF7E36;
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    .signal-card-hold {
        background-color: #1C1C1E;
        border: 1px solid #2C2C2E;
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    .signal-card-sell {
        background-color: rgba(49, 130, 246, 0.2);
        border: 2px solid #3182F6;
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    .signal-card-strong-sell {
        background-color: rgba(0, 81, 255, 0.3);
        border: 2px solid #0051FF;
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    
    .news-card {
        background-color: #1C1C1E;
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid #2C2C2E;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 한글 뉴스 수집 함수
# -----------------------------------------------------------------------------
def get_korean_news(query):
    try:
        encoded_query = urllib.parse.quote(f"{query} 주식")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=4).read()
        root = ET.fromstring(xml_data)
        
        items = root.findall('./channel/item')[:5]
        news_list = []
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text[:16] if item.find('pubDate') is not None else ""
            
            if " - " in title:
                title_parts = title.rsplit(" - ", 1)
                title = title_parts[0]
                source = title_parts[1]
            else:
                source = "뉴스"

            news_list.append({"title": title, "link": link, "date": pub_date, "source": source})
        return news_list
    except:
        return []

# -----------------------------------------------------------------------------
# 3. 화면 상단 종목 검색 및 터치 버튼
# -----------------------------------------------------------------------------
st.markdown("### 🔍 종목 검색")

if "current_symbol" not in st.session_state:
    st.session_state["current_symbol"] = "TSLL"

user_input = st.text_input(
    "티커 입력 (예: TSLL, NVDA, AAPL, TSLA, 005930)", 
    value=st.session_state["current_symbol"]
).strip().upper()

if user_input:
    st.session_state["current_symbol"] = user_input

st.write("🔥 인기 검색 종목:")
col1, col2, col3, col4, col5 = st.columns(5)
if col1.button("TSLL (테슬라2X)"): 
    st.session_state["current_symbol"] = "TSLL"
    st.rerun()
if col2.button("NVDA (엔비디아)"): 
    st.session_state["current_symbol"] = "NVDA"
    st.rerun()
if col3.button("TSLA (테슬라)"): 
    st.session_state["current_symbol"] = "TSLA"
    st.rerun()
if col4.button("AAPL (애플)"): 
    st.session_state["current_symbol"] = "AAPL"
    st.rerun()
if col5.button("005930 (삼성)"): 
    st.session_state["current_symbol"] = "005930"
    st.rerun()

stock_input = st.session_state["current_symbol"]

# 실시간 BATS 피드 연결 (미국 주식 지연 방지)
if stock_input.isdigit() and len(stock_input) == 6:
    tv_symbol = f"KRX:{stock_input}"
    yf_symbol = f"{stock_input}.KS"
else:
    tv_symbol = f"BATS:{stock_input}"
    yf_symbol = stock_input

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 🔥 세분화된 5단계 AI 매수/매도 타이밍 가이드
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def analyze_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

df = analyze_data(yf_symbol)

st.markdown(f"# **{stock_input}** 분석 결과")

if not df.empty and len(df) > 15:
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    curr_price = float(latest['Close'])
    curr_rsi = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
    ma5 = float(latest['MA5'])
    ma20 = float(latest['MA20'])
    
    is_golden_cross = (float(prev['MA5']) <= float(prev['MA20'])) and (ma5 > ma20)
    is_dead_cross = (float(prev['MA5']) >= float(prev['MA20'])) and (ma5 < ma20)
    
    # 1. 🚀 강한 매수
    if is_golden_cross or (ma5 > ma20 and curr_rsi <= 40):
        st.markdown(f"""
            <div class="signal-card-strong-buy">
                <div style="color: #F04452; font-size: 14px; font-weight: 700;">🔥 AI 단타 신호: [강한 매수]</div>
                <div style="font-size: 24px; font-weight: 800; color: #F04452; margin-top: 4px;">🚀 지금 강력 진입 추천 구간!</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 골든크로스 발생 또는 극심한 과매도 구간(RSI {curr_rsi:.1f}) 반등<br>
                    • <b>목표가:</b> ${curr_price * 1.02:,.2f} (+2.0% 익절)<br>
                    • <b>손절가:</b> ${curr_price * 0.992:,.2f} (-0.8% 손절)
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 2. 📈 약한 매수 (눌림목 진입)
    elif ma5 > ma20 and curr_rsi <= 52:
        st.markdown(f"""
            <div class="signal-card-buy">
                <div style="color: #FF7E36; font-size: 14px; font-weight: 700;">📈 AI 단타 신호: [약한 매수 / 분할 진입]</div>
                <div style="font-size: 22px; font-weight: 800; color: #FF7E36; margin-top: 4px;">눌림목 구간 - 분할 매수 고려</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 우상향 흐름 속 단기 정체(RSI {curr_rsi:.1f})로 분할 매수 적기<br>
                    • <b>목표가:</b> ${curr_price * 1.012:,.2f} (+1.2% 익절)<br>
                    • <b>손절가:</b> ${curr_price * 0.99:,.2f} (-1.0% 손절)
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 3. 🚨 강한 매도
    elif is_dead_cross or (ma5 < ma20 and curr_rsi >= 68):
        st.markdown(f"""
            <div class="signal-card-strong-sell">
                <div style="color: #3182F6; font-size: 14px; font-weight: 700;">🚨 AI 단타 신호: [강한 매도 / 즉시 탈출]</div>
                <div style="font-size: 24px; font-weight: 800; color: #3182F6; margin-top: 4px;">⚠️ 전량 매도 및 진입 엄금!</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 데드크로스 연출 또는 단기 과열(RSI {curr_rsi:.1f}) 심화<br>
                    • <b>대응:</b> 즉시 수익/손실 확정 후 눌림목 형성까지 완전히 대기
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 4. 📉 약한 매도 (수익 실현 준비)
    elif ma5 < ma20 or curr_rsi >= 60:
        st.markdown(f"""
            <div class="signal-card-sell">
                <div style="color: #60A5FA; font-size: 14px; font-weight: 700;">📉 AI 단타 신호: [약한 매도 / 비중 축소]</div>
                <div style="font-size: 22px; font-weight: 800; color: #60A5FA; margin-top: 4px;">상승세 둔화 - 분할 매도 구간</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 단기 이평선 하락 전환(RSI {curr_rsi:.1f}), 수익 일부 확정 권장
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 5. ⚪ 관망
    else:
        st.markdown(f"""
            <div class="signal-card-hold">
                <div style="color: #8E8E93; font-size: 14px; font-weight: 700;">⚪ AI 단타 신호: [관망]</div>
                <div style="font-size: 22px; font-weight: 800; color: #FFFFFF; margin-top: 4px;">보유자는 유지 / 신규진입 대기</div>
                <div style="font-size: 14px; color: #8E8E93; margin-top: 6px;">
                    현재 박스권 흐름 중입니다. 명확한 돌파나 눌림 신호가 나올 때까지 대기하세요.
                </div>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 트레이딩뷰 실시간 차트 (Cboe BATS 실시간 데이터 연동)
# -----------------------------------------------------------------------------
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:100%;width:100%;margin:0;padding:0;">
  <div id="tradingview_chart" style="height:750px;width:100%;"></div>
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
    "hide_side_toolbar": true,
    "allow_symbol_change": true,
    "studies": [
      "MASimple@tv-basicstudies",
      "RSI@tv-basicstudies",
      "Volume@tv-basicstudies"
    ],
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""

components.html(tradingview_html, height=760)

# -----------------------------------------------------------------------------
# 6. 한글 뉴스 리스트
# -----------------------------------------------------------------------------
st.markdown("### 📰 한글 주요 뉴스 & 속보")
news_data = get_korean_news(stock_input)

if news_data:
    for news in news_data:
        st.markdown(f"""
            <div class="news-card">
                <a href="{news['link']}" target="_blank" style="text-decoration: none; color: #FFFFFF; font-weight: 600; font-size: 15px;">
                    • {news['title']}
                </a>
                <div style="color: #8E8E93; font-size: 12px; margin-top: 4px;">
                    {news['source']} | {news['date']}
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.write("관련 최신 한글 뉴스를 찾는 중입니다...")
