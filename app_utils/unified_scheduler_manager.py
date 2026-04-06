import schedule
import time
import threading
import logging
from typing import Dict, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedSchedulerManager:
    """统一的调度器管理器，避免schedule库的重复执行问题"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._schedulers: Dict[str, Dict] = {}
            self._running_tasks: Dict[str, bool] = {}
            self._main_scheduler_thread = None
            self._is_running = False
            self._stop_event = threading.Event()
            logger.info("统一调度器管理器已初始化")
    
    def add_scheduler(self, name: str, task_func: Callable, schedule_time: str, 
                     task_type: str = "daily", **kwargs) -> bool:
        """添加调度任务"""
        try:
            if name in self._schedulers:
                logger.warning(f"调度器 {name} 已存在，将被覆盖")
            
            # 创建调度任务
            if task_type == "daily":
                schedule.every().day.at(schedule_time).do(self._execute_task, name, task_func, **kwargs)
            elif task_type == "hourly":
                schedule.every().hour.do(self._execute_task, name, task_func, **kwargs)
            elif task_type == "minute":
                schedule.every(int(schedule_time)).minutes.do(self._execute_task, name, task_func, **kwargs)
            else:
                logger.error(f"不支持的调度类型: {task_type}")
                return False
            
            self._schedulers[name] = {
                'task_func': task_func,
                'schedule_time': schedule_time,
                'task_type': task_type,
                'kwargs': kwargs,
                'last_run': None
            }
            
            logger.info(f"调度器 {name} 添加成功，将在 {schedule_time} 执行")
            return True
            
        except Exception as e:
            logger.error(f"添加调度器 {name} 失败: {e}")
            return False
    
    def _execute_task(self, scheduler_name: str, task_func: Callable, **kwargs):
        """执行任务，防止重复执行"""
        task_key = f"{scheduler_name}_{datetime.now().strftime('%Y-%m-%d')}"
        
        if self._running_tasks.get(task_key, False):
            logger.warning(f"任务 {scheduler_name} 今天已经在运行中，跳过重复执行")
            return
        
        try:
            self._running_tasks[task_key] = True
            self._schedulers[scheduler_name]['last_run'] = datetime.now()
            
            logger.info(f"开始执行任务: {scheduler_name}")
            result = task_func(**kwargs)
            logger.info(f"任务 {scheduler_name} 执行完成")
            
            return result
            
        except Exception as e:
            logger.error(f"任务 {scheduler_name} 执行异常: {e}")
        finally:
            self._running_tasks[task_key] = False
    
    def start_main_scheduler(self):
        """启动主调度器线程"""
        if self._is_running:
            logger.warning("主调度器已经在运行中")
            return
        
        self._is_running = True
        self._stop_event.clear()
        
        def run_scheduler():
            logger.info("主调度器线程已启动")
            while not self._stop_event.is_set():
                try:
                    schedule.run_pending()
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"主调度器运行异常: {e}")
                    time.sleep(60)
        
        self._main_scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._main_scheduler_thread.start()
        logger.info("主调度器已启动")
    
    def stop_main_scheduler(self):
        """停止主调度器"""
        if not self._is_running:
            return
        
        self._is_running = False
        self._stop_event.set()
        
        if self._main_scheduler_thread and self._main_scheduler_thread.is_alive():
            self._main_scheduler_thread.join(timeout=5)
        
        logger.info("主调度器已停止")

# 全局统一调度器管理器实例
unified_scheduler_manager = UnifiedSchedulerManager()

def get_unified_scheduler_manager():
    """获取统一调度器管理器实例"""
    return unified_scheduler_manager
