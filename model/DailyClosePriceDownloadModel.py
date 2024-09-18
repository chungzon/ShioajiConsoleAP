import pymssql
import pandas as pd
import time
import os
from datetime import datetime
import shioaji as sj
import csv
import io
import requests


class DailyClosePriceDownloadModel:
      
    # 創建log資料夾和檔案
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def __init__(self, api):
        self.api = api
        self.log_filename = "logs/stock_download.log"
  

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
        stock_df = pd.read_excel(r'D:\Project\ShioajiConsole\ShioajiConsoleAP\resource\stock_top.xlsx')
        print(stock_df.columns)  # 打印出列標題名稱
        top_30_stocks = stock_df['股票代號'][:5]
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 創建表格
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='stock_data' AND xtype='U')
            CREATE TABLE stock_data (
                stock_id VARCHAR(10),
                date DATE,
                open_price FLOAT,
                high_price FLOAT,
                low_price FLOAT,
                close_price FLOAT,
                volume INT
            )
        """)

        conn.commit()

        # 下載資料並存入資料庫
        for stock_id in top_30_stocks:
            if self.check_stock_exists(stock_id):
                self.download_stock_data(self.api, stock_id, conn, cursor, view, start_date, end_date)
            else:
                self.download_otc_stock_data(self.api, stock_id, conn, cursor, view, start_date, end_date)

        # 關閉資料庫連接
        cursor.close()
        conn.close()

    def write_log(self, message):
        with open(self.log_filename, "a") as log_file:
            log_file.write(f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def download_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date):
        self.write_log(f"開始處理股票 {stock_id}")
        print(f"開始處理股票 {stock_id}")
        view.append_log(f"開始處理股票 {stock_id}")
        current_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        while current_date <= end_date:
            try:
                date_str = current_date.strftime('%Y%m')  # 将日期格式化为YYYYmm
                # 根據日期和股票代碼來構建請求URL
                resp = requests.get(
                    f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?' +
                    f'response=csv&date={date_str}01&stockNo={stock_id}')
                
                if resp.status_code != 200:
                    raise Exception(f'HTTP response code is not 200: {resp.status_code}')
                
                # 解析CSV數據
                lines = io.StringIO(resp.text).readlines()
                lines = lines[1:-5]  # 去除第一行和最後五行
                # 檢查是否包含說明列，並只保留有效數據
                if '說明' in lines[-1]:
                    lines = lines[:lines.index('"說明:"\r\n')]
                reader = csv.DictReader(io.StringIO('\n'.join(lines)))

                for row in reader:
                    gregorian_date_str = self.convert_taiwan_date_to_gregorian(row['日期'].strip())
                    date = pd.to_datetime(gregorian_date_str, format='%Y/%m/%d').strftime('%Y-%m-%d')
                    open_price = float(row['開盤價'].replace(',', '').strip())
                    high_price = float(row['最高價'].replace(',', '').strip())
                    low_price = float(row['最低價'].replace(',', '').strip())
                    close_price = float(row['收盤價'].replace(',', '').strip())
                    volume = int(row['成交股數'].replace(',', '').strip())
                    
                    cursor.execute(
                        """INSERT INTO stock_data 
                        (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (stock_id, date, open_price, high_price, low_price, close_price, volume)
                    )
                    conn.commit()

                    self.write_log(f"成功處理 {stock_id} - {gregorian_date_str}")
                    print(f"成功處理 {stock_id} - {gregorian_date_str}")
                    view.append_log(f"成功處理 {stock_id} - {gregorian_date_str}")
                time.sleep(1)  # 每天間隔1秒

            except Exception as e:
                self.write_log(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                print(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                view.append_log(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")

            current_date += pd.DateOffset(months=1)  # 每次移動到下一個月的開始日期
        time.sleep(30)  # 每支股票之間間隔30秒

    # 先將民國年轉換為西元年
    def convert_taiwan_date_to_gregorian(self, taiwan_date_str):
        parts = taiwan_date_str.split('/')
        year = int(parts[0]) + 1911  # 民國年轉換為西元年
        return f"{year}/{parts[1]}/{parts[2]}"
    
    def download_otc_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date):
        self.write_log(f"開始處理上櫃股票 {stock_id}")
        print(f"開始處理上櫃股票 {stock_id}")
        view.append_log(f"開始處理上櫃股票 {stock_id}")
        current_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        while current_date <= end_date:
            try:
                date_str = self.convert_to_taiwan_date(current_date)  # 将日期格式化为YYYY/mm
                # 根據日期和股票代碼來構建請求URL
                resp = requests.get(
                    f'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_download.php?' +
                    f'l=zh-tw&d={date_str}&stkno={stock_id}&s=0,asc,0'
                )
            
                if resp.status_code != 200:
                    raise Exception(f'HTTP response code is not 200: {resp.status_code}')
            
                # 解析CSV數據
                lines = io.StringIO(resp.text).readlines()
                lines = lines[4:-1]  # 去除前4行和最後1行
                reader = csv.DictReader(io.StringIO('\n'.join(lines)))

                for row in reader:
                    gregorian_date_str = self.convert_taiwan_date_to_gregorian(row['日 期'].strip())
                    date = pd.to_datetime(gregorian_date_str, format='%Y/%m/%d').strftime('%Y-%m-%d')
                    open_price = float(row['開盤'].replace(',', '').strip())
                    high_price = float(row['最高'].replace(',', '').strip())
                    low_price = float(row['最低'].replace(',', '').strip())
                    close_price = float(row['收盤'].replace(',', '').strip())
                    volume = int(row['成交仟股'].replace(',', '').strip())

                    cursor.execute(
                        """INSERT INTO stock_data 
                        (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (stock_id, date, open_price, high_price, low_price, close_price, volume)
                    )
                    conn.commit()

                    self.write_log(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")
                    print(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")
                    view.append_log(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")
                time.sleep(1)  # 每天間隔1秒

            except Exception as e:
                self.write_log(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                print(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                view.append_log(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")

            current_date += pd.DateOffset(months=1)  # 每次移動到下一個月的開始日期
        time.sleep(30)  # 每支股票之間間隔30秒
        
    def convert_to_taiwan_date(self, current_date):
        year = current_date.year - 1911  # 将年份转换为民国年
        taiwan_date_str = f"{year}/{current_date.strftime('%m')}"
        return taiwan_date_str
    
    def check_stock_exists(self, stock_id):
        conn = self.connect_db()
        cursor = conn.cursor()
    
        # SQL query to check if the stock exists
        query = "SELECT COUNT(1) FROM StockTable WHERE id = %s"
        cursor.execute(query, (stock_id,))
    
        # Fetch the result
        result = cursor.fetchone()
    
        # Close the connection
        conn.close()
    
        # If result[0] > 0, the stock exists
        return result[0] > 0
