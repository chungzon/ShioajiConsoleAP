#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試每日KBar資料下載排程器
"""

from DailyKbarsDownloadScheduler import DailyKbarsDownloadScheduler
from datetime import datetime

def test_scheduler():
    """測試排程器功能"""
    print("🧪 開始測試每日KBar資料下載排程器...")
    
    # 創建排程器實例
    scheduler = DailyKbarsDownloadScheduler()
    
    print("✅ 排程器創建成功")
    print(f"📅 當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🕕 排程器將在每日18:00執行下載任務")
    
    # 測試通知功能
    print("🔔 測試通知功能...")
    scheduler.show_notification('測試通知', '這是測試通知，如果您看到這個通知，說明通知功能正常')
    
    print("✅ 測試完成！")
    print("💡 您可以運行 'python DailyKbarsDownloadScheduler.py' 來啟動實際的排程器")

if __name__ == "__main__":
    test_scheduler()
