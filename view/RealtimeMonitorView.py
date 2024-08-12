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
            self.create_tkintertable_frame("分均線", {}).grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
            # self.create_tkintertable_frame("日均線", {}).grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
            # self.create_tkintertable_frame("周均線", {}).grid(row=4, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
            # self.create_tkintertable_frame("月均線", {}).grid(row=5, column=0, columnspan=2, sticky='nsew', padx=5, pady=5),
        ]

        # 第一個圖表
        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, self)
        self.canvas1.get_tk_widget().grid(row=1, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        
        # 第二個圖表
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self)
        self.canvas2.get_tk_widget().grid(row=3, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')

        # 均分图表和表格高度
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)

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
        
        pd = self.model.get_stock_kbar_from_db(stock_id, start_date, end_date)
        lastest_close_price = self.model.get_latest_close_price(stock_id)
        df = self.model.find_peaks_troughs_v34(pd, stock_id, lastest_close_price)
        
        if (lastest_close_price is not None):
            lastest_close_price = round(lastest_close_price, 2)
        

        # 添加排序後的欄位
        df['現價-0.618(sorted)'] = df['現價-0.618'].sort_values(ascending=True).values
        df['Head(sorted)'] = df['Head'].sort_values(ascending=True).values
        df['頸線(sorted)'] = df['頸線'].sort_values(ascending=True).values
        df['Ratio_0.618(sorted)'] = df['Ratio_0.618'].sort_values(ascending=True).values
        df['Ratio_1(sorted)'] = df['Ratio_1'].sort_values(ascending=True).values
        df['Max_Value(sorted)'] = df['Max_Value'].sort_values(ascending=True).values
        
        for col in df.columns:
            if col not in ['Ratio_0.618(sorted)', 'Ratio_1(sorted)', 'Max_Value(sorted)']:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor='center')
        
        for i, row in df.iterrows():
            self.tree.insert('', 'end', values=list(row))
        
        # 繪製第一個圖表
        self.ax1.clear()
        self.ax1.plot(df['Max_Date'], df['現價-0.618'], label='現價-0.618', linestyle='-', color='blue')
        self.ax1.scatter(df['Max_Date'], df['Head'], label='Head', color='red', marker='o')
        self.ax1.scatter(df['Max_Date'], df['頸線'], label='頸線', color='green', marker='x')
        
        for i in range(len(df)):
            self.ax1.text(df['Max_Date'][i], df['現價-0.618'][i], f'{df["Ratio_0.618"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
            self.ax1.text(df['Max_Date'][i], df['Head'][i], f'{df["Max_Value"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
            self.ax1.text(df['Max_Date'][i], df['頸線'][i], f'{df["Ratio_1"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
        
        self.ax1.set_title('Stock Trends', fontproperties=zh_font)
        self.ax1.set_xlabel('Date', fontproperties=zh_font)
        self.ax1.set_ylabel('Value', fontproperties=zh_font)
        self.ax1.legend(prop=zh_font)
        self.canvas1.draw()
        
        # 排序數據
        sorted_df = df.sort_values(by=['現價-0.618(sorted)'])
        head_sorted = df.sort_values(by=['Head(sorted)'])
        neck_sorted = df.sort_values(by=['頸線(sorted)'])

        # 繪製第二個圖表
        self.ax2.clear()
        self.ax2.plot(df['Max_Date'], df['現價-0.618(sorted)'], label='現價-0.618(sorted)', linestyle='-', color='blue')
        self.ax2.scatter(df['Max_Date'], df['Head(sorted)'], label='Head(sorted)', color='red', marker='o')
        self.ax2.scatter(df['Max_Date'], df['頸線(sorted)'], label='頸線(sorted)', color='green', marker='x')
        
        for i in range(len(df)):
            self.ax2.text(df['Max_Date'][i], df['現價-0.618(sorted)'][i], f'{sorted_df["Ratio_0.618(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
            self.ax2.text(df['Max_Date'][i], df['Head(sorted)'][i], f'{head_sorted["Max_Value(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
            self.ax2.text(df['Max_Date'][i], df['頸線(sorted)'][i], f'{neck_sorted["Ratio_1(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
        
        self.ax2.set_title('Sorted Stock Trends', fontproperties=zh_font)
        self.ax2.set_xlabel('Date', fontproperties=zh_font)
        self.ax2.set_ylabel('Value', fontproperties=zh_font)
        self.ax2.legend(prop=zh_font)
        self.canvas2.draw()
        
        # 更新下方表格的数据
        # 分均線
        sma3 = round(self.model.calculate_moving_average(pd['Close_Price'], 3).iloc[-1], 2)
        sma5 = round(self.model.calculate_moving_average(pd['Close_Price'], 5).iloc[-1], 2)
        sma7 = round(self.model.calculate_moving_average(pd['Close_Price'], 7).iloc[-1], 2)
        sma10 = round(self.model.calculate_moving_average(pd['Close_Price'], 10).iloc[-1], 2)
        sma20 = round(self.model.calculate_moving_average(pd['Close_Price'], 20).iloc[-1], 2)
        
        if df['Ratio_0.618'] is not None and df['Ratio_0.618'] is not empty:
            last_ratio_0_618 = round(df['Ratio_0.618'].iloc[-1], 2)
        else:
            last_ratio_0_618 = 'NA'

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
         
        if sma7 < lastest_close_price:
            sma7_singal_1 = 'O'
        else:
            sma7_singal_1 = 'X'
            
        if sma7 < last_ratio_0_618:
            sma7_singal_2 = 'O'
        else:
            sma7_singal_2 = 'X'
            
        if sma10 < lastest_close_price:
            sma10_singal_1 = 'O'
        else:
            sma10_singal_1 = 'X'
            
        if sma10 < last_ratio_0_618:
            sma10_singal_2 = 'O'
        else:
            sma10_singal_2 = 'X'
        
        if sma20 < lastest_close_price:
            sma20_singal_1 = 'O'
        else:
            sma20_singal_1 = 'X'
            
        if sma20 < last_ratio_0_618:
            sma20_singal_2 = 'O'
        else:
            sma20_singal_2 = 'X'
        
        self.update_tkintertable_data("分均線", {
            'SMA3': {'指標':'SMA3', '價格': str(sma3), '收': str(lastest_close_price), '訊號1': sma3_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma3_singal_2},
            'SMA5': {'指標':'SMA5', '價格':str(sma5), '收': str(lastest_close_price), '訊號1': sma5_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma5_singal_2},
            'SMA7': {'指標':'SMA7', '價格': str(sma7), '收': str(lastest_close_price), '訊號1': sma7_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma7_singal_2},
            'SMA10': {'指標':'SMA10', '價格': str(sma10), '收': str(lastest_close_price), '訊號1': sma10_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma10_singal_2},
            'SMA20': {'指標':'SMA20', '價格': str(sma20), '收': str(lastest_close_price), '訊號1': sma20_singal_1, '買點': str(last_ratio_0_618), '訊號2': sma20_singal_2},
        })
        
        if sma3 < lastest_close_price:
            self.table.model.setColorAt(0, 3, 'green',  key='bg')
        elif sma3 >= lastest_close_price:
            self.table.model.setColorAt(0, 3, 'red',  key='bg')
        else:
            self.table.model.setColorAt(0, 3, 'white',  key='bg')
            
        if sma3 < last_ratio_0_618:
            self.table.model.setColorAt(0, 5, 'green',  key='bg')
        elif sma3 >= last_ratio_0_618:
            self.table.model.setColorAt(0, 5, 'red',  key='bg')
        else:
            self.table.model.setColorAt(0, 5, 'white',  key='bg')
            
        if sma5 < lastest_close_price:
            self.table.model.setColorAt(1, 3, 'green',  key='bg')
        elif sma5 >= lastest_close_price:
            self.table.model.setColorAt(1, 3, 'red',  key='bg')
        else:
            self.table.model.setColorAt(1, 3, 'white',  key='bg')
            
        if sma5 < last_ratio_0_618:
            self.table.model.setColorAt(1, 5, 'green',  key='bg')
        elif sma5 >= last_ratio_0_618:
            self.table.model.setColorAt(1, 5, 'red',  key='bg')
        else:
            self.table.model.setColorAt(1, 5, 'white',  key='bg')
            
        if sma7 < lastest_close_price:
            self.table.model.setColorAt(2, 3, 'green',  key='bg')
        elif sma7 >= lastest_close_price:
            self.table.model.setColorAt(2, 3, 'red',  key='bg')
        else:
            self.table.model.setColorAt(2, 3, 'white',  key='bg')
            
        if sma7 < last_ratio_0_618:
            self.table.model.setColorAt(2, 5, 'green',  key='bg')
        elif sma7 >= last_ratio_0_618:
            self.table.model.setColorAt(2, 5, 'red',  key='bg')
        else:
            self.table.model.setColorAt(2, 5, 'white',  key='bg')
            
        if sma10 < lastest_close_price:
            self.table.model.setColorAt(3, 3, 'green',  key='bg')
        elif sma10 >= lastest_close_price:
            self.table.model.setColorAt(3, 3, 'red',  key='bg')
        else:
            self.table.model.setColorAt(3, 3, 'white',  key='bg')
            
        if sma10 < last_ratio_0_618:
            self.table.model.setColorAt(3, 5, 'green',  key='bg')
        elif sma10 >= last_ratio_0_618:
            self.table.model.setColorAt(3, 5, 'red',  key='bg')
        else:
            self.table.model.setColorAt(3, 5, 'white',  key='bg')
            
        if sma20 < lastest_close_price:
            self.table.model.setColorAt(4, 3, 'green',  key='bg')
        elif sma20 >= lastest_close_price:
            self.table.model.setColorAt(4, 3, 'red',  key='bg')
        else:
            self.table.model.setColorAt(4, 3, 'white',  key='bg')
            
        if sma20 < last_ratio_0_618:
            self.table.model.setColorAt(4, 5, 'green',  key='bg')
        elif sma20 >= last_ratio_0_618:
            self.table.model.setColorAt(4, 5, 'red',  key='bg')
        else:
            self.table.model.setColorAt(4, 5, 'white',  key='bg')
            
        self.table.redrawTable()
        # self.update_tkintertable_data("日均線", {
        #     'SMA5': {'指標':'SMA5', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA10': {'指標':'SMA10', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA20': {'指標':'SMA20', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA60': {'指標':'SMA60', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA120': {'指標':'SMA120', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        # })
        # self.update_tkintertable_data("周均線", {
        #     'SMA5': {'指標':'SMA5', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA10': {'指標':'SMA10', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA20': {'指標':'SMA20', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA60': {'指標':'SMA60', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA120': {'指標':'SMA120', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        # })
        # self.update_tkintertable_data("月均線", {
        #     'SMA5': {'指標':'SMA5', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA10': {'指標':'SMA10', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA20': {'指標':'SMA20', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA60': {'指標':'SMA60', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        #     'SMA120': {'指標':'SMA120', '價格': '31.82', '收': '34.5', '訊號1': 'O', '買點': '36.54', '訊號2': 'O'},
        # })


    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
        
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        
        tv.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))

