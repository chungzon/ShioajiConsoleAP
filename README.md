# ShioajiConsole 股票分析與資料匯出系統

## 版本資訊
- **版本**: 1.0.0
- **發布日期**: 2024年12月
- **支援平台**: Windows 10/11
- **Python版本**: 3.8+

## 系統簡介

ShioajiConsole 是一個功能完整的股票分析與資料匯出系統，整合了永豐證券 Shioaji API，提供以下主要功能：

### 主要功能模組

1. **資料分析** - 技術指標計算與波段分析
2. **資料下載** - 股票歷史資料下載與管理
3. **即時監控** - 即時股價監控與警示
4. **資料回測** - 策略回測與績效分析
5. **年度交易量下載** - 年度交易量統計
6. **選股策略** - 多種選股策略與篩選
7. **API服務** - RESTful API 服務提供

## 安裝與執行

### 方法一：直接執行（推薦）
1. 下載 `ShioajiConsole.exe`
2. 雙擊執行即可

### 方法二：從原始碼執行
1. 確保已安裝 Python 3.8+
2. 安裝必要套件：
   ```bash
   pip install -r requirements.txt
   ```
3. 執行主程式：
   ```bash
   python Main.py
   ```

## API 使用說明

### 啟動 API 服務

1. 開啟 ShioajiConsole 應用程式
2. 切換到「API服務」分頁
3. 設定服務參數：
   - **IP地址**: 預設為 `localhost`
   - **端口**: 預設為 `5000`
4. 點擊「啟動服務」按鈕
5. 服務啟動後會顯示服務狀態和 URL

### API 端點說明

#### 1. 健康檢查
```http
GET http://localhost:5000/api/health
```

**回應範例**:
```json
{
    "status": "healthy",
    "message": "股票資料匯出API服務正常運行",
    "timestamp": "2024-12-19T10:30:00"
}
```

#### 2. 股票資料匯出
```http
POST http://localhost:5000/api/export-stock-data
Content-Type: application/json
```

**請求參數**:
```json
{
    "stock_id": "2330",
    "start_date": "2024-01-01",
    "end_date_start": "2024-12-01",
    "end_date_end": "2024-12-31"
}
```

**參數說明**:
- `stock_id`: 股票代碼（字串）
- `start_date`: 起始日期（YYYY-MM-DD 格式）
- `end_date_start`: 結束日期開始（YYYY-MM-DD 格式）
- `end_date_end`: 結束日期結束（YYYY-MM-DD 格式）

**回應範例**:
```json
{
    "success": true,
    "data": [
        {
            "stock_code": "2330",
            "base": "580.00",
            "before_n": "5",
            "calculation_date": "2024-12-01",
            "date": "2024-12-01",
            "date_index": 1,
            "day_of_week": "Sunday",
            "data": {
                "[0]": "450.00",
                "[0.191]": "474.80",
                "[0.382]": "499.60",
                "[0.5]": "515.00",
                "[0.618]": "530.40",
                "[0.809]": "555.20",
                "[1]": "580.00",
                "日(5)_DIFF": "2.50",
                "日(10)_DIFF": "1.80",
                "日(20)_DIFF": "0.95",
                "CDP": "575.00",
                "NH": "580.00",
                "NL": "570.00",
                "AH": "585.00",
                "AL": "565.00",
                "NOW PRICE": "580.00"
            },
            "enable_15k10ma": true,
            "enable_15k20ma": true,
            "extend_over_ratio_dont_buy": "0.03",
            "extend_time": "00:30:00",
            "final_buy": "12:00:00",
            "no_buy_after": "10:00:00",
            "over_ratio_dont_buy": "0.03",
            "success": true
        }
    ],
    "count": 31,
    "successful_count": 31,
    "date_range": {
        "start_date": "2024-01-01",
        "end_date_start": "2024-12-01",
        "end_date_end": "2024-12-31",
        "total_days": 31
    },
    "message": "成功取得股票 2330 的資料，日期區間 2024-12-01 至 2024-12-31，共 31 個日期，成功 31 個"
}
```

#### 3. API 說明
```http
GET http://localhost:5000/
```

