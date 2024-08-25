import pymssql
import pandas as pd
from tkinter import messagebox

class DataAnalysisModel:
  
    def __init__(self, api):
        self.api = api
        
    def connect_db(self):
        conn = pymssql.connect(
            server='127.0.0.1:1433',
            user='TSE_USER',
            password='fuckme',
            database='TSE'
        )
        return conn

    def get_latest_dates(self, stock_id):
        conn = self.connect_db()
        query = f"""
        SELECT 
            (SELECT MAX(ts) FROM Ticks WHERE stock_id = '{stock_id}') AS latest_date_ticks,
            (SELECT MAX(ts) FROM Kbars WHERE stock_id = '{stock_id}') AS latest_date_kbars
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.iloc[0]['latest_date_ticks'], df.iloc[0]['latest_date_kbars']

    def get_kbars_data(self, stock_id, date):
        contract = self.api.Contracts.Stocks[stock_id]
        kbars = self.api.kbars(
            contract=contract,
            start=date.strftime("%Y-%m-%d"),
            end=date.strftime("%Y-%m-%d")
        )
        df = pd.DataFrame({**kbars})
        df.ts = pd.to_datetime(df.ts)  # 將時間戳轉換為datetime
        return df

    def insert_kbars(self, kbars_df, stock_id):
        conn = self.connect_db()
        cursor = conn.cursor()
        for _, row in kbars_df.iterrows():
            cursor.execute("""
                INSERT INTO Kbars (stock_id, ts, open_price, high, low, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (stock_id, row['ts'], row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
        conn.commit()
        cursor.close()
        conn.close()
        
    def get_stock_data_from_db(self, stock_id, start_date, end_date):
        conn = self.connect_db()
        query = f"""
        SELECT ts, Open_Price, High, Low, Close_Price, Volume
        FROM Kbars
        WHERE stock_id = {stock_id} AND ts >= '{start_date}' AND ts <= DATEADD(day, 1, '{end_date}')
        """
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts'])
        df['date'] = df['ts'].dt.date
        conn.close()
        return df
    
    # 定義函數找出每個波段的最高價和最低價，並計算特定比例的價格
    def find_peaks_troughs_v34(self, df):
        segments = []
        ratios = [0.618, 1]
        ratio_columns = [f'Ratio_{ratio}' for ratio in ratios]
    
        i = 0
        while i < len(df):
            max_value = df['High'].iloc[i]
            max_date = df['date'].iloc[i]
        
            j = i + 1
            while j < len(df) and df['High'].iloc[j] >= max_value:
                max_value = df['High'].iloc[j]
                max_date = df['date'].iloc[j]
                j += 1
        
            if j < len(df):
                min_value = df['Low'].iloc[j]
                min_date = df['date'].iloc[j]
            else:
                min_value = df['Low'].iloc[j-1]
                min_date = df['date'].iloc[j-1]
        
            k = j
            while k < len(df) and df['Low'].iloc[k] <= min_value:
                min_value = df['Low'].iloc[k]
                min_date = df['date'].iloc[k]
                k += 1
        
            if max_value > min_value:
                segment = [max_date, max_value, min_date, min_value]
                for ratio in ratios:
                    segment.append((max_value - min_value) / 2 * ratio + min_value)
                segments.append(segment)
        
            i = k
    
        return pd.DataFrame(segments, columns=['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value'] + ratio_columns)
    
    # 獲取最新收盤價
    def get_latest_close_price(self, stock_code):
        contract = self.api.Contracts.Stocks[stock_code]
        snapshot = self.api.snapshots([contract])
        latest_close = snapshot[0].close
        return latest_close
    
    # 從資料庫中獲取每日收盤價
    def get_daily_close_prices_from_db(self, stock_code, days):
        conn = self.connect_db()
        query = f"""
        SELECT ts AS date, close_price
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY CONVERT(date, ts) ORDER BY ts DESC) AS rn
            FROM KBars
            WHERE stock_id = '{stock_code}'
        ) AS sub
        WHERE sub.rn = 1
        ORDER BY date DESC
        OFFSET 0 ROWS
        FETCH NEXT {days + 365} ROWS ONLY
        """
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.sort_index()  # 按日期排序
        return df['close_price']
    
    # 計算移動平均
    def calculate_moving_average(self, prices, window):
        return prices.rolling(window=window).mean()

    # 計算周均線
    def calculate_weekly_average(self, prices, window):
        weekly_prices = prices.resample('W').last()
        return self.calculate_moving_average(weekly_prices, window)

    # 計算月均線
    def calculate_monthly_average(self, prices, window):
        monthly_prices = prices.resample('M').last()
        return self.calculate_moving_average(monthly_prices, window)

    # 儲存資料到Excel
    def save_to_excel(self, peak_trough_df, sma_values, weekly_sma_values, monthly_sma_values, last_ratio_0_618, latest_close_price, output_file_path):
        with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet("Peaks_and_Troughs")
            percent_fmt = workbook.add_format({'num_format': '0.00%'})

            # 儲存波段資料
            peak_trough_df.to_excel(writer, sheet_name='Peaks_and_Troughs', index=False, startrow=0)

            # 確定開始寫入日均線的行數
            start_row = len(peak_trough_df) + 5
        
            worksheet.write(start_row - 1, 0, latest_close_price)

            # 設定日均線表格標題
            headers = ["日均線", "", "", "", "收", "買點", "", "", "", "日均線"]
            worksheet.write_row(start_row, 0, headers)

            # 合併第5欄位和第6欄位的第1列和第2列資料格
            worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
            worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")
        
            #在日均線表格填入收盤價和買點價
            worksheet.write(start_row + 1, 4, latest_close_price)       
            worksheet.write(start_row + 1, 5, last_ratio_0_618)
        
            #買點價-收盤價
            diff_price = last_ratio_0_618 - latest_close_price

            # 合併第5欄位和第6欄位的第3列資料格
            worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")

            #填入日均線(買點價-收盤價)
            worksheet.write(start_row + 3, 4, diff_price)
        
            #計算(買點價-收盤價)/收盤價
            radio_diff_price = diff_price / latest_close_price
        
            # 合併第5欄位和第6欄位的第4列資料格
            worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
        
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)

            # 設定第一欄和第十欄的資料
            sma_labels = ["SMA5", "SMA10", "SMA20", "SMA60", "SMA120"]
            for i, label in enumerate(sma_labels):
                worksheet.write(start_row + i + 1, 0, label)
                worksheet.write(start_row + i + 1, 9, label)

            cell_green_format = workbook.add_format()
            cell_green_format.set_pattern(1)
            cell_green_format.set_bg_color('green')
            cell_red_format = workbook.add_format()
            cell_red_format.set_pattern(1)
            cell_red_format.set_bg_color('red')
            # 填入日均線計算值
            for i, value in enumerate(sma_values):
                worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
                worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
                if not pd.isna(value):
                    if latest_close_price > value:
                        worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
                    if  last_ratio_0_618 > value:
                        worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
                else:
                    print("")
            
            
            #填入數值分析
            if not pd.isna(sma_values[-1]):
                last_daily_sma120 = sma_values[-1]
                diff_last_daily_sma120 = (last_daily_sma120 - latest_close_price).round(2)
                radio_last_dailly_sma120 = (diff_last_daily_sma120 / latest_close_price).round(2)
                diff_sma_120_label = ["(", f"{diff_last_daily_sma120:.2f}", ", ", f"{radio_last_dailly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
                diff_last_daily_sma120 = (last_ratio_0_618 - last_daily_sma120).round(2)
                radio_last_dailly_sma120 = (diff_last_daily_sma120 / last_ratio_0_618).round(2)
                diff_sma_120_label = ["(", f"{diff_last_daily_sma120:.2f}", ", ", f"{radio_last_dailly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
            else:
                print("")   

            # 插入一行空行
            start_row += len(sma_labels) + 3
            worksheet.write_row(start_row, 0, [""] * len(headers))
            start_row += 1

            # 插入周均線表格
            headers = ["月均線", "", "", "", "收", "買點", "", "", "", "月均線"]
            worksheet.write_row(start_row, 0, headers)

            # 合併第5欄位和第6欄位的第1列和第2列資料格
            worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
            worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")

            worksheet.write(start_row + 1, 4, latest_close_price)       
            worksheet.write(start_row + 1, 5, last_ratio_0_618)

            # 合併第5欄位和第6欄位的第3列資料格
            worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
            #填入周均線(買點價-收盤價)
            worksheet.write(start_row + 3, 4, diff_price)
        
            # 合併第5欄位和第6欄位的第4列資料格
            worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
               
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)
        
            # 設定第一欄和第十欄的資料
            weekly_sma_labels = ["周SMA5", "周SMA10", "周SMA20", "周SMA60", "周SMA120"]
            for i, label in enumerate(weekly_sma_labels):
                worksheet.write(start_row + i + 1, 0, label)
                worksheet.write(start_row + i + 1, 9, label)

            # 填入周均線計算值
            for i, value in enumerate(weekly_sma_values):
                worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
                worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
                if not pd.isna(value):
                    if latest_close_price > value:
                        worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
                    if  last_ratio_0_618 > value:
                        worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
                else:
                    print("")
            
            #填入數值分析
            if not pd.isna(weekly_sma_values[-1]):
                last_weekly_sma120 = weekly_sma_values[-1]
                diff_last_weekly_sma120 = (last_weekly_sma120 - latest_close_price).round(2)
                radio_last_weekly_sma120 = (diff_last_weekly_sma120 / latest_close_price).round(2)
                diff_sma_120_label = ["(", f"{diff_last_weekly_sma120:.2f}", ", ", f"{radio_last_weekly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
                diff_last_weekly_sma120 = (last_ratio_0_618 - last_weekly_sma120).round(2)
                radio_last_weekly_sma120 = (diff_last_weekly_sma120 / last_ratio_0_618).round(2)
                diff_sma_120_label = ["(", f"{diff_last_weekly_sma120:.2f}", ", ", f"{radio_last_weekly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
            else:
                print("")

            # 插入一行空行
            start_row += len(weekly_sma_labels) + 2
            worksheet.write_row(start_row, 0, [""] * len(headers))
            start_row += 1

            # 插入月均線表格
            headers = ["月均線", "", "", "", "收", "買點", "", "", "", "月均線"]
            worksheet.write_row(start_row, 0, headers)

            # 合併第5欄位和第6欄位的第1列和第2列資料格
            worksheet.merge_range(start_row + 1, 4, start_row + 2, 4, "")
            worksheet.merge_range(start_row + 1, 5, start_row + 2, 5, "")
        
            worksheet.write(start_row + 1, 4, latest_close_price)       
            worksheet.write(start_row + 1, 5, last_ratio_0_618)

            # 合併第5欄位和第6欄位的第3列資料格
            worksheet.merge_range(start_row + 3, 4, start_row + 3, 5, "")
        
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 3, 4, diff_price)
        
            # 合併第5欄位和第6欄位的第4列資料格
            worksheet.merge_range(start_row + 4, 4, start_row + 4, 5, "")
        
            #填入(買點價-收盤價)/收盤價
            worksheet.write(start_row + 4, 4, radio_diff_price, percent_fmt)

            # 設定第一欄和第十欄的資料
            monthly_sma_labels = ["月SMA5", "月SMA10", "月SMA20", "月SMA60", "月SMA120"]
            for i, label in enumerate(monthly_sma_labels):
                worksheet.write(start_row + i + 1, 0, label)
                worksheet.write(start_row + i + 1, 9, label)

            # 填入月均線計算值
            for i, value in enumerate(monthly_sma_values):
                worksheet.write(start_row + i + 1, 2, value if not pd.isna(value) else "NaN")
                worksheet.write(start_row + i + 1, 7, value if not pd.isna(value) else "NaN")
                if not pd.isna(value):
                    if latest_close_price > value:
                        worksheet.write(start_row + i + 1, 1, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 1, "X", cell_red_format)
                    if  last_ratio_0_618 > value:
                        worksheet.write(start_row + i + 1, 8, "O", cell_green_format)
                    else:
                        worksheet.write(start_row + i + 1, 8, "X", cell_red_format)
                else:
                    print("")
            
            #填入數值分析
            if not pd.isna(monthly_sma_values[-1]):
                last_monthly_sma120 = monthly_sma_values[-1]
                diff_last_monthly_sma120 = (last_monthly_sma120 - latest_close_price).round(2)
                radio_last_monthly_sma120 = (diff_last_monthly_sma120 / latest_close_price).round(2)
                diff_sma_120_label = ["(", f"{diff_last_monthly_sma120:.2f}", ", ", f"{radio_last_monthly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 3, *diff_sma_120_label)
                diff_last_monthly_sma120 = (last_ratio_0_618 - last_monthly_sma120).round(2)
                radio_last_monthly_sma120 = (diff_last_monthly_sma120 / last_ratio_0_618).round(2)
                diff_sma_120_label = ["(", f"{diff_last_monthly_sma120:.2f}", ", ", f"{radio_last_monthly_sma120:0.00%}", ")"]
                worksheet.write_rich_string(start_row + 5, 6, *diff_sma_120_label)
            else:
                print("")
            
         # 設定數字格式
            num_format = workbook.add_format({'num_format': '0.00'})

            # 依列應用格式
            for col_num, col_name in enumerate(peak_trough_df.columns):
                if col_name not in ['Max_Date', 'Min_Date']:
                    worksheet.set_column(col_num, col_num, 12, num_format)

            # 新增折線圖和散佈圖
            line_chart1 = workbook.add_chart({'type': 'line'})
            scatter_chart1 = workbook.add_chart({'type': 'scatter'})
            line_chart2 = workbook.add_chart({'type': 'line'})
            scatter_chart2 = workbook.add_chart({'type': 'scatter'})

            # 設定圖表資料範圍
            max_row = len(peak_trough_df) + 1

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
                    'custom': custom_labels_P,
                    'position': 'below'
                }  # 添加自定義數值標籤
            })
            scatter_chart1.add_series({
                'name': 'Head_Sort',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$M$2:$M${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_N,
                    'position': 'above'
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
            worksheet.insert_chart('S2', line_chart1)
        
            # custom_labels using E column data
            custom_labels_E = [
                {'value': f"='Peaks_and_Troughs'!$F${i}", 'font': {'color': 'blue'}, 'position': 'below'} for i in range(2, max_row)
            ]
        
            # custom_labels using B column data
            custom_labels_B = [
                {'value': f"='Peaks_and_Troughs'!$C${i}", 'font': {'color': 'red'}, 'position': 'above'} for i in range(2, max_row)
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
                    'custom': custom_labels_E,
                    'position': 'below'
                }
            })
            scatter_chart2.add_series({
                'name': 'Head',
                'categories': f"='Peaks_and_Troughs'!$A$2:$A${max_row}",
                'values': f"='Peaks_and_Troughs'!$J$2:$J${max_row}",
                'marker': {'type': 'circle', 'size': 6},
                'data_labels': {
                    'value': True,
                    'custom': custom_labels_B,
                    'position': 'above'
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
        
            line_chart1.set_x_axis({'num_format': ' ', 'line': {'color': 'red', 'width': 1.5}})
            line_chart2.set_x_axis({'num_format': ' ', 'line': {'color': 'red', 'width': 1.5}})

            # 插入第二張圖表到工作表
            line_chart2.combine(scatter_chart2)
            worksheet.insert_chart('S20', line_chart2)

        messagebox.showinfo("完成", f"波段資料及均線資料已儲存到: {output_file_path}")
        
    # Stock(
    # exchange=<Exchange.TSE: 'TSE'>, 
    # code='2890', 
    # symbol='TSE2890', 
    # name='永豐金', 
    # category='17', 
    # unit=1000, 
    # limit_up=19.1, 
    # limit_down=15.7, 
    # reference=17.4, 
    # update_date='2023/01/17', 
    # day_trade=<DayTrade.Yes: 'Yes'>
    # )
    def get_stock_name(self, sotckid):
        contract = self.api.Contracts.Stocks[sotckid]
        return contract['name']
    


