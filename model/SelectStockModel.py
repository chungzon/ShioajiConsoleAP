import os
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta
from model.BaseModel import BaseModel

class SelectStockModel(BaseModel):
    
    
    def __init__(self, api):
        super().__init__(api)  # 繼承父類的初始化
                # 獲取當前文件的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 構建相對路徑
        resource_dir = os.path.join(current_dir, '..', 'resource')
        self.file_path = os.path.join(resource_dir, 'stock_top.xlsx')
        

    def get_top_volumn_stocks(self):
        try:
            # 從 Excel 文件中讀取數據
            stock_df = pd.read_excel(self.file_path)

            # 確認列標題是否包含 '股票代號'
            if '股票代號' in stock_df.columns:
                # 獲取前 50 筆的股票代號
                top_50_stocks = stock_df['股票代號'][:5]
                return top_50_stocks.tolist()  # 轉換為列表形式返回
            else:
                print("列標題中沒有 '股票代號'")
                return []

        except Exception as e:
            print(f"讀取文件時發生錯誤: {e}")
            return []

    def get_stock_data(self, stock_id):
        try:
            # 建立資料庫連接
            conn = self.connect_db()

            # 查詢語句
            query = f"""
            SELECT stock_id, date, high_price, low_price 
            FROM stock_data
            WHERE stock_id = '{stock_id}'
            ORDER BY date ASC
            """

            # 執行查詢並讀取數據到 DataFrame
            df = pd.read_sql(query, conn)

            # 關閉連接
            conn.close()

            return df

        except Exception as e:
            print(f"讀取資料時發生錯誤: {e}")
            return None

    def calculate_wave_extremes(self, df, stock_id):
        # 初始化波段列表
        waves = []
        wave_start_idx = 0
        is_upward = None

        for i in range(1, len(df)):
            if is_upward is None:
                is_upward = df['close_price'].iloc[i] > df['close_price'].iloc[i-1]
                continue

            current_trend = df['close_price'].iloc[i] > df['close_price'].iloc[i-1]

            # 檢查趨勢是否改變
            if current_trend != is_upward:
                wave_end_idx = i - 1
                wave_data = df.iloc[wave_start_idx:wave_end_idx + 1]
                wave_max = wave_data['close_price'].max()
                wave_min = wave_data['close_price'].min()
                waves.append({
                    'start_date': df['date'].iloc[wave_start_idx],
                    'end_date': df['date'].iloc[wave_end_idx],
                    'max_price': wave_max,
                    'min_price': wave_min
                })
                # 重置波段開始索引和趨勢
                wave_start_idx = i - 1
                is_upward = current_trend

        # 最後一個波段
        wave_data = df.iloc[wave_start_idx:]
        wave_max = wave_data['close_price'].max()
        wave_min = wave_data['close_price'].min()
        wave_618 = (wave_max - wave_min) / 2 * 0.618 + wave_min
        wave_head = (wave_max - wave_min) / 2 * 1 + wave_min
        waves.append({
            'start_date': df['date'].iloc[wave_start_idx],
            'end_date': df['date'].iloc[-1],
            'max_price': wave_max,
            'min_price': wave_min,
            '618': wave_618,
            'head': wave_head
        })
        
        latest_close_price = self.get_latest_close_price(stock_id)
        df = pd.DataFrame(waves)
        print(df)
        if latest_close_price and latest_close_price < wave_618:
            return df
        else:
            return None    

    def process_all_stocks(self, ratio):
        top_50_stocks = self.get_top_volumn_stocks()
        all_wave_extremes = []

        for stock_id in top_50_stocks:
            print(f"正在處理股票: {stock_id}")
            stock_data_df = self.get_stock_data(stock_id)
            if stock_data_df is not None and not stock_data_df.empty:
                wave_extremes_df = self.find_peaks_troughs_v34_small(stock_data_df)
                if wave_extremes_df is not None and not wave_extremes_df.empty:
                    wave_extremes_df['stock_id'] = stock_id  # 加入股票代號
                    wave_extremes_df['name'] = self.get_stock_name(stock_id)
                    recent_segment, highest_segment = self.evaluate_segment(wave_extremes_df)
                    
                    isRecent = False
                    isHigh = False
                    if float(ratio) < recent_segment['spread_ratio']:
                        if not isRecent:
                            recent_segment['wave_type'] = '最近波段'
                            all_wave_extremes.append(recent_segment)
                            highest_segment['wave_type'] = '最高波段'
                            all_wave_extremes.append(highest_segment)
                            isRecent = True
                            isHigh = True
                        
                    if float(ratio) < highest_segment['spread_ratio']:
                        if not isHigh:
                            recent_segment['wave_type'] = '最近波段'
                            all_wave_extremes.append(recent_segment)
                            highest_segment['wave_type'] = '最高波段'
                            all_wave_extremes.append(highest_segment)
                            isRecent = True
                            isHigh = True
                        
            else:
                print(f"無法獲取股票 {stock_id} 的數據")
                
        if all_wave_extremes is not None:
            return all_wave_extremes

        # 將所有波段數據合併成一個 DataFrame
        # if all_wave_extremes:
        #     recent_segment, highest_segment = self.evaluate_segment(all_wave_extremes)
        #     if recent_segment and highest_segment:
        #         result_df = pd.concat(recent_segment, ignore_index=True)
        #         result_df = pd.concat(highest_segment, ignore_index=True)
        #         return result_df
        #     else:
        #         return pd.DataFrame()
        # else:
            return pd.DataFrame()
        
    def get_recent_segment(self, segments_df):
        # 获取最近一次波段数据
        if not segments_df.empty:
            return segments_df.iloc[-1]  # 最近一次波段数据在最后一行
        else:
            return None

    def get_highest_segment(self, segments_df):
        # 获取最高点波段数据
        if not segments_df.empty:
            max_value_idx = segments_df['Max_Value'].idxmax()  # 找到最高点波段的索引
            return segments_df.iloc[max_value_idx]
        else:
            return None
        
    def evaluate_segment(self, segments_df):
        recent_segment = self.get_recent_segment(segments_df)
        highest_segment = self.get_highest_segment(segments_df)
        
        return recent_segment, highest_segment