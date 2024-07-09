import shioaji as sj
import pandas as pd
import pymssql
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_ticks_data(api, stock_id, date):
    ticks = api.ticks(
        contract=api.Contracts.Stocks[stock_id],
        date=date.strftime("%Y-%m-%d")
    )
    df = pd.DataFrame({**ticks})
    df.ts = pd.to_datetime(df.ts)
    df["stock_id"] = stock_id
    return df

def insert_data_to_sql(df, server, database, username, password):
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO Ticks (ts, close_price, volume, bid_price, bid_volume, ask_price, ask_volume, tick_type, stock_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for index, row in df.iterrows():
        cursor.execute(insert_query, (
            row['ts'],
            row['close'],
            row['volume'],
            row['bid_price'],
            row['bid_volume'],
            row['ask_price'],
            row['ask_volume'],
            row['tick_type'],
            row['stock_id']
        ))

    conn.commit()
    cursor.close()
    conn.close()

def process_date(api, stock_id, date, server, database, username, password):
    start_time = time.time()
    df = get_ticks_data(api, stock_id, date)
    if not df.empty:
        insert_data_to_sql(df, server, database, username, password)
    end_time = time.time()
    duration = end_time - start_time
    return date, duration

if __name__ == "__main__":
    api = sj.Shioaji(simulation=True)
    api.login(
        api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
        secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
    )
    stock_id = "6152"
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2021, 12, 31)

    server = '127.0.0.1:1433'
    database = 'TSE'
    username = 'TSE_USER'
    password = 'fuckme'

    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    total_start_time = time.time()  # 记录总开始时间

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_date, api, stock_id, date, server, database, username, password): date for date in dates}
        for future in as_completed(futures):
            date, duration = future.result()
            print(f"Date: {date.strftime('%Y-%m-%d')} completed in {duration:.2f} seconds")

    total_end_time = time.time()  # 记录总结束时间
    total_duration = total_end_time - total_start_time  # 计算总花费时间

    print(f"所有資料已經成功抓取並存入資料庫，總花費時間: {total_duration:.2f} 秒")
