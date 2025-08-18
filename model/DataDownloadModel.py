import logging
import pymssql
import pandas as pd

from Event import EventBus, Event
from model.BaseModel import BaseModel
from resource.Resources import get_resource_path, ResourceFileNames


class DataDownloadModel(BaseModel):


    def __init__(self, api):
        self.api = api
        self.event_bus = EventBus()
        self.logger = self.setup_logger()

    def setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('DataDownloadModel')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn

    def get_latest_dates(self, stock_id):
        conn = self.connect_db()
        query = f"""
        SELECT 
            (SELECT MAX(ts) FROM Ticks WHERE stock_id = '{stock_id}') AS latest_date_ticks,
            (SELECT MAX(ts) FROM Kbars WHERE stock_id = '{stock_id}') AS latest_date_kbars
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.iloc[0]['latest_date_ticks'], df.iloc[0]['latest_date_kbars']

    def get_kbars_data(self, stock_id, date):
        contract = self.api.Contracts.Stocks[stock_id]
        kbars = self.api.kbars(
            contract=contract,
            start=date.strftime("%Y-%m-%d"),
            end=date.strftime("%Y-%m-%d")
        )
        df = pd.DataFrame({**kbars})
        df.ts = pd.to_datetime(df.ts)  # 將時間戳轉換為datetime
        return df

    def insert_kbars(self, kbars_df, stock_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        for _, row in kbars_df.iterrows():
            cursor.execute("""
                INSERT INTO Kbars (stock_id, ts, open_price, high, low, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (stock_id, row['ts'], row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
        conn.commit()
        cursor.close()
        conn.close()

    def get_kbars_data_by_start_end_date(self, stock_id, start_date, end_date):
        contract = self.api.Contracts.Stocks[str(stock_id)]
        kbars = self.api.kbars(
            contract=contract,
            start=start_date,
            end=end_date
        )
        df = pd.DataFrame({**kbars})
        df.ts = pd.to_datetime(df.ts)  # 將時間戳轉換為datetime
        return df

    def get_all_stocks_kbars(self, start_date, end_date):
        top_stocks = self.get_top_volumn_stocks()
        for stock_id in top_stocks:
            try:
                kbars_df = self.get_kbars_data_by_start_end_date(stock_id, start_date, end_date)
                if kbars_df.empty:
                    continue
                self.insert_kbars(kbars_df, stock_id)
                self.event_bus.publish(Event("log_message", f"下載股票 {stock_id} 的KBar資料"))
                self.logger.info(f"下載股票 {stock_id} 的KBar資料")
            except Exception as e:
                self.event_bus.publish(Event("log_message", f"下載股票 {stock_id} 的KBar資料失敗: {e}"))

    def download_single_stock_kbars(self, stock_id, start_date, end_date):
        kbars_df = self.get_kbars_data_by_start_end_date(stock_id, start_date, end_date)
        if kbars_df.empty:
            return
        self.insert_kbars(kbars_df, stock_id)
        self.event_bus.publish(Event("log_message", f"下載股票 {stock_id} 的KBar資料")) 

