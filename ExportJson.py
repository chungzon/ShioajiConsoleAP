#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
獨立JSON匯出程式
從資料庫讀取股票資料並匯出為JSON格式
"""

import pymssql
import pandas as pd
import numpy as np
import json
import os
import sys
import math
from datetime import datetime, timedelta
import argparse

class Math:
    """數學運算類別"""
    
    @staticmethod
    def calculate_spread_ratio(max_value, min_value):
        return (max_value - min_value) / min_value * 100

    @staticmethod
    def calculate_ratio_0618(max_value, min_value):
        return round(min_value + (max_value - min_value) / 2 * 0.618, 2)

    @staticmethod
    def calculate_ratio_1(max_value, min_value):
        return round(min_value + (max_value - min_value) / 2 * 1, 2)
    
    @staticmethod
    def calculate_ratio_value(max_value, min_value, ratio):
        return Math.adjust_ratio_price(round(min_value + (max_value - min_value) / 2 * ratio, 2))

    @staticmethod
    def calculate_sma(close_prices, close_date=None):
        # 計算日均線
        daily_5_sma = close_prices.rolling(window=5, min_periods=5).mean()
        daily_10_sma = close_prices.rolling(window=10, min_periods=10).mean()
        daily_20_sma = close_prices.rolling(window=20, min_periods=20).mean()
        daily_60_sma = close_prices.rolling(window=60, min_periods=60).mean()
        daily_120_sma = close_prices.rolling(window=120, min_periods=120).mean()

        daily_sma_5_diff = np.nan
        daily_sma_10_diff = np.nan
        daily_sma_20_diff = np.nan
        daily_sma_60_diff = np.nan
        daily_sma_120_diff = np.nan

        # 日均扣抵值計算
        if not close_prices.empty:
            if len(close_prices) >= 5:
                daily_sma_5_diff = (daily_5_sma.iloc[-1]*5 - close_prices.iloc[-5])/(5-1)
            if len(close_prices) >= 10:
                daily_sma_10_diff = (daily_10_sma.iloc[-1]*10 - close_prices.iloc[-10])/(10-1)
            if len(close_prices) >= 20:
                daily_sma_20_diff = (daily_20_sma.iloc[-1]*20 - close_prices.iloc[-20])/(20-1)
            if len(close_prices) >= 60:
                daily_sma_60_diff = (daily_60_sma.iloc[-1]*60 - close_prices.iloc[-60])/(60-1)
            if len(close_prices) >= 120:
                daily_sma_120_diff = (daily_120_sma.iloc[-1]*120 - close_prices.iloc[-120])/(120-1)
        
        sma_values = [
            round(daily_5_sma.iloc[-1], 2),
            round(daily_10_sma.iloc[-1], 2),
            round(daily_20_sma.iloc[-1], 2),
            round(daily_60_sma.iloc[-1], 2),
            round(daily_120_sma.iloc[-1], 2),
            round(daily_sma_5_diff, 2),
            round(daily_sma_10_diff, 2),
            round(daily_sma_20_diff, 2),
            round(daily_sma_60_diff, 2),
            round(daily_sma_120_diff, 2)
        ]

        # 計算周均線
        weekly_prices = close_prices.resample('W').last()
        weekly_prices = weekly_prices.dropna()
        weekly_5_sma = weekly_prices.rolling(window=5, min_periods=5).mean()
        weekly_10_sma = weekly_prices.rolling(window=10, min_periods=10).mean()
        weekly_20_sma = weekly_prices.rolling(window=20, min_periods=20).mean()
        weekly_60_sma = weekly_prices.rolling(window=60, min_periods=60).mean()
        weekly_120_sma = weekly_prices.rolling(window=120, min_periods=120).mean()

        weekly_sma_5_diff = np.nan
        weekly_sma_10_diff = np.nan
        weekly_sma_20_diff = np.nan
        weekly_sma_60_diff = np.nan
        weekly_sma_120_diff = np.nan

        weekly_index = -2  # 默认取上周周均
        if close_date:
            close_datetime = datetime.strptime(close_date, '%Y-%m-%d')
            is_today = close_datetime.date() == datetime.now().date()
            is_friday = close_datetime.weekday() >= 4  # 周五 (0=周一, 4=周五)
            
            if is_today and is_friday:
                # 是今天且是周五，判断是否下午14:30以后
                if close_datetime.hour >= 14 and close_datetime.minute >= 30:
                    weekly_index = -1  # 是，取本周周均
                else:
                    weekly_index = -2  # 否，取上周周均
            else:
                # 不是今天且周五，判断是否为周五
                if is_friday:
                    weekly_index = -1  # 是，取本周周均
                else:
                    weekly_index = -2  # 否，取上周周均

        monthly_index = -2
        if close_date:
            close_datetime = datetime.strptime(close_date, '%Y-%m-%d')
            if close_datetime.date() == datetime.now().date():
                # 檢查是否為當月最後一天
                next_month = close_datetime.replace(day=28) + timedelta(days=4)
                last_day = next_month - timedelta(days=next_month.day)
                if close_datetime.day == last_day.day:
                    monthly_index = -1
                else:
                    monthly_index = -2
            else:
                # 把close_date的時間設為14:30
                close_datetime = close_datetime.replace(hour=14, minute=30, second=0, microsecond=0)
                # 檢查是否為當月最後一天
                next_month = close_datetime.replace(day=28) + timedelta(days=4)
                last_day = next_month - timedelta(days=next_month.day)
                if close_datetime.day == last_day.day:
                    monthly_index = -1
                else:
                    monthly_index = -2

        if not weekly_prices.empty:
            if len(weekly_prices) >= abs(weekly_index - 5 + 1):
                weekly_sma_5_diff = (weekly_5_sma.iloc[weekly_index]*5 - weekly_prices.iloc[weekly_index-5+1])/(5-1)
            if len(weekly_prices) >= abs(weekly_index - 10 + 1):
                weekly_sma_10_diff = (weekly_10_sma.iloc[weekly_index]*10 - weekly_prices.iloc[weekly_index-10+1])/(10-1)
            if len(weekly_prices) >= abs(weekly_index - 20 + 1):
                weekly_sma_20_diff = (weekly_20_sma.iloc[weekly_index]*20 - weekly_prices.iloc[weekly_index-20+1])/(20-1)
            if len(weekly_prices) >= abs(weekly_index - 60 + 1):
                weekly_sma_60_diff = (weekly_60_sma.iloc[weekly_index]*60 - weekly_prices.iloc[weekly_index-60+1])/(60-1)
            if len(weekly_prices) >= abs(weekly_index - 120 + 1):
                weekly_sma_120_diff = (weekly_120_sma.iloc[weekly_index]*120 - weekly_prices.iloc[weekly_index-120+1])/(120-1)

        # 計算周均線的移動平均
        weekly_sma_values = [
            round(weekly_5_sma.iloc[-1], 2),
            round(weekly_10_sma.iloc[-1], 2),
            round(weekly_20_sma.iloc[-1], 2),
            round(weekly_60_sma.iloc[-1], 2),
            round(weekly_120_sma.iloc[-1], 2),
            round(weekly_sma_5_diff, 2),
            round(weekly_sma_10_diff, 2),
            round(weekly_sma_20_diff, 2),
            round(weekly_sma_60_diff, 2),
            round(weekly_sma_120_diff, 2)
        ]

        # 計算月均線
        monthly_prices = close_prices.resample('ME').last()
        monthly_prices = monthly_prices.dropna()
        monthly_5_sma = monthly_prices.rolling(window=5, min_periods=5).mean()
        monthly_10_sma = monthly_prices.rolling(window=10, min_periods=10).mean()
        monthly_20_sma = monthly_prices.rolling(window=20, min_periods=20).mean()
        monthly_60_sma = monthly_prices.rolling(window=60, min_periods=60).mean()
        monthly_120_sma = monthly_prices.rolling(window=120, min_periods=120).mean()

        monthly_sma_5_diff = np.nan
        monthly_sma_10_diff = np.nan
        monthly_sma_20_diff = np.nan
        monthly_sma_60_diff = np.nan
        monthly_sma_120_diff = np.nan

        if not monthly_prices.empty:
            if len(monthly_prices) >= abs(monthly_index - 5 + 1):
                monthly_sma_5_diff = (monthly_5_sma.iloc[monthly_index]*5 - monthly_prices.iloc[monthly_index-5+1])/(5-1)
            if len(monthly_prices) >= abs(monthly_index - 10 + 1):
                monthly_sma_10_diff = (monthly_10_sma.iloc[monthly_index]*10 - monthly_prices.iloc[monthly_index-10+1])/(10-1)
            if len(monthly_prices) >= abs(monthly_index - 20 + 1):
                monthly_sma_20_diff = (monthly_20_sma.iloc[monthly_index]*20 - monthly_prices.iloc[monthly_index-20+1])/(20-1)
            if len(monthly_prices) >= abs(monthly_index - 60 + 1):
                monthly_sma_60_diff = (monthly_60_sma.iloc[monthly_index]*60 - monthly_prices.iloc[monthly_index-60+1])/(60-1)
            if len(monthly_prices) >= abs(monthly_index - 120 + 1):
                monthly_sma_120_diff = (monthly_120_sma.iloc[monthly_index]*120 - monthly_prices.iloc[monthly_index-120+1])/(120-1)

        # 計算月均線的移動平均
        monthly_sma_values = [
            round(monthly_5_sma.iloc[-1], 2),
            round(monthly_10_sma.iloc[-1], 2),
            round(monthly_20_sma.iloc[-1], 2),
            round(monthly_60_sma.iloc[-1], 2),
            round(monthly_120_sma.iloc[-1], 2),
            round(monthly_sma_5_diff, 2),
            round(monthly_sma_10_diff, 2),
            round(monthly_sma_20_diff, 2),
            round(monthly_sma_60_diff, 2),
            round(monthly_sma_120_diff, 2)
        ]

        return sma_values, weekly_sma_values, monthly_sma_values

    @staticmethod
    def calculate_moving_average(prices, window):
        return prices.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def calculate_weekly_average(prices, window):
        weekly_prices = prices.resample('W').last()
        weekly_prices = weekly_prices.dropna()
        return weekly_prices.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def calculate_monthly_average(prices, window):
        monthly_prices = prices.resample('ME').last()
        return monthly_prices.rolling(window=window, min_periods=window).mean()
    
    @staticmethod
    def calculate_15_minutes_average(prices, window):
        fifteen_minutes_prices = prices.resample('15min').last()
        return fifteen_minutes_prices.rolling(window=window, min_periods=window).mean()
        
    @staticmethod
    def adjust_ratio_price(price):
        if price < 10:
            return round(price, 2)  # 10元以下,保留到小數點後兩位
        elif price < 50:
            return math.ceil(price * 20) / 20  # 10元到50元,向上調整到0.05的倍數
        elif price < 100:
            return math.ceil(price * 10) / 10  # 50元到100元,向上調整到0.1的倍數
        elif price < 500:
            return math.ceil(price * 2) / 2  # 100元到500元,向上調整到0.5的倍數
        elif price < 1000:
            return math.ceil(price)  # 500元到1000元,向上調整到整數
        else:
            return math.ceil(price / 5) * 5  # 1000元以上,向上調整到5的倍數

    @staticmethod
    def calculate_CDP(high, low, close):
        return round((high + low + 2 * close) / 4, 3)
    
    @staticmethod
    def calculate_CDP_NL(CDP, high):
        return round((2 * CDP) - high, 3)
    
    @staticmethod
    def calculate_CDP_NH(CDP, low):
        return round((2 * CDP) - low, 3)

    @staticmethod
    def calculate_CDP_first_target(CDP, NL, NH):
        return round(CDP + (NH - NL), 3)
    
    @staticmethod
    def calculate_AH(CDP, high, low):
        return round(CDP + (high - low), 3)

    @staticmethod
    def calculate_AL(CDP, high, low):
        return round(CDP - (high - low), 3)

    @staticmethod
    def calculate_CDP_5_values(CDP, high, low):
        return CDP, Math.calculate_CDP_NL(CDP, high), Math.calculate_CDP_NH(CDP, low), Math.calculate_AL(CDP, high, low), Math.calculate_AH(CDP, high, low)

    @staticmethod
    def calculate_price_diff_ratio(price_1, price_2):
        return round((price_1 - price_2) / price_2 * 100, 2)

    @staticmethod
    def calculate_price_diff(price_1, price_2):
        return round(price_1 - price_2, 2)

    @staticmethod
    def calculate_down_limit_price(price: float) -> float:
        return round(price * 0.9, 2)

    @staticmethod
    def calculate_up_limit_price(price: float) -> float:
        return round(price * 1.1, 2)
    
    @staticmethod
    def calculate_up_limit_price_1_15(price: float) -> float:
        return round(price * 1.15, 2)
    
    @staticmethod
    def calculate_down_limit_price_1_15(price: float) -> float:
        return round(price * 0.85, 2)

class ExportJson:
    def __init__(self):
        self.db_config = {
            'server': '127.0.0.1:1433',
            'user': 'TSE_USER',
            'password': 'fuckme',
            'database': 'TSE'
        }
    
    def connect_db(self):
        """連接資料庫"""
        try:
            conn = pymssql.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"資料庫連接失敗: {e}")
            return None
    
    def get_stock_data(self, stock_id, start_date, end_date):
        """從資料庫取得股票KBar資料"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            query = """
            SELECT stock_id, ts, open_price, high, low, close_price, volume
            FROM Kbars 
            WHERE stock_id = %s 
            AND ts >= %s 
            AND ts <= %s
            ORDER BY ts
            """
            df = pd.read_sql(query, conn, params=[stock_id, start_date, end_date])
            conn.close()
            
            if not df.empty:
                df['ts'] = pd.to_datetime(df['ts'])
                df.set_index('ts', inplace=True)
            
            return df
        except Exception as e:
            print(f"查詢股票資料失敗: {e}")
            if conn:
                conn.close()
            return None
    
    def find_peaks_troughs_v34_small(self, df):
        segments = []
        ratios = [0, 0.191, 0.382, 0.5, 0.618, 0.809, 1, 1.191, 1.382, 1.5, 1.618, 1.809, 2, 2.191, 2.382, 2.5, 2.618, 2.809, 3, 
                  3.191, 3.382, 3.5, 3.618, 3.809, 4, 4.191, 4.382, 4.5, 4.618, 4.809, 5, 5.191, 5.382, 5.5, 5.618, 5.809, 6]
        ratio_columns = [f'Ratio_{ratio}' for ratio in ratios]
        append_columns = [f'spread_ratio', f'latest_close_price', f'latest_close_price-0.191_ratio', f'latest_close_price-0.618_ratio']
        cdp_columns = [f'CDP', 'NH', 'NL', 'AH', 'AL']

        latest_close_price = df['close_price'].iloc[-1]
        # 取得SMA值
        k15_sma_values = self.calculate_k15_sma(df)
        sma_values, weekly_sma_values, monthly_sma_values = Math.calculate_sma(df['close_price'])

        periods = [5, 10, 20, 60, 120, 'strong', 'weak', '60_diff']
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
                df['high'].iloc[-1], 
                df['low'].iloc[-1], 
                df['close_price'].iloc[-1]
            )
            CDP, NL, NH, AL, AH = Math.calculate_CDP_5_values(CDP, df['high'].iloc[-1], df['low'].iloc[-1])
        except:
            CDP = NL = NH = AL = AH = np.nan

        # 第一階段：找出所有波段
        peaks = []
        troughs = []
        
        wave_start_idx = 0
        current_wave_high = df.iloc[0]['high']
        current_wave_high_date = df.index[0]
        current_wave_low = df.iloc[0]['low']
        current_wave_low_date = df.index[0]
        last_wave_start_idx = 0  # 記錄波段起始位置
        
        # 從第二天開始分析
        for i in range(1, len(df)):
            today_high = df.iloc[i]['high']
            today_low = df.iloc[i]['low']
            yesterday_low = df.iloc[i-1]['low']
            
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
                        'idx': wave_start_idx
                    })
                
                wave_start_idx = i-1
                last_wave_start_idx = i  # 記錄新波段的起始位置
                current_wave_high = today_high
                current_wave_high_date = df.index[i]
                current_wave_low = today_low
                current_wave_low_date = df.index[i]
            else:
                if today_high > current_wave_high:
                    current_wave_high = today_high
                    current_wave_high_date = df.index[i]
                if today_low < current_wave_low:
                    current_wave_low = today_low
                    current_wave_low_date = df.index[i]

        # 處理最後一個波段
        troughs.append({
            'date': current_wave_low_date,
            'price': current_wave_low,
            'idx': wave_start_idx
        })
        
        peaks.append({
            'date': current_wave_high_date,
            'price': current_wave_high,
            'idx': len(df) - 1
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
                if not (last_data['high'] > prev_peak_price or 
                       last_data['low'] < prev_data['low']):
                    # 合併到前一個波段
                    peaks_df = peaks_df.iloc[:-1]
                    troughs_df = troughs_df.iloc[:-1]
                    
                    # 更新前一個波段的資訊
                    if last_data['high'] > peaks_df.iloc[-1]['price']:
                        peaks_df.at[len(peaks_df)-1, 'price'] = last_data['high']
                        peaks_df.at[len(peaks_df)-1, 'date'] = df.index[-1]
                    if last_data['low'] < troughs_df.iloc[-1]['price']:
                        troughs_df.at[len(troughs_df)-1, 'price'] = last_data['low']
                        troughs_df.at[len(troughs_df)-1, 'date'] = df.index[-1]

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
                df.index[end_idx]
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
                latest_close_price_0618_ratio
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
    
    def calculate_ratios(self, extremes_df):
        """計算比例價格 - 使用原本的邏輯"""
        if extremes_df.empty or len(extremes_df) < 2:
            return {}
        
        # 找到最高價和最低價
        max_price = extremes_df['Max_Value'].max()
        min_price = extremes_df['Min_Value'].min()
        
        # 計算各種比例
        ratios = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                 '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                 '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                 '3.191', '3.382', '3.5', '3.618', '3.809', '4',
                 '4.191', '4.382', '4.5', '4.618', '4.809', '5']
        
        ratio_prices = {}
        for ratio in ratios:
            ratio_value = float(ratio)
            price = Math.calculate_ratio_value(max_price, min_price, ratio_value)
            ratio_prices[ratio] = price
        
        return ratio_prices
    
    def calculate_moving_averages(self, df):
        """計算各種移動平均線 - 使用原本的邏輯"""
        if df.empty:
            return {}
        
        close_prices = df['close_price']
        latest_price = close_prices.iloc[-1]
        
        # 使用原本的 Math.calculate_sma 方法
        sma_values, weekly_sma_values, monthly_sma_values = Math.calculate_sma(close_prices)
        
        # 計算15分鐘均線
        k15_sma_values = self.calculate_k15_sma(df)
        
        # 組織均線資料 - 根據原本的返回值結構
        organized_ma_data = {
            '日均線': {
                '5MA': sma_values[0] if not pd.isna(sma_values[0]) else 'N/A',
                '10MA': sma_values[1] if not pd.isna(sma_values[1]) else 'N/A',
                '20MA': sma_values[2] if not pd.isna(sma_values[2]) else 'N/A',
                '60MA': sma_values[3] if not pd.isna(sma_values[3]) else 'N/A',
                '120MA': sma_values[4] if not pd.isna(sma_values[4]) else 'N/A',
                '5MA_DIFF': sma_values[5] if not pd.isna(sma_values[5]) else 'N/A',
                '10MA_DIFF': sma_values[6] if not pd.isna(sma_values[6]) else 'N/A',
                '20MA_DIFF': sma_values[7] if not pd.isna(sma_values[7]) else 'N/A',
                '60MA_DIFF': sma_values[8] if not pd.isna(sma_values[8]) else 'N/A',
                '120MA_DIFF': sma_values[9] if not pd.isna(sma_values[9]) else 'N/A',
            },
            '週均線': {
                '5MA': weekly_sma_values[0] if not pd.isna(weekly_sma_values[0]) else 'N/A',
                '10MA': weekly_sma_values[1] if not pd.isna(weekly_sma_values[1]) else 'N/A',
                '20MA': weekly_sma_values[2] if not pd.isna(weekly_sma_values[2]) else 'N/A',
                '60MA': weekly_sma_values[3] if not pd.isna(weekly_sma_values[3]) else 'N/A',
                '120MA': weekly_sma_values[4] if not pd.isna(weekly_sma_values[4]) else 'N/A',
                '5MA_DIFF': weekly_sma_values[5] if not pd.isna(weekly_sma_values[5]) else 'N/A',
                '10MA_DIFF': weekly_sma_values[6] if not pd.isna(weekly_sma_values[6]) else 'N/A',
                '20MA_DIFF': weekly_sma_values[7] if not pd.isna(weekly_sma_values[7]) else 'N/A',
                '60MA_DIFF': weekly_sma_values[8] if not pd.isna(weekly_sma_values[8]) else 'N/A',
                '120MA_DIFF': weekly_sma_values[9] if not pd.isna(weekly_sma_values[9]) else 'N/A',
            },
            '月均線': {
                '5MA': monthly_sma_values[0] if not pd.isna(monthly_sma_values[0]) else 'N/A',
                '10MA': monthly_sma_values[1] if not pd.isna(monthly_sma_values[1]) else 'N/A',
                '20MA': monthly_sma_values[2] if not pd.isna(monthly_sma_values[2]) else 'N/A',
                '60MA': monthly_sma_values[3] if not pd.isna(monthly_sma_values[3]) else 'N/A',
                '120MA': monthly_sma_values[4] if not pd.isna(monthly_sma_values[4]) else 'N/A',
                '5MA_DIFF': monthly_sma_values[5] if not pd.isna(monthly_sma_values[5]) else 'N/A',
                '10MA_DIFF': monthly_sma_values[6] if not pd.isna(monthly_sma_values[6]) else 'N/A',
                '20MA_DIFF': monthly_sma_values[7] if not pd.isna(monthly_sma_values[7]) else 'N/A',
                '60MA_DIFF': monthly_sma_values[8] if not pd.isna(monthly_sma_values[8]) else 'N/A',
                '120MA_DIFF': monthly_sma_values[9] if not pd.isna(monthly_sma_values[9]) else 'N/A',
            },
            '15分鐘均線': {
                '5MA': k15_sma_values[0] if not pd.isna(k15_sma_values[0]) else 'N/A',
                '10MA': k15_sma_values[1] if not pd.isna(k15_sma_values[1]) else 'N/A',
                '20MA': k15_sma_values[2] if not pd.isna(k15_sma_values[2]) else 'N/A',
                '60MA': k15_sma_values[3] if not pd.isna(k15_sma_values[3]) else 'N/A',
                '120MA': k15_sma_values[4] if not pd.isna(k15_sma_values[4]) else 'N/A',
                'strong': k15_sma_values[5] if not pd.isna(k15_sma_values[5]) else 'N/A',
                'weak': k15_sma_values[6] if not pd.isna(k15_sma_values[6]) else 'N/A',
                '60MA_DIFF': k15_sma_values[7] if not pd.isna(k15_sma_values[7]) else 'N/A',
                '5MA_DIFF': 'N/A',  # 15分鐘均線沒有5MA扣抵值
                '10MA_DIFF': 'N/A',  # 15分鐘均線沒有10MA扣抵值
                '20MA_DIFF': 'N/A',  # 15分鐘均線沒有20MA扣抵值
                '120MA_DIFF': 'N/A',  # 15分鐘均線沒有120MA扣抵值
            },
            'latest_close_price': latest_price
        }
        
        return organized_ma_data
    
    def calculate_k15_sma(self, df):
        """計算15分鐘均線 - 使用原本的邏輯"""
        if df.empty:
            return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
        
        # 轉換時間格式
        df_copy = df.copy()
        df_copy['ts'] = df_copy.index
        df_copy = df_copy.set_index('ts')
        
        # 按日期分組
        daily_groups = df_copy.groupby(df_copy.index.date)
        
        # 存儲所有15K數據
        all_k15 = []
        
        for ts, day_data in daily_groups:
            # 設定當天的起始時間（0915）
            start_time = pd.Timestamp(ts).replace(hour=9, minute=15)
            
            # 重採樣，從0915開始每15分鐘
            k15_day = day_data.resample('15T', origin=start_time, closed='right', label='right').agg({
                'open_price': 'last',
                'high': 'last',
                'low': 'last',
                'close_price': 'last',
                'volume': 'sum'
            })
            
            all_k15.append(k15_day)
        
        # 合併所有日期的數據
        k15 = pd.concat(all_k15)
        
        if k15.empty:
            return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
        
        # 計算15分鐘K線的SMA，處理數據不足的情況
        k15_5sma = Math.calculate_moving_average(k15['close_price'], 5)
        k15_10sma = Math.calculate_moving_average(k15['close_price'], 10)
        k15_20sma = Math.calculate_moving_average(k15['close_price'], 20)
        k15_60sma = Math.calculate_moving_average(k15['close_price'], 60)
        k15_120sma = Math.calculate_moving_average(k15['close_price'], 120)
        
        # 計算15分鐘K線的SMA
        k15_sma = [
            round(k15_5sma.iloc[-1] if not np.isnan(k15_5sma.iloc[-1]) else np.nan, 2),
            round(k15_10sma.iloc[-1] if not np.isnan(k15_10sma.iloc[-1]) else np.nan, 2),
            round(k15_20sma.iloc[-1] if not np.isnan(k15_20sma.iloc[-1]) else np.nan, 2),
            round(k15_60sma.iloc[-1] if not np.isnan(k15_60sma.iloc[-1]) else np.nan, 2),
            round(k15_120sma.iloc[-1] if not np.isnan(k15_120sma.iloc[-1]) else np.nan, 2)
        ]
        
        # 計算續強和續弱
        if not k15.empty and len(k15) >= 20:
            k15_stock_strong = (k15_10sma.iloc[-1]*10 - k15['close_price'].iloc[-10])/(10-1) # 續強公式
            k15_stock_weak = (k15_20sma.iloc[-1]*20 - k15['close_price'].iloc[-20])/(20-1) # 續弱公式
            k15_sma.append(round(k15_stock_strong, 2))
            k15_sma.append(round(k15_stock_weak, 2))
        else:
            k15_sma.extend([np.nan, np.nan])
        
        # 計算60MA扣抵值
        k15_60sma_diff = np.nan
        if len(k15_60sma) >= 60:
            k15_60sma_diff = (k15_60sma.iloc[-1]*60 - k15['close_price'].iloc[-60])/(60-1)
            k15_sma.append(round(k15_60sma_diff, 2))
        else:
            k15_sma.append(np.nan)
        
        return k15_sma
    
    def calculate_indicators(self, df):
        """計算技術指標"""
        if df.empty:
            return {}
        
        close_prices = df['close_price']
        high_prices = df['high']
        low_prices = df['low']
        
        indicators = {}
        
        # 計算AL (最高價)
        indicators['AL'] = high_prices.max()
        
        # 計算NL (最低價)
        indicators['NL'] = low_prices.min()
        
        # 計算NH (最近最高價，最近10天)
        indicators['NH'] = high_prices.tail(10).max()
        
        # 計算AH (最近最低價，最近10天)
        indicators['AH'] = low_prices.tail(10).min()
        
        # 計算CDP (簡化版本)
        recent_high = high_prices.tail(1).iloc[0]
        recent_low = low_prices.tail(1).iloc[0]
        recent_close = close_prices.tail(1).iloc[0]
        indicators['CDP'] = (recent_high + recent_low + recent_close) / 3
        
        return indicators
    
    def get_recent_ratio_prices(self, df, recent_start_date, recent_end_date):
        """計算最近波段的比例價格 - 使用原本的邏輯"""
        if df.empty:
            return {}
        
        # 將date轉換為datetime進行比較
        recent_start_datetime = pd.to_datetime(recent_start_date)
        recent_end_datetime = pd.to_datetime(recent_end_date)
        
        # 篩選最近波段的資料
        recent_df = df[(df.index >= recent_start_datetime) & (df.index <= recent_end_datetime)]
        
        if recent_df.empty:
            return {}
        
        # 使用原本的波段計算邏輯
        recent_extremes = self.find_peaks_troughs_v34_small(recent_df)
        
        if recent_extremes.empty:
            return {}
        
        # 找到最近波段的高低點
        recent_max = recent_extremes['Max_Value'].max()
        recent_min = recent_extremes['Min_Value'].min()
        
        # 計算比例價格
        ratios = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                 '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                 '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                 '3.191', '3.382', '3.5', '3.618', '3.809', '4',
                 '4.191', '4.382', '4.5', '4.618', '4.809', '5']
        
        recent_ratio_prices = {}
        for ratio in ratios:
            ratio_value = float(ratio)
            price = Math.calculate_ratio_value(recent_max, recent_min, ratio_value)
            recent_ratio_prices[ratio] = price
        
        return recent_ratio_prices
    
    def export_to_json(self, stock_id, start_date, end_date, recent_start_date=None, recent_end_date=None, output_path=None):
        """匯出資料為JSON格式"""
        print(f"開始處理股票 {stock_id} 的資料...")
        
        # 如果沒有指定最近波段日期，使用總波段的後半段
        if not recent_start_date or not recent_end_date:
            # 計算日期差的天數
            date_diff = (end_date - start_date).days
            mid_days = date_diff // 2
            mid_date = start_date + timedelta(days=mid_days)
            recent_start_date = mid_date
            recent_end_date = end_date
        
        # 取得股票資料
        df = self.get_stock_data(stock_id, start_date, end_date)
        if df is None or df.empty:
            print(f"無法取得股票 {stock_id} 的資料")
            return False
        
        print(f"成功取得 {len(df)} 筆資料")
        
        # 計算各種資料
        print("計算移動平均線...")
        organized_ma_data = self.calculate_moving_averages(df)
        
        print("計算技術指標...")
        indicator_prices = self.calculate_indicators(df)
        
        print("計算總波段比例價格...")
        ratio_prices = self.calculate_ratios(self.find_peaks_troughs_v34_small(df))
        
        print("計算最近波段比例價格...")
        recent_ratio_prices = self.get_recent_ratio_prices(df, recent_start_date, recent_end_date)
        
        # 準備JSON資料
        data = {}
        
        # 添加當前價格
        latest_close_price = organized_ma_data['latest_close_price']
        data['NOW PRICE'] = f"{latest_close_price:.2f}"
        
        # 定義固定的比例序列
        ratio_sequence = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                         '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                         '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                         '3.191', '3.382', '3.5', '3.618', '3.809', '4',
                         '4.191', '4.382', '4.5', '4.618', '4.809', '5']
        
        # 添加最近波段比例價格
        for ratio in ratio_sequence:
            if recent_ratio_prices and ratio in recent_ratio_prices:
                price = recent_ratio_prices[ratio]
                data[f"N[{ratio}]"] = f"{price:.2f}"
            else:
                data[f"N[{ratio}]"] = "nan"
        
        # 添加總波段比例價格
        for ratio in ratio_sequence:
            if ratio in ratio_prices:
                price = ratio_prices[ratio]
                data[f"[{ratio}]"] = f"{price:.2f}"
            else:
                data[f"[{ratio}]"] = "nan"
        
        # 按照固定順序添加均線和指標數據
        indicator_order = [
            ('日', '120'), ('周', '60'), ('周', '20'), ('日', '60'),
            ('周', '120'), ('月', '5'), ('周', '10'), ('日', '20'),
            'AL', ('周', '5'), 'NL', ('15K', '20'), 'CDP', ('15K', '10'),
            ('15K', '5'), ('15K', 'strong'), ('15K', 'weak'), ('日', '10'), ('日', '5'), 'NH', 'AH',
            ('月', '10'), ('月', '20'), ('月', '60'), ('月', '120'),('日', 'strong'), ('日', 'weak'),
            ('周', 'strong'), ('周', 'weak'),
            # 扣抵值集合
            ('15K', '60MA_DIFF'),
            ('日', '5MA_DIFF'), ('日', '10MA_DIFF'), ('日', '20MA_DIFF'), ('日', '60MA_DIFF'), ('日', '120MA_DIFF'),
            ('周', '5MA_DIFF'), ('周', '10MA_DIFF'), ('周', '20MA_DIFF'), ('周', '60MA_DIFF'), ('周', '120MA_DIFF'),
            ('月', '5MA_DIFF'), ('月', '10MA_DIFF'), ('月', '20MA_DIFF'), ('月', '60MA_DIFF'), ('月', '120MA_DIFF')
        ]
        
        # 添加均線和指標數據
        for item in indicator_order:
            if isinstance(item, tuple):
                prefix, period = item
                key = f"{prefix}({period})_DC"
                if prefix in {'日': '日均線', '周': '週均線', '月': '月均線', '15K': '15分鐘均線'}:
                    ma_type = {'日': '日均線', '周': '週均線', '月': '月均線', '15K': '15分鐘均線'}[prefix]
                    # 處理扣抵值
                    if period.endswith('MA_DIFF'):
                        ma_period = period.replace('MA_DIFF', 'MA_DIFF')
                    # 對於15分鐘均線，需要特殊處理strong和weak
                    elif prefix != '月' and period in ['strong', 'weak']:
                        ma_period = period
                    else:
                        ma_period = f"{period}MA"
                    if (ma_type in organized_ma_data and 
                        ma_period in organized_ma_data[ma_type] and 
                        organized_ma_data[ma_type][ma_period] != 'N/A'):
                        value = organized_ma_data[ma_type][ma_period]
                        data[key] = f"{value:.2f}"
                    else:
                        data[key] = "nan"
            else:
                # 處理指標數據
                key = f"{item}_DC"
                if item in indicator_prices:
                    value = indicator_prices[item]
                    data[key] = f"{value:.2f}"
                else:
                    data[key] = "nan"
        
        # 讀取JSON模板
        template_path = 'resource/export_json_templete.json'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                json_template = json.load(f)
        else:
            # 如果沒有模板，使用預設結構
            json_template = {
                "stock_code": stock_id,
                "base": "0",
                "date": end_date.strftime('%Y-%m-%d'),
                "data": data,
                "over_ratio_dont_buy": "0.03",
                "extend_over_ratio_dont_buy": "0.03",
                "no_buy_after": "10:00:00",
                "final_buy": "12:00:00",
                "extend_time": "00:30:00",
                "enable_15k20ma": True,
                "enable_15k10ma": True,
                "before_n": 2,
            }
        
        # 更新JSON模板中的數據
        json_template['stock_code'] = stock_id
        json_template['base'] = f"{latest_close_price:.2f}"
        json_template['date'] = end_date.strftime('%Y-%m-%d')
        json_template['data'] = data
        
        # 設定輸出路徑
        if not output_path:
            output_path = f"{stock_id}_data_{end_date.strftime('%Y-%m-%d')}.json"
        
        # 寫入JSON檔案
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_template, f, ensure_ascii=False, indent=4)
            print(f"成功匯出JSON檔案: {output_path}")
            return True
        except Exception as e:
            print(f"匯出JSON檔案失敗: {e}")
            return False

def main():
    """主程式"""
    # parser = argparse.ArgumentParser(description='股票資料JSON匯出工具')
    # parser.add_argument('stock_id', help='股票代碼', default='1802')
    # parser.add_argument('start_date', help='起始日期 (YYYY-MM-DD)', default='2024-09-11')
    # parser.add_argument('end_date', help='結束日期 (YYYY-MM-DD)', default='2025-09-11')
    # parser.add_argument('--recent_start', help='最近波段起始日期 (YYYY-MM-DD)', default='2024-09-11')
    # parser.add_argument('--recent_end', help='最近波段結束日期 (YYYY-MM-DD)', default='2025-09-11')
    # parser.add_argument('--output', help='輸出檔案路徑', default='1802_data_2024-09-11.json')
    
    # args = parser.parse_args()
    
    # 解析日期
    try:
        start_date = datetime.strptime('2021-01-01', '%Y-%m-%d').date()
        end_date = datetime.strptime('2025-09-11', '%Y-%m-%d').date()
        recent_start_date = None
        recent_end_date = None
        
        if '2024-09-11':
            recent_start_date = datetime.strptime('2024-01-01', '%Y-%m-%d').date()
        if '2025-09-11':
            recent_end_date = datetime.strptime('2025-09-11', '%Y-%m-%d').date()
    except ValueError as e:
        print(f"日期格式錯誤: {e}")
        print("請使用 YYYY-MM-DD 格式")
        return
    
    # 建立匯出器並執行
    exporter = ExportJson()
    success = exporter.export_to_json(
        stock_id='6877',
        start_date=start_date,
        end_date=end_date,
        recent_start_date=recent_start_date,
        recent_end_date=recent_end_date,
        output_path='1802_data_2024-09-11.json'
    )
    
    if success:
        print("匯出完成！")
    else:
        print("匯出失敗！")
        sys.exit(1)

if __name__ == "__main__":
    main()
