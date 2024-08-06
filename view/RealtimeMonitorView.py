import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pymssql
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta
from matplotlib import font_manager

font_path = 'C:/Windows/Fonts/msjh.ttc'  # 微軟正黑體字體路徑
zh_font = font_manager.FontProperties(fname=font_path)

class RealtimeMonitorView(tk.Frame):
    def __init__(self, parent, controller, model):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.model = model
        self.init_ui()

    def init_ui(self):
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

        # 第一個圖表
        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, self)
        self.canvas1.get_tk_widget().grid(row=1, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')
        
        # 第二個圖表
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self)
        self.canvas2.get_tk_widget().grid(row=3, column=2, rowspan=2, padx=10, pady=10, sticky='nsew')

    def print_message(self):
        stock_id = "2618"
        start_date = '2024-03-29'
        end_date = '2024-03-29'
        
        pd = self.model.get_stock_kbar_from_db(stock_id, start_date, end_date)
        df = self.model.find_peaks_troughs_v34(pd, stock_id)
        
        # 添加排序後的欄位
        df['現價-0.618(sorted)'] = df['現價-0.618'].sort_values(ascending=True).values
        df['Head(sorted)'] = df['Head'].sort_values(ascending=True).values
        df['頸線(sorted)'] = df['頸線'].sort_values(ascending=True).values
        df['Ratio_0.618(sorted)'] = df['Ratio_0.618'].sort_values(ascending=True).values
        df['Ratio_1(sorted)'] = df['Ratio_1'].sort_values(ascending=True).values
        df['Max_Value(sorted)'] = df['Max_Value'].sort_values(ascending=True).values
        
        for col in df.columns:
            if col is not 'Ratio_0.618(sorted)' and col is not 'Ratio_1(sorted)' and col is not 'Max_Value(sorted)':
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor='center')
        
        for i, row in df.iterrows():
            self.tree.insert('', 'end', values=list(row))
        
        # 繪製第一個圖表
        self.ax1.clear()
        self.ax1.plot(df['Max_Date'], df['現價-0.618'], label='現價-0.618', linestyle='-')
        self.ax1.scatter(df['Max_Date'], df['Head'], label='Head', color='red', marker='o')
        self.ax1.scatter(df['Max_Date'], df['頸線'], label='頸線', color='blue', marker='x')
        
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
        # sorted_df = df.sort_values(by=['現價-0.618(sorted)'])
        
        # 繪製第二個圖表
        self.ax2.clear()
        self.ax2.plot(df['Max_Date'], df['現價-0.618(sorted)'], label='現價-0.618(sorted)', linestyle='-')
        self.ax2.scatter(df['Max_Date'], df['Head(sorted)'], label='Head(sorted)', color='red', marker='o')
        self.ax2.scatter(df['Max_Date'], df['頸線(sorted)'], label='頸線(sorted)', color='blue', marker='x')
        
        for i in range(len(df)):
            self.ax2.text(df['Max_Date'][i], df['現價-0.618(sorted)'][i], f'{df["現價-0.618(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
            self.ax2.text(df['Max_Date'][i], df['Head(sorted)'][i], f'{df["Head(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
            self.ax2.text(df['Max_Date'][i], df['頸線(sorted)'][i], f'{df["頸線(sorted)"][i]:.2f}', ha='center', va='bottom', fontproperties=zh_font)
        
        self.ax2.set_title('Sorted Stock Trends', fontproperties=zh_font)
        self.ax2.set_xlabel('Date', fontproperties=zh_font)
        self.ax2.set_ylabel('Value', fontproperties=zh_font)
        self.ax2.legend(prop=zh_font)
        self.canvas2.draw()

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
        
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        
        tv.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))