**回應範例**:
```json
{
    "service": "股票資料匯出API",
    "version": "1.0.0",
    "endpoints": {
        "POST /api/export-stock-data": {
            "description": "匯出股票資料",
            "parameters": {
                "stock_id": "股票代碼 (字串)",
                "start_date": "起始日期 (YYYY-MM-DD)",
                "end_date_start": "結束日期開始 (YYYY-MM-DD)",
                "end_date_end": "結束日期結束 (YYYY-MM-DD)"
            }
        },
        "GET /api/health": "健康檢查",
        "GET /": "API說明"
    }
}
```

### 使用範例

#### Python 範例
```python
import requests
import json

# API 服務地址
base_url = "http://localhost:5000"

# 測試健康檢查
response = requests.get(f"{base_url}/api/health")
print("健康檢查:", response.json())

# 匯出股票資料
data = {
    "stock_id": "2330",
    "start_date": "2024-01-01",
    "end_date_start": "2024-12-01",
    "end_date_end": "2024-12-31"
}

response = requests.post(
    f"{base_url}/api/export-stock-data",
    json=data,
    headers={'Content-Type': 'application/json'}
)

result = response.json()
print("匯出結果:", json.dumps(result, ensure_ascii=False, indent=2))
```

#### JavaScript 範例
```javascript
// 測試健康檢查
fetch('http://localhost:5000/api/health')
    .then(response => response.json())
    .then(data => console.log('健康檢查:', data));

// 匯出股票資料
const data = {
    stock_id: "2330",
    start_date: "2024-01-01",
    end_date_start: "2024-12-01",
    end_date_end: "2024-12-31"
};

fetch('http://localhost:5000/api/export-stock-data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => console.log('匯出結果:', data));
```

#### cURL 範例
```bash
# 健康檢查
curl -X GET http://localhost:5000/api/health

# 匯出股票資料
curl -X POST http://localhost:5000/api/export-stock-data \
  -H "Content-Type: application/json" \
  -d '{
    "stock_id": "2330",
    "start_date": "2024-01-01",
    "end_date_start": "2024-12-01",
    "end_date_end": "2024-12-31"
  }'
```

## 資料格式說明

### 比例價格資料
- `[0]` 到 `[6]`: 斐波那契比例價格
- 基於波段最高價和最低價計算的技術分析支撐阻力位

### SMA 移動平均線資料
- `日(5)_DIFF` 到 `日(120)_DIFF`: 日線移動平均線差異
- `週(5)_DIFF` 到 `週(120)_DIFF`: 週線移動平均線差異
- `月(5)_DIFF` 到 `月(120)_DIFF`: 月線移動平均線差異

### CDP 資料
- `CDP`: 中心價格
- `NH`: 近高
- `NL`: 近低
- `AH`: 最高價
- `AL`: 最低價

## 系統需求

### 最低需求
- Windows 10 或更新版本
- 4GB RAM
- 1GB 可用磁碟空間
- 網路連線（用於 API 資料存取）

### 建議需求
- Windows 11
- 8GB RAM
- 2GB 可用磁碟空間
- 穩定的網路連線

## 故障排除

### 常見問題

1. **API 服務無法啟動**
   - 檢查端口是否被其他程式佔用
   - 確認防火牆設定
   - 檢查網路連線

2. **資料匯出失敗**
   - 確認股票代碼正確
   - 檢查日期格式是否為 YYYY-MM-DD
   - 確認日期範圍合理

3. **應用程式無法啟動**
   - 檢查系統需求
   - 確認所有必要檔案存在
   - 檢查防毒軟體設定

### 日誌查看
- 應用程式內建日誌功能
- 在「API服務」分頁可查看詳細執行日誌
- 錯誤訊息會標示為 ERROR 級別

## 技術支援

如有任何問題或建議，請聯繫：
- 電子郵件: support@example.com
- 技術文件: [GitHub Repository](https://github.com/your-repo/shioajiconsole)

## 授權條款

本軟體僅供學習和研究使用，請遵守相關法規和永豐證券 API 使用條款。

---

**注意**: 本系統僅提供技術分析工具，不構成投資建議。投資有風險，請謹慎評估。