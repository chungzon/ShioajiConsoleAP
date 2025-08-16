#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试整合后的每日收盘价下载调度器
验证调度器是否正常工作
"""

import time
from DataDownloadScheduler import start_scheduler

def main():
    """主函数"""
    print("=" * 60)
    print("测试整合后的每日收盘价下载调度器")
    print("=" * 60)
    
    print("\n1. 启动调度器...")
    scheduler = start_scheduler()
    
    print("2. 调度器已启动，等待10秒观察运行状态...")
    print("   调度器将在每日23:26执行下载任务")
    print("   功能包括：")
    print("   - TWSE数据下载")
    print("   - TPEx数据下载")
    print("   - 数据库存储")
    print("   - 重复下载防护")
    
    # 等待10秒观察调度器运行
    for i in range(10):
        print(f"   等待中... {i+1}/10")
        time.sleep(1)
    
    print("\n3. 测试完成")
    print("=" * 60)
    print("调度器将继续在后台运行")
    print("按 Ctrl+C 可以停止测试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 测试已停止")
