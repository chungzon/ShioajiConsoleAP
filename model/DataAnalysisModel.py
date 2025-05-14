import pymssql
import pandas as pd
from tkinter import messagebox
from model.SelectStockModel import SelectStockModel
from common.Math import Math
from datetime import datetime

class DataAnalysisModel(SelectStockModel):
  
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
        
    
    # 定義函數找出每個波段的最高價和最低價，並計算特定比例的價格
    def find_peaks_troughs_v34(self, df):
        segments = []
        ratios = [0.618, 1]
        ratio_columns = [f'Ratio_{ratio}' for ratio in ratios]
    
        i = 0
        while i < len(df):
            max_value = df['high_price'].iloc[i]
            max_date = df['date'].iloc[i]
        
            j = i + 1
            while j < len(df) and df['high_price'].iloc[j] >= max_value:
                max_value = df['high_price'].iloc[j]
                max_date = df['date'].iloc[j]
                j += 1
        
            if j < len(df):
                min_value = df['low_price'].iloc[j]
                min_date = df['date'].iloc[j]
            else:
                min_value = df['low_price'].iloc[j-1]
                min_date = df['date'].iloc[j-1]
        
            k = j
            while k < len(df) and df['low_price'].iloc[k] <= min_value:
                min_value = df['low_price'].iloc[k]
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
    
    # 取得日期的下一個交易日開盤價格
    def get_next_open_price_date(self, stock_code, date):
        # 取得下一個交易日
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # 查詢下一個交易日的開盤價格
            query = """
                SELECT TOP 1 date, open_price
                FROM stock_data
                WHERE stock_id = %s AND date > %s
                ORDER BY date ASC
            """
            cursor.execute(query, (stock_code, date))
            result = cursor.fetchone()
            
            if result:
                return {
                    'date': result[0],
                    'open_price': result[1]
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error in get_next_open_price_date: {e}")
            return None
            
        finally:
            cursor.close()
            conn.close()
    
    # 從資料庫中獲取每日收盤價
    # def get_daily_close_prices_from_db(self, stock_code, days):
    #     conn = self.connect_db()
    #     query = f"""
    #     SELECT ts AS date, close_price
    #     FROM (
    #         SELECT *,
    #                ROW_NUMBER() OVER (PARTITION BY CONVERT(date, ts) ORDER BY ts DESC) AS rn
    #         FROM KBars
    #         WHERE stock_id = '{stock_code}'
    #     ) AS sub
    #     WHERE sub.rn = 1
    #     ORDER BY date DESC
    #     OFFSET 0 ROWS
    #     FETCH NEXT {days + 365} ROWS ONLY
    #     """
    #     df = pd.read_sql(query, conn)
    #     df['date'] = pd.to_datetime(df['date'])
    #     df.set_index('date', inplace=True)
    #     df = df.sort_index()  # 按日期排序
    #     return df['close_price']
    
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
    

    def get_stock_data_from_all_wave_extremes(self, stock_id, start_date, end_date, recent_start_date, recent_end_date):
        stock_data_df = self.get_stock_data(stock_id, start_date, end_date)
        if stock_data_df is not None and not stock_data_df.empty:
            latest_close_price = self.get_latest_close_price(stock_id)
            # 取得stock_data_df中，date等於end_date的資料
            latest_close_price_date = stock_data_df[stock_data_df['date'] == pd.to_datetime(end_date)]
            latest_close_price_by_date = None
            if latest_close_price_date.empty:
                latest_close_price_by_date = None;
            else:
                latest_close_price_by_date = latest_close_price_date['close_price'].iloc[-1]
            
            # latest_close_price = stock_data_df['close_price'].iloc[-1]
            wave_extremes_df = self.find_peaks_troughs_v34_small(stock_id, stock_data_df, latest_close_price, recent_end_date)
            if wave_extremes_df is not None and not wave_extremes_df.empty:
                wave_extremes_df['stock_id'] = stock_id  # 加入股票代號
                wave_extremes_df['name'] = self.get_stock_name(stock_id)
                recent_segment, highest_segment = self.evaluate_segment(wave_extremes_df, recent_start_date, recent_end_date)
                recent_data_df = self.get_stock_data(stock_id, recent_start_date, recent_end_date)
                recent_segments = self.find_peaks_troughs_v34_small(stock_id, recent_data_df, latest_close_price, recent_end_date)
                if not recent_segments.empty:
                    recent_segment = recent_segments.iloc[-1]
                else:
                    return
                max_value_of_all_waves = wave_extremes_df['Max_Value'].max()
                max_value_index = wave_extremes_df['Max_Value'].idxmax()

                # 獲取最高價的日期
                max_value_date = wave_extremes_df.loc[max_value_index, 'Max_Date']
                # 在最高價之後找最低價
                min_after_max_series = wave_extremes_df.loc[max_value_index:, 'Min_Value']
                min_value_after_max = min_after_max_series.min()
                # min_value_of_all_waves = wave_extremes_df['Min_Value'].min()
                min_after_max_index = min_after_max_series.idxmin()

                # 獲取最低價的日期
                min_value_date = wave_extremes_df.loc[min_after_max_index, 'Min_Date']

                # 計算 ratio_0.191、ratio_0.382、ratio_0.5、ratio_0.618、ratio_0.809、ratio_1
                ratio_0 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0)
                ratio_0191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.191)
                ratio_0382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.382)
                ratio_0500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.5)
                ratio_0809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.809)
                ratio_1191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.191)
                ratio_1382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.382)
                ratio_1500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.5)
                ratio_1618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.618)
                ratio_1809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.809)
                ratio_2 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2)
                ratio_2191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.191)
                ratio_2382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.382)
                ratio_2500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.5)
                ratio_2618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.618)
                ratio_2809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.809)
                ratio_3 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3)
                ratio_3191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.191)
                ratio_3382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.382)
                ratio_3500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.5)
                ratio_3618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.618)
                ratio_3809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.809)
                ratio_4 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4)
                ratio_4191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.191)
                ratio_4382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.382)
                ratio_4500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.5)
                ratio_4618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.618)
                ratio_4809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.809)
                ratio_5 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5)
                ratio_5191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.191)
                ratio_5382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.382)
                ratio_5500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.5)
                ratio_5618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.618)
                ratio_5809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.809)
                ratio_6 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 6)


                # 計算 ratio_0.618 和 ratio_1
                ratio_0618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.618)
                ratio_1 = Math.calculate_ratio_1(max_value_of_all_waves, min_value_after_max)

                # 計算 Head-0.618 價差比例
                head_0618_spread_ratio = round((max_value_of_all_waves - ratio_0618) / ratio_0618, 3)

                # 計算現價-0.191 價差比例
                current_0191_spread_ratio = round((latest_close_price - ratio_0191) / latest_close_price, 3)
                        
                # 計算CDP
                CDP = highest_segment['CDP']
                NH = highest_segment['NH']
                NL = highest_segment['NL']
                AH = highest_segment['AH']
                AL = highest_segment['AL']

                latest_close_prices = recent_segment['latest_close_prices']
                latest_dates = recent_segment['latest_dates']

                segment = {
                    'stock_id': stock_id,
                    'name': '',
                    'latest_close_price': latest_close_price,
                    'wave_type': [None],
                    'Max_Date': max_value_date,
                    'Min_Date': min_value_date,
                    'Max_Value': max_value_of_all_waves,
                    'Min_Value': min_value_after_max,
                    'Ratio_0': ratio_0,
                    'Ratio_0.191': ratio_0191,
                    'Ratio_0.382': ratio_0382,
                    'Ratio_0.5': ratio_0500,
                    'Ratio_0.618': ratio_0618,
                    'Ratio_0.809': ratio_0809,
                    'Ratio_1': ratio_1,
                    'Ratio_1.191': ratio_1191,
                    'Ratio_1.382': ratio_1382,
                    'Ratio_1.5': ratio_1500,
                    'Ratio_1.618': ratio_1618,
                    'Ratio_1.809': ratio_1809,
                    'Ratio_2': ratio_2,
                    'Ratio_2.191': ratio_2191,
                    'Ratio_2.382': ratio_2382,
                    'Ratio_2.5': ratio_2500,
                    'Ratio_2.618': ratio_2618,
                    'Ratio_2.809': ratio_2809,
                    'Ratio_3': ratio_3,
                    'Ratio_3.191': ratio_3191,
                    'Ratio_3.382': ratio_3382,
                    'Ratio_3.5': ratio_3500,
                    'Ratio_3.618': ratio_3618,
                    'Ratio_3.809': ratio_3809,
                    'Ratio_4': ratio_4,
                    'Ratio_4.191': ratio_4191,
                    'Ratio_4.382': ratio_4382,
                    'Ratio_4.5': ratio_4500,
                    'Ratio_4.618': ratio_4618,
                    'Ratio_4.809': ratio_4809,
                    'Ratio_5': ratio_5,
                    'Ratio_5.191': ratio_5191,
                    'Ratio_5.382': ratio_5382,
                    'Ratio_5.5': ratio_5500,
                    'Ratio_5.618': ratio_5618,
                    'Ratio_5.809': ratio_5809,
                    'Ratio_6': ratio_6,
                    'spread_ratio': head_0618_spread_ratio,
                    'latest_close_price-0.191_ratio': current_0191_spread_ratio,
                    'max_value_of_all_waves': max_value_of_all_waves,
                    'min_value_after_max': min_value_after_max,
                    'wave_type': '',
                    'CDP': CDP,
                    'NH': NH,
                    'NL': NL,
                    'AH': AH,
                    'AL': AL,
                    'latest_close_prices': latest_close_prices,
                    'latest_dates': latest_dates,
                    'sma_5': recent_segment.get('sma_5', 'N/A'),
                    'sma_10': recent_segment.get('sma_10', 'N/A'),
                    'sma_20': recent_segment.get('sma_20', 'N/A'),
                    'sma_60': recent_segment.get('sma_60', 'N/A'),
                    'sma_120': recent_segment.get('sma_120', 'N/A'),
                    'weekly_sma_5': recent_segment.get('weekly_sma_5', 'N/A'),
                    'weekly_sma_10': recent_segment.get('weekly_sma_10', 'N/A'),
                    'weekly_sma_20': recent_segment.get('weekly_sma_20', 'N/A'),
                    'weekly_sma_60': recent_segment.get('weekly_sma_60', 'N/A'),
                    'weekly_sma_120': recent_segment.get('weekly_sma_120', 'N/A'),
                    'monthly_sma_5': recent_segment.get('monthly_sma_5', 'N/A'),
                    'monthly_sma_10': recent_segment.get('monthly_sma_10', 'N/A'),
                    'monthly_sma_20': recent_segment.get('monthly_sma_20', 'N/A'),
                    'monthly_sma_60': recent_segment.get('monthly_sma_60', 'N/A'),
                    'monthly_sma_120': recent_segment.get('monthly_sma_120', 'N/A'),
                }
                gap_df = self.get_gap_stocks(stock_data_df)

                now_price = self.get_latest_close_price(stock_id)

                # 取得總波段結束日期的下一個交易日開盤價格
                next_open_price = self.get_next_open_price_date(stock_id, end_date)

                return segment, recent_segment, gap_df, now_price, latest_close_price_by_date, next_open_price # 返回總波段和最近波段

    def get_recent_segment(self, segments_df, recent_start_date, recent_end_date):
        """獲取日期區間內的最近波段"""
        # 將 Min_Date 和 Max_Date 轉換為 datetime.date 類型
        segments_df['Min_Date'] = pd.to_datetime(segments_df['Min_Date']).dt.date
        segments_df['Max_Date'] = pd.to_datetime(segments_df['Max_Date']).dt.date
        
        # 確保 recent_start_date 和 recent_end_date 也是 datetime.date 類型
        if isinstance(recent_start_date, str):
            recent_start_date = datetime.strptime(recent_start_date, '%Y-%m-%d').date()
        if isinstance(recent_end_date, str):
            recent_end_date = datetime.strptime(recent_end_date, '%Y-%m-%d').date()
        
        # 進行日期比較
        recent_segment = segments_df[
            (segments_df['Max_Date'] >= recent_start_date) & 
            (segments_df['Max_Date'] <= recent_end_date) &
            (segments_df['Min_Date'] >= recent_start_date) &
            (segments_df['Min_Date'] <= recent_end_date)
        ]
        
        if not recent_segment.empty:
            return recent_segment.iloc[-1]
        else:
            return None

    def get_highest_segment(self, segments_df):
        # 获取最高点波段数据
        if not segments_df.empty:
            max_value_idx = segments_df['Max_Value'].idxmax()  # 找到最高点波段的索引
            return segments_df.iloc[max_value_idx]
        else:
            return None
        
    def evaluate_segment(self, segments_df, recent_start_date, recent_end_date):
        recent_segment = self.get_recent_segment(segments_df, recent_start_date, recent_end_date)
        highest_segment = self.get_highest_segment(segments_df)
        
        return recent_segment, highest_segment

    # # 從資料庫取得分K資料
    # def get_1min_data(self, stock_id, stock_name):
    #     # 從資料庫取得分K資料
    #     # 將分K資料保存為CSV檔案
    #     # 將分K資料保存為JSON檔案
    #     # 將分K資料保存為XML檔案
    #     # 將分K資料保存為HTML檔案
    #     # 將分K資料保存為PDF檔案
    #     # 將分K資料保存為圖片檔案
