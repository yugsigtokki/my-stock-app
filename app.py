import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import urllib.request
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# 1. 토스증권 스타일 레이아웃 & 최적화 CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PRO 실시간 단타 대시보드",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # 모바일 화면 넓게 쓰기
)

st.markdown("""
    <style>
    /* 토스 어두운 배경 */
    .stApp { background-color: #101012; color: #FFFFFF; }
    
    /* 대형 매매 신호 카드 */
    .signal-card-buy {
        background-color: rgba(240, 68, 82, 0.15);
        border: 2px solid #F04452;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    .signal-card-sell {
        background-color: rgba(49, 130, 246, 0.15);
        border: 2px solid #3182F6;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    .signal-card-hold {
        background-color: #1C1C1E;
        border: 1px solid #2C2C2E;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 15px;
    }
    
    .news-card {
        background-color: #1C1C1E;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid #2C2C2E;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 실시간 뉴스 수집 함수 (구글 뉴스 RSS)
# -----------------------------------------------------------------------------
def get_realtime_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=3).read()
        root = ET.fromstring(xml_data)
        
        items = root.findall('./channel/item')[:5]
        news_list = []
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text[:16] if item.find('pubDate') is not None else ""
            news_list.append({"title": title, "link": link, "date": pub_date})
        return news_list
    except:
        return []

# -----------------------------------------------------------------------------
# 3. 사이드바 및 종목 설정
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ 종목 검색")
stock_input = st.sidebar.text_input("티커 입력 (예: TSLL, NVDA, AAPL)", value="TSLL").strip().upper()

if stock_input.isdigit() and len(stock_input) == 6:
    tv_symbol = f"KRX:{stock_input}"
    yf_symbol = f"{stock_input}.KS"
else:
    tv_symbol = stock_input
    yf_symbol = stock_input

# -----------------------------------------------------------------------------
# 4. 🔥 AI 매수/매도 타이밍 단타 가이드 (명확한 행동 지침)
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

st.markdown(f"# **{stock_input}**")

if not df.empty and len(df) > 15:
    # 핵심 지표 산출
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
    
    # 확실한 알고리즘 조건 판단
    is_golden_cross = (float(prev['MA5']) <= float(prev['MA20'])) and (ma5 > ma20)
    is_dead_cross = (float(prev['MA5']) >= float(prev['MA20'])) and (ma5 < ma20)
    
    # 🔴 매수 타점 조건: (5선이 20선 위에 있음 OR 골든크로스) AND RSI 45 이하(저점)
    if (ma5 > ma20 or is_golden_cross) and curr_rsi <= 50:
        st.markdown(f"""
            <div class="signal-card-buy">
                <div style="color: #F04452; font-size: 14px; font-weight: 700;">🚨 AI 단타 매수 타이밍</div>
                <div style="font-size: 24px; font-weight: 800; color: #F04452; margin-top: 4px;">지금 바로 [매수] 고려 구간!</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>이유:</b> 5분/1분 이평선 우상향 전환 및 단기 저점(RSI {curr_rsi:.1f}) 형성<br>
                    • <b>목표가:</b> ${curr_price * 1.015:,.2f} (+1.5% 익절)<br>
                    • <b>손절가:</b> ${curr_price * 0.99:,.2f} (-1.0% 이탈시 즉시 손절)
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 🔵 매도 타점 조건: (5선이 20선 아래로 이탈 OR 데드크로스) OR RSI 65 이상(과열)
    elif (ma5 < ma20 or is_dead_cross) or curr_rsi >= 65:
        st.markdown(f"""
            <div class="signal-card-sell">
                <div style="color: #3182F6; font-size: 14px; font-weight: 700;">⚠️ AI 단타 매도/관망 타이밍</div>
                <div style="font-size: 24px; font-weight: 800; color: #3182F6; margin-top: 4px;">지금은 [매도] 및 [진입 금지]!</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>이유:</b> 단기 과열 구간(RSI {curr_rsi:.1f})이거나 이평선이 하락세로 꺾였습니다.<br>
                    • <b>대응:</b> 보유 중이라면 분할 매도로 수익 확정, 미보유자는 눌림목까지 대기하세요.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # ⚪ 관망/유지
    else:
        st.markdown(f"""
            <div class="signal-card-hold">
                <div style="color: #8E8E93; font-size: 14px; font-weight: 700;">⚪ AI 단타 관망 구간</div>
                <div style="font-size: 22px; font-weight: 800; color: #FFFFFF; margin-top: 4px;">보유자는 유지 / 신규진입은 관망</div>
                <div style="font-size: 14px; color: #8E8E93; margin-top: 6px;">
                    현재 박스권 횡보 중입니다. 확실한 신호(골든크로스/과매도)가 나올 때까지 대기하세요.
                </div>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 🖥️ 대형 트레이딩뷰 차트 (선 그리기 제거 + 높이 680px로 확대)
# -----------------------------------------------------------------------------
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div id="tradingview_chart" style="height:680px;width:100%"></div>
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
    "hide_side_toolbar": true,  /* 좌측 선 그리기 도구 숨김 (화면 깔끔화) */
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

components.html(tradingview_html, height=690)

# -----------------------------------------------------------------------------
# 6. 📰 실시간 관련 뉴스 & 속보 헤드라인
# -----------------------------------------------------------------------------
st.markdown("### 📰 실시간 주요 뉴스 & 속보")
news_data = get_realtime_news(stock_input)

if news_data:
    for news in news_data:
        st.markdown(f"""
            <div class="news-card">
                <a href="{news['link']}" target="_blank" style="text-decoration: none; color: #FFFFFF; font-weight: 600; font-size: 15px;">
                    • {news['title']}
                </a>
                <div style="color: #8E8E93; font-size: 12px; margin-top: 4px;">{news['date']}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.write("관련 최신 뉴스를 가져오는 중입니다...")
