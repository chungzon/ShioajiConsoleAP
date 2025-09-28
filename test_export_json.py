#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExportJson.py 測試腳本
"""

from ExportJson import ExportJson
from datetime import datetime, timedelta
import os

def test_export_json():
    """測試ExportJson功能"""
    print("開始測試 ExportJson...")
    
    # 建立匯出器
    exporter = ExportJson()
    
    # 測試參數
    stock_id = "2330"  # 台積電
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)  # 最近30天
    
    print(f"測試股票: {stock_id}")
    print(f"測試期間: {start_date} 到 {end_date}")
    
    # 測試匯出
    try:
        success = exporter.export_to_json(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
            output_path=f"test_{stock_id}_export.json"
        )
        
        if success:
            print("✅ 測試成功！")
            print(f"輸出檔案: test_{stock_id}_export.json")
            
            # 檢查檔案是否存在
            if os.path.exists(f"test_{stock_id}_export.json"):
                file_size = os.path.getsize(f"test_{stock_id}_export.json")
                print(f"檔案大小: {file_size} bytes")
            else:
                print("❌ 輸出檔案不存在")
        else:
            print("❌ 測試失敗！")
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_export_json()


