import shioaji as sj
import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import requests
from bs4 import BeautifulSoup

# 初始化 Shioaji API
api = sj.Shioaji(simulation=True)
api.login(
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

# 定義函數找出每個波段的最高價和最低價，並計算特定比例的價格
def find_peaks_troughs_v34(df):
    segments = []
    ratios = [0.618, 1]
    ratio_columns = [f'Ratio_{ratio}' for ratio in ratios]
    
    i = 0
    while i < len(df):
        # Initialize max and min
        max_value = df['High'].iloc[i]
        max_date = df['date'].iloc[i]  # 新增 max_date
        
        # Find max peak
        j = i + 1
        while j < len(df) and df['High'].iloc[j] >= max_value:
            max_value = df['High'].iloc[j]
            max_date = df['date'].iloc[j]  # 更新 max_date
            j += 1
        
        # After finding the max, initialize min
        if j < len(df):
            min_value = df['Low'].iloc[j]
            min_date = df['date'].iloc[j]
        else:
            min_value = df['Low'].iloc[j-1]
            min_date = df['date'].iloc[j-1]
        
        # Find min trough
        k = j
        while k < len(df) and df['Low'].iloc[k] <= min_value:
            min_value = df['Low'].iloc[k]
            min_date = df['date'].iloc[k]
            k += 1
        
        # Ensure max_value is before min_date and no invalid values
        if max_value > min_value:
            segment = [max_date, max_value, min_date, min_value]  # 將 max_date 和 max_value 位置交換
            for ratio in ratios:
                segment.append((max_value - min_value) / 2 * ratio + min_value)
            segments.append(segment)
        
        # Move to the next segment
        i = k
    
    return pd.DataFrame(segments, columns=['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value'] + ratio_columns)  # 將 Max_Date 和 Max_Value 位置交換

# 獲取最新收盤價
def get_latest_close_price(stock_code):
    contract = api.Contracts.Stocks[stock_code]
    snapshot = api.snapshots([contract])
    latest_close = snapshot[0].close
    return latest_close

# 儲存資料到Excel
def save_to_excel(df, output_file_path):
    with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Peaks_and_Troughs', index=False)

        # 取得 xlsxwriter 物件
        workbook = writer.book
        worksheet = writer.sheets['Peaks_and_Troughs']

        # 設定數字格式
        num_format = workbook.add_format({'num_format': '0.00'})

        # 依列應用格式
        for col_num, col_name in enumerate(df.columns):
            if col_name not in ['Max_Date', 'Min_Date']:
                worksheet.set_column(col_num, col_num, 12, num_format)

        # 新增折線圖和散佈圖
        line_chart1 = workbook.add_chart({'type': 'line'})
        scatter_chart1 = workbook.add_chart({'type': 'scatter'})
        line_chart2 = workbook.add_chart({'type': 'line'})
        scatter_chart2 = workbook.add_chart({'type': 'scatter'})

        # 設定圖表資料範圍
        max_row = len(df) + 1

        # custom_labels using P column data
        custom_labels_P = [
            {'value': f"='Peaks_and_Troughs'!$Q${i}", 'font': {'color': 'blue'}} for i in range(2, max_row)
        ]
        
        # custom_labels using N column data
        custom_labels_N = [
            {'value': f"='Peaks_and_Troughs'!$O${i}", 'font': {'color': 'red'}} for i in range(2, max_row)
        ]
        
        # custom_labels using O column data
        custom_labels_O = [
            {'value': f"='Peaks_and_Troughs'!$P${i}", 'font': {'color': 'green'}} for i in range(2, max_row)
        ]

        # 第一張圖表 - 排序後的數列
        line_chart1.add_series({
            'name': '現價-0.618_Sort',
            'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
            'values': f"='Peaks_and_Troughs'!$L$2:$L${max_row}",
            'marker': {'type': 'circle', 'size': 6},
            'data_labels': {
                'value': True,
                'custom': custom_labels_P
            }  # 添加自定義數值標籤
        })
        scatter_chart1.add_series({
            'name': 'Head_Sort',
            'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
            'values': f"='Peaks_and_Troughs'!$M$2:$M${max_row}",
            'marker': {'type': 'circle', 'size': 6},
            'data_labels': {
                'value': True,
                'custom': custom_labels_N
            }
        })
        scatter_chart1.add_series({
            'name': '頸線_Sort',
            'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
            'values': f"='Peaks_and_Troughs'!$N$2:$N${max_row}",
            'marker': {'type': 'circle', 'size': 6},
            'data_labels': {
                'value': True,
                'custom': custom_labels_O
            }
        })

        # 設定第一張圖表標題和軸標籤
        line_chart1.set_title({'name': 'Stock Price Analysis (Sorted)'})
        line_chart1.set_x_axis({'name': 'Index'})
        line_chart1.set_y_axis({'name': 'Value'})
        
        # 插入第一張圖表到工作表
        line_chart1.combine(scatter_chart1)
        worksheet.insert_chart('R2', line_chart1)
        
        # custom_labels using E column data
        custom_labels_E = [
            {'value': f"='Peaks_and_Troughs'!$F${i}", 'font': {'color': 'blue'}} for i in range(2, max_row)
        ]
        
        # custom_labels using B column data
        custom_labels_B = [
            {'value': f"='Peaks_and_Troughs'!$C${i}", 'font': {'color': 'red'}} for i in range(2, max_row)
        ]
        
        # custom_labels using F column data
        custom_labels_F = [
            {'value': f"='Peaks_and_Troughs'!$G${i}", 'font': {'color': 'green'}} for i in range(2, max_row)
        ]

        # 第二張圖表 - 原始數列
        line_chart2.add_series({
            'name': '現價-0.618',
            'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
            'values': f"='Peaks_and_Troughs'!$I$2:$I${max_row}",
            'marker': {'type': 'circle', 'size': 6},
            'data_labels': {
                'value': True,
                'custom': custom_labels_E
            }
        })
        scatter_chart2.add_series({
            'name': 'Head',
            'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
            'values': f"='Peaks_and_Troughs'!$J$2:$J${max_row}",
            'marker': {'type': 'circle', 'size': 6},
            'data_labels': {
                'value': True,
                'custom': custom_labels_B
            }
        })
        scatter_chart2.add_series({
            'name': '頸線',
            'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
            'values': f"='Peaks_and_Troughs'!$K$2:$K${max_row}",
            'marker': {'type': 'circle', 'size': 6},
            'data_labels': {
                'value': True,
                'custom': custom_labels_F
            }})
       
        # 設定第二張圖表標題和軸標籤
        line_chart2.set_title({'name': 'Stock Price Analysis (Original)'})
        line_chart2.set_x_axis({'name': 'Index'})
        line_chart2.set_y_axis({'name': 'Value'})

        # 插入第二張圖表到工作表
        line_chart2.combine(scatter_chart2)
        worksheet.insert_chart('R20', line_chart2)

    messagebox.showinfo("完成", f"波段資料已儲存到: {output_file_path}")

# 主函數
def main(stock_code, input_file_path, output_file_path):
    # 讀取Excel檔案中的資料
    df = pd.read_excel(input_file_path)
    
    # 確保資料欄位名稱正確
    df.columns = ['date', 'High', 'Low']
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')  # 確保日期欄位是yyyy-MM-dd格式

    # 使用 find_peaks_troughs_v34 函數找出波段的最高價和最低價
    peak_trough_df = find_peaks_troughs_v34(df)

    # 四捨五入至小數點以下兩位，不足補0
    peak_trough_df['Ratio_0.618'] = peak_trough_df['Ratio_0.618'].round(2)
    peak_trough_df['Ratio_1'] = peak_trough_df['Ratio_1'].round(2)

    # 獲取最新收盤價
    latest_close_price = get_latest_close_price(stock_code)
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
        'Max_Date': [None],  # 新增 Max_Date
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

    # 儲存資料到 Excel
    save_to_excel(peak_trough_df, output_file_path)

# 建立GUI
def create_gui():
    def run():
        stock_id = entry_stock_id.get()
        input_file_path = entry_input_file_path.get()
        output_file_path = entry_output_file_path.get()

        if not stock_id or not input_file_path or not output_file_path:
            messagebox.showerror("錯誤", "所有欄位均為必填")
            return

        main(stock_id, input_file_path, output_file_path)

    def browse_input_file():
        file_selected = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_selected:
            entry_input_file_path.delete(0, tk.END)
            entry_input_file_path.insert(0, file_selected)

    def browse_output_file():
        file_selected = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_selected:
            entry_output_file_path.delete(0, tk.END)
            entry_output_file_path.insert(0, file_selected)

    # 建立主窗口
    root = tk.Tk()
    root.title("股票資料分析器")

    # 股票代碼
    tk.Label(root, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5)
    entry_stock_id = tk.Entry(root)
    entry_stock_id.grid(row=0, column=1, padx=10, pady=5)

    # 輸入資料檔案路徑
    tk.Label(root, text="資料檔案 (Excel):").grid(row=1, column=0, padx=10, pady=5)
    entry_input_file_path = tk.Entry(root)
    entry_input_file_path.grid(row=1, column=1, padx=10, pady=5)
    tk.Button(root, text="瀏覽", command=browse_input_file).grid(row=1, column=2, padx=10, pady=5)

    # 輸出資料檔案路徑
    tk.Label(root, text="結果檔案 (Excel):").grid(row=2, column=0, padx=10, pady=5)
    entry_output_file_path = tk.Entry(root)
    entry_output_file_path.grid(row=2, column=1, padx=10, pady=5)
    tk.Button(root, text="瀏覽", command=browse_output_file).grid(row=2, column=2, padx=10, pady=5)

    # 執行按鈕
    tk.Button(root, text="分析資料", command=run).grid(row=3, column=0, columnspan=3, pady=20)

    # 啟動主循環
    root.mainloop()

# 執行GUI
if __name__ == "__main__":
    create_gui()
