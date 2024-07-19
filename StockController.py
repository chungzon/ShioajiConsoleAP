import threading
from datetime import datetime, timedelta
from StockModel import connect_db, get_latest_dates, get_kbars, insert_kbars, get_ticks_data, insert_ticks_to_sql, get_stock_data_from_db, save_to_excel, find_peaks_troughs_v34, get_latest_close_price, get_daily_close_prices_from_db, calculate_moving_average, calculate_weekly_average, calculate_monthly_average
from StockView import StockView
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tkinter import filedialog, messagebox
import tkinter as tk
import threading
import pandas as pd
import os

class StockController:
    def __init__(self):
        self.view = StockView(self)
        self.view.mainloop()
    
    def process_date(self, stock_id, date):
        start_time = time.time()
        df = get_ticks_data(stock_id, date)
        if not df.empty:
            insert_ticks_to_sql(df)
        end_time = time.time()
        duration = end_time - start_time
        return date, duration

    def confirm_stock(self):
        stock_id = self.view.entry_stock_id.get()
        if not stock_id:
            self.view.set_status("股票代碼為必填")
            return

        latest_date_ticks, latest_date_kbars = get_latest_dates(stock_id)
        self.view.label_update_date_ticks.config(text=latest_date_ticks.strftime('%Y-%m-%d'))
        self.view.label_update_date_kbars.config(text=latest_date_kbars.strftime('%Y-%m-%d'))
        self.view.set_status(f"股票代碼: {stock_id}")

    def browse_file(self):
        file_selected = filedialog.askdirectory()
        if file_selected:
            self.view.entry_file_path.delete(0, tk.END)
            self.view.entry_file_path.insert(0, file_selected)

    def update_data_ticks(self):
        self.update_data('Ticks')

    def update_data_kbars(self):
        self.update_data('Kbars')

    def update_data(self, data_type):
        stock_id = self.view.entry_stock_id.get()
        if not stock_id:
            self.view.set_status("股票代碼為必填")
            return

        latest_date_ticks, latest_date_kbars = get_latest_dates(stock_id)
        end_date = datetime.today()
        if data_type == 'Ticks':
            start_date = (latest_date_ticks + timedelta(days=1))
            dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
            total_start_time = time.time()  # 记录总开始时间
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.process_date, stock_id, date): date for date in dates}
                for future in as_completed(futures):
                    date, duration = future.result()
                    self.view.set_status(f"Date: {date.strftime('%Y-%m-%d')} completed in {duration:.2f} seconds")
            total_end_time = time.time()  # 记录总结束时间
            total_duration = total_end_time - total_start_time  # 计算总花费时间
            self.view.set_status(f"所有資料已經成功抓取並存入資料庫，總花費時間: {total_duration:.2f} 秒")
        else:
            start_date = (latest_date_kbars + timedelta(days=1)).strftime('%Y-%m-%d')

        self.view.progress_var.set(0)
        self.view.progress_bar.config(maximum=1)
        self.view.set_status("更新資料中...")

    def process_data_update(self, stock_id, start_date, end_date, data_type):
        start_time = time.time()

        kbars_df = get_kbars(stock_id, start_date, end_date)
        insert_kbars(kbars_df, stock_id)

        end_time = time.time()
        elapsed_time = end_time - start_time

        self.view.update_progress(1)
        self.view.set_status(f"{data_type}資料更新成功，花費時間: {elapsed_time:.2f}秒")
    
    def analyze_data(self):
        stock_id = self.view.entry_stock_id.get()
        start_date = self.view.entry_start_date.get()
        end_date = self.view.entry_end_date.get()
        save_path = self.view.entry_file_path.get()

        if not stock_id or not start_date or not end_date or not save_path:
            self.view.set_status("股票代碼、起始日期、結束日期和儲存路徑均為必填")
            return
        
        df = get_stock_data_from_db(stock_id, start_date, end_date)
        if df.empty:
            self.view.set_status("沒有找到任何資料")
            return

        # 執行數據分析
        daily_high_low = df.groupby('date').agg({'High': 'max', 'Low': 'min'}).reset_index()
        #save_to_excel(daily_high_low, stock_id, start_date, end_date, save_path)
        
        # 使用 find_peaks_troughs_v34 函數找出波段的最高價和最低價
        peak_trough_df = find_peaks_troughs_v34(daily_high_low)

        # 四捨五入至小數點以下兩位，不足補0
        peak_trough_df['Ratio_0.618'] = peak_trough_df['Ratio_0.618'].round(2)
        peak_trough_df['Ratio_1'] = peak_trough_df['Ratio_1'].round(2)
    
        #取得最後一0.618價格
        last_ratio_0_618 = peak_trough_df['Ratio_0.618'].iloc[-1]

        # 獲取最新收盤價
        latest_close_price = get_latest_close_price(stock_id)
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
        close_prices = get_daily_close_prices_from_db(stock_id, 120)
    
        # 計算日均線的移動平均
        sma_values = [
            round(calculate_moving_average(close_prices, 5).iloc[-1], 2),
            round(calculate_moving_average(close_prices, 10).iloc[-1], 2),
            round(calculate_moving_average(close_prices, 20).iloc[-1], 2),
            round(calculate_moving_average(close_prices, 60).iloc[-1], 2),
            round(calculate_moving_average(close_prices, 120).iloc[-1], 2),
        ]

        # 計算周均線的移動平均
        weekly_sma_values = [
            round(calculate_weekly_average(close_prices, 5).iloc[-1], 2),
            round(calculate_weekly_average(close_prices, 10).iloc[-1], 2),
            round(calculate_weekly_average(close_prices, 20).iloc[-1], 2),
            round(calculate_weekly_average(close_prices, 60).iloc[-1], 2),
            round(calculate_weekly_average(close_prices, 120).iloc[-1], 2),
        ]

        # 計算月均線的移動平均
        monthly_sma_values = [
            round(calculate_monthly_average(close_prices, 5).iloc[-1], 2),
            round(calculate_monthly_average(close_prices, 10).iloc[-1], 2),
            round(calculate_monthly_average(close_prices, 20).iloc[-1], 2),
            round(calculate_monthly_average(close_prices, 60).iloc[-1], 2),
            round(calculate_monthly_average(close_prices, 120).iloc[-1], 2),
        ]
    
        # 保存到 Excel 文件
        file_name = f"{stock_id}_{start_date}_to_{end_date}.xlsx"
        file_path = os.path.join(save_path, file_name)  
        save_to_excel(peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, file_path)

        
        self.view.set_status(f"分析完成，結果已儲存至: {save_path}")


if __name__ == "__main__":
    StockController()
