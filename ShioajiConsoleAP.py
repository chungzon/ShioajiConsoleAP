# import shioaji as sj
# import pandas as pd
# import os
# import tkinter as tk
# from tkinter import messagebox
# from tkinter import filedialog
# import requests
# from bs4 import BeautifulSoup
# import numpy as np
# import pymssql
# import xlsxwriter

# # 初始化 Shioaji API
# api = sj.Shioaji(simulation=True)
# api.login(
#     api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
#     secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
# )

# # 連接到資料庫
# def connect_db():
#     conn = pymssql.connect(
#         server='127.0.0.1:1433',
#         user='TSE_USER',
#         password='fuckme',
#         database='TSE'
#     )
#     return conn

# # 從資料庫中獲取每日收盤價
# def get_daily_close_prices_from_db(stock_code, days):
#     conn = connect_db()
#     query = f"""
#     SELECT ts AS date, close_price
#     FROM (
#         SELECT *,
#                ROW_NUMBER() OVER (PARTITION BY CONVERT(date, ts) ORDER BY ts DESC) AS rn
#         FROM Ticks
#         WHERE stock_id = '{stock_code}'
#     ) AS sub
#     WHERE sub.rn = 1
#     ORDER BY date DESC
#     OFFSET 0 ROWS
#     FETCH NEXT {days + 3650} ROWS ONLY
#     """
#     df = pd.read_sql(query, conn)
#     df['date'] = pd.to_datetime(df['date'])
#     df.set_index('date', inplace=True)
#     df = df.sort_index()  # 按日期排序
#     return df['close_price']

# # 定義函數找出每個波段的最高價和最低價，並計算特定比例的價格
# def find_peaks_troughs_v34(df):
#     segments = []
#     ratios = [0.618, 1]
#     ratio_columns = [f'Ratio_{ratio}' for ratio in ratios]
    
#     i = 0
#     while i < len(df):
#         max_value = df['High'].iloc[i]
#         max_date = df['date'].iloc[i]
        
#         j = i + 1
#         while j < len(df) and df['High'].iloc[j] >= max_value:
#             max_value = df['High'].iloc[j]
#             max_date = df['date'].iloc[j]
#             j += 1
        
#         if j < len(df):
#             min_value = df['Low'].iloc[j]
#             min_date = df['date'].iloc[j]
#         else:
#             min_value = df['Low'].iloc[j-1]
#             min_date = df['date'].iloc[j-1]
        
#         k = j
#         while k < len(df) and df['Low'].iloc[k] <= min_value:
#             min_value = df['Low'].iloc[k]
#             min_date = df['date'].iloc[k]
#             k += 1
        
#         if max_value > min_value:
#             segment = [max_date, max_value, min_date, min_value]
#             for ratio in ratios:
#                 segment.append((max_value - min_value) / 2 * ratio + min_value)
#             segments.append(segment)
        
#         i = k
    
#     return pd.DataFrame(segments, columns=['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value'] + ratio_columns)

# # 獲取最新收盤價
# def get_latest_close_price(stock_code):
#     contract = api.Contracts.Stocks[stock_code]
#     snapshot = api.snapshots([contract])
#     latest_close = snapshot[0].close
#     return latest_close

# # 計算移動平均
# def calculate_moving_average(prices, window):
#     return prices.rolling(window=window).mean()

# # 計算周均線
# def calculate_weekly_average(prices, window):
#     weekly_prices = prices.resample('W').last()
#     return calculate_moving_average(weekly_prices, window)

# # 計算月均線
# def calculate_monthly_average(prices, window):
#     monthly_prices = prices.resample('M').last()
#     return calculate_moving_average(monthly_prices, window)

# # 儲存資料到Excel
# def save_to_excel(peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, output_file_path):
#     with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
#         workbook = writer.book
#         worksheet = workbook.add_worksheet("Peaks_and_Troughs")
#         percent_fmt = workbook.add_format({'num_format': '0.00%'})

#         # 儲存波段資料
#         peak_trough_df.to_excel(writer, sheet_name='Peaks_and_Troughs', index=False, startrow=0)

#         # 確定開始寫入日均線的行數
#         start_row = len(peak_trough_df) + 5
        
#         worksheet.write(start_row - 1, 0, latest_close_price)

