# import pandas as pd
# import numpy as np
# import os
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import classification_report, accuracy_score
# from sklearn.utils import class_weight
# from keras.models import Sequential, load_model
# from keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D, Flatten
# from keras.callbacks import ModelCheckpoint, EarlyStopping

# # Dowload_path
# USER_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

# # 讀取資料
# df = pd.read_excel(os.path.join(USER_DOWNLOAD_PATH, 'STOCK_DAY_2402_202501-v2.xlsx'), engine='openpyxl')
# df['日期'] = pd.to_datetime(df['日期'].apply(lambda x: f"{int(x.split('/')[0]) + 1911}/{x.split('/')[1]}/{x.split('/')[2]}"), format='%Y/%m/%d', errors='coerce')
# for col in ['成交股數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌價差', '成交筆數']:
#     df[col] = df[col].astype(str).str.replace(',', '').astype(float)

# # 技術指標
# df['MA5'] = df['收盤價'].rolling(window=5).mean()
# df['MA10'] = df['收盤價'].rolling(window=10).mean()
# exp1 = df['收盤價'].ewm(span=12, adjust=False).mean()
# exp2 = df['收盤價'].ewm(span=26, adjust=False).mean()
# df['MACD'] = exp1 - exp2
# df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
# df['MACD_hist'] = df['MACD'] - df['MACD_signal']
# up = df['收盤價'].diff().clip(lower=0)
# down = -df['收盤價'].diff().clip(upper=0)
# rs = up.rolling(window=14).mean() / down.rolling(window=14).mean()
# df['RSI'] = 100 - (100 / (1 + rs))
# df['middle_band'] = df['收盤價'].rolling(window=20).mean()
# df['std'] = df['收盤價'].rolling(window=20).std()
# df['upper_band'] = df['middle_band'] + 2 * df['std']
# df['lower_band'] = df['middle_band'] - 2 * df['std']
# df['OBV'] = (np.sign(df['收盤價'].diff()) * df['成交股數']).fillna(0).cumsum()
# df['H-L'] = df['最高價'] - df['最低價']
# df['H-C'] = np.abs(df['最高價'] - df['收盤價'].shift())
# df['L-C'] = np.abs(df['最低價'] - df['收盤價'].shift())
# df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
# df['ATR'] = df['TR'].rolling(window=14).mean()
# df.drop(['std', 'H-L', 'H-C', 'L-C', 'TR'], axis=1, inplace=True)

# # 二分類標籤：0=下跌或盤整（<=1%），1=上漲（>1%）
# df['Future_Price'] = df['收盤價'].shift(-5)
# df['return'] = (df['Future_Price'] - df['收盤價']) / df['收盤價']
# df['Label'] = df['return'].apply(lambda r: 1 if r > 0.01 else 0)
# df.dropna(inplace=True)

# # 特徵與標準化
# features = ['MA5', 'MA10', 'MACD', 'MACD_signal', 'MACD_hist', 'RSI',
#             'middle_band', 'upper_band', 'lower_band', 'OBV', 'ATR']
# X = df[features]
# y = df['Label']
# scaler = MinMaxScaler()
# X_scaled = scaler.fit_transform(X)

# # 時序資料轉換
# def create_dataset(X, y, time_steps=10):
#     Xs, ys = [], []
#     for i in range(len(X) - time_steps):
#         Xs.append(X[i:i + time_steps])
#         ys.append(y[i + time_steps])
#     return np.array(Xs), np.array(ys)

# X_seq, y_seq = create_dataset(X_scaled, y.values)
# train_size = int(len(X_seq) * 0.7)
# X_train, X_test = X_seq[:train_size], X_seq[train_size:]
# y_train, y_test = y_seq[:train_size], y_seq[train_size:]

# # 類別權重
# weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
# class_weights = dict(enumerate(weights))

# # 建立 CNN-LSTM 模型
# model_path = os.path.join(USER_DOWNLOAD_PATH, 'cnn_lstm_stock_binary.h5')
# if os.path.exists(model_path):
#     print('🔁 載入已訓練模型...')
#     model = load_model(model_path)
# else:
#     print('🧠 訓練 CNN-LSTM 二分類模型...')
#     model = Sequential()
#     model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2])))
#     model.add(MaxPooling1D(pool_size=2))
#     model.add(LSTM(64, return_sequences=False))
#     model.add(Dropout(0.3))
#     model.add(Dense(64, activation='relu'))
#     model.add(Dense(1, activation='sigmoid'))
#     model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

#     early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
#     checkpoint = ModelCheckpoint(model_path, save_best_only=True, monitor='val_accuracy', mode='max')

#     history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2,
#                         class_weight=class_weights, callbacks=[checkpoint, early_stop], verbose=0)

#     # 可視化學習曲線
#     plt.plot(history.history['accuracy'], label='Train Accuracy')
#     plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
#     plt.title('Model Accuracy')
#     plt.xlabel('Epoch')
#     plt.ylabel('Accuracy')
#     plt.legend()
#     plt.grid(True)
#     plt.show()

# # 預測與報告
# y_pred_probs = model.predict(X_test)
# y_pred_labels = (y_pred_probs > 0.5).astype(int)
# print('準確度 (Accuracy):', accuracy_score(y_test, y_pred_labels))
# print('分類報告 (Classification Report):\n', classification_report(y_test, y_pred_labels))

# # 預測未來
# latest_input = X_scaled[-10:]
# latest_input = np.expand_dims(latest_input, axis=0)
# future_prob = model.predict(latest_input)[0][0]
# print(f'未來5日內「上漲」的機率：{future_prob*100:.2f}%')
# print(f'未來5日內「下跌或盤整」的機率：{(1-future_prob)*100:.2f}%')

# 利用永豐金API，抓取股票資料

import shioaji as sj

def get_api():
    api = sj.Shioaji(simulation=True)
    api.login(
            api_key="CV7uuCJ7pB7x2i4T7783dBwiP7NwqhgwNj96J9uPd7PK",
            secret_key="HvDpMQ84VfgsGqBPN4nqfPV1iY9XsoWHst4rd4UimHaf"
        )
    return api

api = get_api()

def get_stock_data(stock_id, start_date, end_date):
    stock = api.Contracts.Stocks[stock_id]
    kbars = api.kbars(
        contract=stock,
        start=start_date,
        end=end_date
    )
    return kbars

stock_id = "2330"
start_date = "2024-01-01"
end_date = "2024-01-05"
kbars = get_stock_data(stock_id, start_date, end_date)
print(kbars)






