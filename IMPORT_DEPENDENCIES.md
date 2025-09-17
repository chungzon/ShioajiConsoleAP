# ShioajiConsoleAP 專案依賴套件說明

## 概述

本文檔詳細說明了 ShioajiConsoleAP 專案中所有使用的 import 語句和依賴套件，包括標準庫、第三方套件和本地模組。

## 安裝方式

### 1. 使用 requirements.txt 安裝

```bash
pip install -r requirements.txt
```

### 2. 手動安裝主要套件

```bash
pip install shioaji pandas numpy pymssql tkcalendar matplotlib PyQt5 scikit-learn requests beautifulsoup4 selenium schedule plyer
```

## 依賴套件分類

### 🔧 核心依賴套件

#### 1. **shioaji** - 永豐金證券API
- **用途**: 連接永豐金證券API，獲取股票數據
- **使用位置**: 
  - `Main.py` - API初始化和登入
  - `model/DataDownloadModel.py` - 下載KBar數據
  - `model/RealtimeMonitorModel.py` - 即時監控
  - `model/BacktestModel.py` - 回測功能
- **版本要求**: >= 1.0.0

#### 2. **pandas** - 數據處理
- **用途**: 數據分析和處理，DataFrame操作
- **使用位置**: 所有model檔案，數據分析功能
- **版本要求**: >= 1.3.0

#### 3. **numpy** - 數值計算
- **用途**: 數值計算和數組操作
- **使用位置**: 
  - `model/BaseModel.py`
  - `common/Math.py`
  - `goldline.py` - 機器學習
- **版本要求**: >= 1.21.0

#### 4. **pymssql** - SQL Server連接
- **用途**: 連接SQL Server資料庫
- **使用位置**: 所有model檔案，數據存儲和讀取
- **版本要求**: >= 2.2.0

### 🖥️ GUI 相關套件

#### 1. **tkinter** - 基礎GUI框架
- **用途**: Python內建GUI框架，建立主界面
- **使用位置**: 所有view檔案和Main.py
- **說明**: Python標準庫，無需額外安裝

#### 2. **tkcalendar** - 日期選擇器
- **用途**: 提供日期選擇功能
- **使用位置**: 所有view檔案
- **版本要求**: >= 1.6.0

#### 3. **tkintertable** - 表格組件
- **用途**: 提供進階表格功能
- **使用位置**: 
  - `view/SelectStockView.py`
  - `view/RealtimeMonitorView.py`
  - `view/BacktestView.py`
- **版本要求**: >= 1.2.0

#### 4. **PyQt5** - 進階GUI組件
- **用途**: 提供更豐富的GUI組件
- **使用位置**: 
  - `view/SelectStockView.py`
  - `view/DataAnalysisView.py`
- **版本要求**: >= 5.15.0

### 📊 數據視覺化套件

#### 1. **matplotlib** - 圖表繪製
- **用途**: 繪製股票走勢圖和技術分析圖表
- **使用位置**: 
  - `view/SelectStockView.py`
  - `view/RealtimeMonitorView.py`
  - `view/BacktestView.py`
- **版本要求**: >= 3.5.0

#### 2. **Pillow (PIL)** - 圖像處理
- **用途**: 圖像處理和截圖功能
- **使用位置**: 
  - `view/SelectStockView.py`
  - `view/DataAnalysisView.py`
- **版本要求**: >= 8.3.0

### 🤖 機器學習套件

#### 1. **scikit-learn** - 機器學習庫
- **用途**: 股票預測模型訓練
- **使用位置**: `goldline.py`
- **版本要求**: >= 1.0.0

#### 2. **joblib** - 模型序列化
- **用途**: 保存和載入訓練好的模型
- **使用位置**: `goldline.py`
- **版本要求**: >= 1.1.0

### 🌐 網路和爬蟲套件

#### 1. **requests** - HTTP請求
- **用途**: 發送HTTP請求，獲取網路數據
- **使用位置**: 
  - `common/Utils.py`
  - `model/DailyClosePriceDownloadModel.py`
  - `StockModel.py`
- **版本要求**: >= 2.25.0

#### 2. **beautifulsoup4** - HTML解析
- **用途**: 解析HTML內容
- **使用位置**: `StockModel.py`
- **版本要求**: >= 4.9.0

#### 3. **selenium** - 網頁自動化
- **用途**: 自動化網頁操作
- **使用位置**: `DailyAverage.py`
- **版本要求**: >= 4.0.0

### ⏰ 排程和通知套件

#### 1. **schedule** - 任務排程
- **用途**: 定時執行任務
- **使用位置**: 
  - `utils/unified_scheduler_manager.py`
  - `DataDownloadScheduler.py`
  - `DailyKbarsDownloadScheduler.py`
- **版本要求**: >= 1.1.0

#### 2. **plyer** - 跨平台通知
- **用途**: 系統通知功能
- **使用位置**: `DataDownloadScheduler.py`
- **版本要求**: >= 2.0.0

#### 3. **win10toast** - Windows通知
- **用途**: Windows系統通知
- **使用位置**: 排程器相關檔案
- **版本要求**: >= 0.9