#         # 設定日均線表格標題
#         headers = ["日均線", "", "", "", "收", "買點", "", "", "", "日均線"]
#         worksheet.write_row(start_row, 0, headers)

#         # 合併第5欄位和第6欄位的第1列和第2列資料格
#         worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
#         worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")
        
#         #在日均線表格填入收盤價和買點價
#         worksheet.write(start_row + 1, 4, latest_close_price)       
#         worksheet.write(start_row + 1, 5, last_ratio_0_618)
        
#         #買點價-收盤價
#         diff_price = last_ratio_0_618 - latest_close_price

#         # 合併第5欄位和第6欄位的第3列資料格
#         worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")

#         #填入日均線(買點價-收盤價)
#         worksheet.write(start_row + 3, 4, diff_price)
        
#         #計算(買點價-收盤價)/收盤價
#         radio_diff_price = diff_price / latest_close_price
        
#         # 合併第5欄位和第6欄位的第4列資料格
#         worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
        
#         #填入(買點價-收盤價)/收盤價
#         worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)

#         # 設定第一欄和第十欄的資料
#         sma_labels = ["SMA5", "SMA10", "SMA20", "SMA60", "SMA120"]
#         for i, label in enumerate(sma_labels):
#             worksheet.write(start_row + i + 1, 0, label)
#             worksheet.write(start_row + i + 1, 9, label)

#         cell_green_format = workbook.add_format()
#         cell_green_format.set_pattern(1)
#         cell_green_format.set_bg_color('green')
#         cell_red_format = workbook.add_format()
#         cell_red_format.set_pattern(1)
#         cell_red_format.set_bg_color('red')
#         # 填入日均線計算值
#         for i, value in enumerate(sma_values):
#             worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
#             worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
#             if not pd.isna(value):
#                 if latest_close_price > value:
#                     worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
#                 else:
#                     worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
#                 if  last_ratio_0_618 > value:
#                     worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
#                 else:
#                     worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
#             else:
#                 print("")
            
            
#         #填入數值分析
#         if not pd.isna(sma_values[-1]):
#             last_daily_sma120 = sma_values[-1]
#             diff_last_daily_sma120 = (last_daily_sma120 - latest_close_price).round(2)
#             radio_last_dailly_sma120 = (diff_last_daily_sma120 / latest_close_price).round(2)
#             diff_sma_120_label = ["(", f"{diff_last_daily_sma120:.2f}", ", ", f"{radio_last_dailly_sma120:0.00%}", ")"]
#             worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
#             diff_last_daily_sma120 = (last_ratio_0_618 - last_daily_sma120).round(2)
#             radio_last_dailly_sma120 = (diff_last_daily_sma120 / last_ratio_0_618).round(2)
#             diff_sma_120_label = ["(", f"{diff_last_daily_sma120:.2f}", ", ", f"{radio_last_dailly_sma120:0.00%}", ")"]
#             worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
#         else:
#             print("")   

#         # 插入一行空行
#         start_row += len(sma_labels) + 3
#         worksheet.write_row(start_row, 0, [""] * len(headers))
#         start_row += 1

#         # 插入周均線表格
#         headers = ["月均線", "", "", "", "收", "買點", "", "", "", "月均線"]
#         worksheet.write_row(start_row, 0, headers)

#         # 合併第5欄位和第6欄位的第1列和第2列資料格
#         worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
#         worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")

#         worksheet.write(start_row + 1, 4, latest_close_price)       
#         worksheet.write(start_row + 1, 5, last_ratio_0_618)

#         # 合併第5欄位和第6欄位的第3列資料格
#         worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
#         #填入周均線(買點價-收盤價)
#         worksheet.write(start_row + 3, 4, diff_price)
        
#         # 合併第5欄位和第6欄位的第4列資料格
#         worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
               
#         #填入(買點價-收盤價)/收盤價
#         worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)
        
#         # 設定第一欄和第十欄的資料
#         weekly_sma_labels = ["周SMA5", "周SMA10", "周SMA20", "周SMA60", "周SMA120"]
#         for i, label in enumerate(weekly_sma_labels):
#             worksheet.write(start_row + i + 1, 0, label)
#             worksheet.write(start_row + i + 1, 9, label)

