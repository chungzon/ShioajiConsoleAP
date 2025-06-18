import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Dowload_path
USER_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
# 模型檔案名稱
MODEL_FILE_NAME = 'trained_stock_model.pkl'

# 讀取資料
df = pd.read_excel(os.path.join(USER_DOWNLOAD_PATH, 'STOCK_DAY_2402_202501-v2.xlsx'), engine='openpyxl')

# 日期轉換
df['日期'] = pd.to_datetime(
    df['日期'].apply(lambda x: f"{int(x.split('/')[0]) + 1911}/{x.split('/')[1]}/{x.split('/')[2]}"),
    format='%Y/%m/%d',
    errors='coerce'
)

# 數值處理
for col in ['成交股數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌價差', '成交筆數']:
    df[col] = df[col].astype(str).str.replace(',', '').astype(float)

df.sort_values(by='日期', inplace=True)
df.reset_index(drop=True, inplace=True)

# 計算技術指標
for window in [5, 10]:
    df[f'MA{window}'] = df['收盤價'].rolling(window=window).mean()

exp1 = df['收盤價'].ewm(span=12, adjust=False).mean()
exp2 = df['收盤價'].ewm(span=26, adjust=False).mean()
df['MACD'] = exp1 - exp2
df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
df['MACD_hist'] = df['MACD'] - df['MACD_signal']

up = df['收盤價'].diff().clip(lower=0)
down = -df['收盤價'].diff().clip(upper=0)
rs = up.rolling(window=14).mean() / down.rolling(window=14).mean()
df['RSI'] = 100 - (100 / (1 + rs))

df['middle_band'] = df['收盤價'].rolling(window=20).mean()
df['std'] = df['收盤價'].rolling(window=20).std()
df['upper_band'] = df['middle_band'] + (df['std'] * 2)
df['lower_band'] = df['middle_band'] - (df['std'] * 2)

df['OBV'] = (np.sign(df['收盤價'].diff()) * df['成交股數']).fillna(0).cumsum()

df['H-L'] = df['最高價'] - df['最低價']
df['H-C'] = np.abs(df['最高價'] - df['收盤價'].shift())
df['L-C'] = np.abs(df['最低價'] - df['收盤價'].shift())
df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
df['ATR'] = df['TR'].rolling(window=14).mean()
df.drop(['std', 'H-L', 'H-C', 'L-C', 'TR'], axis=1, inplace=True)

# 建立預測標籤
df['Future_Price'] = df['收盤價'].shift(-5)
df.dropna(inplace=True)
df['Trend'] = (df['Future_Price'] > df['收盤價']).astype(int)

# 特徵與標籤
features = ['MA5', 'MA10', 'MACD', 'MACD_signal', 'MACD_hist', 'RSI',
            'middle_band', 'upper_band', 'lower_band', 'OBV', 'ATR']
X = df[features]
y = df['Trend']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

# 模型載入或訓練
if os.path.exists(os.path.join(USER_DOWNLOAD_PATH, MODEL_FILE_NAME)):
    print('🔁 載入已訓練模型...')
    model = joblib.load(os.path.join(USER_DOWNLOAD_PATH, MODEL_FILE_NAME))
else:
    print('🧠 訓練新模型...')
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, os.path.join(USER_DOWNLOAD_PATH, MODEL_FILE_NAME))

# 模型預測與評估
y_pred = model.predict(X_test)
print('準確度 (Accuracy):', accuracy_score(y_test, y_pred))
print('分類報告 (Classification Report):\n', classification_report(y_test, y_pred, target_names=['下跌或持平', '上漲']))

# 預測未來機率
latest_data = X.iloc[-1:].values
prob = model.predict_proba(latest_data)[0]
print(f'下週預測上漲機率：{prob[1]*100:.2f}%')
print(f'下週預測下跌或持平機率：{prob[0]*100:.2f}%')
