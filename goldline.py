import pandas as pd
import pymssql
from datetime import datetime, timedelta

class BacktestModel:

    def __init__(self):
        self.trades = []
        self.position = 0  # 持有股票的數量

    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn
    
    # 從資料庫取得每分鐘 K 線資料
    def get_stock_kbar_from_db(self, stock_id, start_date, end_date):
        conn = self.connect_db()
        query = f"""
        SELECT ts, Open_Price, High, Low, Close_Price, Volume
        FROM Kbars
        WHERE stock_id = {stock_id} AND ts >= '{start_date}' AND ts <= DATEADD(day, 1, '{end_date}') ORDER BY ts ASC
        """
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%H:%M:%S')
        df['date'] = df['ts']
        conn.close()
        return df

    # 計算黃金分割線
    def calculate_fibonacci_levels(self, high, low):
        diff = high - low
        return {
            'level_0.382': high - diff * 0.382,
            'level_0.5': high - diff * 0.5,
            'level_0.618': high - diff * 0.618,
        }

    # 執行交易策略
    def trade_strategy(self, kbar):
        high = kbar['High'].max()
        low = kbar['Low'].min()
        close = kbar['Close_Price'].iloc[-1]

        # 計算黃金分割線
        fib_levels = self.calculate_fibonacci_levels(high, low)

        # 根據黃金分割線買賣
        if close <= low:
            self.buy(close)
        elif close >= fib_levels['level_0.618']:
            self.sell(close)

    # 買入股票
    def buy(self, price):
        self.position += 1
        self.trades.append(('BUY', price))
        print(f"Bought at {price}")

    # 賣出股票
    def sell(self, price):
        if self.position > 0:
            self.position -= 1
            self.trades.append(('SELL', price))
            print(f"Sold at {price}")

    # 計算回測期間的損益
    def calculate_profit(self):
        profit = 0
        for i in range(0, len(self.trades), 2):
            if i + 1 < len(self.trades):
                buy_price = self.trades[i][1]
                sell_price = self.trades[i+1][1]
                profit += (sell_price - buy_price) * 1000  # 假設一張 1000 股
        print(f"Total Profit: {profit}")
        return profit

    # 回測指定日期範圍的交易策略
    def backtest(self, stock_id, start_date, end_date):
        kbar_data = self.get_stock_kbar_from_db(stock_id, start_date, end_date)
        
        # 按每分鐘進行交易策略檢查
        for _, kbar in kbar_data.groupby(kbar_data['ts']):
            self.trade_strategy(kbar)
        
        # 回測結束後計算總損益
        self.calculate_profit()

if __name__ == "__main__":
    model = BacktestModel()

    stock_id = "6877"  # 這裡替換成你想要回測的股票 ID
    start_date = '2024-08-14'  # 回測開始日期
    end_date = '2024-08-14'    # 回測結束日期

    model.backtest(stock_id, start_date, end_date)