#         # 填入周均線計算值
#         for i, value in enumerate(weekly_sma_values):
#             worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
#             worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
#             if not pd.isna(value):
#                 if latest_close_price > value:
#                     worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
#                 else:
#                     worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
#                 if  last_ratio_0_618 > value:
#                     worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
#                 else:
#                     worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
#             else:
#                 print("")
            
#         #填入數值分析
#         if not pd.isna(weekly_sma_values[-1]):
#             last_weekly_sma120 = weekly_sma_values[-1]
#             diff_last_weekly_sma120 = (last_weekly_sma120 - latest_close_price).round(2)
#             radio_last_weekly_sma120 = (diff_last_weekly_sma120 / latest_close_price).round(2)
#             diff_sma_120_label = ["(", f"{diff_last_weekly_sma120:.2f}", ", ", f"{radio_last_weekly_sma120:0.00%}", ")"]
#             worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
#             diff_last_weekly_sma120 = (last_ratio_0_618 - last_weekly_sma120).round(2)
#             radio_last_weekly_sma120 = (diff_last_weekly_sma120 / last_ratio_0_618).round(2)
#             diff_sma_120_label = ["(", f"{diff_last_weekly_sma120:.2f}", ", ", f"{radio_last_weekly_sma120:0.00%}", ")"]
#             worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
#         else:
#             print("")

#         # 插入一行空行
#         start_row += len(weekly_sma_labels) + 2
#         worksheet.write_row(start_row, 0, [""] * len(headers))
#         start_row += 1

#         # 插入月均線表格
#         headers = ["月均線", "", "", "", "收", "買點", "", "", "", "月均線"]
#         worksheet.write_row(start_row, 0, headers)

#         # 合併第5欄位和第6欄位的第1列和第2列資料格
#         worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
#         worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")
        
#         worksheet.write(start_row + 1, 4, latest_close_price)       
#         worksheet.write(start_row + 1, 5, last_ratio_0_618)

#         # 合併第5欄位和第6欄位的第3列資料格
#         worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
#         #填入(買點價-收盤價)/收盤價
#         worksheet.write(start_row + 3, 4, diff_price)
        
#         # 合併第5欄位和第6欄位的第4列資料格
#         worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
        
#         #填入(買點價-收盤價)/收盤價
#         worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)

#         # 設定第一欄和第十欄的資料
#         monthly_sma_labels = ["月SMA5", "月SMA10", "月SMA20", "月SMA60", "月SMA120"]
#         for i, label in enumerate(monthly_sma_labels):
#             worksheet.write(start_row + i + 1, 0, label)
#             worksheet.write(start_row + i + 1, 9, label)

#         # 填入月均線計算值
#         for i, value in enumerate(monthly_sma_values):
#             worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
#             worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
#             if not pd.isna(value):
#                 if latest_close_price > value:
#                     worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
#                 else:
#                     worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
#                 if  last_ratio_0_618 > value:
#                     worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
#                 else:
#                     worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
#             else:
#                 print("")
            
#         #填入數值分析
#         if not pd.isna(monthly_sma_values[-1]):
#             last_monthly_sma120 = monthly_sma_values[-1]
#             diff_last_monthly_sma120 = (last_monthly_sma120 - latest_close_price).round(2)
#             radio_last_monthly_sma120 = (diff_last_monthly_sma120 / latest_close_price).round(2)
#             diff_sma_120_label = ["(", f"{diff_last_monthly_sma120:.2f}", ", ", f"{radio_last_monthly_sma120:0.00%}", ")"]
#             worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
#             diff_last_monthly_sma120 = (last_ratio_0_618 - last_monthly_sma120).round(2)
#             radio_last_monthly_sma120 = (diff_last_monthly_sma120 / last_ratio_0_618).round(2)
#             diff_sma_120_label = ["(", f"{diff_last_monthly_sma120:.2f}", ", ", f"{radio_last_monthly_sma120:0.00%}", ")"]
#             worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
#         else:
#             print("")
            
#      # 設定數字格式
#         num_format = workbook.add_format({'num_format': '0.00'})

#         # 依列應用格式
#         for col_num, col_name in enumerate(peak_trough_df.columns):
#             if col_name not in ['Max_Date', 'Min_Date']:
#                 worksheet.set_column(col_num, col_num, 12, num_format)

