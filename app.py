import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib.request
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# 1. 토스증권 테마 디자인 설정 (깔끔한 UI)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Toss Style AI Stock Dashboard",
    page_icon="⚡",
    layout="wide"
)

# 토스증권 느낌의 깔끔한 CSS
st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .stApp { background-color: #101012; color: #FFFFFF; }
    
    /* 카드형 컨테이너 스타일 */
    .toss-card {
        background-color: #1C1C1E;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #2C2C2E;
        margin-bottom: 12px;
    }
    
    /* 메트릭 글자 강조 */
    .toss-title { font-size: 14px; color: #8E8E93; margin-bottom: 4px; }
    .toss-value { font-size: 26px; font-weight: 700; }
    .toss-buy { color: #F04452; font-weight: 700; }  /* 토스 레드 (매수/상승) */
    .toss-sell { color: #3182F6; font-weight: 700; } /* 토스 블루 (매도/하락) */
    
    /* 버튼 스타일 */
    .stButton>button {
        background-color: #3182F6;
        color: white;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        height: 45px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 실시간 뉴스 및 긍정/부정 감성 분석 함수 (구글 뉴스 RSS 이용)
# -----------------------------------------------------------------------------
def fetch_news_sentiment(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=3).read()
        root = ET.fromstring(xml_data)
        
        items = root.findall('./channel/item')[:5]
        news_list = []
        
        pos_words = ['up', 'growth', 'gain', 'buy', 'bull', 'record', 'high', 'surge', 'profit', 'positive']
        neg_words = ['down', 'drop', 'fall', 'sell', 'bear', 'low', 'loss', 'risk', 'crash', 'negative']
        
        score = 0
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            
            title_lower = title.lower()
            for w in pos_words:
                if w in title_lower: score += 1
            for w in neg_words:
                if w in title_lower: score -= 1
                
            news_list.append({"title": title, "link": link})
            
        sentiment = "긍정적 📈" if score > 0 else ("부정적 📉" if score < 0 else "중립적 ⚖️")
        return news_list, sentiment, score
    except Exception:
        return [], "분석 불가 ⚪", 0

# -----------------------------------------------------------------------------
# 3. 사이드바 - 종목 및 주기 선택
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ 주식 설정")

if st.sidebar.button("🔄 실시간 시세 갱신", use_container_width=True):
    st.cache_data.clear()

stock_input = st.sidebar.text_input("종목 검색 (티커)", value="TSLL").strip().upper()

timeframe = st.sidebar.selectbox(
    "차트 주기",
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

ticker = f"{stock_input}.KS" if stock_input.isdigit() and len(stock_input) == 6 else stock_input

# -----------------------------------------------------------------------------
# 4. 데이터 수집 및 복합 지표 산출 (이평선 + RSI + 볼린저밴드 + MACD)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def load_stock_data(symbol, p, i):
    return yf.download(symbol, period=p, interval=i)

try:
    df = load_stock_data(ticker, period, interval)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if not df.empty:
        # 보조지표 계산
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 볼린저 밴드
        df['STD20'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD20'] * 2)
        df['Lower'] = df['MA20'] - (df['STD20'] * 2)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        curr_price = float(latest['Close'])
        price_diff = curr_price - float(prev['Close'])
        pct_change = (price_diff / float(prev['Close'])) * 100

        # -----------------------------------------------------------------------------
        # 5. 토스증권 스타일 헤더 (현재가 및 변동률)
        # -----------------------------------------------------------------------------
        st.markdown(f"## **{stock_input}**")
        color_class = "toss-buy" if price_diff >= 0 else "toss-sell"
        sign = "+" if price_diff >= 0 else ""
        
        st.markdown(f"""
            <div style="margin-bottom: 25px;">
                <span style="font-size: 36px; font-weight: 800;">{curr_price:,.2f}</span> 
                <span style="font-size: 20px;" class="{color_class}">{sign}{price_diff:,.2f} ({sign}{pct_change:.2f}%)</span>
            </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # 6. 🔥 AI 종합 진단 (기술적 지표 + 실시간 뉴스 빅데이터 점수화)
        # -----------------------------------------------------------------------------
        news_list, news_sentiment, news_score = fetch_news_sentiment(stock_input)

        # AI 매매 종합 점수 계산 (100점 만점)
        ai_score = 50
        
        # 1) 이평선 골든크로스
        if float(latest['MA5']) > float(latest['MA20']): ai_score += 15
        else: ai_score -= 15

        # 2) RSI 과매수/과매도
        rsi_val = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
        if rsi_val <= 30: ai_score += 15  # 저점 매수 기회
        elif rsi_val >= 70: ai_score -= 15 # 과열

        # 3) 볼린저 밴드 하단 이탈 여부
        if curr_price <= float(latest['Lower']): ai_score += 10
        elif curr_price >= float(latest['Upper']): ai_score -= 10

        # 4) 뉴스 감성 점수 반영
        ai_score += (news_score * 5)
        ai_score = max(0, min(100, ai_score))

        # 최종 AI 매매 의견 결정
        if ai_score >= 65:
            opinion = "🔴 적극 매수 추천"
            op_desc = "기술적 지표와 최신 뉴스 흐름이 모두 상방을 가리키고 있습니다."
        elif ai_score <= 35:
            opinion = "🔵 매도 / 관망 추천"
            op_desc = "단기 과열 또는 하락 추세 신호가 감지되어 주의가 필요합니다."
        else:
            opinion = "⚪ 중립 (보유)"
            op_desc = "뚜렷한 방향성이 나타나지 않아 관망을 추천합니다."

        # AI 진단 결과 토스 카드
        st.markdown(f"""
            <div class="toss-card">
                <div class="toss-title">🤖 AI 빅데이터 종합 분석 리포트</div>
                <div style="font-size: 22px; font-weight: 700; margin-top: 5px;">{opinion} (점수: {ai_score}점 / 100점)</div>
                <div style="color: #A1A1A6; font-size: 14px; margin-top: 8px;">{op_desc}</div>
            </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # 7. 토스 스타일 심플 차트 (캔들 + 볼린저밴드 + 거래량)
        # -----------------------------------------------------------------------------
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.25, 0.75])

        # 캔들
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='주가', increasing_line_color='#F04452', decreasing_line_color='#3182F6'
        ), row=1, col=1)

        # 볼린저 밴드
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], name='상한선', line=dict(color='#A1A1A6', width=1, dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], name='하한선', line=dict(color='#A1A1A6', width=1, dash='dot')), row=1, col=1)

        # 거래량
        colors = ['#F04452' if c >= o else '#3182F6' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량', marker_color=colors), row=2, col=1)

        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#101012', plot_bgcolor='#101012',
            height=500, margin=dict(l=0, r=0, t=10, b=0),
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # -----------------------------------------------------------------------------
        # 8. 관련 최신 글로벌 뉴스 리스트
        # -----------------------------------------------------------------------------
        st.subheader("📰 실시간 관련 뉴스")
        if news_list:
            for n in news_list:
                st.markdown(f"- [{n['title']}]({n['link']})")
        else:
            st.write("관련 뉴스를 가져올 수 없습니다.")

    else:
        st.error("데이터를 가져오지 못했습니다. 종목 티커를 확인해주세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
