import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# 1. 레이아웃 & 가로 여백 완전히 제거
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
# 3. 화면 상단 종목 검색 & 매매 모드 스위치
# -----------------------------------------------------------------------------
st.markdown("### 🔍 종목 검색 & 매매 스타일 선택")

if "current_symbol" not in st.session_state:
    st.session_state["current_symbol"] = "TSLL"

col_search, col_mode = st.columns([2, 1])

with col_search:
    user_input = st.text_input(
        "티커 입력 (예: TSLL, NVDA, AAPL, TSLA, 005930)", 
        value=st.session_state["current_symbol"]
    ).strip().upper()
    if user_input:
        st.session_state["current_symbol"] = user_input

with col_mode:
    trade_mode = st.radio(
        "🎯 매매 전략 모드",
        ["⚡ 초단타 (1~2%)", "🚀 큰파동 (3~7%+)"],
        horizontal=True
    )

st.write("🔥 인기 검색 종목:")
col1, col2, col3, col4, col5 = st.columns(5)
if col1.button("TSLL (테슬라2X)"): st.session_state["current_symbol"] = "TSLL"; st.rerun()
if col2.button("NVDA (엔비디아)"): st.session_state["current_symbol"] = "NVDA"; st.rerun()
if col3.button("TSLA (테슬라)"): st.session_state["current_symbol"] = "TSLA"; st.rerun()
if col4.button("AAPL (애플)"): st.session_state["current_symbol"] = "AAPL"; st.rerun()
if col5.button("005930 (삼성)"): st.session_state["current_symbol"] = "005930"; st.rerun()

stock_input = st.session_state["current_symbol"]

# 실시간 BATS 피드 연결
if stock_input.isdigit() and len(stock_input) == 6:
    tv_symbol = f"KRX:{stock_input}"
    yf_symbol = f"{stock_input}.KS"
else:
    tv_symbol = f"BATS:{stock_input}"
    yf_symbol = stock_input

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 🔥 모드별 AI 실시간 매수/매도 타이밍 분석
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def analyze_data(symbol, interval):
    try:
        df = yf.download(symbol, period="1d", interval=interval)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

# 모드별 타임프레임 선택
target_interval = "1m" if "초단타" in trade_mode else "5m"
df = analyze_data(yf_symbol, target_interval)

st.markdown(f"# **{stock_input}** 분석 결과 ({trade_mode})")

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
    
    # 목표가/손절가 비율 모드별 설정
    if "초단타" in trade_mode:
        tp_target_pct = 0.018 # +1.8%
        sl_target_pct = 0.008 # -0.8%
    else:
        tp_target_pct = 0.045 # +4.5% (추세 보유 시 무제한 트레일링)
        sl_target_pct = 0.015 # -1.5%
    
    # 1. 🚀 강한 매수
    if is_golden_cross or (ma5 > ma20 and curr_rsi <= 42):
        st.markdown(f"""
            <div class="signal-card-strong-buy">
                <div style="color: #F04452; font-size: 14px; font-weight: 700;">🔥 AI 단타 신호: [강한 매수]</div>
                <div style="font-size: 24px; font-weight: 800; color: #F04452; margin-top: 4px;">🚀 지금 강력 진입 추천 구간!</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 골든크로스 발생 또는 과매도(RSI {curr_rsi:.1f}) 반등 성공<br>
                    • <b>1차 목표가:</b> ${curr_price * (1 + tp_target_pct):,.2f} (+{tp_target_pct*100:.1f}%)<br>
                    • <b>손절가:</b> ${curr_price * (1 - sl_target_pct):,.2f} (-{sl_target_pct*100:.1f}%)
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 2. 📈 약한 매수 (큰파동 모드에서는 추세 지속 홀딩)
    elif ma5 > ma20 and curr_rsi <= 58:
        if "큰파동" in trade_mode and curr_rsi > 48:
            st.markdown(f"""
                <div class="signal-card-buy">
                    <div style="color: #FF7E36; font-size: 14px; font-weight: 700;">🚀 AI 추세 신호: [추세 계속 홀딩 / 크게 먹기]</div>
                    <div style="font-size: 22px; font-weight: 800; color: #FF7E36; margin-top: 4px;">상승 추세 유지 중 - 파동 타고 계속 홀딩!</div>
                    <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                        • <b>판단 이유:</b> 5분봉 이평선 정배열 우상향 유지 중 (RSI {curr_rsi:.1f})<br>
                        • <b>대응:</b> 추세 안 꺾였으니 아직 팔지 말고 목표 수익률까지 더 끌고 가세요!
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="signal-card-buy">
                    <div style="color: #FF7E36; font-size: 14px; font-weight: 700;">📈 AI 단타 신호: [약한 매수 / 눌림목 진입]</div>
                    <div style="font-size: 22px; font-weight: 800; color: #FF7E36; margin-top: 4px;">눌림목 구간 - 분할 매수 고려</div>
                    <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                        • <b>판단 이유:</b> 우상향 흐름 속 단기 정체(RSI {curr_rsi:.1f})로 분할 매수 적기<br>
                        • <b>목표가:</b> ${curr_price * (1 + tp_target_pct*0.7):,.2f}<br>
                        • <b>손절가:</b> ${curr_price * (1 - sl_target_pct):,.2f}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # 3. 🚨 강한 매도
    elif is_dead_cross or (ma5 < ma20 and curr_rsi >= 70):
        st.markdown(f"""
            <div class="signal-card-strong-sell">
                <div style="color: #3182F6; font-size: 14px; font-weight: 700;">🚨 AI 단타 신호: [강한 매도 / 추세 이탈]</div>
                <div style="font-size: 24px; font-weight: 800; color: #3182F6; margin-top: 4px;">⚠️ 전량 익절/손절 및 진입 엄금!</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 데드크로스 발생 또는 과열(RSI {curr_rsi:.1f}) 후 추세 꺾임<br>
                    • <b>대응:</b> 수익 확정 후 눌림목 재형성까지 관망하세요.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 4. 📉 약한 매도
    elif ma5 < ma20 or curr_rsi >= 63:
        st.markdown(f"""
            <div class="signal-card-sell">
                <div style="color: #60A5FA; font-size: 14px; font-weight: 700;">📉 AI 단타 신호: [약한 매도 / 일부 분할 익절]</div>
                <div style="font-size: 22px; font-weight: 800; color: #60A5FA; margin-top: 4px;">상승세 둔화 - 분할 익절 권장</div>
                <div style="font-size: 14px; color: #E5E5EA; margin-top: 8px;">
                    • <b>판단 이유:</b> 단기 상승 동력 약화(RSI {curr_rsi:.1f}), 일부 비중 축소하세요.
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
                    박스권 횡보 중입니다. 방향성이 나올 때까지 대기하세요.
                </div>
            </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 트레이딩뷰 실시간 차트
# -----------------------------------------------------------------------------
tv_interval = "1" if "초단타" in trade_mode else "5"
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:100%;width:100%;margin:0;padding:0;">
  <div id="tradingview_chart" style="height:750px;width:100%;"></div>
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