#         # 新增折線圖和散佈圖
#         line_chart1 = workbook.add_chart({'type': 'line'})
#         scatter_chart1 = workbook.add_chart({'type': 'scatter'})
#         line_chart2 = workbook.add_chart({'type': 'line'})
#         scatter_chart2 = workbook.add_chart({'type': 'scatter'})

#         # 設定圖表資料範圍
#         max_row = len(peak_trough_df) + 1

#         # custom_labels using P column data
#         custom_labels_P = [
#             {'value': f"='Peaks_and_Troughs'!$Q${i}", 'font': {'color': 'blue'}} for i in range(2, max_row)
#         ]
        
#         # custom_labels using N column data
#         custom_labels_N = [
#             {'value': f"='Peaks_and_Troughs'!$O${i}", 'font': {'color': 'red'}} for i in range(2, max_row)
#         ]
        
#         # custom_labels using O column data
#         custom_labels_O = [
#             {'value': f"='Peaks_and_Troughs'!$P${i}", 'font': {'color': 'green'}} for i in range(2, max_row)
#         ]

#         # 第一張圖表 - 排序後的數列
#         line_chart1.add_series({
#             'name': '現價-0.618_Sort',
#             'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
#             'values': f"='Peaks_and_Troughs'!$L$2:$L${max_row}",
#             'marker': {'type': 'circle', 'size': 6},
#             'data_labels': {
#                 'value': True,
#                 'custom': custom_labels_P
#             }  # 添加自定義數值標籤
#         })
#         scatter_chart1.add_series({
#             'name': 'Head_Sort',
#             'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
#             'values': f"='Peaks_and_Troughs'!$M$2:$M${max_row}",
#             'marker': {'type': 'circle', 'size': 6},
#             'data_labels': {
#                 'value': True,
#                 'custom': custom_labels_N
#             }
#         })
#         scatter_chart1.add_series({
#             'name': '頸線_Sort',
#             'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
#             'values': f"='Peaks_and_Troughs'!$N$2:$N${max_row}",
#             'marker': {'type': 'circle', 'size': 6},
#             'data_labels': {
#                 'value': True,
#                 'custom': custom_labels_O
#             }
#         })

#         # 設定第一張圖表標題和軸標籤
#         line_chart1.set_title({'name': 'Stock Price Analysis (Sorted)'})
#         line_chart1.set_x_axis({'name': 'Index'})
#         line_chart1.set_y_axis({'name': 'Value'})
        
#         # 插入第一張圖表到工作表
#         line_chart1.combine(scatter_chart1)
#         worksheet.insert_chart('S2', line_chart1)
        
#         # custom_labels using E column data
#         custom_labels_E = [
#             {'value': f"='Peaks_and_Troughs'!$F${i}", 'font': {'color': 'blue'}} for i in range(2, max_row)
#         ]
        
#         # custom_labels using B column data
#         custom_labels_B = [
#             {'value': f"='Peaks_and_Troughs'!$C${i}", 'font': {'color': 'red'}} for i in range(2, max_row)
#         ]
        
#         # custom_labels using F column data
#         custom_labels_F = [
#             {'value': f"='Peaks_and_Troughs'!$G${i}", 'font': {'color': 'green'}} for i in range(2, max_row)
#         ]

#         # 第二張圖表 - 原始數列
#         line_chart2.add_series({
#             'name': '現價-0.618',
#             'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
#             'values': f"='Peaks_and_Troughs'!$I$2:$I${max_row}",
#             'marker': {'type': 'circle', 'size': 6},
#             'data_labels': {
#                 'value': True,
#                 'custom': custom_labels_E
#             }
#         })
#         scatter_chart2.add_series({
#             'name': 'Head',
#             'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
#             'values': f"='Peaks_and_Troughs'!$J$2:$J${max_row}",
#             'marker': {'type': 'circle', 'size': 6},
#             'data_labels': {
#                 'value': True,
#                 'custom': custom_labels_B
#             }
#         })
#         scatter_chart2.add_series({
#             'name': '頸線',
#             'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
#             'values': f"='Peaks_and_Troughs'!$K$2:$K${max_row}",
#             'marker': {'type': 'circle', 'size': 6},
#             'data_labels': {
#                 'value': True,
#                 'custom': custom_labels_F
#             }})
       
