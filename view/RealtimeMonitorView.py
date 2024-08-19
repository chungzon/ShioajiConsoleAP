import tkinter as tk
from tkinter import ttk
from numpy import empty
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pymssql
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta
from matplotlib import font_manager
from tkintertable import TableCanvas, TableModel
import threading

font_path = 'C:/Windows/Fonts/msjh.ttc'  # 微軟正黑體字體路徑
zh_font = font_manager.FontProperties(fname=font_path)

class RealtimeMonitorView(tk.Frame):
    def __init__(self, parent, controller, model):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.model = model
        self.init_ui()

    def init_ui(self):
        # 左側主表格
        self.tree = ttk.Treeview(self, columns=['Max_Date', 'Max_Value', 'Min_Date', 'Min_Value', 'Ratio_0.618', '現價-0.618', 'Ratio_1', '頸線', 'Head', '現價-0.618(sorted)', 'Head(sorted)', '頸線(sorted)'], show='headings')
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(self.tree, _col, False))

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=1, column=0, sticky='nsew')
        vsb.grid(row=1, column=1, sticky='ns')
        hsb.grid(row=2, column=0, sticky='ew')
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        ttk.Button(self, text="分析資料", command=self.print_message).grid(row=0, column=0, columnspan=3, pady=20)

        # 使用 tkintertable 初始化下方表格，但暂时不填充数据
        self.table_frames = [
            self.create_tkintertable_frame("分均線", {}).grid(row=2, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
            self.create_tkintertable_frame("一分K均線", {}).grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
            self.create_tkintertable_frame("三分K均線", {}).grid(row=4, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
            self.create_tkintertable_frame("五分K均線", {}).grid(row=5, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
        ]

        # 第一個圖表
        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, self)
        self.canvas1.get_tk_widget().grid(row=0, column=2, rowspan=3, padx=10, pady=10, sticky='nsew')
        
        # 第二個圖表
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self)
        self.canvas2.get_tk_widget().grid(row=4, column=2, rowspan=3, padx=10, pady=10, sticky='nsew')

        # 均分图表和表格高度
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(6, weight=1)

    def create_tkintertable_frame(self, title, data):
        frame = ttk.LabelFrame(self, text=title)
        model = TableModel()
        self.table = TableCanvas(frame, model=model, editable=False)
        self.table.show()
        self.__dict__[title] = self.table  # 存储表格对象，以便稍后更新数据
        return frame

    def update_tkintertable_data(self, title, data):
        table = self.__dict__[title]
        model = table.model
        model.deleteRows()  # 清空之前的数据
        model.importDict(data)  # 导入新的数据
        table.redraw()

    def print_message(self):
        stock_id = "2618"
        start_date = '2024-03-29'
        end_date = '2024-03-29'
        
        sim_pd = self.model.get_stock_kbar_from_db(stock_id, start_date, end_date) #讀取模擬資料KBar
        
        #lastest_close_price = self.model.get_latest_close_price(stock_id)
        #當有新的一筆分K資料，重新計算數據，更新圖表和表格
        self.process_data(sim_pd, stock_id)

    def process_data(self, sim_pd, stock_id):
        def update_ui():
            self.pd = pd.DataFrame(columns=['ts', 'Open_Price', 'High', 'Low', 'Close_Price', 'Volume', 'id', 'stock_id'])

            for index, data in sim_pd.iterrows():
                data_dict = data.to_dict()
                # 使用 from_records 方法创建 DataFrame
                new_row = pd.DataFrame.from_records([data_dict])
                self.pd = pd.concat([self.pd, new_row], ignore_index=True)
                self.df = self.model.find_peaks_troughs_v34(self.pd, stock_id, data['Close_Price'])
        
                # 添加排序後的欄位
                self.df['現價-0.618(sorted)'] = self.df['現價-0.618'].sort_values(ascending=True).values
                self.df['Head(sorted)'] = self.df['Head'].sort_values(ascending=True).values
                self.df['頸線(sorted)'] = self.df['頸線'].sort_values(ascending=True).values
                self.df['Ratio_0.618(sorted)'] = self.df['Ratio_0.618'].sort_values(ascending=True).values
                self.df['Ratio_1(sorted)'] = self.df['Ratio_1'].sort_values(ascending=True).values
                self.df['Max_Value(sorted)'] = self.df['Max_Value'].sort_values(ascending=True).values

                for col in self.df.columns:
                    if col not in ['Ratio_0.618(sorted)', 'Ratio_1(sorted)', 'Max_Value(sorted)']:
                        self.tree.heading(col, text=col)
                        self.tree.column(col, width=100, anchor='center')
                        
                for item in self.tree.get_children():
                    self.tree.delete(item)

                for i, row in self.df.iterrows():
                    self.tree.insert('', 'end', values=list(row))

                # 繪製第一個圖表
                self.ax1.clear()
                self.ax1.plot(self.df['Max_Date'], self.df['現價-0.618'], label='現價-0.618', linestyle='-', color='blue')
                self.ax1.scatter(self.df['Max_Date'], self.df['Head'], label='Head', color='red', marker='o')
                self.ax1.scatter(self.df['Max_Date'], self.df['頸線'], label='頸線', color='green', marker='x')

                for i in range(len(self.df)):
                    self.ax1.text(self.df['Max_Date'][i], self.df['現價-0.618'][i], f'{self.df["Ratio_0.618"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
                    self.ax1.text(self.df['Max_Date'][i], self.df['Head'][i], f'{self.df["Max_Value"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
                    self.ax1.text(self.df['Max_Date'][i], self.df['頸線'][i], f'{self.df["Ratio_1"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)

                self.ax1.set_title('Stock Trends', fontproperties=zh_font)
                self.ax1.set_xlabel('Date', fontproperties=zh_font)
                self.ax1.set_ylabel('Value', fontproperties=zh_font)
                self.ax1.legend(prop=zh_font)
                self.canvas1.draw()

                # 排序數據
                sorted_df = self.df.sort_values(by=['現價-0.618(sorted)'])
                head_sorted = self.df.sort_values(by=['Head(sorted)'])
                neck_sorted = self.df.sort_values(by=['頸線(sorted)'])

                # 繪製第二個圖表
                self.ax2.clear()
                self.ax2.plot(self.df['Max_Date'], self.df['現價-0.618(sorted)'], label='現價-0.618(sorted)', linestyle='-', color='blue')
                self.ax2.scatter(self.df['Max_Date'], self.df['Head(sorted)'], label='Head(sorted)', color='red', marker='o')
                self.ax2.scatter(self.df['Max_Date'], self.df['頸線(sorted)'], label='頸線(sorted)', color='green', marker='x')

                for i in range(len(self.df)):
                    self.ax2.text(self.df['Max_Date'][i], self.df['現價-0.618(sorted)'][i], f'{sorted_df["Ratio_0.618(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
                    self.ax2.text(self.df['Max_Date'][i], self.df['Head(sorted)'][i], f'{head_sorted["Max_Value(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
                    self.ax2.text(self.df['Max_Date'][i], self.df['頸線(sorted)'][i], f'{neck_sorted["Ratio_1(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)

                self.ax2.set_title('Sorted Stock Trends', fontproperties=zh_font)
                self.ax2.set_xlabel('Date', fontproperties=zh_font)
                self.ax2.set_ylabel('Value', fontproperties=zh_font)
                self.ax2.legend(prop=zh_font)
                self.canvas2.draw()
                
                self.table.redrawTable()
                self.init_moving_average(stock_id, data['Close_Price'])

                # 延遲1秒鐘
                time.sleep(1)

        # 啟動新執行緒來更新UI，防止卡住
        threading.Thread(target=update_ui).start()
 
    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
        
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        
        tv.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))
        
    def init_moving_average(self, stock_id, lastest_close_price):
        if (lastest_close_price is not None):
            lastest_close_price = round(lastest_close_price, 2)
        # 更新下方表格的数据
        # 分均線
        sma3 = round(self.model.calculate_moving_average(self.pd['Close_Price'], 3).iloc[-1], 2)
        sma5 = round(self.model.calculate_moving_average(self.pd['Close_Price'], 5).iloc[-1], 2)
        sma1 = round(self.model.calculate_moving_average(self.pd['Close_Price'], 1).iloc[-1], 2)
        
        if self.df['Ratio_0.618'] is not None and self.df['Ratio_0.618'] is not empty:
            last_ratio_0_618 = round(self.df['Ratio_0.618'].iloc[-1], 2)
        else:
            last_ratio_0_618 = 'NA'
                    
        if sma1 < lastest_close_price:
            sma1_singal_1 = 'O'
        else:
            sma1_singal_1 = 'X'
            
        if sma1 < last_ratio_0_618:
            sma1_singal_2 = 'O'
        else:
            sma1_singal_2 = 'X'

        if sma3 < lastest_close_price:
            sma3_singal_1 = 'O'
        else:
            sma3_singal_1 = 'X'
            
        if sma3 < last_ratio_0_618:
            sma3_singal_2 = 'O'
        else:
            sma3_singal_2 = 'X'
            
        if sma5 < lastest_close_price:
            sma5_singal_1 = 'O'
        else:
            sma5_singal_1 = 'X'
            
        if sma5 < last_ratio_0_618:
            sma5_singal_2 = 'O'
        else:
            sma5_singal_2 = 'X'
        
        self.update_tkintertable_data("分均線", {
            'SMA1': {'指標':'SMA1', '價格': str(sma1), '收': str(lastest_close_price), '訊號1': sma1_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma1_singal_2},
            'SMA3': {'指標':'SMA3', '價格': str(sma3), '收': str(lastest_close_price), '訊號1': sma3_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma3_singal_2},
            'SMA5': {'指標':'SMA5', '價格': str(sma5), '收': str(lastest_close_price), '訊號1': sma5_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma5_singal_2},
        })


        # 獲取每日收盤價
        close_prices = self.model.get_daily_close_prices_from_db(stock_id, 120)
        
        self.update_one_min_k_ma(self.pd['Close_Price'], lastest_close_price)
        self.update_three_min_k_ma(self.pd['Close_Price'], lastest_close_price)
        self.update_five_min_k_ma(self.pd['Close_Price'], lastest_close_price)
 
    def update_one_min_k_ma(self, df, lastest_close_price):
        ma_5t, ma_7t, ma_10t, ma_20t, ma_60t = self.model.calculate_ma_values(df, k_type='1min')
        lastest_ratio_0618 = round(self.df['Ratio_0.618'].iloc[-1], 2);
        self.update_tkintertable_data("一分K均線", {
            '5T': {'指標':'5T', '價格': str(ma_5t), '收': str(lastest_close_price), '訊號1': 'O' if ma_5t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_5t < lastest_ratio_0618 else 'X'},
            '7T': {'指標':'7T', '價格': str(ma_7t), '收': str(lastest_close_price), '訊號1': 'O' if ma_7t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_7t < lastest_ratio_0618 else 'X'},
            '10T': {'指標':'10T', '價格': str(ma_10t), '收': str(lastest_close_price), '訊號1': 'O' if ma_10t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_10t < lastest_ratio_0618 else 'X'},
            '20T': {'指標':'20T', '價格': str(ma_20t), '收': str(lastest_close_price), '訊號1': 'O' if ma_20t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_20t < lastest_ratio_0618 else 'X'},
            '60T': {'指標':'60T', '價格': str(ma_60t), '收': str(lastest_close_price), '訊號1': 'O' if ma_60t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_60t < lastest_ratio_0618 else 'X'},
        })

    def update_three_min_k_ma(self, df, lastest_close_price):
        ma_5t, ma_7t, ma_10t, ma_20t, ma_60t = self.model.calculate_ma_values(df, k_type='3min')
        lastest_ratio_0618 = round(self.df['Ratio_0.618'].iloc[-1], 2);
        self.update_tkintertable_data("三分K均線", {
            '5T': {'指標':'5T', '價格': str(ma_5t), '收': str(lastest_close_price), '訊號1': 'O' if ma_5t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_5t < lastest_ratio_0618 else 'X'},
            '7T': {'指標':'7T', '價格': str(ma_7t), '收': str(lastest_close_price), '訊號1': 'O' if ma_7t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_7t < lastest_ratio_0618 else 'X'},
            '10T': {'指標':'10T', '價格': str(ma_10t), '收': str(lastest_close_price), '訊號1': 'O' if ma_10t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_10t < lastest_ratio_0618 else 'X'},
            '20T': {'指標':'20T', '價格': str(ma_20t), '收': str(lastest_close_price), '訊號1': 'O' if ma_20t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_20t < lastest_ratio_0618 else 'X'},
            '60T': {'指標':'60T', '價格': str(ma_60t), '收': str(lastest_close_price), '訊號1': 'O' if ma_60t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_60t < lastest_ratio_0618 else 'X'},
        })

    def update_five_min_k_ma(self, df, lastest_close_price):
        ma_5t, ma_7t, ma_10t, ma_20t, ma_60t = self.model.calculate_ma_values(df, k_type='5min')
        lastest_ratio_0618 = round(self.df['Ratio_0.618'].iloc[-1], 2);
        self.update_tkintertable_data("五分K均線", {
            '5T': {'指標':'5T', '價格': str(ma_5t), '收': str(lastest_close_price), '訊號1': 'O' if ma_5t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_5t < lastest_ratio_0618 else 'X'},
            '7T': {'指標':'7T', '價格': str(ma_7t), '收': str(lastest_close_price), '訊號1': 'O' if ma_7t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_7t < lastest_ratio_0618 else 'X'},
            '10T': {'指標':'10T', '價格': str(ma_10t), '收': str(lastest_close_price), '訊號1': 'O' if ma_10t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_10t < lastest_ratio_0618 else 'X'},
            '20T': {'指標':'20T', '價格': str(ma_20t), '收': str(lastest_close_price), '訊號1': 'O' if ma_20t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_20t < lastest_ratio_0618 else 'X'},
            '60T': {'指標':'60T', '價格': str(ma_60t), '收': str(lastest_close_price), '訊號1': 'O' if ma_60t < lastest_close_price else 'X', '買點': str(lastest_ratio_0618), '訊號2': 'O' if ma_60t < lastest_ratio_0618 else 'X'},
        })



