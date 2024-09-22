from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class SelectStockController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def calculate(self, ratio, ratio2, top_n):
        # all_wave_extremes = self.model.process_all_stocks(ratio, ratio2, top_n)
        result = self.model.process_all_stocks(ratio, ratio2, top_n)
        if isinstance(result, str) and result.startswith("錯誤："):
            self.view.show_error(result)
        else:
            # 處理正常的结果
            return result
        