#         # 設定第二張圖表標題和軸標籤
#         line_chart2.set_title({'name': 'Stock Price Analysis (Original)'})
#         line_chart2.set_x_axis({'name': 'Index'})
#         line_chart2.set_y_axis({'name': 'Value'})

#         # 插入第二張圖表到工作表
#         line_chart2.combine(scatter_chart2)
#         worksheet.insert_chart('S20', line_chart2)

#     messagebox.showinfo("完成", f"波段資料及均線資料已儲存到: {output_file_path}")

# # 主函數
# def main(stock_code, input_file_path, output_file_path):
#     # 讀取Excel檔案中的資料
#     df = pd.read_excel(input_file_path)
    
#     # 確保資料欄位名稱正確
#     df.columns = ['date', 'High', 'Low']
#     df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')  # 確保日期欄位是yyyy-MM-dd格式

#     # 使用 find_peaks_troughs_v34 函數找出波段的最高價和最低價
#     peak_trough_df = find_peaks_troughs_v34(df)

#     # 四捨五入至小數點以下兩位，不足補0
#     peak_trough_df['Ratio_0.618'] = peak_trough_df['Ratio_0.618'].round(2)
#     peak_trough_df['Ratio_1'] = peak_trough_df['Ratio_1'].round(2)
    
#     #取得最後一0.618價格
#     last_ratio_0_618 = peak_trough_df['Ratio_0.618'].iloc[-1]

#     # 獲取最新收盤價
#     latest_close_price = get_latest_close_price(stock_code)
#     peak_trough_df['現價'] = round(latest_close_price, 2)

#     # 四捨五入 Max_Value 和 Min_Value 欄位並補0
#     peak_trough_df['Max_Value'] = peak_trough_df['Max_Value'].round(2)
#     peak_trough_df['Min_Value'] = peak_trough_df['Min_Value'].round(2)

#     # 計算現價-0.618，Ratio_0.618 - 現價
#     peak_trough_df['現價-0.618'] = (peak_trough_df['Ratio_0.618'] - peak_trough_df['現價']).round(2)

#     # 計算Head欄位，Max_Value - 現價
#     peak_trough_df['Head'] = (peak_trough_df['Max_Value'] - peak_trough_df['現價']).round(2)

#     # 計算頸線欄位，Ratio_1 - 現價
#     peak_trough_df['頸線'] = (peak_trough_df['Ratio_1'] - peak_trough_df['現價']).round(2)

#     # 找出 Max_Value 和 Min_Value 欄位的最大值和最小值
#     max_max_value = peak_trough_df['Max_Value'].max()
#     min_min_value = peak_trough_df['Min_Value'].min()

#     # 計算前面Max(Max_Value)-Min(Min_Value)/2*0.618+Min(Min_Value)的值，並四捨五入至小數點以下兩位
#     ratio_0_618_value = (max_max_value - min_min_value) / 2 * 0.618 + min_min_value
#     ratio_0_618_value = round(ratio_0_618_value, 2)

#     # 計算前面Max(Max_Value)-Min(Min_Value)/2*1+Min(Min_Value)的值，並四捨五入至小數點以下兩位
#     ratio_1_value = (max_max_value - min_min_value) / 2 * 1 + min_min_value
#     ratio_1_value = round(ratio_1_value, 2)

#     # 新增一列填入 Max(Max_Value)、Min(Min_Value)、Ratio_0.618 和 Ratio_1 的值
#     new_row = pd.DataFrame({
#         'Max_Date': [None],
#         'Max_Value': [max_max_value],
#         'Min_Date': [None],
#         'Min_Value': [min_min_value],
#         'Ratio_0.618': [ratio_0_618_value],
#         'Ratio_1': [ratio_1_value],
#         '現價': [None],
#         '現價-0.618': [None],
#         'Head': [None],
#         '頸線': [None]
#     })
#     peak_trough_df = pd.concat([peak_trough_df, new_row], ignore_index=True)

#     # 排除最後一列進行排序
#     sorted_df = peak_trough_df.iloc[:-1]

