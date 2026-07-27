import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
# 1. 프리미엄 다크 터미널 UI 디스플레이 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ALPHA QUANT PRO - AI 트레이딩 시스템",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* 고급스러운 블랙/다크 메탈 베이스 */
    .stApp { background-color: #0B0E14; color: #E1E6ED; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    
    /* 헤더 & 카드 스타일링 */
    .quant-header {
        background: linear-gradient(135deg, #131B2A 0%, #0B0E14 100%);
        padding: 20px 24px;
        border-radius: 16px;
        border: 1px solid #1E293B;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* 강렬한 AI 시그널 카드 */
    .card-buy {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid #EF4444;
        border-left: 6px solid #EF4444;
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 20px;
    }
    
    .card-sell {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid #3B82F6;
        border-left: 6px solid #3B82F6;
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 20px;
    }
    
    .card-neutral {
        background: linear-gradient(135deg, rgba(100, 116, 139, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid #64748B;
        border-left: 6px solid #64748B;
        padding: 22px;
        border-radius: 14px;
        margin-bottom: 20px;
    }

    .metric-box {
        background: #151D2A;
        border: 1px solid #1E293B;
        padding: 14px;
        border-radius: 10px;
        text-align: center;
    }

    .news-card {
        background: #131B2A;
        border: 1px solid #1E293B;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 한글 뉴스 알고리즘 함수
# -----------------------------------------------------------------------------
def fetch_korean_news(query):
    try:
        encoded_query = urllib.parse.quote(f"{query} 주식 속보")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        xml_data = urllib.request.urlopen(req, timeout=3).read()
        root = ET.fromstring(xml_data)
        
        items = root.findall('./channel/item')[:5]
        news_list = []
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text[:16] if item.find('pubDate') is not None else ""
            
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title, source = parts[0], parts[1]
            else:
                source = "실시간 속보"

            news_list.append({"title": title, "link": link, "date": pub_date, "source": source})
        return news_list
    except:
        return []

# -----------------------------------------------------------------------------
# 3. 메인 트레이딩 터미널 헤더 & 종목 검색
# -----------------------------------------------------------------------------
if 'current_symbol'
