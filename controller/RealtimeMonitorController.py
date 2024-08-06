from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class RealtimeMonitorController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def print_message(self):
        pd = self.model.get_stock_kbar_from_db(2618, '2024-03-29', '2024-03-29')
        df = self.model.find_peaks_troughs_v34(pd, '2618')
        print(df)
        
        #self.view.tree = ttk.Treeview(self, columns=list(df.columns), show='headings')