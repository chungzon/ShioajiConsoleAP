import math

class Math:
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
        sma_values = [
            round(Math.calculate_moving_average(close_prices, 5).iloc[-1], 2),
            round(Math.calculate_moving_average(close_prices, 10).iloc[-1], 2),
            round(Math.calculate_moving_average(close_prices, 20).iloc[-1], 2),
            round(Math.calculate_moving_average(close_prices, 60).iloc[-1], 2),
            round(Math.calculate_moving_average(close_prices, 120).iloc[-1], 2),
        ]

        # 計算周均線的移動平均
        weekly_sma_values = [
            round(Math.calculate_weekly_average(close_prices, 5).iloc[-1], 2),
            round(Math.calculate_weekly_average(close_prices, 10).iloc[-1], 2),
            round(Math.calculate_weekly_average(close_prices, 20).iloc[-1], 2),
            round(Math.calculate_weekly_average(close_prices, 60).iloc[-1], 2),
            round(Math.calculate_weekly_average(close_prices, 120).iloc[-1], 2),
        ]

        # 計算月均線的移動平均
        monthly_sma_values = [
            round(Math.calculate_monthly_average(close_prices, 5).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 10).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 20).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 60).iloc[-1], 2),
            round(Math.calculate_monthly_average(close_prices, 120).iloc[-1], 2),
        ]

        return sma_values, weekly_sma_values, monthly_sma_values

    # 計算移動平均
    @staticmethod
    def calculate_moving_average(prices, window):
        return prices.rolling(window=window).mean()

    # 計算周均線
    @staticmethod
    def calculate_weekly_average(prices, window):
        # # 重採樣到週數據，使用最後一個有效值，並向前填充缺失值
        # weekly_prices = prices.resample('W').last().ffill()

        # # 計算移動平均線
        # weekly_ma = Math.calculate_moving_average(weekly_prices, window)

        # # 將結果對齊到原始的日期索引
        # aligned_weekly_ma = weekly_ma.reindex(prices.index, method='ffill')

        # return aligned_weekly_ma
        weekly_prices = prices.resample('W').last()
        return Math.calculate_moving_average(weekly_prices, window)

    # 計算月均線
    @staticmethod
    def calculate_monthly_average(prices, window):
        # monthly_prices = prices.resample('ME').last().ffill()
        # monthly_ma = Math.calculate_moving_average(monthly_prices, window)
        # aligned_monthly_ma = monthly_ma.reindex(prices.index, method='ffill')
        # return aligned_monthly_ma
        monthly_prices = prices.resample('M').last()
        return Math.calculate_moving_average(monthly_prices, window)
        
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
