from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class DailyClosePriceDownloadController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self
            
    def download_daily_close_price(self, start_date, end_date, stock_id=None):
        if stock_id is None:
            self.model.download_daily_close_price()
        else:
            self.model.download_daily_close_top30_stock(self.view, start_date, end_date, stock_id)

    def start_download_all(self, start_date, end_date):
        self.model.download_daily_close_price_all(self.view, start_date, end_date)
