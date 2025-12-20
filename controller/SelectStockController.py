from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import pandas as pd
from Event import EventBus, Event
class SelectStockController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self
        self.event_bus = EventBus()
        self.event_bus.subscribe("save_kbars_data", self.view.save_kbars_data)

    def calculate(self, start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections, ratio_all_vars, ratio_type_vars):
        # all_wave_extremes = self.model.process_all_stocks(ratio, ratio2, top_n)
        self.model.process_all_stocks(start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections, ratio_all_vars, ratio_type_vars)
        # if isinstance(result, str) and result.startswith("錯誤："):
        #     self.view.show_error(result)
        # else:
        #     # 處理正常的结果
        #     return result
        
    def download_detail_data(self, stock_id, start_date, end_date, file_path):
        self.model.analyze_data(stock_id, start_date, end_date, file_path)

    def show_detail_data(self, stock_id, stock_name):
        recent_segment, total_segment = self.model.get_stock_data_from_all_wave_extremes(stock_id)
        if total_segment is None:
            print(f"沒有找到股票 {stock_id} 的數據")
            return

        # 整理均線數據（使用最近波段數據）
        organized_ma_data = {
            "日均線": {
                "5MA": recent_segment.get('sma_5', 'N/A'),
                "10MA": recent_segment.get('sma_10', 'N/A'),
                "20MA": recent_segment.get('sma_20', 'N/A'),
                "60MA": recent_segment.get('sma_60', 'N/A'),
                "120MA": recent_segment.get('sma_120', 'N/A'),
                "5MA_DIFF": recent_segment.get('sma_5_diff', 'N/A'),
                "10MA_DIFF": recent_segment.get('sma_10_diff', 'N/A'),
                "20MA_DIFF": recent_segment.get('sma_20_diff', 'N/A'),
                "60MA_DIFF": recent_segment.get('sma_60_diff', 'N/A'),
                "120MA_DIFF": recent_segment.get('sma_120_diff', 'N/A')
            },
            "週均線": {
                "5MA": recent_segment.get('weekly_sma_5', 'N/A'),
                "10MA": recent_segment.get('weekly_sma_10', 'N/A'),
                "20MA": recent_segment.get('weekly_sma_20', 'N/A'),
                "60MA": recent_segment.get('weekly_sma_60', 'N/A'),
                "120MA": recent_segment.get('weekly_sma_120', 'N/A'),
                "5MA_DIFF": recent_segment.get('weekly_sma_5_diff', 'N/A'),
                "10MA_DIFF": recent_segment.get('weekly_sma_10_diff', 'N/A'),
                "20MA_DIFF": recent_segment.get('weekly_sma_20_diff', 'N/A'),
                "60MA_DIFF": recent_segment.get('weekly_sma_60_diff', 'N/A'),
                "120MA_DIFF": recent_segment.get('weekly_sma_120_diff', 'N/A')
            },
            "月均線": {
                "5MA": recent_segment.get('monthly_sma_5', 'N/A'),
                "10MA": recent_segment.get('monthly_sma_10', 'N/A'),
                "20MA": recent_segment.get('monthly_sma_20', 'N/A'),
                "60MA": recent_segment.get('monthly_sma_60', 'N/A'),
                "120MA": recent_segment.get('monthly_sma_120', 'N/A'),
                "5MA_DIFF": recent_segment.get('monthly_sma_5_diff', 'N/A'),
                "10MA_DIFF": recent_segment.get('monthly_sma_10_diff', 'N/A'),
                "20MA_DIFF": recent_segment.get('monthly_sma_20_diff', 'N/A'),
                "60MA_DIFF": recent_segment.get('monthly_sma_60_diff', 'N/A'),
                "120MA_DIFF": recent_segment.get('monthly_sma_120_diff', 'N/A')
            },
            "15分鐘均線": {
                "5MA": recent_segment.get('15min_sma_5', 'N/A'),
                "10MA": recent_segment.get('15min_sma_10', 'N/A'),
                "20MA": recent_segment.get('15min_sma_20', 'N/A'),
                "60MA": recent_segment.get('15min_sma_60', 'N/A'),
                "120MA": recent_segment.get('15min_sma_120', 'N/A'),
                "10MA_DIFF": recent_segment.get('15min_sma_10_diff', 'N/A'),
                "20MA_DIFF": recent_segment.get('15min_sma_20_diff', 'N/A'),
                "60_diff": recent_segment.get('15min_sma_60_diff', 'N/A')
            },
            "latest_close_price": total_segment.get('latest_close_price', 'N/A')
        }

        # 最近波段比例價格0.191~3
        recent_ratio_prices = {
            '0': recent_segment.get('Ratio_0', 'N/A'),
            '0.191': recent_segment.get('Ratio_0.191', 'N/A'),
            '0.382': recent_segment.get('Ratio_0.382', 'N/A'),
            '0.5': recent_segment.get('Ratio_0.5', 'N/A'),
            '0.618': recent_segment.get('Ratio_0.618', 'N/A'),
            '0.809': recent_segment.get('Ratio_0.809', 'N/A'),
            '1': recent_segment.get('Ratio_1', 'N/A'),
            '1.191': recent_segment.get('Ratio_1.191', 'N/A'),
            '1.382': recent_segment.get('Ratio_1.382', 'N/A'),
            '1.5': recent_segment.get('Ratio_1.5', 'N/A'),
            '1.618': recent_segment.get('Ratio_1.618', 'N/A'),
            '1.809': recent_segment.get('Ratio_1.809', 'N/A'),
            '2': recent_segment.get('Ratio_2', 'N/A'),
            '2.191': recent_segment.get('Ratio_2.191', 'N/A'),
            '2.382': recent_segment.get('Ratio_2.382', 'N/A'),
            '2.5': recent_segment.get('Ratio_2.5', 'N/A'),
            '2.618': recent_segment.get('Ratio_2.618', 'N/A'),
            '2.809': recent_segment.get('Ratio_2.809', 'N/A'),
            '3': recent_segment.get('Ratio_3', 'N/A'),
            '3.191': recent_segment.get('Ratio_3.191', 'N/A'),
            '3.382': recent_segment.get('Ratio_3.382', 'N/A'),
            '3.5': recent_segment.get('Ratio_3.5', 'N/A'),
            '3.618': recent_segment.get('Ratio_3.618', 'N/A'),
            '3.809': recent_segment.get('Ratio_3.809', 'N/A'),
            '4': recent_segment.get('Ratio_4', 'N/A'),
            '4.191': recent_segment.get('Ratio_4.191', 'N/A'),
            '4.382': recent_segment.get('Ratio_4.382', 'N/A'),
            '4.5': recent_segment.get('Ratio_4.5', 'N/A'),
            '4.618': recent_segment.get('Ratio_4.618', 'N/A'),
            '4.809': recent_segment.get('Ratio_4.809', 'N/A'),
            '5': recent_segment.get('Ratio_5', 'N/A'),
            '5.191': recent_segment.get('Ratio_5.191', 'N/A'),
            '5.382': recent_segment.get('Ratio_5.382', 'N/A'),
            '5.5': recent_segment.get('Ratio_5.5', 'N/A'),
            '5.618': recent_segment.get('Ratio_5.618', 'N/A'),
            '5.809': recent_segment.get('Ratio_5.809', 'N/A'),
            '6': recent_segment.get('Ratio_6', 'N/A')
        }

        # 整理比例價格數據（包括最近波段和總波段）
        ratio_prices = {
            '0': total_segment.get('Ratio_0', 'N/A'),
            '0.191': total_segment.get('Ratio_0.191', 'N/A'),
            '0.382': total_segment.get('Ratio_0.382', 'N/A'),
            '0.5': total_segment.get('Ratio_0.5', 'N/A'),
            '0.618': total_segment.get('Ratio_0.618', 'N/A'),
            '0.809': total_segment.get('Ratio_0.809', 'N/A'),
            '1': total_segment.get('Ratio_1', 'N/A'),
            '1.191': total_segment.get('Ratio_1.191', 'N/A'),
            '1.382': total_segment.get('Ratio_1.382', 'N/A'),
            '1.5': total_segment.get('Ratio_1.5', 'N/A'),
            '1.618': total_segment.get('Ratio_1.618', 'N/A'),
            '1.809': total_segment.get('Ratio_1.809', 'N/A'),
            '2': total_segment.get('Ratio_2', 'N/A'),
            '2.191': total_segment.get('Ratio_2.191', 'N/A'),
            '2.382': total_segment.get('Ratio_2.382', 'N/A'),
            '2.5': total_segment.get('Ratio_2.5', 'N/A'),
            '2.618': total_segment.get('Ratio_2.618', 'N/A'),
            '2.809': total_segment.get('Ratio_2.809', 'N/A'),
            '3': total_segment.get('Ratio_3', 'N/A'),
            '3.191': total_segment.get('Ratio_3.191', 'N/A'),
            '3.382': total_segment.get('Ratio_3.382', 'N/A'),
            '3.5': total_segment.get('Ratio_3.5', 'N/A'),
            '3.618': total_segment.get('Ratio_3.618', 'N/A'),
            '3.809': total_segment.get('Ratio_3.809', 'N/A'),
            '4': total_segment.get('Ratio_4', 'N/A'),
            '4.191': total_segment.get('Ratio_4.191', 'N/A'),
            '4.382': total_segment.get('Ratio_4.382', 'N/A'),
            '4.5': total_segment.get('Ratio_4.5', 'N/A'),
            '4.618': total_segment.get('Ratio_4.618', 'N/A'),
            '4.809': total_segment.get('Ratio_4.809', 'N/A'),
            '5': total_segment.get('Ratio_5', 'N/A'),
            '5.191': total_segment.get('Ratio_5.191', 'N/A'),
            '5.382': total_segment.get('Ratio_5.382', 'N/A'),
            '5.5': total_segment.get('Ratio_5.5', 'N/A'),
            '5.618': total_segment.get('Ratio_5.618', 'N/A'),
            '5.809': total_segment.get('Ratio_5.809', 'N/A'),
            '6': total_segment.get('Ratio_6', 'N/A')
        }

        # 添加其他可能需要的數據（使用總波段數據）
        additional_data = {
            '最高價': total_segment.get('Max_Value', 'N/A'),
            '最低價': total_segment.get('Min_Value', 'N/A'),
            '最新收盤價': total_segment.get('latest_close_price', 'N/A'),
            '價差比例': total_segment.get('spread_ratio', 'N/A'),
            '最新收盤價-0.191比例': total_segment.get('latest_close_price-0.191_ratio', 'N/A'),
            'latest_close_prices': total_segment.get('latest_close_prices', 'N/A'),
            'latest_dates': total_segment.get('latest_dates', 'N/A'),
            '最近波段最高價日期': recent_segment.get('Max_Date', 'N/A'),
            '最近波段最低價日期': recent_segment.get('Min_Date', 'N/A'),
            '總波段最高價日期': total_segment.get('Max_Date', 'N/A'),
            '總波段最低價日期': total_segment.get('Min_Date', 'N/A'),
        }

        # 從 total_segment 獲取所有指標價格
        indicator_prices = {
            'CDP': total_segment.get('CDP', 'N/A'),
            'NH': total_segment.get('NH', 'N/A'),
            'NL': total_segment.get('NL', 'N/A'),
            'AH': total_segment.get('AH', 'N/A'),
            'AL': total_segment.get('AL', 'N/A')
        }

        gap_df = total_segment.get('gap_df', 'N/A')
        now_price = total_segment.get('now_price', 'N/A')
        next_open_price = total_segment.get('next_open_price', 'N/A')
        latest_close_price_by_date = total_segment.get('latest_close_price_by_date', 'N/A')
        short_wave_peak = total_segment.get('short_wave_peak', 'N/A')
        self.view.show_sma_data(stock_id, stock_name, organized_ma_data, recent_ratio_prices, additional_data, indicator_prices, ratio_prices, gap_df, now_price, latest_close_price_by_date, next_open_price, short_wave_peak)
        
    def export_1min_data(self, stock_id, stock_name, end_date):
        # 獲取1分K資料
        df = self.model.get_stock_data_from_db(stock_id, end_date, end_date)
        df['ts'] = pd.to_datetime(df['ts'])
        df = df.set_index('ts')
        # 將資料整理為"序號(流水號),開盤價,最高價,最低價,收盤價,時間"
        df['序號'] = range(1, len(df) + 1)
        df = df.reset_index()
        df = df.rename(columns={'ts': '時間'})  
        df = df[['序號', 'Open_Price', 'High', 'Low', 'Close_Price', '時間']]
        self.event_bus.publish(Event("save_kbars_data", {"df": df, "stock_id": stock_id, "end_date": end_date, "kbar_type": "1_mins"}))

    def export_3min_data(self, stock_id, stock_name, end_date):
        df = self.model.get_stock_data_from_db(stock_id, end_date, end_date)
        # 重採樣，從0900開始每15分鐘
        df['ts'] = pd.to_datetime(df['ts'])
        df = df.set_index('ts')
        start_time = pd.Timestamp(end_date).replace(hour=9, minute=3)
        df_3k = df.resample('3T', origin=start_time, closed='right', label='right').agg({
            'Open_Price': 'first',
            'High': 'max',
            'Low': 'min',
            'Close_Price': 'last',
            'Volume': 'sum'
        })
        
        # 重置索引並重命名時間列
        df_3k = df_3k.reset_index()
        df_3k = df_3k.rename(columns={'ts': '時間'})
        
        # 將資料整理為"序號(流水號),開盤價,最高價,最低價,收盤價,時間"
        df_3k['序號'] = range(1, len(df_3k) + 1)
        df_3k = df_3k[['序號', 'Open_Price', 'High', 'Low', 'Close_Price', '時間']]
        self.event_bus.publish(Event("save_kbars_data", {"df": df_3k, "stock_id": stock_id, "end_date": end_date, "kbar_type": "3_mins"}))

    def export_5min_data(self, stock_id, stock_name, end_date):
        df = self.model.get_stock_data_from_db(stock_id, end_date, end_date)
        df['ts'] = pd.to_datetime(df['ts'])
        df = df.set_index('ts')
        start_time = pd.Timestamp(end_date).replace(hour=9, minute=5)
        df_5k = df.resample('5T', origin=start_time, closed='right', label='right').agg({
            'Open_Price': 'first',
            'High': 'max',
            'Low': 'min',
            'Close_Price': 'last',
            'Volume': 'sum'
        })
        
        # 重置索引並重命名時間列
        df_5k = df_5k.reset_index()
        df_5k = df_5k.rename(columns={'ts': '時間'})
        
        # 將資料整理為"序號(流水號),開盤價,最高價,最低價,收盤價,時間"
        df_5k['序號'] = range(1, len(df_5k) + 1)
        df_5k = df_5k[['序號', 'Open_Price', 'High', 'Low', 'Close_Price', '時間']]
        self.event_bus.publish(Event("save_kbars_data", {"df": df_5k, "stock_id": stock_id, "end_date": end_date, "kbar_type": "5_mins"}))
        
