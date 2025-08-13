import schedule
import time
from threading import Thread
from datetime import datetime, date
from win10toast import ToastNotifier
from model.DataDownloadModel import DataDownloadModel
from time import sleep

class DailyKbarsDownloadScheduler:
    def __init__(self, api):
        # 初始化Shioaji API
        self.api = api
        
        # 初始化數據下載模型
        self.download_model = DataDownloadModel(self.api)
        self.toaster = ToastNotifier()

    def show_notification(self, title, message, duration=5):
        """顯示Windows通知"""
        self.toaster.show_toast(title, message, duration=duration, threaded=True)

    def download_daily_kbars_task(self):
        """下載當日KBar資料的任務"""
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        
        self.show_notification('股票KBar數據下載', f'開始下載 {today_str} 的KBar資料')

        start_time = datetime.now()
        
        try:
            # 使用DataDownloadModel的get_all_stocks_kbars方法下載當日資料
            # self.download_model.get_all_stocks_kbars(today_str, today_str)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            sleep(5)
            
            message = f'{today_str} KBar資料下載成功,耗時 {duration:.2f} 秒'
            self.show_notification('股票KBar數據下載', message)
            
            print(f"✅ {message}")
            
        except Exception as e:
            error_message = f'{today_str} KBar資料下載失敗: {str(e)}'
            self.show_notification('股票KBar數據下載', error_message)
            print(f"❌ {error_message}")

    def run_scheduler(self):
        """運行排程器"""
        # 設定每日18:00執行下載任務
        schedule.every().day.at("18:30").do(self.download_daily_kbars_task)
        
        print("🕕 KBar資料下載排程器已啟動，將在每日18:30執行下載任務")
        self.show_notification('股票KBar數據下載', 'KBar資料下載排程器已啟動，將在每日18:30執行下載任務')

        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒檢查一次排程

def start_daily_kbars_scheduler(api):
    """啟動每日KBar資料下載排程器"""
    scheduler = DailyKbarsDownloadScheduler(api)
    scheduler_thread = Thread(target=scheduler.run_scheduler)
    scheduler_thread.daemon = True  # 設為守護線程，主程序結束時自動結束
    scheduler_thread.start()
    return scheduler_thread

if __name__ == "__main__":
    # 如果直接運行此腳本，則啟動排程器
    start_daily_kbars_scheduler()
    
    # 保持主線程運行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 排程器已停止")
