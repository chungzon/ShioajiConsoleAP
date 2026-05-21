import pymssql
import pandas as pd
import time
import os
from datetime import date, datetime, timedelta
import shioaji as sj
import csv
import io
import requests
from common.Event import Event
import json


class DailyClosePriceDownloadModel:
      
    # 創建log資料夾和檔案
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def __init__(self, api):
        self.api = api
        self.log_filename = "logs/stock_download.log"
        # 獲取當前文件的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 構建相對路徑
        resource_dir = os.path.join(current_dir, '..', 'resource')
        self.tw_all_stocks_file = os.path.join(resource_dir, 'tw_all_stocks.csv')
        self.event = Event()
        # 共用的資料庫連線（延遲建立，重複使用，不每次重連）
        self.conn = None
        self.cursor = None
  

    def write_log(self, message):
        with open(self.log_filename, "a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn

    def get_db(self):
        """取得共用的資料庫連線。

        若連線已存在且仍然有效則重複使用，否則重新建立，
        避免每次呼叫都重新連線。回傳 (conn, cursor)。
        """
        try:
            if self.conn is not None and self.cursor is not None:
                # 測試連線是否仍然有效
                self.cursor.execute("SELECT 1")
                self.cursor.fetchall()
                return self.conn, self.cursor
        except Exception:
            # 連線已失效，關閉後重建
            self.close_db()

        self.conn = self.connect_db()
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def close_db(self):
        """關閉共用的資料庫連線（程式結束或不再使用時呼叫）。"""
        try:
            if self.cursor is not None:
                self.cursor.close()
        except Exception:
            pass
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            pass
        self.cursor = None
        self.conn = None

    def download_daily_close_top30_stock(self, view, start_date, end_date, stock_id=None):
        # 確保資料庫結構正確
        if not self.ensure_database_structure():
            self.write_log("無法確保資料庫結構，退出下載程序")
            return
        
        conn = self.connect_db()
        cursor = conn.cursor()

        if stock_id:
            if self.check_stock_exists(stock_id):
                self.download_stock_data(self.api, stock_id, conn, cursor, view, start_date, end_date)
            else:
                self.download_otc_stock_data(self.api, stock_id, conn, cursor, view, start_date, end_date)
        else:
            # 讀取 CSV 檔案，取得所有股票代碼
            stock_df = pd.read_csv(self.tw_all_stocks_file)
            print(stock_df.columns)  # 打印出列標題名稱
            top_30_stocks = stock_df['StockCode']
            # 下載資料並存入資料庫
            for code in top_30_stocks:
                if self.check_stock_exists(code):
                    self.download_stock_data(self.api, code, conn, cursor, view, start_date, end_date)
                else:
                    self.download_otc_stock_data(self.api, code, conn, cursor, view, start_date, end_date)

        # 關閉資料庫連接
        cursor.close()
        conn.close()

    def write_log(self, message):
        with open(self.log_filename, "a", encoding="utf-8") as log_file:
            log_file.write(f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def download_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date, is_retry=False):
        self.write_log(f"開始處理股票 {stock_id}")
        print(f"開始處理股票 {stock_id}")
        # view.append_log(f"開始處理股票 {stock_id}")
        self.event.notify(f"開始處理股票 {stock_id}")
        current_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        while current_date <= end_date:
            retry_count = 0
            max_retries = 1
            
            while retry_count < max_retries:
                try:
                    date_str = current_date.strftime('%Y%m')  # 将日期格式化为YYYYmm
                    # 根據日期和股票代碼來構建請求URL
                    resp = requests.get(
                        f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?' +
                        f'response=csv&date={date_str}01&stockNo={stock_id}',
                        timeout=30)
                    
                    if resp.status_code != 200:
                        raise Exception(f'HTTP response code is not 200: {resp.status_code}')
                    
                    # 解析CSV數據
                    lines = io.StringIO(resp.text).readlines()
                    lines = lines[1:-5]  # 去除第一行和最後五行
                    # 檢查是否包含說明列，並只保留有效數據
                    if '說明' in lines[-1]:
                        lines = lines[:lines.index('"說明:"\r\n')]
                    reader = csv.DictReader(io.StringIO('\n'.join(lines)))

                    # 收集所有資料，使用 MERGE 語句一次性處理
                    stock_data_list = []
                    for row in reader:
                        gregorian_date_str = self.convert_taiwan_date_to_gregorian(row['日期'].strip())
                        date = pd.to_datetime(gregorian_date_str, format='%Y/%m/%d').strftime('%Y-%m-%d')
                        # {'日期': '114/08/19', '成交股數': '289', '成交金額': '3,622', '開盤價': '--', '最高價': '--', '最低價': '--', '收盤價': '--', '漲跌價差': ' 0.00', '成交筆數': '2', '': ''}
                        volume = int(row['成交股數'].replace(',', '').strip())
                        str_open_price = row['開盤價'].replace(',', '').strip()
                        str_high_price = row['最高價'].replace(',', '').strip()
                        str_low_price = row['最低價'].replace(',', '').strip()
                        str_close_price = row['收盤價'].replace(',', '').strip()
                        
                        if volume < 1000 and (str_open_price == '--' and str_high_price == '--' and str_low_price == '--' and str_close_price == '--'):
                            open_price = 0.0
                            high_price = 0.0
                            low_price = 0.0
                            close_price = 0.0
                            volume = 0
                        else:
                            open_price = float(str_open_price) if str_open_price != '--' else 0.0
                            high_price = float(str_high_price) if str_high_price != '--' else 0.0
                            low_price = float(str_low_price) if str_low_price != '--' else 0.0
                            close_price = float(str_close_price) if str_close_price != '--' else 0.0
                        
                        stock_data_list.append((stock_id, date, open_price, high_price, low_price, close_price, volume))

                    # 使用 MERGE 語句避免重複資料
                    if stock_data_list:
                        self.merge_stock_data_batch(conn, cursor, stock_data_list)
                        self.write_log(f"成功處理 {stock_id} - {current_date.strftime('%Y-%m')} 共 {len(stock_data_list)} 筆資料")
                        print(f"成功處理 {stock_id} - {current_date.strftime('%Y-%m')} 共 {len(stock_data_list)} 筆資料")
                        self.event.notify(f"成功處理 {stock_id} - {current_date.strftime('%Y-%m')} 共 {len(stock_data_list)} 筆資料")
                    
                    break  # 成功處理，跳出重試迴圈
                    
                except Exception as e:
                    retry_count += 1
                    self.write_log(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')} (重試 {retry_count}/{max_retries}): {e}")
                    print(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')} (重試 {retry_count}/{max_retries}): {e}")
                    self.event.notify(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')} (重試 {retry_count}/{max_retries}): {e}")
                    
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)  # 指數退避
                    else:
                        if str(e) == 'No data available' and not is_retry:
                            # view.append_log(f"上市股票 {stock_id} 無資料")
                            self.event.notify(f"上市股票 {stock_id} 無資料")
                            # view.append_log(f"嘗試從上櫃股票處理 {stock_id}")
                            self.event.notify(f"嘗試從上櫃股票處理 {stock_id}") 
                            self.download_otc_stock_data(api, stock_id, conn, cursor, view, start_date, end_date, is_retry=True)
                        break

            time.sleep(1)  # 每天間隔1秒
            current_date += pd.DateOffset(months=1)  # 每次移動到下一個月的開始日期
        time.sleep(5)  # 每支股票之間間隔5秒

    # 先將民國年轉換為西元年
    def convert_taiwan_date_to_gregorian(self, taiwan_date_str):
        parts = taiwan_date_str.split('/')
        year = int(parts[0]) + 1911  # 民國年轉換為西元年
        return f"{year}/{parts[1]}/{parts[2]}"
    
    def download_otc_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date, is_retry=False):
        self.write_log(f"開始處理上櫃股票 {stock_id}")
        print(f"開始處理上櫃股票 {stock_id}")
        # view.append_log(f"開始處理上櫃股票 {stock_id}")
        self.event.notify(f"開始處理上櫃股票 {stock_id}")
        current_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        while current_date <= end_date:
            retry_count = 0
            max_retries = 1
            
            while retry_count < max_retries:
                try:
                    # 將日期轉換為YYYY/MM/DD格式
                    date_str = current_date.strftime('%Y/%m/%d')
                    
                    # 使用新的API URL
                    url = f'https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?response=&date={date_str}&code={stock_id}'
                    resp = requests.get(url, timeout=30)
                
                    if resp.status_code != 200:
                        raise Exception(f'HTTP response code is not 200: {resp.status_code}')
                
                    # 解析JSON數據
                    json_data = resp.json()
                    if json_data['stat'] != 'ok':
                        raise Exception('API response status is not ok')

                    # 獲取數據表
                    if not json_data['tables'] or not json_data['tables'][0]['data']:
                        raise Exception('No data available')

                    data_rows = json_data['tables'][0]['data']
                    
                    # 收集所有資料，使用 MERGE 語句一次性處理
                    stock_data_list = []
                    for row in data_rows:
                        # 檢查數據是否有效
                        if '--' in [row[3], row[4], row[5], row[6]]:  # 開盤、最高、最低、收盤價位置
                            continue

                        # 轉換民國日期為西元日期
                        gregorian_date_str = self.convert_taiwan_date_to_gregorian(row[0].strip())
                        date = pd.to_datetime(gregorian_date_str, format='%Y/%m/%d').strftime('%Y-%m-%d')
                        
                        # 解析數據
                        volume = int(row[1].replace(',', '').strip())
                        open_price = float(row[3].replace(',', '').strip())
                        high_price = float(row[4].replace(',', '').strip())
                        low_price = float(row[5].replace(',', '').strip())
                        close_price = float(row[6].replace(',', '').strip())

                        stock_data_list.append((stock_id, date, open_price, high_price, low_price, close_price, volume))

                    # 使用 MERGE 語句避免重複資料
                    if stock_data_list:
                        self.merge_stock_data_batch(conn, cursor, stock_data_list)
                        self.write_log(f"成功處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')} 共 {len(stock_data_list)} 筆資料")
                        print(f"成功處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')} 共 {len(stock_data_list)} 筆資料")
                        self.event.notify(f"成功處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')} 共 {len(stock_data_list)} 筆資料")

                    break  # 成功處理，跳出重試迴圈

                except Exception as e:
                    retry_count += 1
                    self.write_log(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')} (重試 {retry_count}/{max_retries}): {e}")
                    print(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')} (重試 {retry_count}/{max_retries}): {e}")
                    self.event.notify(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')} (重試 {retry_count}/{max_retries}): {e}")
                    
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)  # 指數退避
                    else:
                        if str(e) == 'No data available' and not is_retry:
                            # view.append_log(f"上櫃股票 {stock_id} 無資料")
                            self.event.notify(f"上櫃股票 {stock_id} 無資料")
                            # view.append_log(f"嘗試從上市股票處理 {stock_id}")
                            self.event.notify(f"嘗試從上市股票處理 {stock_id}")
                            self.download_stock_data(api, stock_id, conn, cursor, view, start_date, end_date)
                        break

            time.sleep(1)  # 每天間隔1秒
            current_date += pd.DateOffset(months=1)  # 每次移動到下一個月的開始日期
        time.sleep(5)  # 每支股票之間間隔5秒
        
    def convert_to_taiwan_date(self, current_date):
        year = current_date.year - 1911  # 将年份转换为民国年
        taiwan_date_str = f"{year}/{current_date.strftime('%m')}"
        return taiwan_date_str
    
    def check_stock_exists(self, stock_id):
        conn = self.connect_db()
        cursor = conn.cursor()
    
        try:
            # SQL query to check if the stock exists - 使用字串比較而不是整數
            query = "SELECT COUNT(1) FROM StockTable WHERE id = %s"
            cursor.execute(query, (str(stock_id),))
    
            # Fetch the result
            result = cursor.fetchone()
    
            # If result[0] > 0, the stock exists
            return result[0] > 0
        except Exception as e:
            self.write_log(f"檢查股票 {stock_id} 是否存在時發生錯誤: {e}")
            return False
        finally:
            # Close the connection
            cursor.close()
            conn.close()

    def download_daily_close_price(self):
        """下載每日收盤價數據的任務"""
        from datetime import date, datetime
        import logging
        
        # 设置日志记录器
        logger = logging.getLogger('DailyClosePriceDownloadModel')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        
        # self.write_log(f'開始下載 {today_str} 的每日收盤價數據')
        logger.info(f"开始下载 {today_str} 的每日收盘价数据")

        start_time = datetime.now()
        success = False
        
        try:
            # 检查是否已经下载过
            if not self.ensure_system_config_table():
                logger.error("無法確保 system_config 表存在,退出程序")
                raise Exception("无法确保系统配置表存在")

            last_download_date = self.get_last_download_date()
            if last_download_date is None:
                logger.error("無法獲取上次下載日期,退出程序")
                raise Exception("无法获取上次下载日期")

            if today <= last_download_date:
                logger.info(f"今天 ({today}) 的數據已經下載過了,最後下載日期為 {last_download_date}")
                self.write_log(f'今天 ({today}) 的數據已經下載過了')
                return

            # 下载TWSE数据
            logger.info("開始從 TWSE 下載每日收盤價數據")
            twse_data = self.download_data_from_twse()
            if twse_data:
                if self.insert_data_to_database(twse_data, is_twse=True):
                    logger.info(f"成功下載TWSE數據，共 {len(twse_data)} 筆")
                    success = True
                else:
                    logger.error("TWSE數據插入數據庫失敗")
            else:
                logger.error("無法從TWSE獲取數據")

            # 下载TPEx数据
            logger.info("開始從 TPEx 下載每日收盤價數據")
            tpex_data = self.download_data_from_tpex()
            if tpex_data:
                if self.insert_data_to_database(tpex_data, is_twse=False):
                    logger.info(f"成功下載TPEx數據，共 {len(tpex_data)} 筆")
                    success = True
                else:
                    logger.error("TPEx數據插入數據庫失敗")
            else:
                logger.error("無法從TPEx獲取數據")

            # 更新最后下载日期
            if self.update_last_download_date(today):
                logger.info(f"成功更新最後下載日期為 {today}")
            else:
                logger.error("更新最後下載日期失敗")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if success:
                message = f'{today_str} 每日收盤價數據下載成功,耗時 {duration:.2f} 秒'
            else:
                message = f'{today_str} 每日收盤價數據下載失敗,請檢查日誌'

            # self.write_log(message)
            print(f"✅ {message}")
            logger.info(f"下载任务完成: {message}")
            
        except Exception as e:
            error_message = f'{today_str} 每日收盤價數據下載過程中發生錯誤: {str(e)}'
            # self.write_log(error_message)
            print(f"❌ {error_message}")
            logger.error(f"下载任务异常: {error_message}")
        finally:
            # 關閉共用的資料庫連線
            self.close_db()

    def download_daily_close_price_all(self, view, start_date, end_date):
        self.download_daily_close_top30_stock(view, start_date, end_date)

    def download_close_price_by_range(self, start_date, end_date):
        """依指定日期區間下載 TWSE + TPEx 收盤價資料"""
        # if not self.ensure_database_structure():
        #     self.write_log("無法確保資料庫結構，退出下載程序")
        #     return

        try:
            current = start_date
            while current <= end_date:
                # 跳過週六日
                if current.weekday() >= 5:
                    current += timedelta(days=1)
                    continue

                date_label = current.strftime('%Y-%m-%d')
                self.event.notify(f"開始下載 {date_label} 收盤價資料...")

                # 下載 TWSE
                twse_data = self.download_data_from_twse(current)
                if twse_data:
                    self.insert_data_to_database(twse_data, is_twse=True)
                    self.event.notify(f"TWSE {date_label} 共 {len(twse_data)} 筆")
                else:
                    self.event.notify(f"TWSE {date_label} 無資料")

                time.sleep(3)

                # 下載 TPEx
                tpex_data = self.download_data_from_tpex(current)
                if tpex_data:
                    self.insert_data_to_database(tpex_data, is_twse=False)
                    self.event.notify(f"TPEx {date_label} 共 {len(tpex_data)} 筆")
                else:
                    self.event.notify(f"TPEx {date_label} 無資料")

                time.sleep(3)
                current += timedelta(days=1)

            self.event.notify("收盤價日期區間下載完成")
        finally:
            # 關閉共用的資料庫連線
            self.close_db()

    def ensure_system_config_table(self):
        """确保系统配置表存在"""
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_config' AND xtype='U')
                CREATE TABLE system_config (
                    name VARCHAR(100) PRIMARY KEY,
                    value VARCHAR(100)
                )
            """)
            conn.commit()
            return True
        except Exception as err:
            self.write_log(f"創建 system_config 表時發生錯誤: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_last_download_date(self):
        """获取上次下载日期"""
        conn = self.connect_db()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM system_config WHERE name = 'last_download_date'")
            result = cursor.fetchone()
            if result:
                return datetime.strptime(result[0], '%Y-%m-%d').date()
            else:
                # 如果參數不存在,創建它並設置為前一天
                yesterday = date.today() - timedelta(days=1)
                cursor.execute(
                    "INSERT INTO system_config (name, value) VALUES (%s, %s)",
                    ('last_download_date', yesterday.strftime('%Y-%m-%d'))
                )
                conn.commit()
                return yesterday
        except Exception as err:
            self.write_log(f"獲取上次下載日期時發生錯誤: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def update_last_download_date(self, download_date):
        """更新最后下载日期"""
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        try:
            cursor.execute("""
                IF EXISTS (SELECT * FROM system_config WHERE name = 'last_download_date')
                    UPDATE system_config SET value = %s WHERE name = 'last_download_date'
                ELSE
                    INSERT INTO system_config (name, value) VALUES ('last_download_date', %s)
            """, (download_date.strftime('%Y-%m-%d'), download_date.strftime('%Y-%m-%d')))
            conn.commit()
            return True
        except Exception as err:
            self.write_log(f"更新上次下載日期時發生錯誤: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def download_data_from_twse(self, target_date=None):
        """从TWSE下载数据"""
        try:
            if target_date is None:
                target_date = date.today()
            date_str = target_date.strftime('%Y%m%d')

            # 根據日期和股票代碼來構建請求URL
            resp = requests.get(
                f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALLBUT0999&response=csv')

            if resp.status_code != 200:
                raise Exception(f'HTTP response code is not 200: {resp.status_code}')
                    
            # 解析CSV數據
            lines = io.StringIO(resp.text).readlines()
            # 找到目標字符串所在的行
            TARGET_STRING = "每日收盤行情(全部(不含權證、牛熊證、可展延牛熊證))"
            start_index = next((i for i, line in enumerate(lines) if TARGET_STRING in line), -1)
            
            if start_index == -1:
                raise Exception(f"未找到包含 '{TARGET_STRING}' 的行")
            
            # 漲跌(+/-)欄位符號說明:+/-/X表示漲/跌/不比價。
            end_index = next((i for i, line in enumerate(lines) if '漲跌(+/-)欄位符號說明:+/-/X表示漲/跌/不比價。' in line), -1)
            
            # 從目標字符串後的第三行開始讀取數據
            lines = lines[start_index + 2:end_index - 1]

            reader = csv.DictReader(io.StringIO('\n'.join(lines)))
            conn = self.connect_db()
            if not conn:
                return None
            
            data = []
            for row in reader:
                try:
                    stock_id = row['證券代號'].strip()
                    stock_name = row['證券名稱'].strip()
                    if row['開盤價'] is not None:
                        open_price = self.parse_float(row['開盤價'].replace(',', '').strip())
                    else:
                        open_price = None

                    if row['最高價'] is not None:
                        high_price = self.parse_float(row['最高價'].replace(',', '').strip())
                    else:
                        high_price = None

                    if row['最低價'] is not None:
                        low_price = self.parse_float(row['最低價'].replace(',', '').strip())
                    else:
                        low_price = None

                    if row['收盤價'] is not None:
                        close_price = self.parse_float(row['收盤價'].replace(',', '').strip())
                    else:
                        close_price = None

                    if row['成交股數'] is not None:
                        volume = self.parse_int(row['成交股數'])
                    else:
                        volume = None

                    stock_data = {
                        'Code': stock_id,
                        'Name': stock_name,
                        'Date': target_date.strftime('%Y-%m-%d'),
                        'OpeningPrice': open_price,
                        'HighestPrice': high_price,
                        'LowestPrice': low_price,
                        'ClosingPrice': close_price,
                        'TradeVolume': volume
                    }
                    data.append(stock_data)
                except Exception as e:
                    self.write_log(f"處理TWSE數據時發生錯誤: {e}")

            return data

        except Exception as e:
            self.write_log(f"下載TWSE數據時發生錯誤: {e}")
            return None

    def download_data_from_tpex(self, target_date=None):
        """从TPEx下载数据（使用 mi-pricing CSV 串流）"""
        try:
            if target_date is None:
                target_date = date.today()
            roc_year = target_date.year - 1911
            roc_date = f"{roc_year}/{target_date.strftime('%m/%d')}"
            date_str = target_date.strftime('%Y-%m-%d')

            url = (
                'https://www.tpex.org.tw/web/stock/aftertrading/'
                'otc_quotes_no1430/stk_wn1430_result.php'
                f'?l=zh-tw&d={roc_date}&se=EW&sect=EW&o=csv'
            )
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            # CSV 以 Big5 編碼回傳
            content = resp.content.decode('big5', errors='replace')
            lines = content.splitlines()

            # 跳過空行和標題行，找到欄位標頭
            # CSV 格式：前幾行可能是標題/空行，欄位標頭包含「代號」
            header_idx = None
            for i, line in enumerate(lines):
                if '代號' in line:
                    header_idx = i
                    break

            if header_idx is None:
                raise Exception('無法找到 CSV 欄位標頭')

            # 從標頭行開始解析
            csv_text = '\n'.join(lines[header_idx:])
            reader = csv.DictReader(io.StringIO(csv_text))

            data = []
            for row in reader:
                try:
                    # CSV 欄位標頭含有不固定的前後空白（例如 '收盤 '、'成交股數  '），
                    # 先把每個 key 去除空白後重建，否則 row.get('收盤') 會取不到值
                    row = {(k or '').strip(): v for k, v in row.items()}

                    # row.get(key) 在欄位缺值時會回傳 None，需用 (... or '') 兜底
                    stock_id = (row.get('代號') or '').strip()
                    # 跳過非股票資料列：空白行、檔尾統計行（「共1007筆」）、
                    # 說明文字（「ETF證券代號第六碼...」）等
                    if not self.is_valid_stock_code(stock_id):
                        continue

                    stock_name = (row.get('名稱') or '').strip()
                    close_price = self.parse_float((row.get('收盤') or '').replace(',', '').strip())
                    open_price = self.parse_float((row.get('開盤') or '').replace(',', '').strip())
                    high_price = self.parse_float((row.get('最高') or '').replace(',', '').strip())
                    low_price = self.parse_float((row.get('最低') or '').replace(',', '').strip())
                    volume = self.parse_int((row.get('成交股數') or '').replace(',', '').strip())

                    data.append({
                        'Code': stock_id,
                        'Name': stock_name,
                        'Date': date_str,
                        'OpeningPrice': open_price,
                        'HighestPrice': high_price,
                        'LowestPrice': low_price,
                        'ClosingPrice': close_price,
                        'TradeVolume': volume
                    })
                except Exception as e:
                    self.write_log(f"處理TPEx CSV行時發生錯誤: {e}")

            return data

        except Exception as e:
            self.write_log(f"TPEx CSV 下載錯誤: {e}")
            return None

    def insert_data_to_database(self, data, is_twse):
        """将数据插入数据库，使用 MERGE 语句避免重复数据"""
        # 取得共用連線，不每次重新連線
        conn, cursor = self.get_db()
        today = date.today().strftime('%Y-%m-%d')

        try:
            # 准备批量数据
            stock_data_list = []
            for stock in data:
                code = stock['Code'].replace('=', '').replace('"', '').strip()
                # 跳過異常代號（檔尾統計行、說明文字等）：
                # 非法代號會超出 stock_id VARCHAR(10) 或污染資料，
                # 嚴重時導致整批 MERGE 失敗、整天資料回滾遺失
                if not self.is_valid_stock_code(code):
                    self.write_log(f"略過異常股票代號: {code!r}")
                    continue
                values = (
                    code,
                    stock.get('Date', today),
                    stock['OpeningPrice'],
                    stock['HighestPrice'],
                    stock['LowestPrice'],
                    stock['ClosingPrice'],
                    stock['TradeVolume']
                )
                stock_data_list.append(values)

            # 使用 MERGE 语句批量处理
            if stock_data_list:
                if self.merge_stock_data_batch(conn, cursor, stock_data_list):
                    self.write_log(f"數據已成功下載並存儲到 stock_data 表中，日期為 {today}，共 {len(stock_data_list)} 筆資料")
                    return True
                else:
                    self.write_log(f"數據寫入 stock_data 表失敗，日期為 {today}（詳見上方 MERGE 錯誤）")
                    return False
            else:
                self.write_log(f"沒有有效數據需要插入，日期為 {today}")
                return True

        except Exception as err:
            self.write_log(f"數據插入錯誤: {err}")
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def merge_stock_data_batch(self, conn, cursor, stock_data_list):
        """使用 MERGE 語句批量處理股票資料，避免重複資料"""
        try:
            # 若上次執行殘留臨時表，先清掉（連線重複使用時的保險）
            cursor.execute(
                "IF OBJECT_ID('tempdb..#temp_stock_data') IS NOT NULL "
                "DROP TABLE #temp_stock_data"
            )

            # 創建臨時表來存儲批量資料
            # stock_id 加上 COLLATE DATABASE_DEFAULT，讓臨時表使用 TSE 資料庫的定序，
            # 避免與 stock_data 表 (Chinese_Taiwan_Stroke_CI_AS) 比對時定序衝突。
            # volume 改用 BIGINT，避免成交股數超過 int 上限造成溢位。
            cursor.execute("""
                CREATE TABLE #temp_stock_data (
                    stock_id VARCHAR(10) COLLATE DATABASE_DEFAULT,
                    date DATE,
                    open_price FLOAT,
                    high_price FLOAT,
                    low_price FLOAT,
                    close_price FLOAT,
                    volume BIGINT
                )
            """)
            
            # 批量插入到臨時表
            insert_sql = """
                INSERT INTO #temp_stock_data 
                (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_sql, stock_data_list)
            
            # 使用 MERGE 語句合併資料
            merge_sql = """
                MERGE stock_data AS target
                USING #temp_stock_data AS source
                ON target.stock_id = source.stock_id AND target.date = source.date
                WHEN MATCHED THEN
                    UPDATE SET 
                        open_price = source.open_price,
                        high_price = source.high_price,
                        low_price = source.low_price,
                        close_price = source.close_price,
                        volume = source.volume
                WHEN NOT MATCHED THEN
                    INSERT (stock_id, date, open_price, high_price, low_price, close_price, volume)
                    VALUES (source.stock_id, source.date, source.open_price, source.high_price, 
                           source.low_price, source.close_price, source.volume);
            """
            cursor.execute(merge_sql)
            
            # 刪除臨時表
            cursor.execute("DROP TABLE #temp_stock_data")
            
            conn.commit()
            return True
            
        except Exception as e:
            self.write_log(f"MERGE 語句執行錯誤: {e}")
            conn.rollback()
            return False

    def parse_float(self, value):
        """解析浮点数"""
        return float(value) if value not in ['--', '----', ''] else None

    def parse_int(self, value):
        """解析整数"""
        return int(value.replace(',', '')) if value not in ['--', '----', ''] else None

    def is_valid_stock_code(self, code):
        """判斷字串是否為有效的股票代號。

        有效代號為純 ASCII 英數字（例如 2330、0050、00679B、020033）。
        可濾掉 CSV 檔尾的統計行（如「共1007筆」）與說明文字
        （如「ETF證券代號第六碼...」），避免被當成股票資料寫入。
        """
        code = (code or '').strip()
        return bool(code) and code.isascii() and code.isalnum() and len(code) <= 10

    def convert_tw_date_to_ad(self, tw_date_str):
        """转换台湾日期为西元日期"""
        tw_date_str = str(tw_date_str)
        
        if len(tw_date_str) != 7:
            raise ValueError("輸入的日期格式不正確。應為 7 位數字，例如 '1131004'")
        
        tw_year = int(tw_date_str[:3])
        month = int(tw_date_str[3:5])
        day = int(tw_date_str[5:])
        
        ad_year = tw_year + 1911
        date_obj = datetime(ad_year, month, day)
        
        return date_obj.strftime('%Y-%m-%d')

    def ensure_database_structure(self):
        """確保資料庫結構正確，包括表格、索引和約束"""
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        try:
            # 檢查並創建 stock_data 表格
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='stock_data' AND xtype='U')
                CREATE TABLE stock_data (
                    stock_id VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    open_price FLOAT,
                    high_price FLOAT,
                    low_price FLOAT,
                    close_price FLOAT,
                    volume BIGINT,
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE(),
                    CONSTRAINT PK_stock_data PRIMARY KEY (stock_id, date)
                )
            """)
            
            # 檢查並創建索引
            indexes = [
                ("IX_stock_data_stock_id", "CREATE INDEX IX_stock_data_stock_id ON stock_data (stock_id)"),
                ("IX_stock_data_date", "CREATE INDEX IX_stock_data_date ON stock_data (date)"),
                ("IX_stock_data_stock_date", "CREATE INDEX IX_stock_data_stock_date ON stock_data (stock_id, date)")
            ]
            
            for index_name, create_sql in indexes:
                cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = '{index_name}' AND object_id = OBJECT_ID('stock_data'))
                    {create_sql}
                """)
            
            conn.commit()
            self.write_log("資料庫結構檢查完成")
            return True
            
        except Exception as e:
            self.write_log(f"資料庫結構檢查錯誤: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def check_data_integrity(self, stock_id=None, start_date=None, end_date=None):
        """檢查資料完整性，找出可能的遺漏或重複資料"""
        conn = self.connect_db()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            # 檢查重複資料
            if stock_id:
                cursor.execute("""
                    SELECT stock_id, date, COUNT(*) as count
                    FROM stock_data 
                    WHERE stock_id = %s
                    GROUP BY stock_id, date
                    HAVING COUNT(*) > 1
                """, (stock_id,))
            else:
                cursor.execute("""
                    SELECT stock_id, date, COUNT(*) as count
                    FROM stock_data 
                    GROUP BY stock_id, date
                    HAVING COUNT(*) > 1
                """)
            
            duplicates = cursor.fetchall()
            
            # 檢查資料遺漏（簡單檢查：檢查是否有連續日期缺失）
            if stock_id and start_date and end_date:
                cursor.execute("""
                    WITH date_series AS (
                        SELECT CAST(dateadd(day, number, %s) AS DATE) as date
                        FROM master.dbo.spt_values
                        WHERE type = 'P' AND number <= DATEDIFF(day, %s, %s)
                    )
                    SELECT ds.date
                    FROM date_series ds
                    LEFT JOIN stock_data sd ON ds.date = sd.date AND sd.stock_id = %s
                    WHERE sd.date IS NULL
                    AND ds.date NOT IN (
                        SELECT date FROM stock_data WHERE stock_id = %s
                    )
                    ORDER BY ds.date
                """, (start_date, start_date, end_date, stock_id, stock_id))
                
                missing_dates = cursor.fetchall()
            else:
                missing_dates = []
            
            result = {
                'duplicates': duplicates,
                'missing_dates': missing_dates,
                'total_duplicates': len(duplicates),
                'total_missing': len(missing_dates)
            }
            
            if duplicates:
                self.write_log(f"發現 {len(duplicates)} 筆重複資料")
            if missing_dates:
                self.write_log(f"發現 {len(missing_dates)} 個遺漏日期")
                
            return result
            
        except Exception as e:
            self.write_log(f"資料完整性檢查錯誤: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def clean_duplicate_data(self, stock_id=None):
        """清理重複資料，保留最新的記錄"""
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        try:
            if stock_id:
                # 清理特定股票的重複資料
                cursor.execute("""
                    WITH RankedData AS (
                        SELECT *,
                               ROW_NUMBER() OVER (PARTITION BY stock_id, date ORDER BY updated_at DESC) as rn
                        FROM stock_data
                        WHERE stock_id = %s
                    )
                    DELETE FROM stock_data
                    WHERE stock_id = %s
                    AND (stock_id, date, updated_at) IN (
                        SELECT stock_id, date, updated_at
                        FROM RankedData
                        WHERE rn > 1
                    )
                """, (stock_id, stock_id))
            else:
                # 清理所有重複資料
                cursor.execute("""
                    WITH RankedData AS (
                        SELECT *,
                               ROW_NUMBER() OVER (PARTITION BY stock_id, date ORDER BY updated_at DESC) as rn
                        FROM stock_data
                    )
                    DELETE FROM stock_data
                    WHERE (stock_id, date, updated_at) IN (
                        SELECT stock_id, date, updated_at
                        FROM RankedData
                        WHERE rn > 1
                    )
                """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                self.write_log(f"成功清理 {deleted_count} 筆重複資料")
            else:
                self.write_log("沒有發現重複資料需要清理")
                
            return True
            
        except Exception as e:
            self.write_log(f"清理重複資料錯誤: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
        