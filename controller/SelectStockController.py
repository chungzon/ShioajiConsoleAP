from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class SelectStockController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def calculate(self, ratio):
        self.model.process_all_stocks(ratio)