from asyncio.windows_events import NULL
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tkinter import filedialog, messagebox
import tkinter as tk
import os
import pandas as pd

from Event import Event, EventBus


class DataAnalysisController:
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self
        self.event_bus = EventBus()
        self.event_bus.subscribe("save_kbars_data", self.view.save_kbars_data)

    def check_stock_data(self):
        stock_id = self.view.entry_stock_id.get()
        if not stock_id:
            self.view.set_status("股票代碼為必填")
            return

        latest_date_ticks, latest_date_kbars = self.model.get_latest_dates(stock_id)
        if latest_date_ticks is not None:
            self.view.label_update_date_ticks.config(text=f"Ticks 更新日期: {latest_date_ticks.strftime('%Y-%m-%d')}")
        else:
            self.view.label_update_date_ticks.config(text=f"Ticks 更新日期: 尚未有資料")
            
        if latest_date_kbars is not None:
            self.view.label_update_date_kbars.config(text=f"Kbars 更新日期: {latest_date_kbars.strftime('%Y-%m-%d')}")
        else:
            self.view.label_update_date_kbars.config(text=f"Kbars 更新日期: 尚未有資料")

        self.view.set_status(f"股票代碼: {stock_id}")
     
    def browse_file(self):
        file_selected = filedialog.askdirectory()
        if file_selected:
            self.view.entry_file_path.delete(0, tk.END)
            self.view.entry_file_path.insert(0, file_selected)
            
    def analyze_data(self):
        stock_id = self.view.entry_stock_id.get()
        start_date = self.view.entry_start_date.get()
        end_date = self.view.entry_end_date.get()
        save_path = self.view.entry_file_path.get()
        if not stock_id or not start_date or not end_date or not save_path:
            self.view.set_status("股票代碼和日期均為必填")
            return

        df = self.model.get_stock_data(stock_id, start_date, end_date)
        daily_high_low = df.groupby('date').agg({'high_price': 'max', 'low_price': 'min'}).reset_index()
        peak_trough_df = self.model.find_peaks_troughs_v34(daily_high_low)

        # 四捨五入至小數點以下兩位，不足補0
        peak_trough_df['Ratio_0.618'] = peak_trough_df['Ratio_0.618'].round(2)
        peak_trough_df['Ratio_1'] = peak_trough_df['Ratio_1'].round(2)
    
        #取得最後一0.618價格
        last_ratio_0_618 = peak_trough_df['Ratio_0.618'].iloc[-1]

        # 獲取最新收盤價
        latest_close_price = self.model.get_latest_close_price(stock_id)
        peak_trough_df['現價'] = round(latest_close_price, 2)

        # 四捨五入 Max_Value 和 Min_Value 欄位並補0
        peak_trough_df['Max_Value'] = peak_trough_df['Max_Value'].round(2)
        peak_trough_df['Min_Value'] = peak_trough_df['Min_Value'].round(2)

        # 計算現價-0.618，Ratio_0.618 - 現價
        peak_trough_df['現價-0.618'] = (peak_trough_df['Ratio_0.618'] - peak_trough_df['現價']).round(2)

        # 計算Head欄位，Max_Value - 現價
        peak_trough_df['Head'] = (peak_trough_df['Max_Value'] - peak_trough_df['現價']).round(2)

        # 計算頸線欄位，Ratio_1 - 現價
        peak_trough_df['頸線'] = (peak_trough_df['Ratio_1'] - peak_trough_df['現價']).round(2)

        # 找出 Max_Value 和 Min_Value 欄位的最大值和最小值
        max_max_value = peak_trough_df['Max_Value'].max()
        min_min_value = peak_trough_df['Min_Value'].min()

        # 計算前面Max(Max_Value)-Min(Min_Value)/2*0.618+Min(Min_Value)的值，並四捨五入至小數點以下兩位
        ratio_0_618_value = (max_max_value - min_min_value) / 2 * 0.618 + min_min_value
        ratio_0_618_value = round(ratio_0_618_value, 2)

        # 計算前面Max(Max_Value)-Min(Min_Value)/2*1+Min(Min_Value)的值，並四捨五入至小數點以下兩位
        ratio_1_value = (max_max_value - min_min_value) / 2 * 1 + min_min_value
        ratio_1_value = round(ratio_1_value, 2)

        # 新增一列填入 Max(Max_Value)、Min(Min_Value)、Ratio_0.618 和 Ratio_1 的值
        new_row = pd.DataFrame({
            'Max_Date': [None],
            'Max_Value': [max_max_value],
            'Min_Date': [None],
            'Min_Value': [min_min_value],
            'Ratio_0.618': [ratio_0_618_value],
            'Ratio_1': [ratio_1_value],
            '現價': [None],
            '現價-0.618': [None],
            'Head': [None],
            '頸線': [None]
        })
        peak_trough_df = pd.concat([peak_trough_df, new_row], ignore_index=True)

        # 排除最後一列進行排序
        sorted_df = peak_trough_df.iloc[:-1]

        # 計算排序欄位
        peak_trough_df['現價-0.618_Sort'] = sorted_df['現價-0.618'].sort_values().tolist() + [None]
        peak_trough_df['Head_Sort'] = sorted_df['Head'].sort_values().tolist() + [None]
        peak_trough_df['頸線_Sort'] = sorted_df['頸線'].sort_values().tolist() + [None]
        peak_trough_df['max由小到大'] = sorted_df['Max_Value'].sort_values().tolist() + [None]
        peak_trough_df['Radio_1_Sort'] = sorted_df['Ratio_1'].sort_values().tolist() + [None]
        peak_trough_df['Radio_0.618_Sort'] = sorted_df['Ratio_0.618'].sort_values().tolist() + [None]

        # 新增流水號欄位
        peak_trough_df['No'] = range(1, len(peak_trough_df) + 1)

        # 將 No 欄位移到 Max_Value 前
        cols = list(peak_trough_df.columns)
        cols.insert(0, cols.pop(cols.index('No')))
        peak_trough_df = peak_trough_df[cols]

        # 獲取每日收盤價
        sma_values, weekly_sma_values, monthly_sma_values, latest_close_prices, latest_dates = self.model.calculate_sma(stock_id)
            
        # 設定儲存路徑和檔名
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        stock_name = self.model.get_stock_name(stock_id)
        if stock_name is not NULL:
            stock_name = stock_name.replace('*', '-')
    
        file_name = f"{stock_id}({stock_name})_{start_date}_to_{end_date}.xlsx"
        file_path = os.path.join(save_path, file_name)
        self.model.save_to_excel(peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, file_path)
        self.view.set_status("資料分析完成並已儲存")

    def show_detail_data(self):
        stock_id = self.view.entry_stock_id.get()
        start_date = self.view.entry_start_date.get()
        end_date = self.view.entry_end_date.get()
        recent_start_date = self.view.entry_recent_start_date.get()
        recent_end_date = self.view.entry_recent_end_date.get()

        # 檢查輸入的日期是否正確
        if not start_date or not end_date or not recent_start_date or not recent_end_date:
            self.view.set_status("日期輸入不正確")
            return
        
        # 檢查波段日期區間是否在總波段日期區間內
        if start_date > recent_start_date or end_date < recent_end_date:
            self.view.set_status("波段日期區間不在總波段日期區間內")
            return
        
        stock_name = self.model.get_stock_name(stock_id)
        if stock_name is not NULL:
            stock_name = stock_name.replace('*', '-')

        total_segment, recent_segment, gap_df, now_price, latest_close_price_by_date, next_open_price = self.model.get_stock_data_from_all_wave_extremes(stock_id, start_date, end_date, recent_start_date, recent_end_date)
        if total_segment is None:
            print(f"沒有找到股票 {stock_id} 的數據")
            return

        # 整理均線數據（使用最近波段數據）
        organized_ma_data = {
            "日均線": {
                "5MA": total_segment.get('sma_5', 'N/A'),
                "10MA": total_segment.get('sma_10', 'N/A'),
                "20MA": total_segment.get('sma_20', 'N/A'),
                "60MA": total_segment.get('sma_60', 'N/A'),
                "120MA": total_segment.get('sma_120', 'N/A')
            },
            "週均線": {
                "5MA": total_segment.get('weekly_sma_5', 'N/A'),
                "10MA": total_segment.get('weekly_sma_10', 'N/A'),
                "20MA": total_segment.get('weekly_sma_20', 'N/A'),
                "60MA": total_segment.get('weekly_sma_60', 'N/A'),
                "120MA": total_segment.get('weekly_sma_120', 'N/A')
            },
            "月均線": {
                "5MA": total_segment.get('monthly_sma_5', 'N/A'),
                "10MA": total_segment.get('monthly_sma_10', 'N/A'),
                "20MA": total_segment.get('monthly_sma_20', 'N/A'),
                "60MA": total_segment.get('monthly_sma_60', 'N/A'),
                "120MA": total_segment.get('monthly_sma_120', 'N/A')
            },
            "15分鐘均線": {
                "5MA": recent_segment.get('15min_sma_5', 'N/A'),
                "10MA": recent_segment.get('15min_sma_10', 'N/A'),
                "20MA": recent_segment.get('15min_sma_20', 'N/A'),
                "60MA": recent_segment.get('15min_sma_60', 'N/A'),
                "120MA": recent_segment.get('15min_sma_120', 'N/A')
            }
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
            '5': recent_segment.get('Ratio_5', 'N/A')
        }

        # 整理比例價格數據（包括最近波段和總波段）
        total_ratio_prices = {
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
            '5': total_segment.get('Ratio_5', 'N/A')        
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
            '總波段最低價日期': total_segment.get('Min_Date', 'N/A')
        }

        # 從 total_segment 獲取所有指標價格
        indicator_prices = {
            'CDP': total_segment.get('CDP', 'N/A'),
            'NH': total_segment.get('NH', 'N/A'),
            'NL': total_segment.get('NL', 'N/A'),
            'AH': total_segment.get('AH', 'N/A'),
            'AL': total_segment.get('AL', 'N/A')
        }

        self.view.show_sma_data(stock_id, stock_name, organized_ma_data, recent_ratio_prices, additional_data, indicator_prices, total_ratio_prices, gap_df, now_price, latest_close_price_by_date, next_open_price)
        
    def export_1min_data(self, stock_id, stock_name, end_date):
        # 獲取1分K資料
        df = self.model.get_stock_data_from_db(stock_id, end_date, end_date)
        # 將資料整理為"序號(流水號),開盤價,最高價,最低價,收盤價,時間"
        df['序號'] = range(1, len(df) + 1)
        df = df[['序號', 'Open_Price', 'High', 'Low', 'Close_Price', 'ts']]
        self.event_bus.publish(Event("save_kbars_data", {"df": df, "stock_id": stock_id, "end_date": end_date, "kbar_type": "1_mins"}))

    def export_3min_data(self, stock_id, stock_name, end_date):
        df = self.model.get_stock_data_from_db(stock_id, end_date, end_date)
        # 重採樣，從0900開始每15分鐘
        df['ts'] = pd.to_datetime(df['ts'])
        df = df.set_index('ts')
        start_time = pd.Timestamp(end_date).replace(hour=9, minute=3)
        df_3k = df.resample('3T', origin=start_time, closed='right', label='right').agg({
            'Open_Price': 'last',
            'High': 'last',
            'Low': 'last',
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
            'Open_Price': 'last',
            'High': 'last',
            'Low': 'last',
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
        