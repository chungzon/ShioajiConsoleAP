import pymssql
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta

class RealtimeMonitorModel:


    def __init__(self, api):
        self.api = api
        
    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn
    
    # 訂閱即時行情
    def subscribe_stock(self, contract, interval_minutes):
        # 設定回調函數，處理即時行情資料
        def quote_callback(exchange, quote):
            # 取得當前時間
            current_time = datetime.now()
            # 計算下次取得資料的時間點
            next_time = (current_time + timedelta(minutes=interval_minutes)).replace(second=0, microsecond=0)
            # 打印行情資料
            print(f"Exchange: {exchange}, Quote: {quote}")
            # 等待到下一次取得資料的時間點
            while datetime.now() < next_time:
                time.sleep(1)

        # 設定回調函數
        self.api.quote.set_on_tick_stk_v1_callback(quote_callback)
        # 訂閱行情資料
        self.api.quote.subscribe(
            contract,
            quote_type=sj.constant.QuoteType.Tick,
            version=sj.constant.QuoteVersion.v1
        )
        
    #測試資料
    def get_stock_kbar_from_db(self, stock_id, start_date, end_date):
        conn = self.connect_db()
        query = f"""
        SELECT ts, Open_Price, High, Low, Close_Price, Volume
        FROM Kbars
        WHERE stock_id = {stock_id} AND ts >= '{start_date}' AND ts <= DATEADD(day, 1, '{end_date}') ORDER BY ts ASC
        """
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%H:%M:%S')
        df['date'] = df['ts']
        conn.close()
        return df
    
    def find_peaks_troughs_v34(self, df, stock_id, lastest_close_price):
        segments = []
        ratios = [0.618, 1]
        columns = [f'Ratio_0.618', f'現價-0.618', f'Ratio_1', f'頸線', f'Head']
    
        i = 0
        while i < len(df):
            max_value = df['High'].iloc[i]
            max_date = df['date'].iloc[i]
        
            j = i + 1
            while j < len(df) and df['High'].iloc[j] >= max_value:
                max_value = df['High'].iloc[j]
                max_date = df['date'].iloc[j]
                j += 1
        
            if j < len(df):
                min_value = df['Low'].iloc[j]
                min_date = df['date'].iloc[j]
            else:
                min_value = df['Low'].iloc[j-1]
                min_date = df['date'].iloc[j-1]
        
            k = j
            while k < len(df) and df['Low'].iloc[k] <= min_value:
                min_value = df['Low'].iloc[k]
                min_date = df['date'].iloc[k]
                k += 1
        
            if max_value > min_value:
                segment = [max_date, max_value, min_date, min_value]
                for ratio in ratios:
                    value = ((max_value - min_value) / 2 * ratio + min_value).round(2);
                    segment.append(value)
                    result = (value-lastest_close_price).round(2)
                    segment.append(result)
                head = (max_value - lastest_close_price).round(2)
                segment.append(head)
                segments.append(segment)
                
        
            i = k
    
        return pd.DataFrame(segments, columns=['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value'] + columns)
    
    def find_peaks_troughs_v34_real(self, df, stock_id, lastest_close_price):
        segments = []
        ratios = [0.618, 1]
        columns = [f'Ratio_0.618', f'現價-0.618', f'Ratio_1', f'頸線', f'Head']
    
        i = 0
        while i < len(df):
            max_value = df['High'].iloc[i]
            max_date = df['date'].iloc[i]
        
            j = i + 1
            while j < len(df) and df['High'].iloc[j] >= max_value:
                max_value = df['High'].iloc[j]
                max_date = df['date'].iloc[j]
                j += 1
        
            if j < len(df):
                min_value = df['Low'].iloc[j]
                min_date = df['date'].iloc[j]
            else:
                min_value = df['Low'].iloc[j-1]
                min_date = df['date'].iloc[j-1]
        
            k = j
            while k < len(df) and df['Low'].iloc[k] <= min_value:
                min_value = df['Low'].iloc[k]
                min_date = df['date'].iloc[k]
                k += 1
        
            if max_value[0] > min_value[0]:
                segment = [max_date, max_value, min_date, min_value]
                for ratio in ratios:
                    value = round(((max_value[0] - min_value[0]) / 2 * ratio + min_value[0]), 2);
                    segment.append(value)
                    result = (value-lastest_close_price).round(2)
                    segment.append(result)
                head = (max_value[0] - lastest_close_price).round(2)
                segment.append(head)
                segments.append(segment)
                
        
            i = k
    
        return pd.DataFrame(segments, columns=['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value'] + columns)
    
     # 獲取最新收盤價
    def get_latest_close_price(self, stock_code):
        contract = self.api.Contracts.Stocks[stock_code]
        snapshot = self.api.snapshots([contract])
        latest_close = snapshot[0].close
        return latest_close

    # 計算移動平均
    def calculate_moving_average(self, prices, window):
        return prices.rolling(window=window).mean()

    def calculate_ma_values(self, close_prices, k_type='1min'):
        multiplier = 1 if k_type == '1min' else 3 if k_type == '3min' else 5  # 根據K線類型決定倍數
    
        ma_5t = self.calculate_moving_average(close_prices, 5 * multiplier).iloc[-1]
        ma_10t = self.calculate_moving_average(close_prices, 10 * multiplier).iloc[-1]
        ma_20t = self.calculate_moving_average(close_prices, 20 * multiplier).iloc[-1]
        ma_60t = self.calculate_moving_average(close_prices, 60 * multiplier).iloc[-1]
        ma_120t = self.calculate_moving_average(close_prices, 120 * multiplier).iloc[-1]

        return round(ma_5t, 2), round(ma_10t, 2), round(ma_20t, 2), round(ma_60t, 2), round(ma_120t, 2)


    
    # 從資料庫中獲取每日收盤價
    def get_daily_close_prices_from_db(self, stock_code, days):
        conn = self.connect_db()
        query = f"""
        SELECT ts AS date, close_price
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY CONVERT(date, ts) ORDER BY ts DESC) AS rn
            FROM KBars
            WHERE stock_id = '{stock_code}'
        ) AS sub
        WHERE sub.rn = 1
        ORDER BY date DESC
        OFFSET 0 ROWS
        FETCH NEXT 266 ROWS ONLY
        """
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.sort_index()  # 按日期排序
        return df['close_price']
    
    # 計算周均線
    def calculate_weekly_average(self, prices, window):
        weekly_prices = prices.resample('W').last()
        return self.calculate_moving_average(weekly_prices, window)

    # 計算月均線
    def calculate_monthly_average(self, prices, window):
        monthly_prices = prices.resample('M').last()
        return self.calculate_moving_average(monthly_prices, window)
    
    # 漲停價、跌停價
    def get_stock_limit_prices(self, sotckid):
        contract = self.api.Contracts.Stocks[sotckid]
        return contract['limit_up'], contract['limit_down']

    def get_realtime_snapshot(self, stock_id):
        contracts = [self.api.Contracts.Stocks[stock_id]]
        snapshots = self.api.snapshots(contracts)
        return snapshots
    
    def snapshots_to_dataframe(self, snapshots):
        data = []
        # 官方寫法
        # df = pd.DataFrame(s.__dict__ for s in snapshots)
        # df.ts = pd.to_datetime(df.ts)
        for snap in snapshots:
            data.append({
                'date': pd.to_datetime(snap.ts).strftime('%H:%M:%S'),  # 將 nanosecond timestamp 轉換為 datetime
                'Open_Price': snap.open,
                'High': snap.high,
                'Low': snap.low,
                'Close_Price': snap.close,
                'Volume': snap.volume,
                'Total_Volume': snap.total_volume,
                'Amount': snap.amount,
                'Total_Amount': snap.total_amount,
                'Buy_Price': snap.buy_price,
                'Buy_Volume': snap.buy_volume,
                'Sell_Price': snap.sell_price,
                'Sell_Volume': snap.sell_volume,
                'Stock_ID': snap.code,
                'Exchange': snap.exchange,
                'ts': pd.to_datetime(snap.ts).strftime('%H:%M:%S'),
            })

        df = pd.DataFrame(data)
        return df