import math
from pydoc import cli
import numpy as np
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
    def calculate_sma(close_prices):
        # 計算日均線weak、strong
        daily_5_sma = Math.calculate_moving_average(close_prices, 5)
        daily_10_sma = Math.calculate_moving_average(close_prices, 10)
        daily_20_sma = Math.calculate_moving_average(close_prices, 20)
        daily_60_sma = Math.calculate_moving_average(close_prices, 60)
        daily_120_sma = Math.calculate_moving_average(close_prices, 120)

        daily_sma_strong = np.nan
        daily_sma_weak = np.nan
        if not close_prices.empty and len(close_prices) >= 10:
            daily_sma_strong = (daily_10_sma.iloc[-1]*10 - close_prices.iloc[-10])/(10-1) # 續強公式
        if not close_prices.empty and len(close_prices) >= 20:
            daily_sma_weak = (daily_20_sma.iloc[-1]*20 - close_prices.iloc[-20])/(20-1) # 續弱公式

        sma_values = [
            round(daily_5_sma.iloc[-1], 2),
            round(daily_10_sma.iloc[-1], 2),
            round(daily_20_sma.iloc[-1], 2),
            round(daily_60_sma.iloc[-1], 2),
            round(daily_120_sma.iloc[-1], 2),
            round(daily_sma_strong, 2),
            round(daily_sma_weak, 2)
        ]

        # 計算周均線weak、strong
        weekly_prices = close_prices.resample('W').last()
        weekly_prices = weekly_prices.dropna()
        weekly_5_sma = Math.calculate_moving_average(weekly_prices, 5)
        weekly_10_sma = Math.calculate_moving_average(weekly_prices, 10)
        weekly_20_sma = Math.calculate_moving_average(weekly_prices, 20)
        weekly_60_sma = Math.calculate_moving_average(weekly_prices, 60)
        weekly_120_sma = Math.calculate_moving_average(weekly_prices, 120)

        weekly_sma_strong = np.nan
        weekly_sma_weak = np.nan

        if not weekly_prices.empty:
            if len(weekly_prices) >= 10:
                weekly_sma_strong = (weekly_10_sma.iloc[-1]*10 - weekly_prices.iloc[-10])/(10-1) # 續強公式
            if len(weekly_prices) >= 20:
                weekly_sma_weak = (weekly_20_sma.iloc[-1]*20 - weekly_prices.iloc[-20])/(20-1) # 續弱公式
        else:
            weekly_sma_strong = np.nan
            weekly_sma_weak = np.nan

        # 計算周均線的移動平均
        weekly_sma_values = [
            round(weekly_5_sma.iloc[-1], 2),
            round(weekly_10_sma.iloc[-1], 2),
            round(weekly_20_sma.iloc[-1], 2),
            round(weekly_60_sma.iloc[-1], 2),
            round(weekly_120_sma.iloc[-1], 2),
            round(weekly_sma_strong, 2),
            round(weekly_sma_weak, 2)
        ]

        # 計算月均線的移動平均
        monthly_sma_values = [
            round(Math.calculate_monthly_average(close_prices, 5).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 10).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 20).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 60).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 120).iloc[-1], 2),
            np.nan,
            np.nan
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

