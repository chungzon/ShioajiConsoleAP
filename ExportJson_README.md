# ExportJson.py 使用說明

## 概述

`ExportJson.py` 是一個獨立的股票資料匯出工具，可以從資料庫讀取股票資料並匯出為JSON格式。此程式不依賴其他檔案，可以獨立運行。

## 功能特點

- 🔍 **資料庫讀取**: 從SQL Server資料庫讀取股票KBar資料
- 📊 **技術分析**: 計算移動平均線、技術指標、比例價格
- 📈 **波段分析**: 自動尋找波峰波谷，計算總波段和最近波段比例
- 📋 **JSON匯出**: 按照指定格式匯出為JSON檔案
- 🎯 **獨立運行**: 不依賴GUI或其他程式檔案

## 安裝需求

確保已安裝以下套件：
```bash
pip install pymssql pandas numpy
```

## 使用方法

### 1. 命令列使用

```bash
# 基本用法
python ExportJson.py 2330 2024-01-01 2024-01-31

# 指定最近波段日期
python ExportJson.py 2330 2024-01-01 2024-01-31 --recent_start 2024-01-15 --recent_end 2024-01-31

# 指定輸出檔案路徑
python ExportJson.py 2330 2024-01-01 2024-01-31 --output my_stock_data.json
```

### 2. 參數說明

- `stock_id`: 股票代碼（必填）
- `start_date`: 起始日期，格式：YYYY-MM-DD（必填）
- `end_date`: 結束日期，格式：YYYY-MM-DD（必填）
- `--recent_start`: 最近波段起始日期，格式：YYYY-MM-DD（選填）
- `--recent_end`: 最近波段結束日期，格式：YYYY-MM-DD（選填）
- `--output`: 輸出檔案路徑（選填）

### 3. 程式內使用

```python
from ExportJson import ExportJson

# 建立匯出器
exporter = ExportJson()

# 匯出資料
success = exporter.export_to_json(
    stock_id='2330',
    start_date=datetime(2024, 1, 1).date(),
    end_date=datetime(2024, 1, 31).date(),
    recent_start_date=datetime(2024, 1, 15).date(),
    recent_end_date=datetime(2024, 1, 31).date(),
    output_path='output.json'
)
```

## 資料庫設定

程式預設連接以下資料庫設定：
- **伺服器**: 127.0.0.1:1433
- **使用者**: TSE_USER
- **密碼**: fuckme
- **資料庫**: TSE

如需修改，請編輯 `ExportJson.py` 中的 `db_config` 字典。

## 輸出格式

匯出的JSON檔案包含以下結構：

```json
{
    "stock_code": "2330",
    "base": "580.00",
    "date": "2024-01-31",
    "data": {
        "NOW PRICE": "580.00",
        "N[0]": "500.00",
        "N[0.191]": "515.00",
        // ... 更多比例價格
        "日(5)_DC": "575.00",
        "日(10)_DC": "570.00",
        // ... 更多均線資料
        "AL_DC": "590.00",
        "NL_DC": "480.00",
        // ... 更多技術指標
    },
    "over_ratio_dont_buy": "0.03",
    "extend_over_ratio_dont_buy": "0.03",
    "no_buy_after": "10:00:00",
    "final_buy": "12:00:00",
    "extend_time": "00:30:00",
    "enable_15k20ma": true,
    "enable_15k10ma": true,
    "before_n": 2
}
```

## 計算內容

### 1. 比例價格
- 總波段比例：基於整個期間的波峰波谷計算
- 最近波段比例：基於指定最近期間的波峰波谷計算
- 比例序列：0, 0.191, 0.382, 0.5, 0.618, 0.809, 1, 1.191, 1.382, 1.5, 1.618, 1.809, 2, 2.191, 2.382, 2.5, 2.618, 2.809, 3, 3.191, 3.382, 3.5, 3.618, 3.809, 4, 4.191, 4.382, 4.5, 4.618, 4.809, 5

### 2. 移動平均線
- **日均線**: 5MA, 10MA, 20MA, 60MA, 120MA
- **週均線**: 5MA, 10MA, 20MA, 60MA, 120MA
- **月均線**: 5MA, 10MA, 20MA, 60MA, 120MA
- **15分鐘均線**: 5MA, 10MA, 20MA, 60MA, 120MA
- **扣抵值**: 各均線的扣抵值計算

### 3. 技術指標
- **AL**: 最高價
- **NL**: 最低價
- **NH**: 最近最高價（最近10天）
- **AH**: 最近最低價（最近10天）
- **CDP**: 中心點價格

## 使用範例

### 範例1：基本匯出
```bash
python ExportJson.py 2330 2024-01-01 2024-01-31
```
輸出檔案：`2330_data_2024-01-31.json`

### 範例2：指定最近波段
```bash
python ExportJson.py 2330 2024-01-01 2024-01-31 --recent_start 2024-01-15 --recent_end 2024-01-31
```

### 範例3：自訂輸出路徑
```bash
python ExportJson.py 2330 2024-01-01 2024-01-31 --output /path/to/output.json
```

## 注意事項

1. **資料庫連接**: 確保資料庫服務正在運行且連接設定正確
2. **資料完整性**: 確保指定日期範圍內有足夠的股票資料
3. **記憶體使用**: 大量資料可能消耗較多記憶體
4. **檔案權限**: 確保有寫入輸出目錄的權限

## 錯誤處理

程式會自動處理以下錯誤：
- 資料庫連接失敗
- 股票資料不存在
- 日期格式錯誤
- 檔案寫入失敗

錯誤訊息會顯示在控制台中，幫助診斷問題。

## 版本資訊

- **版本**: 1.0.0
- **Python**: 3.7+
- **依賴**: pymssql, pandas, numpy
- **資料庫**: SQL Server


