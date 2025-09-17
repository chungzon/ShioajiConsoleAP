# ShioajiConsoleAP 股票分析系統

## 📋 專案概述

ShioajiConsoleAP 是一個基於永豐金證券API的股票分析系統，提供數據下載、即時監控、技術分析、回測和選股等功能。

## 🚀 快速開始

### 1. 環境要求
- **Python**: 3.7 或更高版本
- **作業系統**: Windows 10/11 (主要支援)
- **記憶體**: 4GB 以上
- **網路**: 穩定的網路連接

### 2. 安裝依賴套件

```bash
# 一鍵安裝所有依賴
pip install -r requirements.txt
```

### 3. 運行主程式

```bash
python Main.py
```

## 📁 專案結構

```
ShioajiConsoleAP_export/
├── Main.py                           # 主程式入口
├── requirements.txt                  # 依賴套件清單
├── README.md                        # 專案說明
├── INSTALL_GUIDE.md                 # 安裝指南
├── IMPORT_DEPENDENCIES.md           # 詳細依賴說明
├── model/                           # 數據模型層
│   ├── BaseModel.py
│   ├── DataDownloadModel.py
│   ├── DataAnalysisModel.py
│   ├── RealtimeMonitorModel.py
│   ├── BacktestModel.py
│   ├── SelectStockModel.py
│   └── DailyClosePriceDownloadModel.py
├── view/                            # 視圖層
│   ├── DataDownloadView.py
│   ├── DataAnalysisView.py
│   ├── RealtimeMonitorView.py
│   ├── BacktestView.py
│   ├── SelectStockView.py
│   └── DailyClosePriceDownloadView.py
├── controller/                      # 控制器層
│   ├── DataDownloadController.py
│   ├── DataAnalysisController.py
│   ├── RealtimeMonitorController.py
│   ├── BacktestController.py
│   ├── SelectStockController.py
│   └── DailyClosePriceDownloadController.py
├── common/                          # 共用模組
│   ├── Event.py
│   ├── Math.py
│   ├── Utils.py
│   └── enum/
│       └── StockType.py
├── resource/                        # 資源文件
│   ├── Resources.py
│   ├── tw_all_stocks.csv
│   └── chromedriver-win64/
├── utils/                           # 工具模組
│   └── unified_scheduler_manager.py
└── 其他功能檔案...
```

## 🔧 主要功能

### 1. 數據下載
- 股票KBar數據下載
- 即時Tick數據獲取
- 日收盤價數據下載
- 自動排程下載

### 2. 即時監控
- 股票即時價格監控
- 技術指標計算
- 圖表顯示

### 3. 數據分析
- 技術分析工具
- 統計分析功能
- 數據視覺化

### 4. 回測系統
- 策略回測
- 績效分析
- 風險評估

### 5. 選股策略
- 多種選股條件
- 策略組合
- 結果導出

## 📦 核心依賴套件

### 主要套件
- **shioaji**: 永豐金證券API
- **pandas**: 數據處理
- **numpy**: 數值計算
- **pymssql**: SQL Server連接
- **matplotlib**: 圖表繪製
- **tkinter**: GUI框架 (Python標準庫)

### 完整清單
詳細的依賴套件說明請參考 [IMPORT_DEPENDENCIES.md](IMPORT_DEPENDENCIES.md)

## ⚙️ 系統設定

### 1. 資料庫設定
- 安裝 SQL Server 或 SQL Server Express
- 建立資料庫 `TSE`
- 建立使用者 `TSE_USER`
- 設定連接字串: `127.0.0.1:1433`

### 2. API 設定
- 申請永豐金證券 API 金鑰
- 在 `Main.py` 中更新 API 金鑰和密鑰

### 3. ChromeDriver 設定
- 確保 `resource/chromedriver-win64/chromedriver.exe` 存在
- 版本需與 Chrome 瀏覽器匹配

## 🛠️ 故障排除

### 常見問題

#### 1. tkinter 錯誤
- **問題**: `ERROR: Could not find a version that satisfies the requirement tkinter`
- **解決**: tkinter 是 Python 標準庫，無需通過 pip 安裝
- **Windows**: 通常隨 Python 一起安裝
- **Linux**: `sudo apt-get install python3-tk`

#### 2. 套件安裝失敗
```bash
# 升級 pip
python -m pip install --upgrade pip

# 使用國內鏡像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 3. PyQt5 安裝問題
```bash
# Windows
pip install PyQt5

# 或使用 conda
conda install pyqt
```

#### 4. pymssql 安裝問題
```bash
# 可能需要 Visual C++ Build Tools
# 或使用 conda
conda install pymssql
```

## 📚 文件說明

- **[INSTALL_GUIDE.md](INSTALL_GUIDE.md)**: 快速安裝指南
- **[IMPORT_DEPENDENCIES.md](IMPORT_DEPENDENCIES.md)**: 詳細的依賴套件說明
- **[README_DailyKbarsScheduler.md](README_DailyKbarsScheduler.md)**: 每日KBar下載排程器說明

## 🔄 版本資訊

- **版本**: 1.0.0
- **Python**: 3.7+
- **最後更新**: 2024年1月
- **相容性**: Windows 10/11

## 📞 支援

如有問題或建議，請：
1. 查看相關文件
2. 檢查錯誤日誌
3. 聯繫開發團隊

---

**注意**: 本專案主要針對 Windows 環境開發，其他作業系統可能需要額外設定。


