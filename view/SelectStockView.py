import tkinter as tk
from tkinter import ttk, messagebox
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
import pyperclip

font_path = 'C:/Windows/Fonts/msjh.ttc'  # 微軟正黑體字體路徑
zh_font = font_manager.FontProperties(fname=font_path)

class SelectStockView(tk.Frame):
    
    def __init__(self, parent, controller, model):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.model = model
        self.init_ui()

    def init_ui(self):
        style = ttk.Style()
        style.configure('Treeview',
                           background='white')
        style.map('Treeview',
                     background=[('selected', 'blue')])
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        ttk.Label(frame, text="0618與Head價差比例").pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(frame, text="±").pack(side=tk.LEFT)
        self.ratio_entry = ttk.Entry(frame)
        self.ratio_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(frame, text="現價-0618比例").pack(side=tk.LEFT, padx=5)
        ttk.Label(frame, text="±").pack(side=tk.LEFT)
        self.ratio_entry2 = ttk.Entry(frame)
        self.ratio_entry2.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(frame, text="標的交易量前").pack(side=tk.LEFT, padx=(5,0))
        self.top_n_entry = ttk.Entry(frame, width=5)
        self.top_n_entry.insert(0, "20")  # 預設值為20
        self.top_n_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(frame, text="名").pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(frame, text="篩選", command=self.calculate).pack(side=tk.LEFT, padx=5)

        # 設置 LabelFrame 來包含 Treeview
        self.table_frame = ttk.LabelFrame(self, text="股票資訊")
        self.table_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # 定義欄位名稱
        columns = ['股票代碼', '股票名稱', '現價','波段', '買點', '頸線', 'Head', 'Max_Date', 'Max_Value', 'Min_Date', 'Min_Value', 'Head-0618價差比例', '現價-0618比例']

        # 設置 Treeview 並定義列
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        self.tree.tag_configure('Blue', background="lightblue")
        self.tree.tag_configure('White', background="white")

        # 定義每個欄位的標題和寬度
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')

        # 將 Treeview 放置在 LabelFrame 中
        self.tree.grid(row=0, column=0, sticky="nsew")

        # 綁定雙擊事件
        self.tree.bind("<Double-1>", self.on_double_click)

        # 添加垂直滾動條
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        # 添加水平滾動條
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=hsb.set)

        # 設置框架的網格配置，使其能夠隨著窗口調整大小
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
    def calculate(self):
        ratio = self.ratio_entry.get()
        ratio2 = self.ratio_entry2.get()
        top_n = self.top_n_entry.get()
        ratio2 = self.ratio_entry2.get()

        # ratio為必要 
        if ratio == '': 
            messagebox.showerror("錯誤", "請輸入ratio")
            return
        # ratio2為選填
        if ratio2 == '':
            ratio2 = 0

        # 清空 TreeView 中的現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        all_wave_extremes = self.controller.calculate(ratio, ratio2, top_n)
        
        for index, segment in enumerate(all_wave_extremes):
            stock_id = segment['stock_id']  # 假設 stock_id 已在 segments 中
            stock_name = segment['name'] # 股票名稱
            latest_close_price = segment['latest_close_price']
            wave_type = segment['wave_type']
            max_date = segment['Max_Date']
            min_date = segment['Min_Date']
            max_value = segment['Max_Value']
            min_value = segment['Min_Value']
            ratio_0618 = round(segment['Ratio_0.618'], 2)  # 買點
            ratio_1 = round(segment['Ratio_1'], 2) # 頸線
            spread_ratio = round(segment['spread_ratio'], 2)  # 價差比例
            ratio_0618_ratio = round(segment['latest_close_price-0.618_ratio'], 2)
            tag = 'Blue' if (index // 2) % 2 == 0 else 'White'
            self.tree.insert('', 'end', values=(stock_id, stock_name, latest_close_price, wave_type, ratio_0618, ratio_1, max_value, max_date, max_value, min_date, min_value, spread_ratio, ratio_0618_ratio), tags=(tag)) 


    def show_error(self, message):
        messagebox.showerror("錯誤", message)

    def on_double_click(self, event):
        item = self.tree.selection()[0]  # 獲取選中的項目
        stock_code = self.tree.item(item, "values")[0]  # 獲取第一列（股票代碼）
        pyperclip.copy(stock_code)  # 複製到剪貼板
        self.show_copy_message(stock_code)

    def show_copy_message(self, stock_code):
        # 創建一個臨時標籤來顯示複製成功的消息
        msg = ttk.Label(self, text=f"已複製股票代碼: {stock_code}", foreground="green")
        msg.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 設置定時器，2秒後刪除消息
        self.after(2000, msg.destroy)