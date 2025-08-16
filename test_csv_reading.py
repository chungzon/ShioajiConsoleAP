#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修訂後的CSV文件讀取功能
"""

import pandas as pd
import os
from model.BaseModel import BaseModel
import shioaji as sj

def test_csv_reading():
    """測試CSV文件讀取功能"""
    print("🧪 開始測試CSV文件讀取功能...")
    
    # 測試直接讀取CSV文件
    print("\n📁 測試直接讀取CSV文件...")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resource_dir = os.path.join(current_dir, 'resource')
        csv_path = os.path.join(resource_dir, 'tw_all_stocks.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"✅ CSV文件讀取成功")
            print(f"📊 文件大小: {len(df)} 行")
            print(f"📋 列標題: {list(df.columns)}")
            print(f"🔢 前5筆資料:")
            print(df.head())
        else:
            print(f"❌ CSV文件不存在: {csv_path}")
            return False
    except Exception as e:
        print(f"❌ 讀取CSV文件時發生錯誤: {e}")
        return False
    
    # 測試BaseModel的get_top_volumn_stocks方法
    print("\n🔧 測試BaseModel的get_top_volumn_stocks方法...")
    try:
        # 創建一個模擬的API對象
        class MockAPI:
            pass
        
        mock_api = MockAPI()
        base_model = BaseModel(mock_api)
        
        # 測試獲取所有股票
        all_stocks = base_model.get_top_volumn_stocks()
        if isinstance(all_stocks, list):
            print(f"✅ 成功獲取所有股票，共 {len(all_stocks)} 支")
            print(f"🔢 前10支股票: {all_stocks[:10]}")
        else:
            print(f"❌ 獲取股票列表失敗: {all_stocks}")
            return False
        
        # 測試獲取前10支股票
        top_10_stocks = base_model.get_top_volumn_stocks(10)
        if isinstance(top_10_stocks, list) and len(top_10_stocks) == 10:
            print(f"✅ 成功獲取前10支股票: {top_10_stocks}")
        else:
            print(f"❌ 獲取前10支股票失敗: {top_10_stocks}")
            return False
            
    except Exception as e:
        print(f"❌ 測試BaseModel時發生錯誤: {e}")
        return False
    
    print("\n✅ 所有測試通過！")
    return True

if __name__ == "__main__":
    test_csv_reading()




