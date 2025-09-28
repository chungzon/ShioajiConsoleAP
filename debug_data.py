#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
除錯資料庫資料
"""

import pymssql
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from common.Math import Math

def debug_data():
    try:
        # 連接資料庫
        conn = pymssql.connect(server='127.0.0.1:1433', user='TSE_USER', password='fuckme', database='TSE')
        print('資料庫連接成功')
        
        # 查詢1802的資料
        query = """
        SELECT stock_id, ts, open_price, high, low, close_price, volume
        FROM Kbars 
        WHERE stock_id = '1802' 
        AND ts >= '2024-09-11' 
        AND ts <= '2025-09-11'
        ORDER BY ts
        """
        
        df = pd.read_sql(query, conn)
        print(f'總資料筆數: {len(df)}')
        
        if len(df) > 0:
            print(f'日期範圍: {df["ts"].min()} 到 {df["ts"].max()}')
            
            # 轉換時間格式
            df['ts'] = pd.to_datetime(df['ts'])
            df.set_index('ts', inplace=True)
            
            # 測試週均線計算
            print('\n=== 週均線計算測試 ===')
            weekly_prices = df['close_price'].resample('W').last()
            weekly_prices = weekly_prices.dropna()
            print(f'週均線資料筆數: {len(weekly_prices)}')
            if len(weekly_prices) > 0:
                print(f'週均線最近5筆:')
                print(weekly_prices.tail(5).to_string())
                
                # 計算週均線
                for period in [5, 10, 20, 60, 120]:
                    if len(weekly_prices) >= period:
                        ma = Math.calculate_moving_average(weekly_prices, period)
                        print(f'週{period}MA: {ma.iloc[-1]:.2f}')
                    else:
                        print(f'週{period}MA: 資料不足 (需要{period}筆，只有{len(weekly_prices)}筆)')
            
            # 測試月均線計算
            print('\n=== 月均線計算測試 ===')
            monthly_prices = df['close_price'].resample('M').last()
            monthly_prices = monthly_prices.dropna()
            print(f'月均線資料筆數: {len(monthly_prices)}')
            if len(monthly_prices) > 0:
                print(f'月均線最近5筆:')
                print(monthly_prices.tail(5).to_string())
                
                # 計算月均線
                for period in [5, 10, 20, 60, 120]:
                    if len(monthly_prices) >= period:
                        ma = Math.calculate_moving_average(monthly_prices, period)
                        print(f'月{period}MA: {ma.iloc[-1]:.2f}')
                    else:
                        print(f'月{period}MA: 資料不足 (需要{period}筆，只有{len(monthly_prices)}筆)')
            
            # 測試Math.calculate_sma
            print('\n=== Math.calculate_sma 測試 ===')
            try:
                sma_values, weekly_sma_values, monthly_sma_values = Math.calculate_sma(df['close_price'])
                print(f'日均線值: {sma_values}')
                print(f'週均線值: {weekly_sma_values}')
                print(f'月均線值: {monthly_sma_values}')
            except Exception as e:
                print(f'Math.calculate_sma 錯誤: {e}')
        else:
            print('沒有找到資料')
        
        conn.close()
    except Exception as e:
        print(f'錯誤: {e}')

if __name__ == "__main__":
    debug_data()




