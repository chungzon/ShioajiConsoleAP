import numpy as np
import pymssql
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta
import os
from common.Math import Math
from resource.Resources import get_resource_path, ResourceFileNames

class BaseModel:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resource_dir = os.path.join(current_dir, '..', 'resource')
    file_path =  os.path.join(resource_dir, 'stock_top.xlsx')

    def __init__(self, api):
        self.api = api
        # 獲取當前文件的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 構建相對路徑到resource目錄
        resource_dir = os.path.join(current_dir, '..', 'resource')
        self.file_path = os.path.join(resource_dir, 'tw_all_stocks.csv')
        
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
        SELECT DISTINCT ts, Open_Price, High, Low, Close_Price, Volume
        FROM Kbars
        WHERE stock_id = {stock_id} AND ts >= '{start_date}' AND ts <= DATEADD(day, 1, '{end_date}') ORDER BY ts ASC
        """
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['date'] = df['ts']
        conn.close()
        return df

    # 分K資料
    def get_stock_kbar_from_db_top300(self, stock_id, recent_end_date=None):
        conn = self.connect_db()
        if recent_end_date is None:
            query = f"""
            SELECT DISTINCT TOP 300 ts, Open_Price, High, Low, Close_Price, Volume
            FROM Kbars
            WHERE stock_id = '{stock_id}' ORDER BY ts DESC
            """
        else:
            # recent_end_date 往前推30天
            recent_end_date = pd.to_datetime(recent_end_date) + pd.Timedelta(days=1)
            query = f"""
            SELECT DISTINCT TOP 300 ts, Open_Price, High, Low, Close_Price, Volume
            FROM Kbars
            WHERE stock_id = '{stock_id}' AND ts <= '{recent_end_date}' ORDER BY ts DESC
            """
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d %H:%M:%S')
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
    
     # 獲取最新收盤價
    def get_latest_close_price(self, stock_code):
        contract = self.api.Contracts.Stocks[str(stock_code)]
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
    def get_daily_close_prices_from_db(self, stock_code, days=365):
        conn = self.connect_db()
        query = f"""
        SELECT DISTINCT TOP {days} date, close_price
        FROM stock_data
        WHERE stock_id = '{stock_code}'
        ORDER BY date DESC
        """
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.sort_index()  # 按日期排序
        return df['close_price']

    # 從資料庫中獲取某個日期之前包含該日期  每日收盤價
    def get_daily_close_prices_from_db_by_date(self, stock_code, date):
        conn = self.connect_db()
        query = f"""
        SELECT DISTINCT date, close_price
        FROM stock_data
        WHERE stock_id = '{stock_code}' AND date <= '{date}'
        ORDER BY date DESC
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
        
    # 商品名稱
    def get_stock_name(self, sotckid):
        try:
            contract = self.api.Contracts.Stocks[str(sotckid)]
            return contract['name']
        except Exception as e:
            print(f"取得股票名稱時發生錯誤: {e}")
            return sotckid
    
    def get_kbars_data(self, stock_id, date):
        contract = self.api.Contracts.Stocks[stock_id]
        kbars = self.api.kbars(
            contract=contract,
            start=date.strftime("%Y-%m-%d"),
            end=date.strftime("%Y-%m-%d")
        )
        df = pd.DataFrame({**kbars})
        df.ts = pd.to_datetime(df.ts)  # 將時間戳轉換為datetime
        return df

    def insert_kbars(self, kbars_df, stock_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        for _, row in kbars_df.iterrows():
            cursor.execute("""
                INSERT INTO Kbars (stock_id, ts, open_price, high, low, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (stock_id, row['ts'], row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
        conn.commit()
        cursor.close()
        conn.close()

    # 定義函數找出每個波段的最高價和最低價，並計算特定比例的價格
    def find_peaks_troughs_v34_small(self, stock_id, df, latest_close_price, recent_end_date=None):
        segments = []
        ratios = [0, 0.191, 0.382, 0.5, 0.618, 0.809, 1, 1.191, 1.382, 1.5, 1.618, 1.809, 2, 2.191, 2.382, 2.5, 2.618, 2.809, 3, 
                  3.191, 3.382, 3.5, 3.618, 3.809, 4, 4.191, 4.382, 4.5, 4.618, 4.809, 5, 5.191, 5.382, 5.5, 5.618, 5.809, 6]
        ratio_columns = [f'Ratio_{ratio}' for ratio in ratios]
        append_columns = [f'spread_ratio', f'latest_close_price', f'latest_close_price-0.191_ratio', f'latest_close_price-0.618_ratio', f'latest_close_prices', f'latest_dates']
        cdp_columns = [f'CDP', 'NH', 'NL', 'AH', 'AL']

        latest_close_price = df['close_price'].iloc[-1]
        # 取得SMA值
        k15_sma_values = self.calculate_k15_sma(stock_id, recent_end_date)
        sma_values, weekly_sma_values, monthly_sma_values, latest_close_prices, latest_dates = self.calculate_sma(stock_id, recent_end_date)

        periods = [5, 10, 20, 60, 120, 'strong', 'weak']
        sma_periods = [5, 10, 20, 60, 120, '5_diff', '10_diff', '20_diff', '60_diff', '120_diff']
        sma_columns = [f'sma_{period}' for period in sma_periods]
        weekly_sma_periods = [5, 10, 20, 60, 120, '5_diff', '10_diff', '20_diff', '60_diff', '120_diff']
        weekly_sma_columns = [f'weekly_sma_{period}' for period in weekly_sma_periods]
        monthly_sma_periods = [5, 10, 20, 60, 120, '5_diff', '10_diff', '20_diff', '60_diff', '120_diff']
        monthly_sma_columns = [f'monthly_sma_{period}' for period in monthly_sma_periods]
        k15_sma_columns = [f'15min_sma_{period}' for period in periods]

        # 計算CDP
        try:
            CDP = Math.calculate_CDP(
                df['high_price'].iloc[-1], 
                df['low_price'].iloc[-1], 
                df['close_price'].iloc[-1]
            )
            CDP, NL, NH, AL, AH = Math.calculate_CDP_5_values(CDP, df['high_price'].iloc[-1], df['low_price'].iloc[-1])
        except:
            CDP = NL = NH = AL = AH = np.nan

        # 第一階段：找出所有波段
        peaks = []
        troughs = []
        
        wave_start_idx = 0
        current_wave_high = df.iloc[0]['high_price']
        current_wave_high_date = df.iloc[0]['date']
        current_wave_low = df.iloc[0]['low_price']
        current_wave_low_date = df.iloc[0]['date']
        last_wave_start_idx = 0  # 記錄波段起始位置
        
        # 從第二天開始分析
        for i in range(1, len(df)):
            today_high = df.iloc[i]['high_price']
            today_low = df.iloc[i]['low_price']
            yesterday_low = df.iloc[i-1]['low_price']
            
            if today_low > yesterday_low:
                if i > 1:
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
                
                wave_start_idx = i-1
                last_wave_start_idx = i  # 記錄新波段的起始位置
                current_wave_high = today_high
                current_wave_high_date = df.iloc[i]['date']
                current_wave_low = today_low
                current_wave_low_date = df.iloc[i]['date']
            else:
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

        # 檢查最後一個波段是否只有一筆資料
        if len(df) - last_wave_start_idx == 1:  # 如果最後一個波段只有一筆資料
            if len(peaks_df) > 1:  # 確保有前一個波段
                last_data = df.iloc[-1]
                prev_data = df.iloc[-2]
                prev_peak_price = peaks_df.iloc[-2]['price']
                
                # 檢查條件：最高價是否高於前一波段最高價或最低價是否低於前一天最低價
                if not (last_data['high_price'] > prev_peak_price or 
                       last_data['low_price'] < prev_data['low_price']):
                    # 合併到前一個波段
                    peaks_df = peaks_df.iloc[:-1]
                    troughs_df = troughs_df.iloc[:-1]
                    
                    # 更新前一個波段的資訊
                    if last_data['high_price'] > peaks_df.iloc[-1]['price']:
                        peaks_df.at[len(peaks_df)-1, 'price'] = last_data['high_price']
                        peaks_df.at[len(peaks_df)-1, 'date'] = last_data['date']
                    if last_data['low_price'] < troughs_df.iloc[-1]['price']:
                        troughs_df.at[len(troughs_df)-1, 'price'] = last_data['low_price']
                        troughs_df.at[len(troughs_df)-1, 'date'] = last_data['date']

        # 第二階段：整理波段並計算其他指標
        for i in range(len(peaks_df)):
            current_high = peaks_df.iloc[i]['price']
            current_high_date = peaks_df.iloc[i]['date']
            start_date = troughs_df.iloc[i]['date']
            start_idx = troughs_df.iloc[i]['idx']
            end_idx = peaks_df.iloc[i]['idx']
            
            current_low = troughs_df.iloc[i]['price']
            current_low_date = troughs_df.iloc[i]['date']

            # 建立波段資料
            segment_data = []
            
            # 1. 基本波段資訊
            segment_data.extend([
                current_high_date,
                current_high,
                current_low_date,
                current_low,
                start_date,
                df.iloc[end_idx]['date']
            ])
            
            # 2. 比例價格
            ratio_prices = []
            for ratio in ratios:
                ratio_price = Math.calculate_ratio_value(current_high, current_low, ratio)
                ratio_prices.append(ratio_price)
            segment_data.extend(ratio_prices)
            
            # 3. 附加資訊
            spread_ratio = (current_high - ratio_prices[4]) / current_high
            latest_close_price_0191_ratio = (latest_close_price - ratio_prices[1]) / latest_close_price
            latest_close_price_0618_ratio = (latest_close_price - ratio_prices[4]) / latest_close_price
            
            segment_data.extend([
                spread_ratio,
                latest_close_price,
                latest_close_price_0191_ratio,
                latest_close_price_0618_ratio,
                latest_close_prices,
                latest_dates
            ])
            
            # 4. SMA值
            sma_diff_values = []
            

            segment_data.extend(sma_values)
            segment_data.extend(weekly_sma_values)
            segment_data.extend(monthly_sma_values)
            segment_data.extend(k15_sma_values)
            
            # 5. CDP值
            segment_data.extend([CDP, NH, NL, AH, AL])
            
            segments.append(segment_data)

        
        # 創建最終的DataFrame
        columns = (['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value', 'Start_Date', 'End_Date'] + 
                  ratio_columns + append_columns + sma_columns + 
                  weekly_sma_columns + monthly_sma_columns + 
                  k15_sma_columns + cdp_columns)
        
        result_df = pd.DataFrame(segments, columns=columns)
        
        return result_df

    def analyze_data(self, stock_id, start_date, end_date, save_path):
        if not stock_id or not start_date or not end_date or not save_path:
            raise Exception("下載失敗")
        df = self.get_stock_data(stock_id, start_date, end_date)
        latest_close_price = self.get_latest_close_price(stock_id)
        # daily_high_low = df.groupby('date').agg({'High': 'max', 'Low': 'min'}).reset_index()
        peak_trough_df = self.find_peaks_troughs_v34_small(stock_id, df, latest_close_price)
        # 刪除不需要的列
        peak_trough_df = peak_trough_df.drop(columns=['spread_ratio', 'latest_close_price', 'latest_close_price-0.618_ratio'])

        # 四捨五入至小數點以下兩位，不足補0
        peak_trough_df['Ratio_0.618'] = peak_trough_df['Ratio_0.618'].round(2)
        peak_trough_df['Ratio_1'] = peak_trough_df['Ratio_1'].round(2)
    
        #取得最後一0.618價格
        last_ratio_0_618 = peak_trough_df['Ratio_0.618'].iloc[-1]

        peak_trough_df['現價'] = round(latest_close_price, 2)

        # 四捨五入 Max_Value 和 Min_Value 欄位並補0
        peak_trough_df['Max_Value'] = peak_trough_df['Max_Value'].round(2)
        peak_trough_df['Min_Value'] = peak_trough_df['Min_Value'].round(2)

        # 計算現價-0.618，Ratio_0.618 - 現價
        peak_trough_df['現價-0.618'] = (peak_trough_df['Ratio_0.618'] - peak_trough_df['現價']).round(2)

        # 計算Head欄位，Max_Value - 現價
        peak_trough_df['Head'] = (peak_trough_df['Max_Value'] - peak_trough_df['現價']).round(2)

        # 計算頸線欄位，Ratio_1 - 現價
        peak_trough_df['頸線'] = (peak_trough_df['Ratio_1'] - peak_trough_df['現價']).round(2)

        # 找出 Max_Value 和 Min_Value 欄位的最大值和最小值
        max_max_value = peak_trough_df['Max_Value'].max()
        min_min_value = peak_trough_df['Min_Value'].min()

        # 獲取最高價的日期
        max_value_index = peak_trough_df['Max_Value'].idxmax()
        max_value_date = peak_trough_df.loc[max_value_index, 'Max_Date']
        # 在最高價之後找最低價
        min_after_max_series = peak_trough_df.loc[max_value_index:, 'Min_Value']
        min_value_after_max = min_after_max_series.min()
        min_after_max_index = min_after_max_series.idxmin()

        # 獲取最低價的日期
        min_value_date = peak_trough_df.loc[min_after_max_index, 'Min_Date']

        # 計算 ratio_0.618 和 ratio_1
        ratio_0618_after_max = Math.calculate_ratio_0618(max_max_value, min_value_after_max)
        ratio_1_after_max = Math.calculate_ratio_1(max_max_value, min_value_after_max)

        # 計算前面Max(Max_Value)-Min(Min_Value)/2*0.618+Min(Min_Value)的值，並四捨五入至小數點以下兩位
        ratio_0_618_value = (max_max_value - min_min_value) / 2 * 0.618 + min_min_value
        ratio_0_618_value = round(ratio_0_618_value, 2)

        # 計算前面Max(Max_Value)-Min(Min_Value)/2*1+Min(Min_Value)的值，並四捨五入至小數點以下兩位
        ratio_1_value = (max_max_value - min_min_value) / 2 * 1 + min_min_value
        ratio_1_value = round(ratio_1_value, 2)

        # 新增一列填入 Max(Max_Value)、Min(Min_Value)、Ratio_0.618 和 Ratio_1 的值
        new_row = pd.DataFrame({
            'Max_Date': [None],
            'Max_Value': [max_max_value],
            'Min_Date': [None],
            'Min_Value': [min_value_after_max],
            'Ratio_0.618': [ratio_0618_after_max],
            'Ratio_1': [ratio_1_after_max],
            '現價': [None],
            '現價-0.618': [None],
            'Head': [None],
            '頸線': [None]
        })
        peak_trough_df = pd.concat([peak_trough_df, new_row], ignore_index=True)

        # 排除最後一列進行排序
        sorted_df = peak_trough_df.iloc[:-1]

        # 計算排序欄位
        peak_trough_df['現價-0.618_Sort'] = sorted_df['現價-0.618'].sort_values().tolist() + [None]
        peak_trough_df['Head_Sort'] = sorted_df['Head'].sort_values().tolist() + [None]
        peak_trough_df['頸線_Sort'] = sorted_df['頸線'].sort_values().tolist() + [None]
        peak_trough_df['max由小到大'] = sorted_df['Max_Value'].sort_values().tolist() + [None]
        peak_trough_df['Radio_1_Sort'] = sorted_df['Ratio_1'].sort_values().tolist() + [None]
        peak_trough_df['Radio_0.618_Sort'] = sorted_df['Ratio_0.618'].sort_values().tolist() + [None]

        # 新增流水號欄位
        peak_trough_df['No'] = range(1, len(peak_trough_df) + 1)

        # 將 No 欄位移到 Max_Value 前
        cols = list(peak_trough_df.columns)
        cols.insert(0, cols.pop(cols.index('No')))
        peak_trough_df = peak_trough_df[cols]

        # 獲取每日收盤價
        close_prices = self.get_daily_close_prices_from_db(stock_id, 120)
    
        # 計算日均線的移動平均
        sma_values = [
            round(self.calculate_moving_average(close_prices, 5).iloc[-1], 2),
            round(self.calculate_moving_average(close_prices, 10).iloc[-1], 2),
            round(self.calculate_moving_average(close_prices, 20).iloc[-1], 2),
            round(self.calculate_moving_average(close_prices, 60).iloc[-1], 2),
            round(self.calculate_moving_average(close_prices, 120).iloc[-1], 2),
        ]

        # 計算周均線的移動平均
        weekly_sma_values = [
            round(self.calculate_weekly_average(close_prices, 5).iloc[-1], 2),
            round(self.calculate_weekly_average(close_prices, 10).iloc[-1], 2),
            round(self.calculate_weekly_average(close_prices, 20).iloc[-1], 2),
            round(self.calculate_weekly_average(close_prices, 60).iloc[-1], 2),
            round(self.calculate_weekly_average(close_prices, 120).iloc[-1], 2),
        ]

        # 計算月均線的移動平均
        monthly_sma_values = [
            round(self.calculate_monthly_average(close_prices, 5).iloc[-1], 2),
            round(self.calculate_monthly_average(close_prices, 10).iloc[-1], 2),
            round(self.calculate_monthly_average(close_prices, 20).iloc[-1], 2),
            round(self.calculate_monthly_average(close_prices, 60).iloc[-1], 2),
            round(self.calculate_monthly_average(close_prices, 120).iloc[-1], 2),
        ]
        
        # 設定儲存路徑和檔名
        # if not os.path.exists(save_path):
        #     os.makedirs(save_path)
            
        stock_name = self.get_stock_name(stock_id)
        if stock_name is not None:
            stock_name = stock_name.replace('*', '-')
    
        file_name = f"{stock_id}({stock_name})_{start_date}_to_{end_date}.xlsx"
        file_path = os.path.join(save_path, file_name)
        self.save_to_excel(peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, file_path)
        

    def get_stock_data(self, stock_id, start_date, end_date):
        try:
            # 建立資料庫連接
            conn = self.connect_db()

            # 查詢語句
            query = f"""
            SELECT DISTINCT stock_id, date, high_price, low_price 
            FROM stock_data
            WHERE stock_id = '{stock_id}'
            AND date >= '{start_date}'
            AND date <= '{end_date}'
            ORDER BY date ASC
            """

            # 執行查詢並讀取數據到 DataFrame
            df = pd.read_sql(query, conn)

            # 關閉連接
            conn.close()

            return df

        except Exception as e:
            print(f"讀取資料時發生錯誤: {e}")
            return None


        # 儲存資料到Excel
    def save_to_excel(self, peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, output_file_path):
        with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet("Peaks_and_Troughs")
            percent_fmt = workbook.add_format({'num_format': '0.00%'})

            # 儲存波段資料
            peak_trough_df.to_excel(writer, sheet_name='Peaks_and_Troughs', index=False, startrow=0)

            # 確定開始寫入日均線的行數
            start_row = len(peak_trough_df) + 5
        
            worksheet.write(start_row - 1, 0, latest_close_price)

            # 設定日均線表格標題
            headers = ["日均線", "", "", "", "收", "買點", "", "", "", "日均線"]
            worksheet.write_row(start_row, 0, headers)

            # 合併第5欄位和第6欄位的第1列和第2列資料格
            worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
            worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")
        
            #在日均線表格填入收盤價和買點價
            worksheet.write(start_row + 1, 4, latest_close_price)       
            worksheet.write(start_row + 1, 5, last_ratio_0_618)
        
            #買點價-收盤價
            diff_price = last_ratio_0_618 - latest_close_price

            # 合併第5欄位和第6欄位的第3列資料格
            worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")

            #填入日均線(買點價-收盤價)
            worksheet.write(start_row + 3, 4, diff_price)
        
            #計算(買點價-收盤價)/收盤價
            radio_diff_price = diff_price / latest_close_price
        
            # 合併第5欄位和第6欄位的第4列資料格
            worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
        
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)

            # 設定第一欄和第十欄的資料
            sma_labels = ["SMA5", "SMA10", "SMA20", "SMA60", "SMA120"]
            for i, label in enumerate(sma_labels):
                worksheet.write(start_row + i + 1, 0, label)
                worksheet.write(start_row + i + 1, 9, label)

            cell_green_format = workbook.add_format()
            cell_green_format.set_pattern(1)
            cell_green_format.set_bg_color('green')
            cell_red_format = workbook.add_format()
            cell_red_format.set_pattern(1)
            cell_red_format.set_bg_color('red')
            # 填入日均線計算值
            for i, value in enumerate(sma_values):
                worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
                worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
                if not pd.isna(value):
                    if latest_close_price > value:
                        worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
                    if  last_ratio_0_618 > value:
                        worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
                else:
                    print("")
            
            
            #填入數值分析
            if not pd.isna(sma_values[-1]):
                last_daily_sma120 = sma_values[-1]
                diff_last_daily_sma120 = (last_daily_sma120 - latest_close_price).round(2)
                radio_last_dailly_sma120 = (diff_last_daily_sma120 / latest_close_price).round(2)
                diff_sma_120_label = ["(", f"{diff_last_daily_sma120:.2f}", ", ", f"{radio_last_dailly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
                diff_last_daily_sma120 = (last_ratio_0_618 - last_daily_sma120).round(2)
                radio_last_dailly_sma120 = (diff_last_daily_sma120 / last_ratio_0_618).round(2)
                diff_sma_120_label = ["(", f"{diff_last_daily_sma120:.2f}", ", ", f"{radio_last_dailly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
            else:
                print("")   

            # 插入一行空行
            start_row += len(sma_labels) + 3
            worksheet.write_row(start_row, 0, [""] * len(headers))
            start_row += 1

            # 插入周均線表格
            headers = ["月均線", "", "", "", "收", "買點", "", "", "", "月均線"]
            worksheet.write_row(start_row, 0, headers)

            # 合併第5欄位和第6欄位的第1列和第2列資料格
            worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
            worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")

            worksheet.write(start_row + 1, 4, latest_close_price)       
            worksheet.write(start_row + 1, 5, last_ratio_0_618)

            # 合併第5欄位和第6欄位的第3列資料格
            worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
            #填入周均線(買點價-收盤價)
            worksheet.write(start_row + 3, 4, diff_price)
        
            # 合併第5欄位和第6欄位的第4列資料格
            worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
               
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)
        
            # 設定第一欄和第十欄的資料
            weekly_sma_labels = ["周SMA5", "周SMA10", "周SMA20", "周SMA60", "周SMA120"]
            for i, label in enumerate(weekly_sma_labels):
                worksheet.write(start_row + i + 1, 0, label)
                worksheet.write(start_row + i + 1, 9, label)

            # 填入周均線計算值
            for i, value in enumerate(weekly_sma_values):
                worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
                worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
                if not pd.isna(value):
                    if latest_close_price > value:
                        worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
                    if  last_ratio_0_618 > value:
                        worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
                else:
                    print("")
            
            #填入數值分析
            if not pd.isna(weekly_sma_values[-1]):
                last_weekly_sma120 = weekly_sma_values[-1]
                diff_last_weekly_sma120 = (last_weekly_sma120 - latest_close_price).round(2)
                radio_last_weekly_sma120 = (diff_last_weekly_sma120 / latest_close_price).round(2)
                diff_sma_120_label = ["(", f"{diff_last_weekly_sma120:.2f}", ", ", f"{radio_last_weekly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
                diff_last_weekly_sma120 = (last_ratio_0_618 - last_weekly_sma120).round(2)
                radio_last_weekly_sma120 = (diff_last_weekly_sma120 / last_ratio_0_618).round(2)
                diff_sma_120_label = ["(", f"{diff_last_weekly_sma120:.2f}", ", ", f"{radio_last_weekly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
            else:
                print("")

            # 插入一行空行
            start_row += len(weekly_sma_labels) + 2
            worksheet.write_row(start_row, 0, [""] * len(headers))
            start_row += 1

            # 插入月均線表格
            headers = ["月均線", "", "", "", "收", "買點", "", "", "", "月均線"]
            worksheet.write_row(start_row, 0, headers)

            # 合併第5欄位和第6欄位的第1列和第2列資料格
            worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
            worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")
        
            worksheet.write(start_row + 1, 4, latest_close_price)       
            worksheet.write(start_row + 1, 5, last_ratio_0_618)

            # 合併第5欄位和第6欄位的第3列資料格
            worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 3, 4, diff_price)
        
            # 合併第5欄位和第6欄位的第4列資料格
            worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
        
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)

            # 設定第一欄和第十欄的資料
            monthly_sma_labels = ["月SMA5", "月SMA10", "月SMA20", "月SMA60", "月SMA120"]
            for i, label in enumerate(monthly_sma_labels):
                worksheet.write(start_row + i + 1, 0, label)
                worksheet.write(start_row + i + 1, 9, label)

            # 填入月均線計算值
            for i, value in enumerate(monthly_sma_values):
                worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
                worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
                if not pd.isna(value):
                    if latest_close_price > value:
                        worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
                    if  last_ratio_0_618 > value:
                        worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
                else:
                    print("")
            
            #填入數值分析
            if not pd.isna(monthly_sma_values[-1]):
                last_monthly_sma120 = monthly_sma_values[-1]
                diff_last_monthly_sma120 = (last_monthly_sma120 - latest_close_price).round(2)
                radio_last_monthly_sma120 = (diff_last_monthly_sma120 / latest_close_price).round(2)
                diff_sma_120_label = ["(", f"{diff_last_monthly_sma120:.2f}", ", ", f"{radio_last_monthly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
                diff_last_monthly_sma120 = (last_ratio_0_618 - last_monthly_sma120).round(2)
                radio_last_monthly_sma120 = (diff_last_monthly_sma120 / last_ratio_0_618).round(2)
                diff_sma_120_label = ["(", f"{diff_last_monthly_sma120:.2f}", ", ", f"{radio_last_monthly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
            else:
                print("")
            
         # 設定數字格式
            num_format = workbook.add_format({'num_format': '0.00'})

            # 依列應用格式
            for col_num, col_name in enumerate(peak_trough_df.columns):
                if col_name not in ['Max_Date', 'Min_Date']:
                    worksheet.set_column(col_num, col_num, 12, num_format)

            # 新增折線圖和散佈圖
            line_chart1 = workbook.add_chart({'type': 'line'})
            scatter_chart1 = workbook.add_chart({'type': 'scatter'})
            line_chart2 = workbook.add_chart({'type': 'line'})
            scatter_chart2 = workbook.add_chart({'type': 'scatter'})

            # 設定圖表資料範圍
            max_row = len(peak_trough_df) + 1

            # custom_labels using P column data
            custom_labels_P = [
                {'value': f"='Peaks_and_Troughs'!$Q${i}", 'font': {'color': 'blue'}} for i in range(2, max_row)
            ]
        
            # custom_labels using N column data
            custom_labels_N = [
                {'value': f"='Peaks_and_Troughs'!$O${i}", 'font': {'color': 'red'}} for i in range(2, max_row)
            ]
        
            # custom_labels using O column data
            custom_labels_O = [
                {'value': f"='Peaks_and_Troughs'!$P${i}", 'font': {'color': 'green'}} for i in range(2, max_row)
            ]

            # 第一張圖表 - 排序後的數列
            line_chart1.add_series({
                'name': '現價-0.618_Sort',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$L$2:$L${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_P,
                    'position': 'below'
                }  # 添加自定義數值標籤
            })
            scatter_chart1.add_series({
                'name': 'Head_Sort',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$M$2:$M${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_N,
                    'position': 'above'
                }
            })
            scatter_chart1.add_series({
                'name': '頸線_Sort',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$N$2:$N${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_O
                }
            })

            # 設定第一張圖表標題和軸標籤
            line_chart1.set_title({'name': 'Stock Price Analysis (Sorted)'})
            line_chart1.set_x_axis({'name': 'Index'})
            line_chart1.set_y_axis({'name': 'Value'})
        
            # 插入第一張圖表到工作表
            line_chart1.combine(scatter_chart1)
            worksheet.insert_chart('S2', line_chart1)
        
            # custom_labels using E column data
            custom_labels_E = [
                {'value': f"='Peaks_and_Troughs'!$F${i}", 'font': {'color': 'blue'}, 'position': 'below'} for i in range(2, max_row)
            ]
        
            # custom_labels using B column data
            custom_labels_B = [
                {'value': f"='Peaks_and_Troughs'!$C${i}", 'font': {'color': 'red'}, 'position': 'above'} for i in range(2, max_row)
            ]
        
            # custom_labels using F column data
            custom_labels_F = [
                {'value': f"='Peaks_and_Troughs'!$G${i}", 'font': {'color': 'green'}} for i in range(2, max_row)
            ]

            # 第二張圖表 - 原始數列
            line_chart2.add_series({
                'name': '現價-0.618',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$I$2:$I${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_E,
                    'position': 'below'
                }
            })
            scatter_chart2.add_series({
                'name': 'Head',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$J$2:$J${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_B,
                    'position': 'above'
                }
            })
            scatter_chart2.add_series({
                'name': '頸線',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$K$2:$K${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_F
                }})
       
            # 設定第二張圖表標題和軸標籤
            line_chart2.set_title({'name': 'Stock Price Analysis (Original)'})
            line_chart2.set_x_axis({'name': 'Index'})
            line_chart2.set_y_axis({'name': 'Value'})
        
            line_chart1.set_x_axis({'num_format': ' ', 'line': {'color': 'red', 'width': 1.5}})
            line_chart2.set_x_axis({'num_format': ' ', 'line': {'color': 'red', 'width': 1.5}})

            # 插入第二張圖表到工作表
            line_chart2.combine(scatter_chart2)
            worksheet.insert_chart('S20', line_chart2)

            # 設定數字格式
            num_format = workbook.add_format({'num_format': '0.00'})

            # 設置日期格式
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

            # 依列應用格式
            for col_num, col_name in enumerate(peak_trough_df.columns):
                if col_name in ['Max_Date', 'Min_Date']:
                    # 為日期列設置更寬的寬度，例如 15 個字符寬
                    worksheet.set_column(col_num, col_num, 15, date_format)
                else:
                    worksheet.set_column(col_num, col_num, 12, num_format)  

        # messagebox.showinfo("完成", f"波段資料及均線資料已儲存到: {output_file_path}")

    def calculate_sma(self, stock_id, recent_end_date=None):
        if recent_end_date is None:
            daily_close_prices = self.get_daily_close_prices_from_db(stock_id, 30*120)
        else:
            daily_close_prices = self.get_daily_close_prices_from_db_by_date(stock_id, recent_end_date)
        # 获取最近5个收盘价和日期
        latest_close_prices = daily_close_prices.values[-5:].tolist()
        latest_dates = daily_close_prices.index[-5:].strftime('%Y-%m-%d').tolist()
        sma_values, weekly_sma_values, monthly_sma_values = Math.calculate_sma(daily_close_prices, recent_end_date)
        return sma_values, weekly_sma_values, monthly_sma_values, latest_close_prices, latest_dates

    def calculate_k15_sma(self, stock_id, recent_end_date=None):
        if recent_end_date is None:
            kbars = self.get_stock_kbar_from_db_top300(stock_id)
        else:
            kbars = self.get_stock_kbar_from_db_top300(stock_id, recent_end_date)

        if kbars.empty:
            return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
        
        # 轉換時間格式
        kbars['date'] = pd.to_datetime(kbars['date'])
        kbars = kbars.set_index('date')
        
        # 按日期分組
        daily_groups = kbars.groupby(kbars.index.date)
        
        # 存儲所有15K數據
        all_k15 = []
        
        for date, day_data in daily_groups:
            # 設定當天的起始時間（0900）
            start_time = pd.Timestamp(date).replace(hour=9, minute=15)
            
            # 重採樣，從0900開始每15分鐘
            k15_day = day_data.resample('15T', origin=start_time, closed='right', label='right').agg({
                'Open_Price': 'last',
                'High': 'last',
                'Low': 'last',
                'Close_Price': 'last',
                'Volume': 'sum'
            })
            
            all_k15.append(k15_day)
        
        # 合併所有日期的數據
        k15 = pd.concat(all_k15)

        # 計算15分鐘K線的SMA，處理數據不足的情況
        k15_5sma = k15['Close_Price'].rolling(window=5, min_periods=5).mean().iloc[-1]
        k15_10sma = k15['Close_Price'].rolling(window=10, min_periods=10).mean().iloc[-1]
        k15_20sma = k15['Close_Price'].rolling(window=20, min_periods=20).mean().iloc[-1]
        k15_60sma = k15['Close_Price'].rolling(window=60, min_periods=60).mean().iloc[-1]
        k15_120sma = k15['Close_Price'].rolling(window=120, min_periods=120).mean().iloc[-1]

        # 計算15分鐘K線的SMA
        k15_sma = [
            round(k15_5sma if not np.isnan(k15_5sma) else np.nan, 2),
            round(k15_10sma if not np.isnan(k15_10sma) else np.nan, 2),
            round(k15_20sma if not np.isnan(k15_20sma) else np.nan, 2),
            round(k15_60sma if not np.isnan(k15_60sma) else np.nan, 2),
            round(k15_120sma if not np.isnan(k15_120sma) else np.nan, 2)
        ]

        # 日期不為NULL
        if recent_end_date is not None:
            # 取出符合recent_end_date日期的資料
            recent_end_date = pd.to_datetime(recent_end_date)
            # 將時間格式轉換為2025-06-06 13:30:00
            recent_end_date = recent_end_date.strftime('%Y-%m-%d')
            
            # 從k15找出特定日期的資料，K15的index格式為2025-06-06 13:30:00，所以需要找出index的日期為2025-06-06的資料
            #date_data = k15[k15.index.strftime('%Y-%m-%d') == recent_end_date]
            
            
            if not k15.empty and len(k15) >= 20:
                # k15_stock_strong = (k15_10sma*10 - k15['Close_Price'].iloc[-10] + k15['Close_Price'].iloc[-1])/(10-1) # 續強公式
                # k15_stock_weak = (k15_20sma*20 - k15['Close_Price'].iloc[-20] + k15['Close_Price'].iloc[-1])/(20-1) # 續弱公式
                k15_stock_strong = (k15_10sma*10 - k15['Close_Price'].iloc[-10])/(10-1) # 續強公式
                k15_stock_weak = (k15_20sma*20 - k15['Close_Price'].iloc[-20])/(20-1) # 續弱公式
                k15_sma.append(round(k15_stock_strong, 2))
                k15_sma.append(round(k15_stock_weak, 2))
            else:
                k15_sma.extend([np.nan, np.nan])
        else:
            # 當 recent_end_date 為 None 時，也要返回7個值以匹配期望的列數
            k15_sma.extend([np.nan, np.nan])

        return k15_sma

    def get_top_volumn_stocks(self, top_n=None):
        try:
            # 從 CSV 文件中讀取數據
            stock_df = pd.read_csv(
                get_resource_path(ResourceFileNames.TW_ALL_STOCKS_CSV), 
                dtype={'StockCode': str}  # 將股票代號列指定為字串類型
             )

            # 確認列標題是否包含 'StockCode'
            if 'StockCode' in stock_df.columns:
                available_stocks = len(stock_df['StockCode'])
                if top_n is None:
                    top_stocks = stock_df['StockCode']
                    return top_stocks.tolist()
                
                top_n = int(top_n)  # 确保 top_n 是整数
                if available_stocks < top_n:
                    return f"錯誤：只有 {available_stocks} 筆資料可用，少於要求的 {top_n} 筆"
                else:
                    top_stocks = stock_df['StockCode'][:top_n]
                    return top_stocks.tolist()
            else:
                print("列標題中沒有 'StockCode'")
                return []

        except Exception as e:
            print(f"讀取文件時發生錯誤: {e}")
            return []
        
    # 找出跳空缺口的資料和日期。
    def get_gap_stocks(self, df):
        """
        找出跳空缺口的資料和日期。
        
        :param df: DataFrame，包含 date, open_price, high_price, low_price, close_price 等欄位
        :return: 包含跳空缺口資訊的 DataFrame
        """
        gaps = []

        for i in range(1, len(df)):
            current_low = df.iloc[i]['low_price']
            current_high = df.iloc[i]['high_price']
            
            if current_low > df.iloc[i - 1]['high_price']:
                gap_type = "向上跳空"
                current_open = current_low
                prev_close = df.iloc[i - 1]['high_price']
            elif current_high < df.iloc[i - 1]['low_price']:
                gap_type = "向下跳空"
                current_open = current_high
                prev_close = df.iloc[i - 1]['low_price']
            else:
                continue
            
            gap_info = {
                'date': df.iloc[i]['date'],
                'previous_close': prev_close,
                'current_open': current_open,
                'gap_type': gap_type
            }
            gaps.append(gap_info)
        
        return pd.DataFrame(gaps)
    
    # 取得日期的收盤價
    def get_close_price_by_date(self, stock_id, date):
        kbars = self.get_stock_kbar_from_db(stock_id, date, date)
        return kbars.iloc[0]['close_price']

    def get_stock_data_from_db(self, stock_id, start_date, end_date):
        conn = self.connect_db()
        query = f"""
        SELECT DISTINCT ts, Open_Price, High, Low, Close_Price, Volume
        FROM Kbars
        WHERE stock_id = '{stock_id}' AND ts >= '{start_date}' AND ts <= DATEADD(day, 1, '{end_date}')
        """
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts'])
        df['date'] = df['ts'].dt.date
        conn.close()
        return df