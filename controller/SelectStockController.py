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
        