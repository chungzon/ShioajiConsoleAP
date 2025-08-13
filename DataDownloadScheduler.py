import schedule
import time
from threading import Thread
from datetime import datetime
from win10toast import ToastNotifier
from AutoDownloadDailyClosePrice import AutoDownloadDailyClosePrice
from time import sleep

class DataDownloadScheduler:
    def __init__(self):
        self.downloader = AutoDownloadDailyClosePrice()
        self.toaster = ToastNotifier()

    def show_notification(self, title, message, duration=5):
        self.toaster.show_toast(title, message, duration=duration, threaded=True)

    def download_task(self):
        self.show_notification('股票數據下載', '開始下載每日收盤價數據')

        start_time = datetime.now()
        success = self.downloader.run()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        sleep(5)

        if success:
            message = f'數據下載成功,耗時 {duration:.2f} 秒'
        else:
            message = f'數據下載失敗,請檢查日誌'

        self.show_notification('股票數據下載', message)

    def run_scheduler(self):
        schedule.every().day.at("17:30").do(self.download_task)
        
        while True:
            schedule.run_pending()
            print("run_pending")
            time.sleep(30)  # 每分鐘檢查一次

def start_scheduler():
    scheduler = DataDownloadScheduler()
    scheduler_thread = Thread(target=scheduler.run_scheduler)
    scheduler_thread.start()
    return scheduler_thread