### 🛠️ 其他工具套件

#### 1. **pyperclip** - 剪貼簿操作
- **用途**: 複製內容到剪貼簿
- **使用位置**: `view/SelectStockView.py`
- **版本要求**: >= 1.8.0

#### 2. **xlsxwriter** - Excel文件寫入
- **用途**: 生成Excel文件
- **使用位置**: `StockModel.py`
- **版本要求**: >= 3.0.0

## Python 標準庫

### 核心標準庫
- **datetime** - 日期時間處理
- **threading** - 多線程處理
- **concurrent.futures** - 並發執行
- **logging** - 日誌記錄
- **os** - 作業系統介面
- **json** - JSON數據處理
- **csv** - CSV文件處理
- **io** - 輸入輸出操作
- **time** - 時間相關功能
- **math** - 數學運算
- **enum** - 枚舉類型
- **collections** - 集合數據結構
- **functools** - 函數工具
- **queue** - 隊列數據結構
- **typing** - 類型提示
- **re** - 正則表達式
- **calendar** - 日曆功能

## 本地模組結構

### 專案內部模組
```
├── model/                    # 數據模型層
│   ├── BaseModel.py         # 基礎模型類
│   ├── DataDownloadModel.py # 數據下載模型
│   ├── DataAnalysisModel.py # 數據分析模型
│   ├── RealtimeMonitorModel.py # 即時監控模型
│   ├── BacktestModel.py     # 回測模型
│   ├── SelectStockModel.py  # 選股模型
│   └── DailyClosePriceDownloadModel.py # 日收盤價下載模型
├── view/                    # 視圖層
│   ├── DataDownloadView.py  # 數據下載視圖
│   ├── DataAnalysisView.py  # 數據分析視圖
│   ├── RealtimeMonitorView.py # 即時監控視圖
│   ├── BacktestView.py      # 回測視圖
│   ├── SelectStockView.py   # 選股視圖
│   └── DailyClosePriceDownloadView.py # 日收盤價下載視圖
├── controller/              # 控制器層
│   ├── DataDownloadController.py
│   ├── DataAnalysisController.py
│   ├── RealtimeMonitorController.py
│   ├── BacktestController.py
│   ├── SelectStockController.py
│   └── DailyClosePriceDownloadController.py
├── common/                  # 共用模組
│   ├── Event.py            # 事件系統
│   ├── Math.py             # 數學工具
│   ├── Utils.py            # 通用工具
│   └── enum/
│       └── StockType.py    # 股票類型枚舉
├── resource/               # 資源文件
│   └── Resources.py        # 資源管理
└── utils/                  # 工具模組
    └── unified_scheduler_manager.py # 統一排程管理器
```

## 安裝注意事項

### 1. 系統要求
- **Python版本**: 3.7 或更高版本
- **作業系統**: Windows 10/11 (主要支援)
- **記憶體**: 建議 4GB 以上
- **硬碟空間**: 至少 2GB 可用空間

### 2. 資料庫設定
- **SQL Server**: 需要安裝 SQL Server 或 SQL Server Express
- **連接設定**: 預設連接 `127.0.0.1:1433`
- **資料庫名稱**: TSE
- **使用者**: TSE_USER

### 3. 瀏覽器驅動
- **ChromeDriver**: 位於 `resource/chromedriver-win64/`
- **版本**: 需要與Chrome瀏覽器版本匹配

### 4. API設定
- **Shioaji API**: 需要申請永豐金證券API金鑰
- **模擬模式**: 預設使用模擬模式進行測試

## 常見問題排除

### 1. 套件安裝失敗
```bash
# 升級pip
python -m pip install --upgrade pip

# 使用國內鏡像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. PyQt5 安裝問題
```bash
# Windows
pip install PyQt5

# 如果失敗，嘗試
pip install PyQt5-tools
```

### 3. pymssql 安裝問題
```bash
# 可能需要安裝 Microsoft Visual C++ Build Tools
# 或使用 conda 安裝
conda install pymssql
```

### 4. tkinter 問題
- tkinter 是Python標準庫，通常不需要額外安裝
- 在某些Linux發行版可能需要: `sudo apt-get install python3-tk`

## 版本相容性

| 套件 | 最低版本 | 推薦版本 | 測試版本 |
|------|----------|----------|----------|
| Python | 3.7 | 3.9+ | 3.11 |
| shioaji | 1.0.0 | 1.2.0+ | 1.3.0 |
| pandas | 1.3.0 | 1.5.0+ | 2.0.0 |
| numpy | 1.21.0 | 1.24.0+ | 1.24.0 |
| matplotlib | 3.5.0 | 3.6.0+ | 3.7.0 |
| PyQt5 | 5.15.0 | 5.15.0+ | 5.15.0 |

## 更新日誌

- **2024-01-XX**: 初始版本，建立基本依賴說明
- **2024-01-XX**: 新增機器學習相關套件
- **2024-01-XX**: 完善GUI套件說明
- **2024-01-XX**: 新增排程和通知套件

## 聯絡資訊

如有任何問題或建議，請聯繫開發團隊或提交Issue。


