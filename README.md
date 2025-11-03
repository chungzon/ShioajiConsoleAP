# ShioajiConsole 股票分析與資料匯出系統

## 版本資訊
- **版本**: 1.1.0 ⭐ 新版本
- **發布日期**: 2025年11月
- **支援平台**: Windows 10/11
- **Python版本**: 3.8+

### 更新內容 (v1.1.0)
- ✅ **新增 SQL 查詢版 API** (`/api/export-stock-data-use-sql`)
  - 使用 SQL 直接查詢總波段，效能更優
  - 獨立實現，不影響原有程式碼
  - 支援完整的技術指標計算（CDP、均線、扣抵值）
- ✅ 優化資料處理流程
- ✅ 增強錯誤處理機制

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

**說明**: 此端點使用 Python 波段計算方法（`find_peaks_troughs_v34_small`）來分析總波段。

#### 3. 股票資料匯出（使用 SQL 查詢）⭐ 新功能
```http
POST http://localhost:5000/api/export-stock-data-use-sql
Content-Type: application/json
```

**請求參數**:
```json
{
    "stock_id": "2467",
    "start_date": "2020-01-01",
    "end_date_start": "2025-10-15",
    "end_date_end": "2025-10-17"
}
```

**參數說明**:
- `stock_id`: 股票代碼（字串）
- `start_date`: 起始日期（YYYY-MM-DD 格式）
- `end_date_start`: 結束日期開始（YYYY-MM-DD 格式）
- `end_date_end`: 結束日期結束（YYYY-MM-DD 格式）

**功能特色**:
- ✅ 使用 SQL 查詢直接從資料庫查找總波段最高價和最低價
- ✅ 完全獨立實現，不依賴波段計算方法
- ✅ 直接計算 CDP、均線和扣抵值
- ✅ 效能更優，計算速度更快
- ✅ 不影響原有程式碼邏輯

**SQL 查詢邏輯**:
```sql
-- 查找期間內的最高價及其日期
-- 以及最高價之後的最低價及其日期
WITH PeriodData AS (
    SELECT *
    FROM stock_data
    WHERE stock_id = '2467'
    AND date BETWEEN '2020-01-01' AND '2025-10-17'
),
MaxHigh AS (
    SELECT TOP 1 date AS max_high_date, high_price AS max_high
    FROM PeriodData
    ORDER BY high_price DESC, date ASC
)
SELECT
    P1.max_high,
    P1.max_high_date,
    P2.date AS min_low_date_after_high,
    P2.low_price AS min_low_after_high
FROM MaxHigh P1
CROSS APPLY (
    SELECT TOP 1 low_price, date
    FROM PeriodData
    WHERE date > P1.max_high_date
    ORDER BY low_price ASC, date ASC
) P2
```

**與標準版的差異**:
| 項目 | 標準版 (`/api/export-stock-data`) | SQL版 (`/api/export-stock-data-use-sql`) |
|------|-----------------------------------|-------------------------------------------|
| 總波段查找 | Python 波段計算 | SQL 直接查詢 |
| CDP 計算 | 透過波段計算獲取 | 直接使用最後一天數據計算 |
| 均線計算 | 透過波段計算獲取 | 直接調用計算方法 |
| 效能 | 需完整波段分析 | 僅需 SQL 查詢 + 直接計算 |
| 程式碼獨立性 | 與波段計算耦合 | 完全獨立 |

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

#### 4. API 說明
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
        "POST /api/export-stock-data-use-sql": {
            "description": "匯出股票資料（使用SQL查詢總波段）",
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

**標準版 API**:
```python
import requests
import json

# API 服務地址
base_url = "http://localhost:5000"

# 測試健康檢查
response = requests.get(f"{base_url}/api/health")
print("健康檢查:", response.json())

# 匯出股票資料（標準版）
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

**SQL 版 API** ⭐ 推薦使用:
```python
import requests
import json

# API 服務地址
base_url = "http://localhost:5000"

# 匯出股票資料（SQL版 - 效能更佳）
data = {
    "stock_id": "2467",
    "start_date": "2020-01-01",
    "end_date_start": "2025-10-15",
    "end_date_end": "2025-10-17"
}

response = requests.post(
    f"{base_url}/api/export-stock-data-use-sql",
    json=data,
    headers={'Content-Type': 'application/json'},
    timeout=60  # SQL版通常更快，但建議設定timeout
)

if response.status_code == 200:
    result = response.json()
    print(f"成功: {result['successful_count']}/{result['count']} 個日期")
    print("資料:", json.dumps(result['data'][:2], ensure_ascii=False, indent=2))  # 顯示前2筆
else:
    print("錯誤:", response.text)
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

# 匯出股票資料（標準版）
curl -X POST http://localhost:5000/api/export-stock-data \
  -H "Content-Type: application/json" \
  -d '{
    "stock_id": "2330",
    "start_date": "2024-01-01",
    "end_date_start": "2024-12-01",
    "end_date_end": "2024-12-31"
  }'

# 匯出股票資料（SQL版）⭐ 推薦
curl -X POST http://localhost:5000/api/export-stock-data-use-sql \
  -H "Content-Type: application/json" \
  -d '{
    "stock_id": "2467",
    "start_date": "2020-01-01",
    "end_date_start": "2025-10-15",
    "end_date_end": "2025-10-17"
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

## API 選擇建議

### 何時使用 SQL 版 API (`/api/export-stock-data-use-sql`) ⭐ 推薦

**建議使用情境**:
- ✅ 需要快速查詢總波段資料
- ✅ 處理大量日期範圍的資料
- ✅ 僅需要總波段的最高價和最低價
- ✅ 追求更好的效能表現
- ✅ 獨立系統整合，不依賴波段分析邏輯

**優點**:
- 🚀 效能優異：直接 SQL 查詢，無需完整波段計算
- 🔒 程式碼獨立：不影響原有波段分析邏輯
- 💡 簡單高效：計算流程更直接清晰
- ⚡ 快速回應：適合大量資料處理

### 何時使用標準版 API (`/api/export-stock-data`)

**建議使用情境**:
- 需要完整的波段分析資訊
- 依賴現有的波段計算邏輯
- 需要與現有系統保持一致性

**優點**:
- 📊 完整波段分析：提供詳細的波段計算結果
- 🔄 邏輯一致：與現有系統計算方式相同
- 📈 波段資訊豐富：包含所有波段的詳細資料

### 效能比較

| 比較項目 | 標準版 | SQL版 ⭐ |
|---------|--------|----------|
| 查詢速度 | 較慢 | 快速 |
| 記憶體使用 | 較高 | 較低 |
| 適用場景 | 完整分析 | 快速查詢 |
| 資料量限制 | 中小型 | 大型可 |
| 維護性 | 與主系統耦合 | 獨立維護 |

### 推薦方案

對於大多數使用場景，我們**強烈推薦使用 SQL 版 API** (`/api/export-stock-data-use-sql`)，因為它提供：
- ⚡ 更快的回應速度
- 🎯 更精確的總波段查詢
- 🔧 更簡單的維護方式
- 🛡️ 更好的程式碼獨立性

## 技術支援

如有任何問題或建議，請聯繫：
- 電子郵件: support@example.com
- 技術文件: [GitHub Repository](https://github.com/your-repo/shioajiconsole)

## 授權條款

本軟體僅供學習和研究使用，請遵守相關法規和永豐證券 API 使用條款。

---

**注意**: 本系統僅提供技術分析工具，不構成投資建議。投資有風險，請謹慎評估。