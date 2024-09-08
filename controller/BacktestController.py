from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class BacktestController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def print_message(self):
        pd = self.model.get_stock_kbar_from_db(2618, '2024-03-29', '2024-03-29')
        df = self.model.find_peaks_troughs_v34(pd, '2618')
        print(df)
        
        #self.view.tree = ttk.Treeview(self, columns=list(df.columns), show='headings')
        
    def download_kbars_data(self, stock_id, start_date, end_date):
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            dates = [start_date_obj + timedelta(days=i) for i in range((end_date_obj - start_date_obj).days + 1)]
            total_start_time = time.time()
            with ThreadPoolExecutor(max_workers=1) as executor:
                futures = {executor.submit(self.process_data_update, stock_id, date): date for date in dates}
                for future in as_completed(futures):
                    date, duration = future.result()
                
    def process_data_update(self, stock_id, date):
        start_time = time.time()
        kbars_df = self.model.get_kbars_data(stock_id, date)
        if not kbars_df.empty:
            self.model.insert_kbars(kbars_df, stock_id)
        end_time = time.time()
        duration = end_time - start_time
        return date, duration