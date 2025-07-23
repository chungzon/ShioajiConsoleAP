from datetime import datetime, time
import math
from pydoc import cli
import numpy as np
from common import Utils
from common.enum.StockType import StockType

class Math:
    # 股票交易手續費
    stock_fee = 0.001425
    # 股票交易稅
    stock_tax = 0.003
    # 當沖交易稅
    stock_tax_today = 0.0015
    # 交易稅
    stock_tax_type = {
        StockType.DAY_TRADING: 0.0015,
        StockType.LONG_TERM: 0.003,
        StockType.MARGIN_TRADING: 0.001425,
        StockType.SHORT_TRADING: 0.001425
    }

    """
    數學運算類別
    """
    @staticmethod
    def calculate_spread_ratio(max_value, min_value):
        return (max_value - min_value) / min_value * 100

    @staticmethod
    def calculate_ratio_0618(max_value, min_value):
        return round(min_value + (max_value - min_value) / 2 * 0.618, 2)

    @staticmethod
    def calculate_ratio_1(max_value, min_value):
        return round(min_value + (max_value - min_value) / 2 * 1, 2)
    
    @staticmethod
    def calculate_ratio_value(max_value, min_value, ratio):
        return Math.adjust_ratio_price(round(min_value + (max_value - min_value) / 2 * ratio, 2))

    # 日移動平均，週移動平均，月移動平均
    # 5、10、20、60、120
    @staticmethod
    def calculate_sma(close_prices, close_date=None):
        # 計算日均線weak、strong
        daily_5_sma = Math.calculate_moving_average(close_prices, 5)
        daily_10_sma = Math.calculate_moving_average(close_prices, 10)
        daily_20_sma = Math.calculate_moving_average(close_prices, 20)
        daily_60_sma = Math.calculate_moving_average(close_prices, 60)
        daily_120_sma = Math.calculate_moving_average(close_prices, 120)

        daily_sma_5_diff = np.nan
        daily_sma_10_diff = np.nan
        daily_sma_20_diff = np.nan
        daily_sma_60_diff = np.nan
        daily_sma_120_diff = np.nan

        # 日均扣抵值計算
        if not close_prices.empty:
            if len(close_prices) >= 5:
                daily_sma_5_diff = (daily_5_sma.iloc[-1]*5 - close_prices.iloc[-5])/(5-1)
            if len(close_prices) >= 10:
                daily_sma_10_diff = (daily_10_sma.iloc[-1]*10 - close_prices.iloc[-10])/(10-1)
            if len(close_prices) >= 20:
                daily_sma_20_diff = (daily_20_sma.iloc[-1]*20 - close_prices.iloc[-20])/(20-1)
            if len(close_prices) >= 60:
                daily_sma_60_diff = (daily_60_sma.iloc[-1]*60 - close_prices.iloc[-60])/(60-1)
            if len(close_prices) >= 120:
                daily_sma_120_diff = (daily_120_sma.iloc[-1]*120 - close_prices.iloc[-120])/(120-1)
        
        sma_values = [
            round(daily_5_sma.iloc[-1], 2),
            round(daily_10_sma.iloc[-1], 2),
            round(daily_20_sma.iloc[-1], 2),
            round(daily_60_sma.iloc[-1], 2),
            round(daily_120_sma.iloc[-1], 2),
            round(daily_sma_5_diff, 2),
            round(daily_sma_10_diff, 2),
            round(daily_sma_20_diff, 2),
            round(daily_sma_60_diff, 2),
            round(daily_sma_120_diff, 2)
        ]


        # 計算周均線的扣抵值和移動平均
        weekly_prices = close_prices.resample('W').last()
        weekly_prices = weekly_prices.dropna()
        weekly_5_sma = Math.calculate_moving_average(weekly_prices, 5)
        weekly_10_sma = Math.calculate_moving_average(weekly_prices, 10)
        weekly_20_sma = Math.calculate_moving_average(weekly_prices, 20)
        weekly_60_sma = Math.calculate_moving_average(weekly_prices, 60)
        weekly_120_sma = Math.calculate_moving_average(weekly_prices, 120)

        weekly_sma_5_diff = np.nan
        weekly_sma_10_diff = np.nan
        weekly_sma_20_diff = np.nan
        weekly_sma_60_diff = np.nan
        weekly_sma_120_diff = np.nan

        weekly_index = -2
        if close_date:
            close_datetime = datetime.strptime(close_date, '%Y-%m-%d')
            if Utils.is_today(close_date):
                if Utils.is_after_friday_1430(close_datetime):
                    weekly_index = -1
                else:
                    weekly_index = -2
            else:
                weekly_index = -2

        monthly_index = -2
        if close_date:
            close_datetime = datetime.strptime(close_date, '%Y-%m-%d')
            if Utils.is_today(close_date):
                if Utils.is_last_day_of_month(close_datetime):
                    monthly_index = -1
                else:
                    monthly_index = -2
            else:
                monthly_index = -2


        if not weekly_prices.empty:
            if len(weekly_prices) >= 5:
                weekly_sma_5_diff = (weekly_5_sma.iloc[weekly_index]*5 - weekly_prices.iloc[weekly_index-5+1])/(5-1)
            if len(weekly_prices) >= 10:
                weekly_sma_10_diff = (weekly_10_sma.iloc[weekly_index]*10 - weekly_prices.iloc[weekly_index-10+1])/(10-1)
            if len(weekly_prices) >= 20:
                weekly_sma_20_diff = (weekly_20_sma.iloc[weekly_index]*20 - weekly_prices.iloc[weekly_index-20+1])/(20-1)
            if len(weekly_prices) >= 60:
                weekly_sma_60_diff = (weekly_60_sma.iloc[weekly_index]*60 - weekly_prices.iloc[weekly_index-60+1])/(60-1)
            if len(weekly_prices) >= 120:
                weekly_sma_120_diff = (weekly_120_sma.iloc[weekly_index]*120 - weekly_prices.iloc[weekly_index-120+1])/(120-1)

        # 計算周均線的移動平均
        weekly_sma_values = [
            round(weekly_5_sma.iloc[-1], 2),
            round(weekly_10_sma.iloc[-1], 2),
            round(weekly_20_sma.iloc[-1], 2),
            round(weekly_60_sma.iloc[-1], 2),
            round(weekly_120_sma.iloc[-1], 2),
            round(weekly_sma_5_diff, 2),
            round(weekly_sma_10_diff, 2),
            round(weekly_sma_20_diff, 2),
            round(weekly_sma_60_diff, 2),
            round(weekly_sma_120_diff, 2)
        ]

        # 計算月均線的扣抵值和移動平均
        monthly_prices = close_prices.resample('M').last()
        monthly_prices = monthly_prices.dropna()
        monthly_5_sma = Math.calculate_moving_average(monthly_prices, 5)
        monthly_10_sma = Math.calculate_moving_average(monthly_prices, 10)
        monthly_20_sma = Math.calculate_moving_average(monthly_prices, 20)
        monthly_60_sma = Math.calculate_moving_average(monthly_prices, 60)
        monthly_120_sma = Math.calculate_moving_average(monthly_prices, 120)

        monthly_sma_5_diff = np.nan
        monthly_sma_10_diff = np.nan
        monthly_sma_20_diff = np.nan
        monthly_sma_60_diff = np.nan
        monthly_sma_120_diff = np.nan

        # 判斷日期的月份是否

        if not monthly_prices.empty:
            if len(monthly_prices) >= 5:
                monthly_sma_5_diff = (monthly_5_sma.iloc[monthly_index]*5 - monthly_prices.iloc[monthly_index-5+1])/(5-1)
            if len(monthly_prices) >= 10:
                monthly_sma_10_diff = (monthly_10_sma.iloc[monthly_index]*10 - monthly_prices.iloc[monthly_index-10+1])/(10-1)
            if len(monthly_prices) >= 20:
                monthly_sma_20_diff = (monthly_20_sma.iloc[monthly_index]*20 - monthly_prices.iloc[monthly_index-20+1])/(20-1)
            if len(monthly_prices) >= 60:
                monthly_sma_60_diff = (monthly_60_sma.iloc[monthly_index]*60 - monthly_prices.iloc[monthly_index-60+1])/(60-1)
            if len(monthly_prices) >= 120:
                monthly_sma_120_diff = (monthly_120_sma.iloc[monthly_index]*120 - monthly_prices.iloc[monthly_index-120+1])/(120-1)

        # 計算月均線的移動平均
        monthly_sma_values = [
            round(monthly_5_sma.iloc[-1], 2),
            round(monthly_10_sma.iloc[-1], 2),
            round(monthly_20_sma.iloc[-1], 2),
            round(monthly_60_sma.iloc[-1], 2),
            round(monthly_120_sma.iloc[-1], 2),
            round(monthly_sma_5_diff, 2),
            round(monthly_sma_10_diff, 2),
            round(monthly_sma_20_diff, 2),
            round(monthly_sma_60_diff, 2),
            round(monthly_sma_120_diff, 2)
        ]

        return sma_values, weekly_sma_values, monthly_sma_values

    # 計算移動平均
    @staticmethod
    def calculate_moving_average(prices, window):
        return prices.rolling(window=window, min_periods=window).mean()

    # 計算周均線
    @staticmethod
    def calculate_weekly_average(prices, window):
        weekly_prices = prices.resample('W').last()
        weekly_prices = weekly_prices.dropna()
        return Math.calculate_moving_average(weekly_prices, window)

    # 計算月均線
    @staticmethod
    def calculate_monthly_average(prices, window):
        monthly_prices = prices.resample('M').last()
        return Math.calculate_moving_average(monthly_prices, window)
    
    # 計算15分鐘均線
    @staticmethod
    def calculate_15_minutes_average(prices, window):
        fifteen_minutes_prices = prices.resample('15min').last()
        return Math.calculate_moving_average(fifteen_minutes_prices, window)
        
    # 根據價格區間，調整各種比例的價格
    @staticmethod
    def adjust_ratio_price(price):
        if price < 10:
            return round(price, 2)  # 10元以下,保留到小數點後兩位
        elif price < 50:
            return math.ceil(price * 20) / 20  # 10元到50元,向上調整到0.05的倍數
        elif price < 100:
            return math.ceil(price * 10) / 10  # 50元到100元,向上調整到0.1的倍數
        elif price < 500:
            return math.ceil(price * 2) / 2  # 100元到500元,向上調整到0.5的倍數
        elif price < 1000:
            return math.ceil(price)  # 500元到1000元,向上調整到整數
        else:
            return math.ceil(price / 5) * 5  # 1000元以上,向上調整到5的倍數

    @staticmethod
    def calculate_CDP(high, low, close):
        return round((high + low + 2 * close) / 4, 3)
    
    # 計算CDP支撐(NL)
    @staticmethod
    def calculate_CDP_NL(CDP, high):
        return round((2 * CDP) - high, 3)
    
    # 計算CDP阻力(NH)
    @staticmethod
    def calculate_CDP_NH(CDP, low):
        return round((2 * CDP) - low, 3)

    # 計算CDP第一目標(TP)
    @staticmethod
    def calculate_CDP_first_target(CDP, NL, NH):
        return round(CDP + (NH - NL), 3)
    
    # 昨日行情最高價(AH = CDP + (最高價 - 最低價))
    @staticmethod
    def calculate_AH(CDP, high, low):
        return round(CDP + (high - low), 3)

    # 昨日行情最低價(AL = CDP - (最高價 - 最低價))
    @staticmethod
    def calculate_AL(CDP, high, low):
        return round(CDP - (high - low), 3)

    # 計算CDP中的5個數據，CDP、NL、NH、AL、AH
    @staticmethod
    def calculate_CDP_5_values(CDP, high, low):
        return CDP, Math.calculate_CDP_NL(CDP, high), Math.calculate_CDP_NH(CDP, low), Math.calculate_AL(CDP, high, low), Math.calculate_AH(CDP, high, low)

    # 計算手續費
    @staticmethod
    def calculate_fee(buy_price, sell_price, stock_type, fee_discount):
        try:
            buy_fee = buy_price * 1000 * Math.stock_fee * (fee_discount / 10)
            sell_fee = sell_price * 1000 * (Math.stock_fee * (fee_discount / 10) + Math.stock_tax_type[stock_type])
            fee = buy_fee + sell_fee
            return round(fee, 2)
        except (ValueError, TypeError):
            return 0

    # 計算獲利
    @staticmethod
    def calculate_profit(buy_price, sell_price, stock_type, fee_discount):
        try:
            buy_price = float(buy_price)
            sell_price = float(sell_price)
            fee = Math.calculate_fee(buy_price, sell_price, stock_type, fee_discount)
            # 四捨五入至整數
            return int(round((sell_price - buy_price) * 1000 - fee, 0))
        except (ValueError, TypeError):
            return 0 

    # 計算價格差比例
    @staticmethod
    def calculate_price_diff_ratio(price_1, price_2):
        return round((price_1 - price_2) / price_2 * 100, 2)

    # 計算價格差
    @staticmethod
    def calculate_price_diff(price_1, price_2):
        return round(price_1 - price_2, 2)
