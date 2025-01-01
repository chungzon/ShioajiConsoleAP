import pymssql
import shioaji as sj
import pandas as pd
from datetime import datetime, timedelta
import time
from win10toast import ToastNotifier
import os
from decimal import Decimal

# 初始化 Shioaji API
api = sj.Shioaji(simulation=False)
api.login(
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

# 初始化通知器
notifier = ToastNotifier()

# 儲存即時行情資料
realtime_data = []

# 訂閱即時行情回調函數
def quote_callback(exchange, tick):
    global realtime_data
    data = {
        'datetime': tick.datetime,
        'open': float(tick.open),
        'high': float(tick.high),
        'low': float(tick.low),
        'close': float(tick.close),
        'volume': tick.volume,
    }
    realtime_data.append(data)

# 訂閱即時行情
def subscribe_realtime_data(stock_code):
    contract = api.Contracts.Stocks[stock_code]
    api.quote.set_on_tick_stk_v1_callback(quote_callback)
    api.quote.subscribe(contract, quote_type=sj.constant.QuoteType.Tick, version=sj.constant.QuoteVersion.v1)

# 取消訂閱即時行情
def unsubscribe_realtime_data(stock_code):
    contract = api.Contracts.Stocks[stock_code]
    api.quote.unsubscribe(contract, quote_type=sj.constant.QuoteType.Tick, version=sj.constant.QuoteVersion.v1)

# 使用黃金分割率計算回撤目標
def calculate_fibonacci_levels(high, low):
    diff = float(high) - float(low)
    levels = {
        'Level_0': float(high),
        'Level_0.382': float(high) - 0.382 * diff,
        'Level_0.5': float(high) - 0.5 * diff,
        'Level_0.618': float(high) - 0.618 * diff,
        'Level_1': float(low)
    }
    return levels

# 買賣點判斷
def identify_trade_signals(df):
    df['SMA_5'] = df['close'].rolling(window=5).mean()
    df['SMA_10'] = df['close'].rolling(window=10).mean()

    buy_signals = []
    sell_signals = []

    for i in range(1, len(df)):
        if df['close'][i] > df['SMA_5'][i] and df['close'][i-1] <= df['SMA_5'][i-1]:
            buy_signals.append((df.index[i], df['close'][i]))
        elif df['close'][i] < df['SMA_5'][i] and df['close'][i-1] >= df['SMA_5'][i-1]:
            sell_signals.append((df.index[i], df['close'][i]))

    return buy_signals, sell_signals

# 通知使用者
def notify_user(message):
    notifier.show_toast("股票交易提醒", message, duration=10)

# 計算投資報酬率
def calculate_roi(buy_price, sell_price):
    roi = (sell_price - buy_price) / buy_price * 100
    return roi

# 保存交易紀錄
def save_trade_record(stock_code, action, price, roi=None):
    record = {
        '日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '股票代碼': stock_code,
        '動作': action,
        '價格': price,
        '投資報酬率': roi if roi is not None else ''
    }
    
    file_path = 'D:\\TradingData\\交易紀錄.xlsx'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
    else:
        df = pd.DataFrame(columns=['日期', '股票代碼', '動作', '價格', '投資報酬率'])
    
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_excel(file_path, index=False)

# 監控股票價格
def monitor_stock(stock_code):
    buy_price = None

    while True:
        if len(realtime_data) < 5:
            time.sleep(60)  # 等待足夠的即時資料
            continue
        
        df = pd.DataFrame(realtime_data)
        df.set_index('datetime', inplace=True)
        
        highest_price = df['high'].max()
        lowest_price = df['low'].min()
        fib_levels = calculate_fibonacci_levels(highest_price, lowest_price)

        buy_signals, sell_signals = identify_trade_signals(df)
        current_price = df['close'].iloc[-1]
        print(f"當前價格: {current_price}")

        if buy_price is None and current_price <= fib_levels['Level_0.618']:
            buy_price = current_price
            notify_user(f"股票 {stock_code} 已達買點，當前價格: {current_price}")
            save_trade_record(stock_code, '買入', current_price)

        if buy_price is not None and current_price >= fib_levels['Level_0.382']:
            sell_price = current_price
            roi = calculate_roi(buy_price, sell_price)
            notify_user(f"股票 {stock_code} 已達賣點，當前價格: {current_price}，投資報酬率: {roi:.2f}%")
            save_trade_record(stock_code, '賣出', current_price, roi)
            buy_price = None  # Reset buy price after selling

        if current_price < fib_levels['Level_1']:
            notify_user(f"股票 {stock_code} 可能繼續下探，當前價格: {current_price}")

        time.sleep(60)  # 每分鐘檢查一次

def connect_db():
    conn = pymssql.connect(
        server = '127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn

def get_stock_data_from_db(conn, stock_code, start_date, end_date):
    query = f"""
    SELECT distinct date, open_price, high_price, low_price, close_price, volume
    FROM stock_data
    WHERE stock_id = '{stock_code}' AND date >= '{start_date}' AND date <= '{end_date}'
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_stock_data(stock_code, start_date, end_date):
    conn = connect_db()
    df = get_stock_data_from_db(conn, stock_code, start_date, end_date)
    return df

def get_wave_extremes(stock_code):
    start_date = '2024-01-01'
    end_date = '2024-12-26'
    df = get_stock_data(stock_code, start_date, end_date)
    
    # 初始化變量
    waves = []
    wave_start_idx = 0
    prev_low = df.iloc[0]['low_price']
    
    # 分析波段
    for i in range(1, len(df)):
        current_low = df.iloc[i]['low_price']
        
        # 如果當前最低價高於前一個最低價，表示前一個波段結束
        if current_low > prev_low:
            # 計算前一個波段的最高價
            segment = df.iloc[wave_start_idx:i]
            wave_high = segment['high_price'].max()
            wave_high_date = segment[segment['high_price'] == wave_high]['date'].iloc[0]
            
            # 記錄波段資訊
            waves.append({
                'wave_start_date': df.iloc[wave_start_idx]['date'],
                'wave_end_date': df.iloc[i-1]['date'],
                'low_price': prev_low,
                'high_price': wave_high,
                'high_price_date': wave_high_date
            })
            
            # 更新新波段的起始位置
            wave_start_idx = i
        
        prev_low = current_low
    
    # 處理最後一個波段
    segment = df.iloc[wave_start_idx:]
    wave_high = segment['high_price'].max()
    wave_high_date = segment[segment['high_price'] == wave_high]['date'].iloc[0]
    
    waves.append({
        'wave_start_date': df.iloc[wave_start_idx]['date'],
        'wave_end_date': df.iloc[-1]['date'],
        'low_price': prev_low,
        'high_price': wave_high,
        'high_price_date': wave_high_date
    })
    
    # 轉換為DataFrame
    wave_extremes = pd.DataFrame(waves)
    
    print("\n波段分析：")
    for i, wave in wave_extremes.iterrows():
        print(f"\n波段 {i+1}:")
        print(f"波段起始日: {wave['wave_start_date'].strftime('%Y-%m-%d')}")
        print(f"波段結束日: {wave['wave_end_date'].strftime('%Y-%m-%d')}")
        print(f"波段最低價: {wave['low_price']:.2f}")
        print(f"波段最高價: {wave['high_price']:.2f}")
        print(f"最高價日期: {wave['high_price_date'].strftime('%Y-%m-%d')}")
    
    return wave_extremes
# 主函數
def main(stock_code):
    get_wave_extremes(stock_code)
    # subscribe_realtime_data(stock_code)
    # try:
    #     monitor_stock(stock_code)
    # finally:
    #     unsubscribe_realtime_data(stock_code)

if __name__ == "__main__":
    stock_code = '3013'  # 替換為您想要查詢的股票代碼
    main(stock_code)
