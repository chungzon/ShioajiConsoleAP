from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class SelectStockController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def calculate(self, start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections):
        # all_wave_extremes = self.model.process_all_stocks(ratio, ratio2, top_n)
        result = self.model.process_all_stocks(start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections)
        if isinstance(result, str) and result.startswith("錯誤："):
            self.view.show_error(result)
        else:
            # 處理正常的结果
            return result
        
    def download_detail_data(self, stock_id, start_date, end_date, file_path):
        self.model.analyze_data(stock_id, start_date, end_date, file_path)

    def show_detail_data(self, stock_id):
        stock_data = self.model.get_stock_data_from_all_wave_extremes(stock_id)
        if stock_data is None:
            print(f"沒有找到股票 {stock_id} 的數據")
            return

        # 整理均線數據
        organized_ma_data = {
            "日均線": {
                "5日": stock_data.get('sma_5', 'N/A'),
                "10日": stock_data.get('sma_10', 'N/A'),
                "20日": stock_data.get('sma_20', 'N/A'),
                "60日": stock_data.get('sma_60', 'N/A'),
                "120日": stock_data.get('sma_120', 'N/A')
            },
            "週均線": {
                "5週": stock_data.get('weekly_sma_5', 'N/A'),
                "10週": stock_data.get('weekly_sma_10', 'N/A'),
                "20週": stock_data.get('weekly_sma_20', 'N/A'),
                "60週": stock_data.get('weekly_sma_60', 'N/A'),
                "120週": stock_data.get('weekly_sma_120', 'N/A')
            },
            "月均線": {
                "5月": stock_data.get('monthly_sma_5', 'N/A'),
                "10月": stock_data.get('monthly_sma_10', 'N/A'),
                "20月": stock_data.get('monthly_sma_20', 'N/A'),
                "60月": stock_data.get('monthly_sma_60', 'N/A'),
                "120月": stock_data.get('monthly_sma_120', 'N/A')
            }
        }

        # 整理比例價格數據
        ratio_prices = {
            '0.191': stock_data.get('Ratio_0.191', 'N/A'),
            '0.382': stock_data.get('Ratio_0.382', 'N/A'),
            '0.5': stock_data.get('Ratio_0.5', 'N/A'),
            '0.618': stock_data.get('Ratio_0.618', 'N/A'),
            '0.809': stock_data.get('Ratio_0.809', 'N/A'),
            '1': stock_data.get('Ratio_1', 'N/A'),
            '1.382': stock_data.get('Ratio_1.382', 'N/A'),
            '1.5': stock_data.get('Ratio_1.5', 'N/A'),
            '1.618': stock_data.get('Ratio_1.618', 'N/A'),
            '2': stock_data.get('Ratio_2', 'N/A'),
            '4': stock_data.get('Ratio_4', 'N/A')
        }

        # 添加其他可能需要的數據
        additional_data = {
            '最高價': stock_data.get('Max_Value', 'N/A'),
            '最低價': stock_data.get('Min_Value', 'N/A'),
            '最新收盤價': stock_data.get('latest_close_price', 'N/A'),
            '價差比例': stock_data.get('spread_ratio', 'N/A'),
            '最新收盤價-0.618比例': stock_data.get('latest_close_price-0.618_ratio', 'N/A')
        }

        self.view.show_sma_data(stock_id, organized_ma_data, ratio_prices, additional_data)
        