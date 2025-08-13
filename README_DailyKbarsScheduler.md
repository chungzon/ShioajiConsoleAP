# 每日KBar資料下載排程器

## 概述

`DailyKbarsDownloadScheduler` 是一個自動化排程器，專門用於每日18:00自動下載當日股票KBar交易資料。此排程器模仿了現有的 `DataDownloadScheduler.py` 結構，並整合了 `DataDownloadModel.py` 中的 `get_all_stocks_kbars` 方法。

## 功能特點

- 🕕 **定時執行**: 每日18:00自動執行下載任務
- 📊 **KBar資料下載**: 下載當日所有股票的KBar資料
- 🔔 **Windows通知**: 下載開始和完成時會顯示系統通知
- 🛡️ **錯誤處理**: 包含完整的異常處理和日誌記錄
- 🧵 **多線程**: 使用守護線程，不會阻塞主程序
- 📁 **CSV資料源**: 使用 `tw_all_stocks.csv` 作為股票資料來源

## 檔案結構

```
├── DailyKbarsDownloadScheduler.py    # 主要的排程器類別
├── test_daily_kbars_scheduler.py     # 測試腳本
├── test_csv_reading.py               # CSV讀取測試腳本
└── README_DailyKbarsScheduler.md     # 說明文件
```

## 資料來源

排程器使用 `resource/tw_all_stocks.csv` 文件作為股票資料來源，該文件包含以下欄位：

- **StockCode**: 股票代號
- **StockName**: 股票名稱  
- **Category**: 股票類別（上市、上櫃、興櫃等）

## 使用方法

### 1. 直接運行排程器

```bash
python DailyKbarsDownloadScheduler.py
```

這會啟動排程器，它將在每日18:00自動執行下載任務。

### 2. 在您的程序中整合

```python
from DailyKbarsDownloadScheduler import start_daily_kbars_scheduler

# 啟動排程器
scheduler_thread = start_daily_kbars_scheduler()

# 您的其他程序邏輯...
# 排程器會在背景運行，不會阻塞主程序
```

### 3. 測試排程器

```bash
python test_daily_kbars_scheduler.py
```

這會測試排程器的基本功能，包括通知系統。

### 4. 測試CSV讀取功能

```bash
python test_csv_reading.py
```

這會測試修訂後的CSV文件讀取功能。

## 配置說明

### API設定

排程器使用以下Shioaji API設定：

```python
api = sj.Shioaji(simulation=True)  # 模擬模式
api.login(
    api_key="您的API金鑰",
    secret_key="您的密鑰"
)
```

**注意**: 請將API金鑰和密鑰替換為您自己的憑證。

### 排程時間

預設排程時間為每日18:00，您可以修改以下行來調整：

```python
schedule.every().day.at("18:00").do(self.download_daily_kbars_task)
```

### 資料來源設定

排程器會自動讀取 `resource/tw_all_stocks.csv` 文件中的股票列表。如果您需要更新股票列表，請：

1. 運行 `ExportStockCodeCSV.py` 來生成最新的股票列表
2. 或者手動更新 `tw_all_stocks.csv` 文件

## 依賴套件

- `schedule`: 用於排程管理
- `shioaji`: 永豐金證券API
- `win10toast`: Windows通知系統
- `pandas`: 數據處理
- `pymssql`: 資料庫連接

## 工作流程

1. **初始化**: 創建Shioaji API連接和DataDownloadModel實例
2. **排程設定**: 設定每日18:00執行下載任務
3. **股票列表讀取**: 從 `tw_all_stocks.csv` 讀取股票列表
4. **下載執行**: 調用 `get_all_stocks_kbars` 方法下載當日資料
5. **通知**: 下載完成後顯示成功或失敗通知
6. **日誌記錄**: 在控制台輸出詳細的執行日誌

## 修訂說明

### 主要變更

1. **資料來源變更**: 從Excel文件改為CSV文件
2. **列名對應**: 
   - 舊: `股票代號` → 新: `StockCode`
   - 舊: `股票名稱` → 新: `StockName`
   - 舊: `類別` → 新: `Category`
3. **文件讀取方式**: 從 `pd.read_excel()` 改為 `pd.read_csv()`

### 受影響的文件

- `model/BaseModel.py`: 修訂 `get_top_volumn_stocks` 方法
- `model/DailyClosePriceDownloadModel.py`: 修訂股票列表讀取邏輯
- `DailyKbarsDownloadScheduler.py`: 使用修訂後的資料讀取方法

## 注意事項

- 排程器使用守護線程，主程序結束時會自動停止
- 確保您的電腦在18:00時處於開機狀態
- 下載過程可能需要幾分鐘，取決於股票數量和網路速度
- 建議在首次使用前先運行測試腳本確認功能正常
- 確保 `resource/tw_all_stocks.csv` 文件存在且格式正確

## 故障排除

### 常見問題

1. **通知不顯示**: 確認Windows通知權限已開啟
2. **API連接失敗**: 檢查網路連接和API憑證
3. **資料庫錯誤**: 確認資料庫連接設定正確
4. **CSV讀取失敗**: 確認 `tw_all_stocks.csv` 文件存在且格式正確

### 日誌查看

排程器會在控制台輸出詳細的執行日誌，包括：
- 下載開始和完成時間
- 成功/失敗狀態
- 執行耗時
- 錯誤詳情（如果有）

## 版本資訊

- 版本: 1.1.0
- 創建日期: 2024年
- 最後修訂: 2024年（CSV資料源整合）
- 相容性: Python 3.7+
