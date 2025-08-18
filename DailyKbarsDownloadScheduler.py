import time
from threading import Thread
from datetime import datetime, date
from model.DataDownloadModel import DataDownloadModel
from utils.unified_scheduler_manager import get_unified_scheduler_manager

class DailyKbarsDownloadScheduler:
    def __init__(self, api):
        # 初始化Shioaji API
        self.api = api
        
        # 初始化數據下載模型
        self.download_model = DataDownloadModel(self.api)
        
        # 获取统一调度器管理器
        self.scheduler_manager = get_unified_scheduler_manager()

    def show_notification(self, title, message, duration=5):
        """顯示系統通知"""
        try:
            # 尝试使用 plyer
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=duration
            )
        except ImportError:
            # 如果 plyer 不可用，使用控制台通知
            self._console_notification(title, message)
        except Exception as e:
            print(f"通知发送异常: {e}")
            # 降级到控制台通知
            self._console_notification(title, message)

    def _console_notification(self, title, message):
        """控制台通知"""
        separator = "=" * 60
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{separator}")
        print(f"📢 通知时间: {timestamp}")
        print(f"📋 标题: {title}")
        print(f"📝 内容: {message}")
        print(f"{separator}\n")

    def download_daily_kbars_task(self):
        """下載當日KBar資料的任務"""
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        
        self.show_notification('股票KBar數據下載', f'開始下載 {today_str} 的KBar資料')

        start_time = datetime.now()
        
        try:
            # 使用DataDownloadModel的get_all_stocks_kbars方法下載當日資料
            self.download_model.get_all_stocks_kbars(today_str, today_str)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            time.sleep(5)
            
            message = f'{today_str} KBar資料下載成功,耗時 {duration:.2f} 秒'
            self.show_notification('股票KBar數據下載', message)
            
            print(f"✅ {message}")
            
        except Exception as e:
            error_message = f'{today_str} KBar資料下載失敗: {str(e)}'
            self.show_notification('股票KBar數據下載', error_message)
            print(f"❌ {error_message}")

    def setup_scheduler(self):
        """设置调度任务"""
        # 添加每日KBar下载任务
        self.scheduler_manager.add_scheduler(
            name="daily_kbars_download",
            task_func=self.download_daily_kbars_task,
            schedule_time="17:30",
            task_type="daily"
        )
        
        print("🕕 KBar資料下載排程任務已設置，將在每日17:30執行下載任務")

def start_daily_kbars_scheduler(api):
    """啟動每日KBar資料下載排程器"""
    scheduler = DailyKbarsDownloadScheduler(api)
    
    # 设置调度任务
    scheduler.setup_scheduler()
    
    # 启动主调度器（如果还没有启动）
    scheduler_manager = get_unified_scheduler_manager()
    if not scheduler_manager._is_running:
        scheduler_manager.start_main_scheduler()
    
    return scheduler

if __name__ == "__main__":
    # 如果直接運行此腳本，則啟動排程器
    start_daily_kbars_scheduler(None)
    
    # 保持主線程運行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 排程器已停止")
