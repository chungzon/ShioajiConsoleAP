import requests
from datetime import datetime, timedelta, time
import calendar

'''
    取得當週最後交易日
    取得當月最後交易日
    判斷是否是當週最後交易日
    判斷是否是當月最後交易日
    判斷是否是當週最後交易日
'''
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

def is_after_friday_1430(target_date: datetime) -> bool:
    # 日期為週五，且時間為14:30之後
    if target_date.weekday() < 4:
        return False
    elif target_date.weekday() == 4:
        return target_date.time() >= time(14, 30)  
    else:
        return True

def is_today(date_str: str) -> bool:
    """
    判斷傳入的日期字串是否為今天
    參數格式：'YYYY-MM-DD'
    """
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        return input_date == today
    except ValueError:
        return False  # 日期格式錯誤時回傳 False
    
def is_last_day_of_month(date: datetime) -> bool:
    """
    判斷傳入日期是否為當月最後一天
    """
    last_day = calendar.monthrange(date.year, date.month)[1]
    if date.day == last_day:
        if date.time() >= time(14, 30):
            return True
        else:
            return False
    else:
        return False



# 🔍 測試範例
# date_to_check = "20250630"

# is_week_last = is_last_trade_day_of_week(date_to_check)
# is_month_last = is_last_trade_day_of_month(date_to_check)

# print(f"{date_to_check} 是當週最後交易日？→ {'是' if is_week_last else '否'}")
# print(f"{date_to_check} 是當月最後交易日？→ {'是' if is_month_last else '否'}")

# print(calculate_down_limit_price(44.2))
# print(calculate_up_limit_price(44.2))