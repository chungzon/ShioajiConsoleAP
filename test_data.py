#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料庫資料
"""

import pymssql
import pandas as pd
from datetime import datetime

def test_data():
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
            print(f'最近5筆資料:')
            print(df.tail(5)[['ts', 'close_price']].to_string())
            
            # 檢查週均線資料
            df['ts'] = pd.to_datetime(df['ts'])
            df.set_index('ts', inplace=True)
            
            # 計算週均線
            weekly_prices = df['close_price'].resample('W').last()
            weekly_prices = weekly_prices.dropna()
            print(f'週均線資料筆數: {len(weekly_prices)}')
            if len(weekly_prices) > 0:
                print(f'週均線最近5筆:')
                print(weekly_prices.tail(5).to_string())
            
            # 計算月均線
            monthly_prices = df['close_price'].resample('ME').last()
            monthly_prices = monthly_prices.dropna()
            print(f'月均線資料筆數: {len(monthly_prices)}')
            if len(monthly_prices) > 0:
                print(f'月均線最近5筆:')
                print(monthly_prices.tail(5).to_string())
        else:
            print('沒有找到資料')
        
        conn.close()
    except Exception as e:
        print(f'錯誤: {e}')

if __name__ == "__main__":
    test_data()




