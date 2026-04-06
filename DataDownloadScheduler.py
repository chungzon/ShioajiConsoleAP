import time
from threading import Thread
from datetime import datetime, date, timedelta
import requests
import json
import logging
import pymssql
import csv
import io
from app_utils.unified_scheduler_manager import get_unified_scheduler_manager
from plyer import notification


# python -m pip install plyer

class DataDownloadScheduler:
    def __init__(self, api=None):
        # 初始化Shioaji API（可选）
        self.api = api
        
        # 初始化日志
        self.logger = self.setup_logger()
        
        # 获取统一调度器管理器
        self.scheduler_manager = get_unified_scheduler_manager()
        
        # API URLs
        self.twse_api_url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        self.tpex_api_url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"

    def setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('DataDownloadScheduler')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def show_notification(self, title, message, duration=5):
        """顯示系統通知"""
        try:
            # 尝试使用 plyer
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=duration
            )
        except ImportError:
            # 如果 plyer 不可用，使用控制台通知
            self._console_notification(title, message)
        except Exception as e:
            self.logger.warning(f"通知发送失败: {e}")
            # 降级到控制台通知
            self._console_notification(title, message)

    def _console_notification(self, title, message):
        """控制台通知"""
        separator = "=" * 60
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{separator}")
        print(f"📢 通知时间: {timestamp}")
        print(f"📋 标题: {title}")
        print(f"📝 内容: {message}")
        print(f"{separator}\n")

    def connect_db(self):
        """连接数据库"""
        try:
            conn = pymssql.connect(
                server='127.0.0.1:1433',
                user='TSE_USER',
                password='fuckme',
                database='TSE'
            )
            return conn
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return None

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
        except pymssql.Error as err:
            self.logger.error(f"創建 system_config 表時發生錯誤: {err}")
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
        """更新最后下载日期"""
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
                    self.logger.error(f"處理TWSE數據時發生錯誤: {e}")

            return data

        except Exception as e:
            self.logger.error(f"下載TWSE數據時發生錯誤: {e}")
            return None

    def download_data_from_tpex(self):
        """从TPEx下载数据"""
        try:
            response = requests.get(self.tpex_api_url)
            response.raise_for_status()
            return json.loads(response.text)
        except requests.RequestException as e:
            self.logger.error(f"TPEx API 請求錯誤: {e}")
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
            self.logger.info(f"數據已成功下載並存儲到 stock_data 表中，日期為 {today}")
            return True
        except pymssql.Error as err:
            self.logger.error(f"數據插入錯誤: {err}")
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

    def download_task(self):
        """下載每日收盤價數據的任務"""
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        
        self.show_notification('股票數據下載', f'開始下載 {today_str} 的每日收盤價數據')
        self.logger.info(f"开始下载 {today_str} 的每日收盘价数据")

        start_time = datetime.now()
        success = False
        
        try:
            # 检查是否已经下载过
            if not self.ensure_system_config_table():
                self.logger.error("無法確保 system_config 表存在,退出程序")
                raise Exception("无法确保系统配置表存在")

            last_download_date = self.get_last_download_date()
            if last_download_date is None:
                self.logger.error("無法獲取上次下載日期,退出程序")
                raise Exception("无法获取上次下载日期")

            if today <= last_download_date:
                self.logger.info(f"今天 ({today}) 的數據已經下載過了,最後下載日期為 {last_download_date}")
                self.show_notification('股票數據下載', f'今天 ({today}) 的數據已經下載過了')
                return

            # 下载TWSE数据
            self.logger.info("開始從 TWSE 下載每日收盤價數據")
            twse_data = self.download_data_from_twse()
            if twse_data:
                if self.insert_data_to_database(twse_data, is_twse=True):
                    self.logger.info(f"成功下載TWSE數據，共 {len(twse_data)} 筆")
                    success = True
                else:
                    self.logger.error("TWSE數據插入數據庫失敗")
            else:
                self.logger.error("無法從TWSE獲取數據")

            # 下载TPEx数据
            self.logger.info("開始從 TPEx 下載每日收盤價數據")
            tpex_data = self.download_data_from_tpex()
            if tpex_data:
                if self.insert_data_to_database(tpex_data, is_twse=False):
                    self.logger.info(f"成功下載TPEx數據，共 {len(tpex_data)} 筆")
                    success = True
                else:
                    self.logger.error("TPEx數據插入數據庫失敗")
            else:
                self.logger.error("無法從TPEx獲取數據")

            # 更新最后下载日期
            if self.update_last_download_date(today):
                self.logger.info(f"成功更新最後下載日期為 {today}")
            else:
                self.logger.error("更新最後下載日期失敗")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if success:
                message = f'{today_str} 每日收盤價數據下載成功,耗時 {duration:.2f} 秒'
            else:
                message = f'{today_str} 每日收盤價數據下載失敗,請檢查日誌'

            self.show_notification('股票數據下載', message)
            print(f"✅ {message}")
            self.logger.info(f"下载任务完成: {message}")
            
        except Exception as e:
            error_message = f'{today_str} 每日收盤價數據下載過程中發生錯誤: {str(e)}'
            self.show_notification('股票數據下載', error_message)
            print(f"❌ {error_message}")
            self.logger.error(f"下载任务异常: {error_message}")

    def setup_scheduler(self):
        """设置调度任务"""
        # 添加每日收盘价下载任务
        self.scheduler_manager.add_scheduler(
            name="daily_close_price_download",
            task_func=self.download_task,
            schedule_time="18:30",
            task_type="daily"
        )
        
        self.logger.info("每日收盘价下载调度任务已设置")

def start_scheduler(api=None):
    """啟動每日收盤價數據下載排程器"""
    scheduler = DataDownloadScheduler(api)
    
    # 设置调度任务
    scheduler.setup_scheduler()
    
    # 启动主调度器（如果还没有启动）
    scheduler_manager = get_unified_scheduler_manager()
    if not scheduler_manager._is_running:
        scheduler_manager.start_main_scheduler()
    
    return scheduler
    

# if __name__ == "__main__":
#     # 如果直接運行此腳本，則啟動排程器
#     start_scheduler()
#     
#     # 保持主線程運行
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\n🛑 排程器已停止")

