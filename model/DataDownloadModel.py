import pymssql
import pandas as pd

from Event import EventBus, Event
from model.BaseModel import BaseModel


class DataDownloadModel(BaseModel):


    def __init__(self, api):
        self.api = api
        self.event_bus = EventBus()
        
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
            kbars_df = self.get_kbars_data_by_start_end_date(stock_id, start_date, end_date)
            self.insert_kbars(kbars_df, stock_id)
            self.event_bus.publish(Event("log_message", f"下載股票 {stock_id} 的KBar資料"))

