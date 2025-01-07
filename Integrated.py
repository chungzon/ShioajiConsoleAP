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

def find_peaks_troughs_v34_small(df):
    peaks = []
    troughs = []
    
    # 第一階段：找出所有波段
    wave_start_idx = 0
    current_wave_high = df.iloc[0]['high_price']
    current_wave_high_date = df.iloc[0]['date']
    current_wave_low = df.iloc[0]['low_price']
    current_wave_low_date = df.iloc[0]['date']
    
    for i in range(1, len(df)):
        today_high = df.iloc[i]['high_price']
        today_low = df.iloc[i]['low_price']
        yesterday_low = df.iloc[i-1]['low_price']
        
        # 如果今天最低價比前一天高，表示新波段開始
        if today_low > yesterday_low:
            # 記錄前一個波段
            if i > 1:  # 確保不是第一天
                troughs.append({
                    'date': current_wave_low_date,
                    'price': current_wave_low,
                    'idx': wave_start_idx
                })
                
                peaks.append({
                    'date': current_wave_high_date,
                    'price': current_wave_high,
                    'idx': df[df['date'] == current_wave_high_date].index[0]
                })
            
            # 開始新波段
            wave_start_idx = i-1  # 從前一天開始算起
            current_wave_high = today_high
            current_wave_high_date = df.iloc[i]['date']
            current_wave_low = today_low
            current_wave_low_date = df.iloc[i]['date']
            
        else:
            # 更新當前波段的最高價和最低價
            if today_high > current_wave_high:
                current_wave_high = today_high
                current_wave_high_date = df.iloc[i]['date']
            if today_low < current_wave_low:
                current_wave_low = today_low
                current_wave_low_date = df.iloc[i]['date']
    
    # 處理最後一個波段
    troughs.append({
        'date': current_wave_low_date,
        'price': current_wave_low,
        'idx': wave_start_idx
    })
    
    peaks.append({
        'date': current_wave_high_date,
        'price': current_wave_high,
        'idx': df[df['date'] == current_wave_high_date].index[0]
    })
    
    # 轉換為DataFrame並排序
    peaks_df = pd.DataFrame(peaks).sort_values('idx').reset_index(drop=True)
    troughs_df = pd.DataFrame(troughs).sort_values('idx').reset_index(drop=True)
    
    # 第二階段：整理波段
    merged_waves = []
    for i in range(len(peaks_df)):
        merged_waves.append({
            'wave_start_date': troughs_df.iloc[i]['date'],
            'wave_end_date': peaks_df.iloc[i]['date'],
            'high_price': peaks_df.iloc[i]['price'],
            'high_price_date': peaks_df.iloc[i]['date'],
            'low_price': troughs_df.iloc[i]['price'],
            'low_price_date': troughs_df.iloc[i]['date']
        })
    
    # 轉換為DataFrame
    merged_waves_df = pd.DataFrame(merged_waves)
    
    # 列印整理後的波段資訊
    print("\n整理後的波段分析：")
    for i, wave in merged_waves_df.iterrows():
        print(f"\n第 {i+1} 個波段:")
        print(f"波段期間: {wave['wave_start_date'].strftime('%Y-%m-%d')} 到 {wave['wave_end_date'].strftime('%Y-%m-%d')}")
        print(f"最高價: {wave['high_price']:.2f} ({wave['high_price_date'].strftime('%Y-%m-%d')})")
        print(f"最低價: {wave['low_price']:.2f} ({wave['low_price_date'].strftime('%Y-%m-%d')})")
        print(f"漲幅: {((wave['high_price'] - wave['low_price']) / wave['low_price'] * 100):.2f}%")
    
    return peaks_df, troughs_df, merged_waves_df

# 主函數
def main(stock_code):
    # get_wave_extremes(stock_code)
    df = get_stock_data(stock_code, '2024-12-08', '2025-01-07')
    find_peaks_troughs_v34_small(df)
    # subscribe_realtime_data(stock_code)
    # try:
    #     monitor_stock(stock_code)
    # finally:
    #     unsubscribe_realtime_data(stock_code)

if __name__ == "__main__":
    stock_code = '8047'  # 替換為您想要查詢的股票代碼
    main(stock_code)
