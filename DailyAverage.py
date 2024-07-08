import shioaji as sj
import pandas as pd
from datetime import datetime, timedelta
import xlsxwriter
import numpy as np

# 初始化 Shioaji API
api = sj.Shioaji(simulation=True)
api.login(
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

# 獲取歷史ticks的最後一筆作為每日收盤價
def get_daily_close_prices(stock_code, days):
    contract = api.Contracts.Stocks[stock_code]
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days + 140)  # 多取一些天數以確保有足夠的交易日數據

    all_ticks = []

    current_date = start_date
    while current_date <= end_date:
        try:
            ticks = api.ticks(
                contract=contract, 
                date=current_date.strftime('%Y-%m-%d')
            )
            if len(ticks.ts) > 0:
                last_tick = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'close': ticks.close[-1]
                }
                all_ticks.append(last_tick)
        except Exception as e:
            pass  # 忽略沒有交易數據的日期
        current_date += timedelta(days=1)

    df = pd.DataFrame(all_ticks)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df = df[df.index.dayofweek < 5]  # 只保留工作日

    return df['close'].tail(days + 120)

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
        sma_labels = ["SMA5", "SMA10", "SMA20", "SMA120"]
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
        weekly_sma_labels = ["周SMA5", "周SMA10", "周SMA20", "周SMA120"]
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
        monthly_sma_labels = ["月SMA5", "月SMA10", "月SMA20", "月SMA120"]
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
    stock_code = "6125"  # 替換為您想要查詢的股票代碼

    # 獲取每日收盤價
    close_prices = get_daily_close_prices(stock_code, 120)
    
    # 計算日均線的移動平均
    sma_values = [
        round(calculate_moving_average(close_prices, 5).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 10).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 20).iloc[-1], 2),
        round(calculate_moving_average(close_prices, 120).iloc[-1], 2),
    ]

    # 計算周均線的移動平均
    weekly_sma_values = [
        round(calculate_weekly_average(close_prices, 5).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 10).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 20).iloc[-1], 2),
        round(calculate_weekly_average(close_prices, 120).iloc[-1], 2),
    ]

    # 計算月均線的移動平均
    monthly_sma_values = [
        round(calculate_monthly_average(close_prices, 5).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 10).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 20).iloc[-1], 2),
        round(calculate_monthly_average(close_prices, 120).iloc[-1], 2),
    ]
    
    # 保存到 Excel 文件
    save_to_excel('D:\TradingData\日周月均線_with_SMA.xlsx', sma_values, weekly_sma_values, monthly_sma_values)
    
if __name__ == "__main__":
    main()