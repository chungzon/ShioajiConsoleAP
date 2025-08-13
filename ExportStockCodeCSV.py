import os
import shioaji as sj
import pandas as pd
from resource.Resources import get_resource_path, ResourceFileNames

# 登入永豐金帳號（替換成你的帳號密碼）
# api = sj.Shioaji()
api = sj.Shioaji(simulation=True)
api.login(
    api_key="CV7uuCJ7pB7x2i4T7783dBwiP7NwqhgwNj96J9uPd7PK",
    secret_key="HvDpMQ84VfgsGqBPN4nqfPV1iY9XsoWHst4rd4UimHaf"
    )

file_path = get_resource_path(ResourceFileNames.TW_ALL_STOCKS_CSV)

# 取得所有股票商品
tw_stocks = api.Contracts.Stocks

# 整理資料
stock_list = []
for exchange in tw_stocks: 
    for stock in exchange:
        if len(stock.code) == 4:
            print(stock.code)
            stock_list.append({
                "StockCode": stock.code,
                "StockName": stock.name,
                "Category": stock.category
            })

# 建立 DataFrame
df = pd.DataFrame(stock_list)

# 儲存 CSV
df.to_csv(file_path, index=False, encoding="utf-8-sig")

print(f"✅ 已儲存為 {file_path}")
