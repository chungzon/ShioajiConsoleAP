# 統整目前邏輯為一份完整的 Python 程式碼，保留設定與函數結構

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# 三大法人欄位對應
T86_COLUMNS = {
    '證券代號': 'stock_id',
    '外陸資買賣超股數(不含外資自營商)': 'foreign',
    '投信買賣超股數': 'investment',
    '自營商買賣超股數': 'dealer'
}

# 抓取三大法人買賣超
def get_t86_data(date_str):
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALL"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data['stat'] != 'OK':
            return pd.DataFrame()
        df = pd.DataFrame(data['data'], columns=data['fields'])
        df = df.rename(columns=T86_COLUMNS)
        df = df[['stock_id', 'foreign', 'investment', 'dealer']]
        for col in ['foreign', 'investment', 'dealer']:
            df[col] = df[col].str.replace(',', '', regex=False).astype(float)
        return df
    except:
        return pd.DataFrame()

# 抓取個股日資料
def get_stock_day_data(stock_no, end_date: datetime, required_days: int = 30):
    """
    從指定日期往前回推，抓取足夠的股價與成交量資料（跨月）
    """
    df_all = pd.DataFrame()
    months_to_check = 4  # 最多往前查4個月

    for i in range(months_to_check):
        date_check = end_date - pd.DateOffset(months=i)
        date_str = date_check.strftime('%Y%m01')
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={stock_no}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data['stat'] != 'OK':
                continue
            df = pd.DataFrame(data['data'], columns=data['fields'])

            def convert_tw_date(date_str):
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3 and parts[0].isdigit():
                        tw_year = int(parts[0])
                        ad_year = tw_year + 1911
                        return f"{ad_year}-{parts[1]}-{parts[2]}"
                return date_str

            df['日期'] = df['日期'].apply(convert_tw_date)
            df['日期'] = pd.to_datetime(df['日期'], format='%Y-%m-%d', errors='coerce')
            df['收盤價'] = df['收盤價'].str.replace(',', '', regex=False).replace(['X', '--'], None).astype(float)
            df['成交股數'] = df['成交股數'].str.replace(',', '', regex=False).replace(['X', '--'], None).astype(float)

            df = df[['日期', '收盤價', '成交股數']].dropna()
            df_all = pd.concat([df_all, df])
        except Exception as e:
            print(f"{stock_no} 資料抓取錯誤: {e}")
            continue

        # 資料足夠就中斷
        df_all = df_all[df_all['日期'] <= end_date].sort_values('日期')
        if len(df_all) >= required_days:
            break

    return df_all.sort_values('日期').tail(required_days)


def is_new_high(df, end_date, window=20):
    df = df[df['日期'] <= end_date].sort_values('日期')
    recent_prices = df.tail(window)['收盤價']
    if len(recent_prices) < window:
        return False
    return recent_prices.iloc[-1] >= recent_prices.max()

def is_volume_up(df, end_date, short=5, long=20):
    df = df[df['日期'] <= end_date].sort_values('日期')
    if len(df) < long:
        return False
    short_avg = df.tail(short)['成交股數'].mean()
    long_avg = df.tail(long)['成交股數'].mean()
    return short_avg > long_avg

# 波動計算（自訂門檻）
def check_volatility_custom(df, end_date, threshold=0.03):
    df = df[df['日期'] <= end_date].sort_values('日期').tail(5)
    if len(df) < 5:
        return False
    max_price = df['收盤價'].max()
    min_price = df['收盤價'].min()
    volatility = (max_price - min_price) / min_price
    return volatility <= threshold

# 抓取前200名成交量股票
def get_top_volume_stocks(target_date: str, top_n=200):
    date_str = target_date.replace('-', '')
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALL"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'tables' not in data or len(data['tables']) < 9:
            return []
        
        # 取得第9個表格（通常是個股成交量資料）
        table_data = data['tables'][8]  # 索引8對應第9個表格
        if 'data' not in table_data or 'fields' not in table_data:
            return []
            
        df = pd.DataFrame(table_data['data'], columns=table_data['fields'])
        df = df.rename(columns={df.columns[0]: "stock_id", df.columns[2]: "volume"})
        df['volume'] = df['volume'].str.replace(',', '', regex=False).astype(float)
        df = df[df['stock_id'].str.len() == 4]
        df = df.sort_values('volume', ascending=False).head(top_n)
        return df['stock_id'].tolist()
    except:
        return []

def has_institutional_buying(stock_no: str, ref_date: datetime, days: int = 10) -> bool:
    count = 0
    for i in range(0, 20):  # 多抓一點避免遇到假日
        check_date = ref_date - timedelta(days=i)
        if check_date.weekday() >= 5:  # 跳過週末
            continue
        date_str = check_date.strftime('%Y%m%d')
        t86 = get_t86_data(date_str)
        if t86.empty:
            continue
        row = t86[t86['stock_id'] == stock_no]
        if not row.empty and (row['foreign'].values[0] > 0 or row['investment'].values[0] > 0 or row['dealer'].values[0] > 0):
            count += 1
        if count > 0:
            return True
        days -= 1
        if days <= 0:
            break
    return False

# 主程式：篩選法人買超 + 波動小於 3% 的標的（限前200名成交量）
def fetch_filtered_stocks_looser_criteria_v2(target_date: str, volume_top_n=200, volatility_threshold=0.03):
    top_stocks = set(get_top_volume_stocks(target_date, volume_top_n))
    date = datetime.strptime(target_date, "%Y-%m-%d")
    date_str = date.strftime('%Y%m%d')
    t86 = get_t86_data(date_str)
    result = []

    if t86.empty:
        return pd.DataFrame()

    for _, row in t86.iterrows():
        stock_no = row['stock_id']
        if stock_no not in top_stocks:
            continue
        if row['foreign'] > 0 or row['investment'] > 0 or row['dealer'] > 0:
            df_price = get_stock_day_data(stock_no, date)
            if df_price.empty:
                continue
            try:
                vol_check = check_volatility_custom(df_price, date, threshold=volatility_threshold)
                new_high = is_new_high(df_price, date, window=20)
                vol_up = is_volume_up(df_price, date, short=5, long=20)
                has_buying = has_institutional_buying(stock_no, date, days=10)

                if vol_check and new_high and vol_up and has_buying:
                    result.append({'股票代號': stock_no})
                    print(f"股票代號: {stock_no}, 波動: {vol_check}, 新高: {new_high}, 成交量: {vol_up}")
            except:
                continue
        time.sleep(0.2)

    return pd.DataFrame(result)

# 執行範例：2025-07-01 當日查詢
target_date = "2025-08-05"
filtered_df = fetch_filtered_stocks_looser_criteria_v2(target_date, volume_top_n=250, volatility_threshold=0.03)

# 顯示結果
print(f"法人買超 + 波動 <3% + 成交量前200名 (共 {len(filtered_df)} 檔股票):")
if not filtered_df.empty:
    print(filtered_df.to_string(index=False))
else:
    print("沒有找到符合條件的股票")
