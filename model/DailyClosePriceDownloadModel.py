import pymssql
import pandas as pd
import time
import os
from datetime import datetime
import shioaji as sj


class DailyClosePriceDownloadModel:
      
    # 創建log資料夾和檔案
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def __init__(self, api):
        self.api = api
  

    def write_log(self, message):
        with open(self.log_filename, "a") as log_file:
            log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn
        
    def download_daily_close_top30_stock(self, view):
        # 讀取 Excel 檔案，取得交易量前30名的股票代碼
        stock_df = pd.read_excel('D:/Project/ShioajiConsole/ShioajiConsoleAP/resource/stock_top.xlsx')
        print(stock_df.columns)  # 打印出列標題名稱
        top_30_stocks = stock_df['股票代號'][:1]
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 創建表格
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='stock_data' AND xtype='U')
            CREATE TABLE stock_data (
                stock_id VARCHAR(10),
                date DATE,
                close_price FLOAT
            )
        """)
        conn.commit()

        # 下載資料並存入資料庫
        for stock_id in top_30_stocks:
            self.download_stock_data(self.api, stock_id, conn, cursor, view)

        # 關閉資料庫連接
        cursor.close()
        conn.close()

    def download_stock_data(self, api, stock_id, conn, cursor, view):
        self.write_log(f"開始處理股票 {stock_id}")
        print(f"開始處理股票 {stock_id}")
        view.append_log(f"開始處理股票 {stock_id}")
        for year in range(2024, 2025):  # 111年到113年
            for month in range(1, 2):  # 每年的月份
                date = f"{year}-{month:02d}-01"  # 每個月的日期
                try:
                    # 取得當月所有天的交易資料
                    days_in_month = pd.date_range(start=date, periods=1, freq='M').days_in_month[0]
                    for day in range(1, days_in_month + 1):
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        ticks = api.ticks(
                            contract=api.Contracts.Stocks[str(stock_id)],
                            date=date_str,
                            query_type=sj.constant.TicksQueryType.LastCount,
                            last_cnt=1,
                        )
                        if ticks.close:
                            # 獲取當天最後一筆交易的收盤價
                            last_close_price = ticks.close[-1]
                            cursor.execute("INSERT INTO stock_data (stock_id, date, close_price) VALUES (%s, %s, %s)",
                                           (stock_id, date_str, last_close_price))
                            conn.commit()
                        self.write_log(f"成功處理 {stock_id} - {date_str}")
                        print(f"成功處理 {stock_id} - {date_str}")
                        view.append_log(f"成功處理 {stock_id} - {date_str}")
                        time.sleep(1)  # 每天間隔1秒
                except Exception as e:
                    self.write_log(f"錯誤處理 {stock_id} - {year} 年 {month} 月: {e}")
                    print(f"錯誤處理 {stock_id} - {year} 年 {month} 月: {e}")
                    view.append_log(f"錯誤處理 {stock_id} - {year} 年 {month} 月: {e}")
        time.sleep(30)  # 每支股票之間間隔30秒
