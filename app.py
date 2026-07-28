import time
import datetime

# --- [설정 영역] ---
TARGET_STOCK_CODE = "005930"  # 예: 삼성전자 종목 코드
TARGET_PRICE = 72400          # 목표 매수/매도 기준 가격
IS_RUNNING = True

def check_market_time():
    """현재 주식 장 운영 시간인지 확인하는 함수"""
    now = datetime.datetime.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # 평일(월~금)이고 9시부터 15시 30분 사이일 때만 True
    if now.weekday() < 5 and start_time <= now <= end_time:
        return True
    return False

def get_current_price(code):
    """현재 주가를 가져오는 함수 (증권사 API 연동부)"""
    # TODO: 사용하는 증권사 API의 현재가 조회 함수로 교체
    current_price = 72400  # 예시 데이터
    return current_price

def execute_buy_order(code, price):
    """매수 주문을 넣는 함수"""
    print(f"[매수 주문 접수] 종목: {code} | 가격: {price}원")
    # TODO: 증권사 API 매수 주문 함수 연동

def execute_sell_order(code, price):
    """매도 주문을 넣는 함수"""
    print(f"[매도 주문 접수] 종목: {code} | 가격: {price}원")
    # TODO: 증권사 API 매도 주문 함수 연동

def main_trading_bot():
    print("=== 자동매매 프로그램 가동 시작 ===")
    
    global IS_RUNNING
    while IS_RUNNING:
        try:
            # 1. 장 운영 시간이 아니면 1분 대기 후 스킵
            if not check_market_time():
                print("장 운영 시간이 아닙니다. 대기 중...")
                time.sleep(60)
                continue

            # 2. 현재가 조회
            current_price = get_current_price(TARGET_STOCK_CODE)
            print(f"현재가 확인 중... 종목: {TARGET_STOCK_CODE} | 현재가: {current_price}원")

            # 3. 매수/매도 조건 검사 및 실행
            if current_price <= TARGET_PRICE:
                print("조건 충족: 매수 시도")
                execute_buy_order(TARGET_STOCK_CODE, current_price)
                # 매수 후 반복을 멈추거나 상태 변경 가능
                # IS_RUNNING = False 

            # 4. 서버 과부하 방지를 위한 딜레이 (3초마다 체크)
            time.sleep(3)

        except Exception as e:
            print(f"[에러 발생]: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main_trading_bot()
