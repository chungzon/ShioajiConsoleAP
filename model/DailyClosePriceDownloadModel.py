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
        
    def download_daily_close_top30_stock(self, view, start_date, end_date):
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
            self.download_stock_data(self.api, stock_id, conn, cursor, view, start_date, end_date)

        # 關閉資料庫連接
        cursor.close()
        conn.close()

    def download_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date):
        self.write_log(f"開始處理股票 {stock_id}")
        print(f"開始處理股票 {stock_id}")
        view.append_log(f"開始處理股票 {stock_id}")
        current_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        while current_date <= end_date:
            try:        
                ticks = self.api.ticks(
                    contract=self.api.Contracts.Stocks[stock_id],
                    date=current_date.strftime('%Y-%m-%d'),
                    query_type=sj.constant.TicksQueryType.LastCount,
                    last_cnt=1,
                )
                if ticks.close:
                    cursor.execute(
                        "INSERT INTO stock_data (stock_id, date, close_price) VALUES (%s, %s, %s)",
                        (stock_id, current_date.strftime('%Y-%m-%d'), ticks.close[0])
                )
                conn.commit()
                self.write_log(f"成功處理 {stock_id} - {current_date}")
                print(f"成功處理 {stock_id} - {current_date}")
                view.append_log(f"成功處理 {stock_id} - {current_date}")
                time.sleep(1)  # 每天間隔1秒
            except Exception as e:
                self.write_log(f"錯誤處理 {stock_id} - {current_date}: {e}")
                print(f"錯誤處理 {stock_id} - {current_date}: {e}")
                view.append_log(f"錯誤處理 {stock_id} - {current_date}: {e}")
            current_date += pd.DateOffset(months=1)
        time.sleep(30)  # 每支股票之間間隔30秒
