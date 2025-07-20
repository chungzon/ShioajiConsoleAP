import requests
from datetime import datetime, timedelta
import calendar

def get_trade_dates_in_week(target_date: str) -> list:
    dt = datetime.strptime(target_date, "%Y%m%d")
    monday = dt - timedelta(days=dt.weekday())
    dates = [(monday + timedelta(days=i)).strftime("%Y%m%d") for i in range(5)]

    trade_dates = []
    for d in dates:
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={d}&type=ALLBUT0999"
        resp = requests.get(url)
        if resp.status_code == 200 and resp.json().get("stat") == "OK":
            trade_dates.append(d)
    return trade_dates

def is_last_trade_day_of_week(target_date: str) -> bool:
    trade_dates = get_trade_dates_in_week(target_date)
    return trade_dates and target_date == trade_dates[-1]

def get_trade_dates_in_month(target_date: str) -> list:
    dt = datetime.strptime(target_date, "%Y%m%d")
    first_day = dt.replace(day=1)
    last_day = dt.replace(day=calendar.monthrange(dt.year, dt.month)[1])

    days = []
    current = first_day
    while current <= last_day:
        days.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    trade_dates = []
    for d in days:
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={d}&type=ALLBUT0999"
        resp = requests.get(url)
        if resp.status_code == 200 and resp.json().get("stat") == "OK":
            trade_dates.append(d)
    return trade_dates

def is_last_trade_day_of_month(target_date: str) -> bool:
    trade_dates = get_trade_dates_in_month(target_date)
    return trade_dates and target_date == trade_dates[-1]

# 🔍 測試範例
# date_to_check = "20250630"

# is_week_last = is_last_trade_day_of_week(date_to_check)
# is_month_last = is_last_trade_day_of_month(date_to_check)

# print(f"{date_to_check} 是當週最後交易日？→ {'是' if is_week_last else '否'}")
# print(f"{date_to_check} 是當月最後交易日？→ {'是' if is_month_last else '否'}")
