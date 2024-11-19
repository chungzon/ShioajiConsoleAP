from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from Event import EventBus, Event

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
            with ThreadPoolExecutor(max_workers=1) as executor:
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

    def start_download_all(self, start_date, end_date):
        # 訂閱日誌消息
        self.model.event_bus.subscribe("log_message", self.view.handle_log_message)
        
        # 創建並啟動下載線程
        download_thread = threading.Thread(
            target=self.run_download,
            args=(start_date, end_date),
            daemon=True  # 設置為守護線程，這樣主程序結束時線程會自動結束
        )
        download_thread.start()
    
    def run_download(self, start_date, end_date):
        try:
            self.model.get_all_stocks_kbars(start_date, end_date)
        except Exception as e:
            # 發送錯誤消息到界面
            self.model.event_bus.publish(Event("log_message", f"下載過程發生錯誤: {str(e)}"))
        
