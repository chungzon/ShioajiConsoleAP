import os
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta
from model.BaseModel import BaseModel
from common.Math import Math

class SelectStockModel(BaseModel):
    
    
    def __init__(self, api):
        super().__init__(api)  # 繼承父類的初始化
                # 獲取當前文件的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 構建相對路徑
        resource_dir = os.path.join(current_dir, '..', 'resource')
        self.file_path = os.path.join(resource_dir, 'stock_top.xlsx')
        

    def get_top_volumn_stocks(self, top_n):
        try:
            # 從 Excel 文件中讀取數據
            stock_df = pd.read_excel(self.file_path)

            # 確認列標題是否包含 '股票代號'
            if '股票代號' in stock_df.columns:
                top_n = int(top_n)  # 确保 top_n 是整数
                available_stocks = len(stock_df['股票代號'])
                if available_stocks < top_n:
                    return f"錯誤：只有 {available_stocks} 筆資料可用，少於要求的 {top_n} 筆"
                else:
                    top_stocks = stock_df['股票代號'][:top_n]
                    return top_stocks.tolist()
            else:
                print("列標題中沒有 '股票代號'")
                return []

        except Exception as e:
            print(f"讀取文件時發生錯誤: {e}")
            return []

    def get_stock_data(self, stock_id, start_date, end_date):
        try:
            # 建立資料庫連接
            conn = self.connect_db()

            # 查詢語句
            query = f"""
            SELECT stock_id, date, high_price, low_price 
            FROM stock_data
            WHERE stock_id = '{stock_id}'
            AND date >= '{start_date}'
            AND date <= '{end_date}'
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

    def process_all_stocks(self, start_date, end_date, ratio, ratio2, top_n, recent_wave_var, highest_wave_var, total_wave_var):
        top_50_stocks = self.get_top_volumn_stocks(top_n)
        if isinstance(top_50_stocks, str) and top_50_stocks.startswith("錯誤："):
            return top_50_stocks
        else:
            # 處理正常的结果
            all_wave_extremes = []

            for stock_id in top_50_stocks:
                print(f"正在處理股票: {stock_id}")
                stock_data_df = self.get_stock_data(stock_id, start_date, end_date)
                if stock_data_df is not None and not stock_data_df.empty:
                    latest_close_price = self.get_latest_close_price(stock_id)
                    wave_extremes_df = self.find_peaks_troughs_v34_small(stock_data_df, latest_close_price)
                    if wave_extremes_df is not None and not wave_extremes_df.empty:
                        wave_extremes_df['stock_id'] = stock_id  # 加入股票代號
                        wave_extremes_df['name'] = self.get_stock_name(stock_id)
                        recent_segment, highest_segment = self.evaluate_segment(wave_extremes_df)
                        max_value_of_all_waves = wave_extremes_df['Max_Value'].max()
                        max_value_index = wave_extremes_df['Max_Value'].idxmax()

                        # 獲取最高價的日期
                        max_value_date = wave_extremes_df.loc[max_value_index, 'Max_Date']
                           # 在最高價之後找最低價
                        min_after_max_series = wave_extremes_df.loc[max_value_index:, 'Min_Value']
                        min_value_after_max = min_after_max_series.min()
                        min_after_max_index = min_after_max_series.idxmin()

                        # 獲取最低價的日期
                        min_value_date = wave_extremes_df.loc[min_after_max_index, 'Min_Date']

                        # 計算 ratio_0.618 和 ratio_1
                        ratio_0618 = Math.calculate_ratio_0618(max_value_of_all_waves, min_value_after_max)
                        ratio_1 = Math.calculate_ratio_1(max_value_of_all_waves, min_value_after_max)

                        # 計算 Head-0.618 價差比例
                        head_0618_spread_ratio = round((max_value_of_all_waves - ratio_0618) / ratio_0618, 3)

                        # 計算現價-0.618 價差比例
                        current_0618_spread_ratio = round((latest_close_price - ratio_0618) / latest_close_price, 3)

                        segment = {
                            'stock_id': stock_id,
                            'name': '',
                            'latest_close_price': latest_close_price,
                            'wave_type': [None],
                            'Max_Date': max_value_date,
                            'Min_Date': min_value_date,
                            'Max_Value': max_value_of_all_waves,
                            'Min_Value': min_value_after_max,
                            'Ratio_0.618': ratio_0618,
                            'Ratio_1': ratio_1,
                            'spread_ratio': head_0618_spread_ratio,
                            'latest_close_price-0.618_ratio': current_0618_spread_ratio,
                            'max_value_of_all_waves': max_value_of_all_waves,
                            'min_value_after_max': min_value_after_max,
                            'wave_type': ''
                        }

                        isRecent = False
                        isHigh = False
                        isSummary = False

                        if (float(ratio) < recent_segment['spread_ratio'] or float(ratio) * -1 > recent_segment['spread_ratio']) \
                            and not isRecent:
                            if (float(ratio2) == 0) \
                                or ((float(ratio2) != 0 and recent_wave_var) \
                                    and (float(ratio2) >= recent_segment['latest_close_price-0.618_ratio'] \
                                        and float(ratio2) * -1 <= recent_segment['latest_close_price-0.618_ratio'])):
                                recent_segment['wave_type'] = '最近波段'
                                recent_segment['max_value_of_all_waves'] = max_value_of_all_waves
                                recent_segment['min_value_after_max'] = min_value_after_max
                                all_wave_extremes.append(recent_segment)
                                highest_segment['wave_type'] = '最高波段'
                                highest_segment['max_value_of_all_waves'] = max_value_of_all_waves
                                highest_segment['min_value_after_max'] = min_value_after_max
                                all_wave_extremes.append(highest_segment)
                                all_wave_extremes.append(segment)
                                isRecent = True
                                isHigh = True
                                isSummary = True

                        if (float(ratio) < highest_segment['spread_ratio'] or float(ratio) * -1 > highest_segment['spread_ratio']) \
                            and not isHigh:
                            if (float(ratio2) == 0) \
                                or ((float(ratio2) != 0 and highest_wave_var) \
                                    and (float(ratio2) >= highest_segment['latest_close_price-0.618_ratio'] \
                                        and float(ratio2) * -1 <= highest_segment['latest_close_price-0.618_ratio'])):
                                recent_segment['wave_type'] = '最近波段'
                                recent_segment['max_value_of_all_waves'] = max_value_of_all_waves
                                recent_segment['min_value_after_max'] = min_value_after_max
                                all_wave_extremes.append(recent_segment)
                                highest_segment['wave_type'] = '最高波段'
                                highest_segment['max_value_of_all_waves'] = max_value_of_all_waves
                                highest_segment['min_value_after_max'] = min_value_after_max
                                all_wave_extremes.append(highest_segment)
                                all_wave_extremes.append(segment)
                                isRecent = True
                                isHigh = True
                                isSummary = True

                        if (float(ratio) < head_0618_spread_ratio or float(ratio) * -1 > head_0618_spread_ratio) \
                            and not isSummary:
                            if (float(ratio2) == 0) \
                                or ((float(ratio2) != 0 and total_wave_var) \
                                    and (float(ratio2) >= current_0618_spread_ratio \
                                        and float(ratio2) * -1 <= current_0618_spread_ratio)):
                                recent_segment['wave_type'] = '最近波段'
                                recent_segment['max_value_of_all_waves'] = max_value_of_all_waves
                                recent_segment['min_value_after_max'] = min_value_after_max
                                all_wave_extremes.append(recent_segment)
                                highest_segment['wave_type'] = '最高波段'
                                highest_segment['max_value_of_all_waves'] = max_value_of_all_waves
                                highest_segment['min_value_after_max'] = min_value_after_max
                                all_wave_extremes.append(highest_segment)
                                all_wave_extremes.append(segment)
                                isRecent = True
                                isHigh = True
                                isSummary = True
              
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
    
    