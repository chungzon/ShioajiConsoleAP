import shioaji as sj
import pandas as pd
from datetime import datetime, timedelta
import pymssql
import concurrent.futures
import time

# 初始化 Shioaji API
api = sj.Shioaji(simulation=True)
api.login(
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

# 獲取歷史Kbars數據
def get_kbars(stock_code, start_date, end_date):
    contract = api.Contracts.Stocks[stock_code]
    kbars = api.kbars(contract, start=start_date, end=end_date)
    
    df = pd.DataFrame({**kbars})
    df.ts = pd.to_datetime(df.ts)  # 將時間戳轉換為datetime
    return df

# 連接SQL Server資料庫
def connect_db():
    conn = pymssql.connect(
        server='127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn

# 插入數據到Kbars表
def insert_kbars(df, stock_code):
    conn = connect_db()
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO Kbars (stock_id, ts, Open_Price, High, Low, Close_Price, Volume) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (stock_code, row.ts, row.Open, row.High, row.Low, row.Close, row.Volume)
        )
    
    conn.commit()
    cursor.close()
    conn.close()

# 多執行緒任務
def process_kbars(stock_code, start_date, end_date):
    start_time = time.time()
    
    # 獲取Kbars數據
    kbars_df = get_kbars(stock_code, start_date, end_date)
    
    # 插入數據到資料庫
    insert_kbars(kbars_df, stock_code)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    return elapsed_time

# 主函數
def main():
    #stock_codes = ["2486", "2467", "2464"]  # 替換為您想要查詢的股票代碼列表
    stock_codes = ["1513"]
    start_date = "2024-04-01"
    end_date = "2024-07-12"
  
    total_start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_kbars, stock_code, start_date, end_date) for stock_code in stock_codes]
        for future in concurrent.futures.as_completed(futures):
            elapsed_time = future.result()
            print(f"單個任務花費時間: {elapsed_time:.2f}秒")
    
    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time
    
    print(f"總花費時間: {total_elapsed_time:.2f}秒")

if __name__ == "__main__":
    main()