#     # 計算排序欄位
#     peak_trough_df['現價-0.618_Sort'] = sorted_df['現價-0.618'].sort_values().tolist() + [None]
#     peak_trough_df['Head_Sort'] = sorted_df['Head'].sort_values().tolist() + [None]
#     peak_trough_df['頸線_Sort'] = sorted_df['頸線'].sort_values().tolist() + [None]
#     peak_trough_df['max由小到大'] = sorted_df['Max_Value'].sort_values().tolist() + [None]
#     peak_trough_df['Radio_1_Sort'] = sorted_df['Ratio_1'].sort_values().tolist() + [None]
#     peak_trough_df['Radio_0.618_Sort'] = sorted_df['Ratio_0.618'].sort_values().tolist() + [None]

#     # 新增流水號欄位
#     peak_trough_df['No'] = range(1, len(peak_trough_df) + 1)

#     # 將 No 欄位移到 Max_Value 前
#     cols = list(peak_trough_df.columns)
#     cols.insert(0, cols.pop(cols.index('No')))
#     peak_trough_df = peak_trough_df[cols]

#     # 獲取每日收盤價
#     close_prices = get_daily_close_prices_from_db(stock_code, 120)
    
#     # 計算日均線的移動平均
#     sma_values = [
#         round(calculate_moving_average(close_prices, 5).iloc[-1], 2),
#         round(calculate_moving_average(close_prices, 10).iloc[-1], 2),
#         round(calculate_moving_average(close_prices, 20).iloc[-1], 2),
#         round(calculate_moving_average(close_prices, 60).iloc[-1], 2),
#         round(calculate_moving_average(close_prices, 120).iloc[-1], 2),
#     ]

#     # 計算周均線的移動平均
#     weekly_sma_values = [
#         round(calculate_weekly_average(close_prices, 5).iloc[-1], 2),
#         round(calculate_weekly_average(close_prices, 10).iloc[-1], 2),
#         round(calculate_weekly_average(close_prices, 20).iloc[-1], 2),
#         round(calculate_weekly_average(close_prices, 60).iloc[-1], 2),
#         round(calculate_weekly_average(close_prices, 120).iloc[-1], 2),
#     ]

#     # 計算月均線的移動平均
#     monthly_sma_values = [
#         round(calculate_monthly_average(close_prices, 5).iloc[-1], 2),
#         round(calculate_monthly_average(close_prices, 10).iloc[-1], 2),
#         round(calculate_monthly_average(close_prices, 20).iloc[-1], 2),
#         round(calculate_monthly_average(close_prices, 60).iloc[-1], 2),
#         round(calculate_monthly_average(close_prices, 120).iloc[-1], 2),
#     ]
    
#     # 保存到 Excel 文件
#     save_to_excel(peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, output_file_path)

# # 建立GUI
# def create_gui():
#     def run():
#         stock_id = entry_stock_id.get()
#         input_file_path = entry_input_file_path.get()
#         output_file_path = entry_output_file_path.get()

#         if not stock_id or not input_file_path or not output_file_path:
#             messagebox.showerror("錯誤", "所有欄位均為必填")
#             return

#         main(stock_id, input_file_path, output_file_path)

#     def browse_input_file():
#         file_selected = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
#         if file_selected:
#             entry_input_file_path.delete(0, tk.END)
#             entry_input_file_path.insert(0, file_selected)

#     def browse_output_file():
#         file_selected = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
#         if file_selected:
#             entry_output_file_path.delete(0, tk.END)
#             entry_output_file_path.insert(0, file_selected)

#     # 建立主窗口
#     root = tk.Tk()
#     root.title("股票資料分析器")

#     # 股票代碼
#     tk.Label(root, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5)
#     entry_stock_id = tk.Entry(root)
#     entry_stock_id.grid(row=0, column=1, padx=10, pady=5)

#     # 輸入資料檔案路徑
#     tk.Label(root, text="資料檔案 (Excel):").grid(row=1, column=0, padx=10, pady=5)
#     entry_input_file_path = tk.Entry(root)
#     entry_input_file_path.grid(row=1, column=1, padx=10, pady=5)
#     tk.Button(root, text="瀏覽", command=browse_input_file).grid(row=1, column=2, padx=10, pady=5)

#     # 輸出資料檔案路徑
#     tk.Label(root, text="結果檔案 (Excel):").grid(row=2, column=0, padx=10, pady=5)
#     entry_output_file_path = tk.Entry(root)
#     entry_output_file_path.grid(row=2, column=1, padx=10, pady=5)
#     tk.Button(root, text="瀏覽", command=browse_output_file).grid(row=2, column=2, padx=10, pady=5)

