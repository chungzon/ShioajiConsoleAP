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

class SelectStockView(tk.Frame):
    
    def __init__(self, parent, controller, model):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.model = model
        self.init_ui()

    def init_ui(self):
        ttk.Label(self, text="0618與Head價差比例").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.ratio_entry = ttk.Entry(self)
        self.ratio_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Button(self, text="篩選", command=self.calculate).grid(row=0, column=2, pady=20, padx=10, sticky=tk.W)

        # 設置 LabelFrame 來包含 Treeview
        self.table_frame = ttk.LabelFrame(self, text="股票資訊")
        self.table_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # 定義欄位名稱
        columns = ['股票代碼', '股票名稱', '現價', '0618', 'Head', '價差比例']

        # 設置 Treeview 並定義列
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')

        # 定義每個欄位的標題和寬度
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')

        # 將 Treeview 放置在 LabelFrame 中
        self.tree.grid(row=0, column=0, sticky="nsew")

        # 插入測試數據
        self.tree.insert('', 'end', values=('2330', '台積電', '600', '595', '610', '1.6%'))
        self.tree.insert('', 'end', values=('2317', '鴻海', '110', '108', '115', '2.3%'))

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
        self.controller.calculate(ratio)