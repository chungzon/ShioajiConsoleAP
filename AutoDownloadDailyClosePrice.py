import requests
import json
from datetime import date
import logging
import pymssql
import csv
import io
from datetime import datetime, timedelta

class AutoDownloadDailyClosePrice:
    def __init__(self):
        self.logger = self.setup_logger()
        self.twse_api_url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        self.tpex_api_url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"

    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn

    def setup_logger(self):
        logger = logging.getLogger('AutoDownloadDailyClosePrice')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def download_data_from_api(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return json.loads(response.text)
        except requests.RequestException as e:
            self.logger.error(f"API 請求錯誤: {e}")
            return None

    def insert_data_to_database(self, data, is_twse):
        conn = self.connect_db()
        if not conn:
            return

        cursor = conn.cursor()

        sql = """INSERT INTO stock_data 
                 (stock_id, date, open_price, high_price, low_price, close_price, volume) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""

        today = date.today().strftime('%Y-%m-%d')

        try:
            for stock in data:
                if is_twse:
                    values = (
                        stock['Code'],
                        today,
                        stock['OpeningPrice'],
                        stock['HighestPrice'],
                        stock['LowestPrice'],
                        stock['ClosingPrice'],
                        stock['TradeVolume']
                    )
                else:  # TPEx data
                    values = (
                        stock['SecuritiesCompanyCode'],
                        self.convert_tw_date_to_ad(stock['Date']),
                        self.parse_float(stock['Open']),
                        self.parse_float(stock['High']),
                        self.parse_float(stock['Low']),
                        self.parse_float(stock['Close']),
                        self.parse_int(stock['TradingShares'])
                    )
                cursor.execute(sql, values)

            conn.commit()
            self.logger.info(f"數據已成功下載並存儲到 stock_data 表中，日期為 {today}")
            return True
        except pymssql.Error as err:
            self.logger.error(f"數據插入錯誤: {err}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def download_data_from_twse(self):
        try:
            today = date.today().strftime('%Y%m%d')  # 将日期格式化为YYYYmm，20241001
            
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
                return
            
            data = []
            for row in reader:
                # gregorian_date_str = self.convert_taiwan_date_to_gregorian(row['日期'].strip())
                try:
                    stock_id = row['證券代號'].strip()
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
                        'Date': today,
                        'OpeningPrice': open_price,
                        'HighestPrice': high_price,
                        'LowestPrice': low_price,
                        'ClosingPrice': close_price,
                        'TradeVolume': volume
                    }
                    data.append(stock_data)
                    print(stock_data)
                except Exception as e:
                    print(f"錯誤處理{e}")

            return data
                        

        except Exception as e:
            print(f"錯誤處理{e}")
            

    def download_twse_data(self):
        self.logger.info("開始下載 TWSE 每日收盤價數據")
        data = self.download_data_from_twse()
        if data:
            self.insert_data_to_database(data, is_twse=True)
        self.logger.info("TWSE 數據下載完成")

    def download_tpex_data(self):
        self.logger.info("開始下載 TPEx 每日收盤價數據")
        data = self.download_data_from_api(self.tpex_api_url)
        if data:
            self.insert_data_to_database(data, is_twse=False)
        self.logger.info("TPEx 數據下載完成")

    def parse_float(self, value):
        return float(value) if value not in ['--', '----', '']  else None

    def parse_int(self, value):
        return int(value.replace(',', '')) if value not in ['--', '----', ''] else None

    def run(self):
        success = False
        if not self.ensure_system_config_table():
            self.logger.error("無法確保 system_config 表存在,退出程序")
            success = False

        last_download_date = self.get_last_download_date()
        today = date.today()

        if last_download_date is None:
            self.logger.error("無法獲取上次下載日期,退出程序")
            success = False

        if today <= last_download_date:
            self.logger.info(f"今天 ({today}) 的數據已經下載過了,最後下載日期為 {last_download_date}")
            success = False

        self.logger.info("開始從 TWSE 下載每日收盤價數據")
        data = self.download_data_from_twse()
        if data:
            if self.insert_data_to_database(data):
                self.logger.info(f"成功更新TWSE最後下載日期為 {today}")
                success = True
            else:
                self.logger.error("更新最後TWSE下載日期失敗")
                success = False
        else:
            self.logger.error("無法從TWSE獲取數據")
            success = False
        self.logger.info("TWSE下載完成")

        data = self.download_tpex_data()
        if data:
            if self.insert_data_to_database(data):
                self.logger.info(f"成功更新TPEx最後下載日期為 {today}")
                success = True
            else:
                self.logger.error("更新最後TPEx下載日期失敗")
                success = False
        else:
            self.logger.error("無法從TPEx獲取數據")
            success = False
        self.logger.info("TPEx下載完成")
        
        if self.update_last_download_date(today):
            self.logger.info(f"成功更新最後下載日期為 {today}")
            success = True
        else:
            self.logger.error("更新最後下載日期失敗")
            success = False
        return success

    def get_last_download_date(self):
        conn = self.connect_db()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM system_config WHERE name = 'auto_download_daily_close_date'")
            result = cursor.fetchone()
            if result:
                return date.fromisoformat(result[0])
            else:
                # 如果參數不存在,創建它並設置為前一天
                yesterday = date.today() - timedelta(days=1)
                cursor.execute(
                    "INSERT INTO system_config (name, value) VALUES (%s, %s)",
                    ('auto_download_daily_close_date', yesterday.isoformat())
                )
                conn.commit()
                return yesterday
        except pymssql.Error as err:
            self.logger.error(f"獲取上次下載日期時發生錯誤: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def update_last_download_date(self, new_date):
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE system_config SET value = %s WHERE name = 'auto_download_daily_close_date'",
                (new_date.isoformat(),)
            )
            conn.commit()
            return True
        except pymssql.Error as err:
            self.logger.error(f"更新上次下載日期時發生錯誤: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def convert_taiwan_date_to_gregorian(self, taiwan_date_str):
        parts = taiwan_date_str.split('/')
        year = int(parts[0]) + 1911  # 民國年轉換為西元年
        return f"{year}/{parts[1]}/{parts[2]}"

    def convert_tw_date_to_ad(self, tw_date_str):
    # 確保輸入是字符串類型
        tw_date_str = str(tw_date_str)
        
        # 檢查輸入長度是否正確
        if len(tw_date_str) != 7:
            raise ValueError("輸入的日期格式不正確。應為 7 位數字，例如 '1131004'")
        
        # 提取年、月、日
        tw_year = int(tw_date_str[:3])
        month = int(tw_date_str[3:5])
        day = int(tw_date_str[5:])
        
        # 轉換為西元年
        ad_year = tw_year + 1911
        
        # 創建日期對象
        date_obj = datetime(ad_year, month, day)
        
        # 格式化為所需的字符串格式
        return date_obj.strftime('%Y-%m-%d')
    
    def ensure_system_config_table(self):
        conn = self.connect_db()
        if not conn:
            return False

        cursor = conn.cursor()
        try:
            # 檢查 system_config 表是否存在
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_config' AND xtype='U')
                CREATE TABLE system_config (
                    name VARCHAR(100) PRIMARY KEY,
                    value VARCHAR(100)
                )
            """)
            conn.commit()
            return True
        except pymssql.Error as err:
            self.logger.error(f"創建 system_config 表時發生錯誤: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    auto_download = AutoDownloadDailyClosePrice()
    auto_download.run()