#     # 執行按鈕
#     tk.Button(root, text="分析資料", command=run).grid(row=3, column=0, columnspan=3, pady=20)

#     # 啟動主循環
#     root.mainloop()
    


# # 執行GUI
# if __name__ == "__main__":
#     create_gui()

# import shioaji as sj
# import pandas as pd
# from datetime import datetime, timedelta

# def main():
#     # 初始化 Shioaji API
#     api = sj.Shioaji(simulation=True)
#     api.login(
#         api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
#         secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
#     )

#  # 列出所有可用的指數合約
#     print("Available index contracts:")
#     # for index in api.Contracts.Indexs:
#     #     print(index, api.Contracts.Indexs[index])

#     # 假設加權指數代碼是 'TWSE01'
#     contract = api.Contracts.Indexs["TSE"]["TSE001"]

#     # 訂閱即時行情
#     def quote_callback(exchange, quote):
#         print(f"Exchange: {exchange}, Quote: {quote}")

#     api.quote.set_on_tick_stk_v1_callback(quote_callback)
#     api.quote.subscribe(
#         contract,
#         quote_type=sj.constant.QuoteType.Quote,
#         version=sj.constant.QuoteVersion.v1
#     )

#     # 獲取 K 線圖資料
#     start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
#     end_date = datetime.now().strftime('%Y-%m-%d')

#     kbars = api.kbars(
#         contract=contract,
#         start=start_date,
#         end=end_date
#     )

#     df = pd.DataFrame({**kbars})
#     df.ts = pd.to_datetime(df.ts)
#     print(df)

#     # 登出
#     api.logout()

import re
import pandas as pd
import pymssql

# 清理股票名称中的特殊字符
def clean_stock_name(stock_name):
    return re.sub(r'[\*\#]', '', stock_name)

# 连接数据库
def connect_db():
    conn = pymssql.connect(
        server='127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn

# 处理 Excel 中的股票数据
def process_stock_data(file_path):
    try:
        df = pd.read_excel(file_path, header=None)  # 没有标题行，直接读取
        return df
    except Exception as e:
        print(f"讀取文件時發生錯誤: {e}")
        return None

# 解析并分类股票数据
def parse_stock_data(df):
    parsed_data = []
    current_category = None
    current_market = None

    for _, row in df.iterrows():
        if pd.isna(row[0]) and not pd.isna(row[1]):  # 市场类型 (上市/上柜)
            current_market = row[1]
        elif not pd.isna(row[0]):  # 类股种类
            current_category = row[0]
        else:  # 股票信息
            stock_id = row[2]
            stock_name = clean_stock_name(row[3])
            parsed_data.append({
                'id': stock_id,
                'stock_name': stock_name,
                'market_type': current_market,
                'stock_category': current_category
            })
    
    return pd.DataFrame(parsed_data)

# 插入股票数据到数据库
def insert_stock_data(conn, df):
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO StockTable (id, stock_name, market_type, stock_category)
            VALUES (%s, %s, %s, %s)
        """, (row['id'], row['stock_name'], row['market_type'], row['stock_category']))
    conn.commit()
    cursor.close()

# 创建或更新数据库表
def create_or_update_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='StockTable' AND xtype='U')
        CREATE TABLE StockTable (
            id VARCHAR(10) PRIMARY KEY,
            stock_name NVARCHAR(100),
            market_type NVARCHAR(10),
            stock_category NVARCHAR(100)
        )
    """)
    conn.commit()
    cursor.close()

def main():
    file_path = r'D:\Project\ShioajiConsole\ShioajiConsoleAP\resource\StockTable2.xlsx'
    conn = connect_db()
    cursor = conn.cursor()
    df = pd.read_excel(file_path, sheet_name='工作表1')
    for index, row in df.iterrows():
        # Split '有價證券代號及名稱' into id and stock_name
        stock_id, stock_name = row['有價證券代號及名稱'].split('　')
        
        # Extract market_type and stock_category
        market_type = row['市場別']
        stock_category = row['產業別']
        
        # Insert data into StockTable
        cursor.execute('''
            INSERT INTO StockTable (id, stock_name, market_type, stock_category)
            VALUES (%s, %s, %s, %s)
        ''', (stock_id, stock_name, market_type, stock_category))
    
    # Commit the transaction
    conn.commit()
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()

