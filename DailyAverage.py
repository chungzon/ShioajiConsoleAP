import pandas as pd
from datetime import datetime, timedelta
import xlsxwriter
import numpy as np
import pymssql

def connect_db():
    conn = pymssql.connect(
        server='127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn

# 從資料庫中獲取每日收盤價
def get_daily_close_prices_from_db(stock_code, days):
    conn = connect_db()
    query = f"""
    SELECT ts AS date, close_price
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY CONVERT(date, ts) ORDER BY ts DESC) AS rn
        FROM Ticks
        WHERE stock_id = '{stock_code}'
    ) AS sub
    WHERE sub.rn = 1
    ORDER BY date DESC
    OFFSET 0 ROWS
    FETCH NEXT {days + 120} ROWS ONLY
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df = df.sort_index()  # 按日期排序
    return df['close_price']

# 計算移動平均
def calculate_moving_average(prices, window):
    return prices.rolling(window=window).mean()

# 計算周均線
def calculate_weekly_average(prices, window):
    weekly_prices = prices.resample('W').mean()
    return calculate_moving_average(weekly_prices, window)

# 計算月均線
def calculate_monthly_average(prices, window):
    monthly_prices = prices.resample('M').mean()
    return calculate_moving_average(monthly_prices, window)

# 保存到 Excel
def save_to_excel(filename, sma_values, weekly_sma_values, monthly_sma_values):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("日均線")

        # 設定欄位名稱
        headers = ["日均線", "", "", "", "收", "買點", "", "", "", "日均線"]
        worksheet.write_row(0, 0, headers)

        # 合併第5欄位和第6欄位的第1列和第2列資料格
        worksheet.merge_range(1, 4, 2, 4, "")
        worksheet.merge_range(1, 5, 2, 5, "")

        # 合併第5欄位和第6欄位的第3列資料格
        worksheet.merge_range(3, 4, 3, 5, "")
        
        # 合併第5欄位和第6欄位的第4列資料格
        worksheet.merge_range(4, 4, 4, 5, "")

        # 設定第一欄和第十欄的資料
        sma_labels = ["SMA5", "SMA10", "SMA20", "SMA60", "SMA120"]
        for i, label in enumerate(sma_labels):
            worksheet.write(i + 1, 0, label)
            worksheet.write(i + 1, 9, label)

        # 填入日均線計算值
        for i, value in enumerate(sma_values):
            worksheet.write(i + 1, 2, value if not pd.isna(value) else "NaN")
            worksheet.write(i + 1, 7, value if not pd.isna(value) else "NaN")

        # 插入一行空行
        start_row = len(sma_labels) + 3
        worksheet.write_row(start_row, 0, [""] * len(headers))
        start_row += 1

        # 插入周均線表格
        worksheet.write_row(start_row, 0, headers)

        # 合併第5欄位和第6欄位的第1列和第2列資料格
        worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
        worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")

        # 合併第5欄位和第6欄位的第3列資料格
        worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
        # 合併第5欄位和第6欄位的第4列資料格
        worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")

        # 設定第一欄和第十欄的資料
        weekly_sma_labels = ["周SMA5", "周SMA10", "周SMA20", "周SMA60", "周SMA120"]
        for i, label in enumerate(weekly_sma_labels):
            worksheet.write(start_row + i + 1, 0, label)
            worksheet.write(start_row + i + 1, 9, label)

        # 填入周均線計算值
        for i, value in enumerate(weekly_sma_values):
            worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
            worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")

        # 插入一行空行
        start_row += len(weekly_sma_labels) + 2
        worksheet.write_row(start_row, 0, [""] * len(headers))
        start_row += 1

        # 插入月均線表格
        worksheet.write_row(start_row, 0, headers)

        # 合併第5欄位和第6欄位的第1列和第2列資料格
        worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
        worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")

        # 合併第5欄位和第6欄位的第3列資料格
        worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
        # 合併第5欄位和第6欄位的第4列資料格
        worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")

        # 設定第一欄和第十欄的資料
        monthly_sma_labels = ["月SMA5", "月SMA10", "月SMA20", "月SMA60", "月SMA120"]
        for i, label in enumerate(monthly_sma_labels):
            worksheet.write(start_row + i + 1, 0, label)
            worksheet.write(start_row + i + 1, 9, label)

        # 填入月均線計算值
        for i, value in enumerate(monthly_sma_values):
            worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
            worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")

    print(f"資料已儲存到: {filename}")

# 主函數
def main():
    stock_code = "6152"  # 替換為您想要查詢的股票代碼

    # 獲取每日收盤價
    close_prices = get_daily_close_prices_from_db(stock_code, 120)
    
    # 計算日均線的移動平均
    sma_values = [
        round(calculate_moving_average(close_prices, 5).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 10).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 20).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 60).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 120).iloc[-1], 2),
    ]

    # 計算周均線的移動平均
    weekly_sma_values = [
        round(calculate_weekly_average(close_prices, 5).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 10).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 20).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 60).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 120).iloc[-1], 2),
    ]

    # 計算月均線的移動平均
    monthly_sma_values = [
        round(calculate_monthly_average(close_prices, 5).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 10).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 20).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 60).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 120).iloc[-1], 2),
    ]
    
    # 保存到 Excel 文件
    save_to_excel('D:\TradingData\日周月均線_with_SMA.xlsx', sma_values, weekly_sma_values, monthly_sma_values)

if __name__ == "__main__":
    main()
