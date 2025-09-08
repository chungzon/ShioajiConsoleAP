# ShioajiConsoleAP 快速安裝指南

## 🚀 快速開始

### 1. 環境要求
- **Python**: 3.7 或更高版本
- **作業系統**: Windows 10/11
- **記憶體**: 4GB 以上
- **網路**: 穩定的網路連接

### 2. 一鍵安裝

```bash
# 1. 下載專案
git clone [專案網址]
cd ShioajiConsoleAP_export

# 2. 安裝所有依賴套件
pip install -r requirements.txt

# 3. 運行主程式
python Main.py
```

## 📦 主要依賴套件

### 核心套件
```bash
pip install shioaji pandas numpy pymssql
```

### GUI 套件
```bash
# tkinter 是 Python 標準庫，無需安裝
pip install tkcalendar tkintertable PyQt5
```

### 視覺化套件
```bash
pip install matplotlib Pillow
```

### 機器學習套件
```bash
pip install scikit-learn joblib
```

### 網路套件
```bash
pip install requests beautifulsoup4 selenium
```

### 排程套件
```bash
pip install schedule plyer win10toast
```

### 工具套件
```bash
pip install pyperclip xlsxwriter
```

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

## 🔧 故障排除

### 常見問題

#### 1. 套件安裝失敗
```bash
# 升級 pip
python -m pip install --upgrade pip

# 使用國內鏡像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 2. PyQt5 安裝問題
```bash
# Windows
pip install PyQt5

# 或使用 conda
conda install pyqt
```

#### 3. pymssql 安裝問題
```bash
# 可能需要 Visual C++ Build Tools
# 或使用 conda
conda install pymssql
```

#### 4. tkinter 問題
- **Windows**: tkinter 通常隨 Python 一起安裝，無需額外安裝
- **Linux**: 可能需要 `sudo apt-get install python3-tk`
- **macOS**: 通常已包含，如果沒有可通過 Homebrew 安裝
- **注意**: tkinter 不應該出現在 requirements.txt 中，因為它是標準庫

## 📋 檢查清單

安裝完成後，請確認：

- [ ] Python 3.7+ 已安裝
- [ ] 所有依賴套件已安裝
- [ ] SQL Server 已設定
- [ ] API 金鑰已配置
- [ ] ChromeDriver 已準備
- [ ] 主程式可正常運行

## 📞 需要幫助？

如果遇到問題，請：
1. 查看詳細說明文件 `IMPORT_DEPENDENCIES.md`
2. 檢查錯誤日誌
3. 聯繫開發團隊

---

**注意**: 本專案主要針對 Windows 環境開發，其他作業系統可能需要額外設定。
