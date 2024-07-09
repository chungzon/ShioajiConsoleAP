import shioaji as sj
import pandas as pd
from datetime import datetime, timedelta
import pymssql

# 初始化 Shioaji API
api = sj.Shioaji(simulation=True)
api.login(
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

# 获取历史Kbars数据
def get_kbars(stock_code, start_date, end_date):
    contract = api.Contracts.Stocks[stock_code]
    kbars = api.kbars(contract, start=start_date, end=end_date)
    
    # 将时间戳转换为datetime之前进行筛选
   # valid_ts_mask = (kbars.ts > 0) & (kbars.ts < 253402300799000)  # 253402300799000是9999-12-31的时间戳(ms)
    #filtered_kbars = {key: value[valid_ts_mask] for key, value in kbars.items()}
    
    df = pd.DataFrame({**kbars})
    df.ts = pd.to_datetime(df.ts)  # 将时间戳转换为datetime
    return df

# 连接SQL Server数据库
def connect_db():
    conn = pymssql.connect(
        server = '127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn

# 插入数据到Kbars表
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

# 主函数
def main():
    stock_code = "6152"  # 替换为您想要查询的股票代码
    start_date = "2004-02-01"
    end_date = "2024-07-08"

    # 获取Kbars数据
    kbars_df = get_kbars(stock_code, start_date, end_date)
    
    # 插入数据到数据库
    insert_kbars(kbars_df, stock_code)

if __name__ == "__main__":
    main()
