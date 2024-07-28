from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class DataDownloadController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def update_data(self, data_type, stock_id=None, start_date=None, end_date=None):
        if stock_id is None:
            stock_id = self.view.entry_stock_id.get()
            
        if not stock_id:
            self.view.set_status("股票代碼為必填")
            return
        
        latest_date_ticks, latest_date_kbars = self.model.get_latest_dates(stock_id)
        
        if end_date is None:
            end_date = datetime.today()
                    
        if data_type == 'Ticks':
            if start_date is None:
                start_date = (latest_date_ticks + timedelta(days=1))
            dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
            total_start_time = time.time()  # 紀錄總開始時間
            self.view.set_progress_config(maximum=len(dates))
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.process_date, stock_id, date): date for date in dates}
                completed_tasks = 0
                for future in as_completed(futures):
                    date, duration = future.result()
                    completed_tasks += 1
                    progress = (completed_tasks / len(dates)) * 100
                    self.view.update_progress(progress)
                    self.view.set_status(f"Date: {date.strftime('%Y-%m-%d')} completed in {duration:.2f} seconds")
            total_end_time = time.time()  # 紀錄總結束時間
            total_duration = total_end_time - total_start_time  # 計算總花費時間
            self.view.set_status(f"所有資料已經成功抓取並存入資料庫，總花費時間: {total_duration:.2f} 秒")
        else:
            if start_date is None:
                start_date = (latest_date_kbars + timedelta(days=1))
            dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
            total_start_time = time.time()  # 紀錄總開始時間
            self.view.set_progress_config(len(dates))
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.process_data_update, stock_id, date): date for date in dates}
                completed_tasks = 0
                for future in as_completed(futures):
                    date, duration = future.result()
                    completed_tasks += 1
                    progress = (completed_tasks / len(dates)) * 100
                    self.view.update_progress(progress)
                    # self.view.set_status(f"Date: {date.strftime('%Y-%m-%d')} completed in {duration:.2f} seconds")
            total_end_time = time.time()  # 紀錄總結束時間
            total_duration = total_end_time - total_start_time  # 計算總花費時間
            # self.view.set_status(f"所有資料已經成功抓取並存入資料庫，總花費時間: {total_duration:.2f} 秒")
            
    def process_data_update(self, stock_id, date):
        start_time = time.time()
        kbars_df = self.model.get_kbars_data(stock_id, date)
        if not kbars_df.empty:
            self.model.insert_kbars(kbars_df, stock_id)
        end_time = time.time()
        duration = end_time - start_time
        return date, duration
