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

