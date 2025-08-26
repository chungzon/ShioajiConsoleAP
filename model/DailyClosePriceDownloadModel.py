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
        
    def download_daily_close_top30_stock(self, view, start_date, end_date, stock_id=None):
        
        
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
        with open(self.log_filename, "a") as log_file:
            log_file.write(f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def download_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date, is_retry=False):
        self.write_log(f"開始處理股票 {stock_id}")
        print(f"開始處理股票 {stock_id}")
        # view.append_log(f"開始處理股票 {stock_id}")
        self.event.notify(f"開始處理股票 {stock_id}")
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
                    # {'日期': '114/08/19', '成交股數': '289', '成交金額': '3,622', '開盤價': '--', '最高價': '--', '最低價': '--', '收盤價': '--', '漲跌價差': ' 0.00', '成交筆數': '2', '': ''}
                    volume = int(row['成交股數'].replace(',', '').strip())
                    str_open_price = row['開盤價'].replace(',', '').strip()
                    str_high_price = row['最高價'].replace(',', '').strip()
                    str_low_price = row['最低價'].replace(',', '').strip()
                    str_close_price = row['收盤價'].replace(',', '').strip()
                    if volume < 1000 and (str_open_price == '--' and str_high_price == '--' and str_low_price == '--' and str_close_price == '--'):
                        open_price = close_price
                        high_price = close_price
                        low_price = close_price
                        close_price = close_price
                        volume = 0
                    else:
                        open_price = float(str_open_price)
                        high_price = float(str_high_price)
                        low_price = float(str_low_price)
                        close_price = float(str_close_price)
                    
                    cursor.execute(
                        """INSERT INTO stock_data 
                        (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (stock_id, date, open_price, high_price, low_price, close_price, volume)
                    )
                    conn.commit()

                    self.write_log(f"成功處理 {stock_id} - {gregorian_date_str}")
                    print(f"成功處理 {stock_id} - {gregorian_date_str}")
                    # view.append_log(f"成功處理 {stock_id} - {gregorian_date_str}")
                    self.event.notify(f"成功處理 {stock_id} - {gregorian_date_str}")
                time.sleep(1)  # 每天間隔1秒

            except Exception as e:
                self.write_log(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                print(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                # view.append_log(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                self.event.notify(f"錯誤處理 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                if str(e) == 'No data available' and not is_retry:
                    # view.append_log(f"上市股票 {stock_id} 無資料")
                    self.event.notify(f"上市股票 {stock_id} 無資料")
                    # view.append_log(f"嘗試從上櫃股票處理 {stock_id}")
                    self.event.notify(f"嘗試從上櫃股票處理 {stock_id}") 
                    self.download_otc_stock_data(self, api, stock_id, conn, cursor, view, start_date, end_date, is_retry=True)

            current_date += pd.DateOffset(months=1)  # 每次移動到下一個月的開始日期
        time.sleep(5)  # 每支股票之間間隔30秒

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
            try:
                # 將日期轉換為YYYY/MM/DD格式
                date_str = current_date.strftime('%Y/%m/%d')
                
                # 使用新的API URL
                url = f'https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?response=&date={date_str}&code={stock_id}'
                resp = requests.get(url)
            
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

                    cursor.execute(
                        """INSERT INTO stock_data 
                        (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (stock_id, date, open_price, high_price, low_price, close_price, volume)
                    )
                    conn.commit()

                    self.write_log(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")
                    print(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")
                    # view.append_log(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")
                    self.event.notify(f"成功處理上櫃股票 {stock_id} - {gregorian_date_str}")

                time.sleep(1)  # 每天間隔1秒

            except Exception as e:
                self.write_log(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                print(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                # view.append_log(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                self.event.notify(f"錯誤處理上櫃股票 {stock_id} - {current_date.strftime('%Y-%m')}: {e}")
                if str(e) == 'No data available' and not is_retry:
                    # view.append_log(f"上櫃股票 {stock_id} 無資料")
                    self.event.notify(f"上櫃股票 {stock_id} 無資料")
                    # view.append_log(f"嘗試從上市股票處理 {stock_id}")
                    self.event.notify(f"嘗試從上市股票處理 {stock_id}")
                    self.download_stock_data(api, stock_id, conn, cursor, view, start_date, end_date)

            current_date += pd.DateOffset(months=1)  # 每次移動到下一個月的開始日期
        time.sleep(5)  # 每支股票之間間隔30秒
        
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

    def download_data_from_twse(self):
        """从TWSE下载数据"""
        try:
            today = date.today().strftime('%Y%m%d')
            
            # 根據日期和股票代碼來構建請求URL
            resp = requests.get(
                f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={today}&type=ALLBUT0999&response=csv')

            if resp.status_code != 200:
                raise Exception(f'HTTP response code is not 200: {resp.status_code}')
                    
            # 解析CSV數據
            lines = io.StringIO(resp.text).readlines()
            # 找到目標字符串所在的行
            TARGET_STRING = "每日收盤行情(全部(不含權證、牛熊證))"
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
                        'Date': today,
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

    def download_data_from_tpex(self):
        """从TPEx下载数据"""
        try:
            tpex_api_url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"
            response = requests.get(tpex_api_url)
            response.raise_for_status()
            return json.loads(response.text)
        except requests.RequestException as e:
            self.write_log(f"TPEx API 請求錯誤: {e}")
            return None

    def insert_data_to_database(self, data, is_twse):
        """将数据插入数据库"""
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        sql = """INSERT INTO stock_data 
                 (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""

        today = date.today().strftime('%Y-%m-%d')

        try:
            for stock in data:
                if is_twse:
                    values = (
                        stock['Code'].replace('=', '').replace('"', ''),
                        today,
                        stock['OpeningPrice'],
                        stock['HighestPrice'],
                        stock['LowestPrice'],
                        stock['ClosingPrice'],
                        stock['TradeVolume']
                    )
                else:  # TPEx data
                    values = (
                        stock['SecuritiesCompanyCode'].replace('=', '').replace('"', ''),
                        self.convert_tw_date_to_ad(stock['Date']),
                        self.parse_float(stock['Open']),
                        self.parse_float(stock['High']),
                        self.parse_float(stock['Low']),
                        self.parse_float(stock['Close']),
                        self.parse_int(stock['TradingShares'])
                    )
                cursor.execute(sql, values)

            conn.commit()
            self.write_log(f"數據已成功下載並存儲到 stock_data 表中，日期為 {today}")
            return True
        except Exception as err:
            self.write_log(f"數據插入錯誤: {err}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def parse_float(self, value):
        """解析浮点数"""
        return float(value) if value not in ['--', '----', ''] else None

    def parse_int(self, value):
        """解析整数"""
        return int(value.replace(',', '')) if value not in ['--', '----', ''] else None

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
        