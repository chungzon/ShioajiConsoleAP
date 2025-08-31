import tkinter as tk
from tkinter import ttk, messagebox
from numpy import empty
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import shioaji as sj
from datetime import datetime, timedelta
from matplotlib import font_manager
from tkintertable import TableCanvas, TableModel
import pyperclip
from tkinter import filedialog
from collections import OrderedDict
import os
from tkinter import font as tkfont
import threading
from queue import Queue

from common.Math import Math
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt
from functools import partial
from PIL import ImageGrab

font_path = 'C:/Windows/Fonts/msjh.ttc'  # 微軟正黑體字體路徑
zh_font = font_manager.FontProperties(fname=font_path)

class SelectStockView(tk.Frame):
    
    def __init__(self, parent, controller, model):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.model = model
         # 獲取下載資料夾路徑
        self.downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.init_ui()
        self.data_queue = Queue()  # 用于存储待处理的股票数据
        self.processing = False
        self.start_update_thread()
        self.model.event.register(self.print_stock_list)

        self.setup_ratio_tabs()

    def init_ui(self):
        style = ttk.Style()
        style.configure('Treeview',
                           background='white')
        style.map('Treeview',
                     background=[('selected', 'blue')])
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # 第一行
        row1_frame = ttk.Frame(main_frame)
        row1_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # 添加日期選擇元件
        # date_frame = ttk.Frame(row1_frame)
        # date_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(row1_frame, text="開始日期:").pack(side=tk.LEFT)
        self.start_date = DateEntry(row1_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(row1_frame, text="結束日期:").pack(side=tk.LEFT)
        self.end_date = DateEntry(row1_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.pack(side=tk.LEFT)

        # 設置默認日期（例如：最近一年）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        self.start_date.set_date(start_date)
        self.end_date.set_date(end_date)

        ttk.Label(row1_frame, text="0618與Head價差比例").pack(side=tk.LEFT, padx=(10,5))
        ttk.Label(row1_frame, text="±").pack(side=tk.LEFT)
        self.ratio_entry = ttk.Entry(row1_frame, width=10)
        self.ratio_entry.insert(0, "0.15")  # 設置預設值為 0.15
        self.ratio_entry.pack(side=tk.LEFT, padx=(0,5))
        
        self.recent_wave_var = tk.BooleanVar()
        self.highest_wave_var = tk.BooleanVar()
        self.total_wave_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(row1_frame, text="最近波段", variable=self.recent_wave_var).pack(side=tk.LEFT, padx=(10, 10))
        ttk.Checkbutton(row1_frame, text="最高波段", variable=self.highest_wave_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(row1_frame, text="總波段", variable=self.total_wave_var).pack(side=tk.LEFT)

        # 標的交易量前
        ttk.Label(row1_frame, text="標的交易量前").pack(side=tk.LEFT, padx=(5,0))
        self.top_n_entry = ttk.Entry(row1_frame, width=5)
        self.top_n_entry.insert(0, "1763")  # 預設值為1763
        self.top_n_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(row1_frame, text="名").pack(side=tk.LEFT, padx=(0,5))

        ttk.Button(row1_frame, text="匯出股票代碼txt", command=self.export_stock_codes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(row1_frame, text="篩選", command=self.calculate).pack(side=tk.RIGHT, padx=(0, 5))

        # 第二行（按鈕）
        row2_frame = ttk.Frame(main_frame)
        row2_frame.grid(row=1, column=0, sticky="w", pady=(0, 5))

        self.ma_selections = {
            'daily': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                      20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=True), 
                      120: tk.BooleanVar(value=False)},
            'weekly': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                       20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=True), 
                       120: tk.BooleanVar(value=False)},
            'monthly': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                        20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=True), 
                        120: tk.BooleanVar(value=False)},
            '15min': {5: tk.BooleanVar(value=True), 10: tk.BooleanVar(value=True), 
                     20: tk.BooleanVar(value=True)}
        }
        self.select_all_vars = {
            'daily': tk.BooleanVar(value=False),
            'weekly': tk.BooleanVar(value=False),
            'monthly': tk.BooleanVar(value=False),
            '15min': tk.BooleanVar(value=True)
        }
        ma_types = [("日均線", 'daily'), ("週均線", 'weekly'), ("月均線", 'monthly'), ("15分K", '15min')]
        ma_frame = ttk.LabelFrame(row2_frame, text="均線")
        ma_frame.grid(row=0, column=0, sticky="nw", pady=(0, 5))
        for i, (ma_type, ma_key) in enumerate(ma_types):
            # frame = ttk.Frame(ma_frame)
            # frame.pack(padx=5, pady=5, anchor="w")
            
            # ttk.Label(ma_frame, text=ma_type, width=8).pack(side="left")
            ttk.Label(ma_frame, text=ma_type, width=8).grid(row=i, column=0, sticky="w", padx=(0, 5))
            
            # 添加全選 checkbox
            select_all_cb = ttk.Checkbutton(ma_frame, text="全選", 
                                            variable=self.select_all_vars[ma_key],
                                            command=lambda k=ma_key: self.toggle_all(k))
            select_all_cb.grid(row=i, column=1, sticky="w", padx=(0, 10))
            j = 1
            for period in [5, 10, 20, 60, 120]:
                if ma_key == '15min' and period not in [5, 10, 20]:
                    continue
                j = j + 1
                cb = ttk.Checkbutton(ma_frame, text=f"{period}", 
                                     variable=self.ma_selections[ma_key][period],
                                     command=lambda k=ma_key: self.update_select_all(k))
                cb.grid(row=i, column=j, sticky="w", padx=(0, 5))

        # self.ratio_checkbox_frame = ttk.Frame(row2_frame)
        self.ratio_checkbox_frame = ttk.LabelFrame(row2_frame, text="[買價、現價]價差比例")
        self.ratio_checkbox_frame.grid(row=0, column=1, sticky="nw", pady=(0, 5), padx=(5, 5))
        ratio_diff_frame = ttk.Frame(self.ratio_checkbox_frame)
        ratio_diff_frame.grid(row=0, column=0, sticky="w")
        self.ratio_diff_vars = { 
            'buy': tk.BooleanVar(value=True),
            'current': tk.BooleanVar(value=True)
        }
        ttk.Checkbutton(ratio_diff_frame, text="買價", variable=self.ratio_diff_vars['buy']).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Checkbutton(ratio_diff_frame, text="現價", variable=self.ratio_diff_vars['current']).pack(side=tk.LEFT, padx=(0, 5))    
        ttk.Label(ratio_diff_frame, text="+").pack(side=tk.LEFT)
        self.ratio_positive_entry = ttk.Entry(ratio_diff_frame, width=5)
        self.ratio_positive_entry.insert(0, "0.00")  # 設置預設值為 0.03    
        self.ratio_positive_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(ratio_diff_frame, text="~").pack(side=tk.LEFT)
        ttk.Label(ratio_diff_frame, text="-").pack(side=tk.LEFT)
        self.ratio_native_entry = ttk.Entry(ratio_diff_frame, width=5)
        self.ratio_native_entry.insert(0, "0.03")  # 設置預設值為 0.05
        self.ratio_native_entry.pack(side=tk.LEFT, padx=(0,5))

        ratio_frame = ttk.Frame(self.ratio_checkbox_frame)
        ratio_frame.grid(row=1, column=0, sticky="w")

        self.ratio_all_vars = {
            '0.191': tk.BooleanVar(value=True),
            '0.382': tk.BooleanVar(value=True),
            '0.5': tk.BooleanVar(value=True),
            '0.618': tk.BooleanVar(value=True),
            '0.809': tk.BooleanVar(value=True),
            '1': tk.BooleanVar(value=True),
            '1.191': tk.BooleanVar(value=True),
            '1.382': tk.BooleanVar(value=True),
            '1.5': tk.BooleanVar(value=True),
            '1.618': tk.BooleanVar(value=True),
            '1.809': tk.BooleanVar(value=True),
            '2': tk.BooleanVar(value=True),
        }
        # 比例0.191、0.382、0.5、0.618、0.809、1、1.191、1.382、1.5、1.618、1.809、2的checkbox，共12個
        for index, ratio in enumerate(self.ratio_all_vars.keys()):
            cb = ttk.Checkbutton(ratio_frame, text=f"{ratio}", variable=self.ratio_all_vars[ratio])
            column = index % 6
            row = index // 6
            cb.grid(row=row, column=column, sticky="w", padx=(0, 5))


        # 設置 LabelFrame 來包含 Treeview
        self.table_frame = ttk.LabelFrame(self, text="股票資訊")
        self.table_frame.grid(row=2, column=0, pady=10, sticky="nsew")

        # 建立一個notebook，每個notebook均為TreeView
        self.notebook = ttk.Notebook(self.table_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # # 定義欄位名稱
        # columns = ['股票代碼', '股票名稱', '現價','波段', 'Head-0618價差比例', '現價-0191比例', '0.191', '0.382', '0.5', '0.618', '0.809', '頸線', 'Head', 'Max_Date', 'Max_Value', 'Min_Date', 'Min_Value', '下載']

        # # 設置 Treeview 並定義列
        # self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        # self.tree.tag_configure('Blue', background="lightblue")
        # self.tree.tag_configure('White', background="white")

        # # 定義每個欄位的標題和寬度
        # for col in columns:
        #     self.tree.heading(col, text=col)
        #     self.tree.column(col, width=100, anchor='center')

        # self.tree.heading("下載", text="下載")
        # self.tree.column("下載", width=60, anchor="center")  # 設置下載列的寬度和對齊方式

        # # 將 Treeview 放置在 LabelFrame 
        # self.tree.grid(row=0, column=0, sticky="nsew")

        # # 綁定事件
        # self.tree.bind("<Double-1>", self.on_double_click)
        # self.tree.bind("<Button-1>", self.on_click)

        # # 添加垂直滾動條
        # vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        # vsb.grid(row=0, column=1, sticky="ns")
        # self.tree.configure(yscrollcommand=vsb.set)

        # # 添加水平滾動條
        # hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        # hsb.grid(row=1, column=0, sticky="ew")
        # self.tree.configure(xscrollcommand=hsb.set)

        # 設置框架的網格配置，使其能夠隨著窗口調整大小
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
    def calculate(self):
        if self.processing:
            messagebox.showinfo("提示", "正在處理中，請稍候...")
            return
        
        # 清空notebook中的所有分頁
        # for page in self.notebook.winfo_children():
        #     page.destroy()

        #清空notebook中的所有分頁內的TreeView
        for page in self.notebook.winfo_children():
            if isinstance(page, ttk.Frame):
                for child in page.winfo_children():
                    if isinstance(child, ttk.Treeview):
                        child.delete(*child.get_children())

        start_date = self.start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date.get_date().strftime('%Y-%m-%d')
        ratio = self.ratio_entry.get()
        positive_ratio = self.ratio_positive_entry.get()    # 現價-0618比例(正)
        native_ratio = self.ratio_native_entry.get()    # 0618-現價比例(負)
        top_n = self.top_n_entry.get()
        recent_wave_var = self.recent_wave_var.get()
        highest_wave_var = self.highest_wave_var.get()
        total_wave_var = self.total_wave_var.get() 

        # ratio為必要 
        if ratio == '': 
            messagebox.showerror("錯誤", "請輸入ratio")
            return
        # positive_ratio為必填
        if positive_ratio == '':
            messagebox.showerror("錯誤", "請輸入positive_ratio")
            return

        # native_ratio為必填
        if native_ratio == '':
            messagebox.showerror("錯誤", "請輸入native_ratio")
            return

        # 收集均線選擇
        ma_selections = {
            'daily': {period: var.get() for period, var in self.ma_selections['daily'].items()},
            'weekly': {period: var.get() for period, var in self.ma_selections['weekly'].items()},
            'monthly': {period: var.get() for period, var in self.ma_selections['monthly'].items()},
            '15min': {period: var.get() for period, var in self.ma_selections['15min'].items()}
        }

        ratio_all_vars = {ratio: var.get() for ratio, var in self.ratio_all_vars.items()}

        ratio_type_vars = {
            'buy': self.ratio_diff_vars['buy'].get(),
            'current': self.ratio_diff_vars['current'].get()
        }

        # 清空 TreeView 中的現有數據
        # for item in self.tree.get_children():
        #     self.tree.delete(item)
        
        self.processing = True
        
        # 启动处理线程
        process_thread = threading.Thread(
            target=self.process_calculation,
            args=(start_date, end_date, ratio, positive_ratio, native_ratio,
                  top_n, recent_wave_var, highest_wave_var, total_wave_var,
                  ma_selections, ratio_all_vars, ratio_type_vars)
        )
        process_thread.daemon = True
        process_thread.start()

    def process_calculation(self, *args):
        """在新线程中处理计算"""
        # self.controller.calculate(*args)
        try:
            self.controller.calculate(*args)
        except Exception as e:
            self.tree.after(0, messagebox.showerror, "錯誤", f"計算過程中發生錯誤：{str(e)}")
        finally:
            self.processing = False
            self.notebook.after(0, self._calculation_finished)

    def _calculation_finished(self):
        """计算完成后的处理"""
        if not self.processing:
            messagebox.showinfo("完成", "篩選完成")

    def show_error(self, message):
        messagebox.showerror("錯誤", message)

    def on_double_click(self, event):
        """雙擊事件處理"""
        tree = event.widget
        region = tree.identify("region", event.x, event.y)
        
        if region == "cell":
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            values = tree.item(item)['values']
            
            if not values:
                return
            
            stock_id = values[0]
            wave_type = values[3]  # 波段類型
            
            if column == "#17":  # 下載欄位
                if wave_type == "最高波段":
                    self.download_stock_data(stock_id)
                else:
                    self.show_stock_detail(stock_id)
            else:  # 股票代號欄位
                # 複製到剪貼簿
                self.clipboard_clear()
                self.clipboard_append(stock_id)
                print(f"已複製股票代號: {stock_id}")

    def on_click(self, event):
        # 從事件對象獲取觸發事件的 TreeView
        tree = event.widget
        
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            if column == f"#{len(tree['columns'])}" and tree.item(item, "values")[16] == '下載':  # 最後一列
                stock_id = tree.item(item, "values")[0]  # 假設股票代碼是第一列
                max_date = tree.item(item, "values")[13]  # 最高價波段日期
                self.download_detail_data(stock_id, max_date)
            elif column == f"#{len(tree['columns'])}" and tree.item(item, "values")[16] == '詳細資料':  # 最後一列
                stock_id = tree.item(item, "values")[0]  # 假設股票代碼是第一列
                stock_name = tree.item(item, "values")[1]  # 股票名稱
                # 點擊詳細資料，顯示詳細資料會彈跳出一個視窗顯示詳細資料
                self.show_detail_data(stock_id, stock_name)

    def show_copy_message(self, stock_code):
        # 創建一個時標來顯示複製成功的消息
        msg = ttk.Label(self, text=f"已複製股票代碼: {stock_code}", foreground="green")
        msg.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 設置定時器，2秒後刪除消息
        self.after(2000, msg.destroy)

    def export_stock_codes(self):
        # 獲取所有分頁的數據，並按比例排序（實際上已經排序好了）
        all_data = []
        for tab in self.notebook.tabs():
            tab_title = self.notebook.tab(tab, "text")
            ratio = tab_title.split()[1]  # 獲取比例數值
            
            # 獲取該分頁的TreeView
            tab_frame = self.notebook.children[tab.split('.')[-1]]  # 正確獲取分頁frame
            tree = None
            for child in tab_frame.winfo_children():
                if isinstance(child, ttk.Treeview):
                    tree = child
                    break
            
            if tree:
                # 獲取該分頁中的所有股票代碼，保持原始順序
                stock_codes = OrderedDict()
                for item in tree.get_children():
                    stock_code = tree.item(item, "values")[0]
                    if stock_code not in stock_codes:
                        stock_codes[stock_code] = None
                
                if stock_codes:  # 只添加有數據的分頁
                    all_data.append({
                        'ratio': ratio,
                        'codes': list(stock_codes.keys())
                    })

        if not all_data:
            messagebox.showinfo("提示", "沒有可匯出的數據")
            return

        # 獲取下載資料夾路徑
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # 設置默認文件名
        default_filename = "stock_codes.txt"
        
        # 選擇文件保存位置
        file_path = filedialog.asksaveasfilename(
            initialdir=downloads_path,
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                # 寫入日期範圍
                start_date = self.start_date.get_date().strftime('%Y-%m-%d')
                end_date = self.end_date.get_date().strftime('%Y-%m-%d')
                file.write(f"Date:{start_date}~{end_date}\n")
                
                # 寫入均線選擇條件
                ma_conditions = []
                
                # 日均線
                daily_selected = [str(period) for period, var in self.ma_selections['daily'].items() if var.get()]
                if daily_selected:
                    ma_conditions.append(f"日均:{','.join(daily_selected)}")
                
                # 週均線
                weekly_selected = [str(period) for period, var in self.ma_selections['weekly'].items() if var.get()]
                if weekly_selected:
                    ma_conditions.append(f"週均:{','.join(weekly_selected)}")
                
                # 月均線
                monthly_selected = [str(period) for period, var in self.ma_selections['monthly'].items() if var.get()]
                if monthly_selected:
                    ma_conditions.append(f"月均:{','.join(monthly_selected)}")
                
                # 15分K
                min15_selected = [str(period) for period, var in self.ma_selections['15min'].items() if var.get()]
                if min15_selected:
                    ma_conditions.append(f"15分均:{','.join(min15_selected)}")
                
                # 寫入均線條件
                if ma_conditions:
                    file.write('\n'.join(ma_conditions) + '\n')
                
                # 寫入價差比例條件
                ratio_conditions = []
                if self.ratio_diff_vars['current'].get():
                    positive_ratio = self.ratio_positive_entry.get()
                    native_ratio = self.ratio_native_entry.get()
                    ratio_conditions.append(f"現價:+{positive_ratio}~-{native_ratio}")
                
                if self.ratio_diff_vars['buy'].get():
                    positive_ratio = self.ratio_positive_entry.get()
                    native_ratio = self.ratio_native_entry.get()
                    ratio_conditions.append(f"買價:+{positive_ratio}~-{native_ratio}")
                
                if ratio_conditions:
                    file.write('\n'.join(ratio_conditions) + '\n')
                
                # 添加分隔線
                file.write('\n')
                
                # 寫入股票代碼數據
                for data in all_data:
                    # 寫入比例標記
                    file.write(f"# 比例 {data['ratio']}\n")
                    
                    # 將股票代碼分組，每組最多60個
                    codes = data['codes']
                    lines = ["\t".join(codes[i:i+60]) for i in range(0, len(codes), 60)]
                    
                    # 寫入該比例的所有股票代碼
                    file.write("\n".join(lines))
                    
                    # 添加空白行分隔不同比例的數據
                    file.write("\n\n")
                
            self.show_copy_message("股票代碼已匯出")

    def download_detail_data(self, stock_id, max_date):
        print(stock_id)
        if max_date:
            start_date = max_date
        else:
            start_date = self.start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date.get_date().strftime('%Y-%m-%d')

        # 打開文件對話框讓用戶選擇保存位置
        initial_dir = os.path.expanduser("~/Downloads")  # 預設為用戶的文檔目錄
        directory = filedialog.askdirectory(
            initialdir=initial_dir,
            title="選擇保存目錄"
        )

        if directory:  # 如果用戶選擇了文件路徑
            self.controller.download_detail_data(stock_id, start_date, end_date, directory)
        else:
            print("下載已取消")
        
    def show_detail_data(self, stock_id, stock_name):
        # 彈跳出一個視窗以顯示詳細資料
        self.controller.show_detail_data(stock_id, stock_name)
        

    def create_ma_table(self, ma_data, ma_type):
        # 创建通用的均价表格
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(5)
        table.setHorizontalHeaderLabels(["週期", "價格"])
                # 設置表頭樣式
        header_font = QFont('Microsoft JhengHei', 12, QFont.Bold)
        table.horizontalHeader().setFont(header_font)
        
        ma_periods = ['5MA', '10MA', '20MA', '60MA', '120MA']
        for row, period in enumerate(ma_periods):
            # 设置周期
            period_item = QTableWidgetItem(period)
            table.setItem(row, 0, period_item)
            
            # 设置价格
            price = ma_data[ma_type].get(period, 'N/A')
            if hasattr(price, 'item'):
                price = f"{price.item():.2f}"
            price_item = QTableWidgetItem(str(price))
            table.setItem(row, 1, price_item)
        
        table.resizeColumnsToContents()
        return table

    def create_ratio_table(self, ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox_state):
        # self.ratio_table = QTableWidget()
        # self.ratio_table.setColumnCount(5)  # 比例、總波段、指標, 最近波段
        
        # 设置固定的比例序列
        ratios = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                 '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                 '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                 '3.191', '3.382', '3.5', '3.618', '3.809', '4',
                 '4.191', '4.382', '4.5', '4.618', '4.809', '5',
                 '5.191', '5.382', '5.5', '5.618', '5.809', '6']
        
        # 計算總行
        total_rows = (len(ratios) * 2 - 1) + 2
        self.ratio_table.setRowCount(total_rows)
        self.ratio_table.setHorizontalHeaderLabels(["比例", "最近波段", "指標", "總波段", "獲利"])
        header_font = QFont('Microsoft JhengHei', 12, QFont.Bold)
        self.ratio_table.horizontalHeader().setFont(header_font)
        font = QFont()
        font.setPointSize(13)
        self.ratio_table.setFont(font)

        def find_row_for_value(value):
            min_price = float(ratio_prices['0'])
            max_price = float(ratio_prices['5'])
            
            # 如果value是字串，轉換為浮點數
            if isinstance(value, str):
                value = float(value)

            # 如果价格小于最小比例价格
            if value < min_price:
                return 0  # 第一个空白行
            
            # 如果价格大于最大比例价
            if value > max_price:
                return total_rows - 1  # 最后一个空白行
            
            # 在比例价格之间查找位置
            for i, ratio in enumerate(ratios[:-1]):
                current_price = float(ratio_prices[ratio])
                next_price = float(ratio_prices[ratios[i + 1]])
                
                row = (i * 2) + 1  # 考虑偏移
                
                if abs(value - current_price) < 0.01:
                    return row
                elif current_price < value < next_price or next_price < value < current_price:
                    return row + 1
            
            return total_rows - 1  # 如果没找到合适的位置，放在最后

        def format_price_text(name, value, is_recent_ratio=False):
            if hasattr(value, 'item'):
                value = value.item()
            return f"{name}：{value:.2f}"

        # 設置比例欄位和總波段欄位
        def setup_basic_columns():
            # 設置交替行顏色
            for row in range(total_rows):
                is_alternate = (row % 2) == 0
                color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
                
                # 第一行和最後一行是空白行
                if row == 0 or row == total_rows - 1:
                    for col in range(4):
                        item = QTableWidgetItem("")
                        item.setBackground(QBrush(color))
                        self.ratio_table.setItem(row, col, item)
                    continue
                
                # 比例行
                if (row - 1) % 2 == 0 and (row - 1) // 2 < len(ratios):
                    ratio_idx = (row - 1) // 2
                    
                    # 比例欄位
                    ratio_item = QTableWidgetItem(ratios[ratio_idx])
                    ratio_item.setBackground(QBrush(color))
                    self.ratio_table.setItem(row, 0, ratio_item)
                    
                    # 總波段欄位
                    wave_price = ratio_prices[ratios[ratio_idx]]
                    if hasattr(wave_price, 'item'):
                        wave_price = wave_price.item()
                    price_item = QTableWidgetItem(f"{wave_price:.2f}")
                    price_item.setBackground(QBrush(color))
                    self.ratio_table.setItem(row, 1, price_item)
                
                # 中間的空白行
                else:
                    for col in range(4):
                        item = QTableWidgetItem("")
                        item.setBackground(QBrush(color))
                        self.ratio_table.setItem(row, col, item)

        def add_sorted_prices_to_cell(row, prices_list):
            """將所有價格一起排序後添加到指標列"""
            # 按價格排序所有價格
            sorted_prices = sorted(prices_list, key=lambda x: x[1])
            
            # 生成顯示文本
            text_lines = []
            for name, value, is_recent_ratio in sorted_prices:
                if is_recent_ratio:
                    text_lines.append("")  # 最近波段價格的位置用空行表示
                else:
                    text_lines.append(format_price_text(name, value))
            
            # 創建表格項並設置文本
            indicator_item = QTableWidgetItem('\n'.join(text_lines))
            
            # 設置背景色
            is_alternate = (row % 2) == 0
            color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
            indicator_item.setBackground(QBrush(color))
            
            # 設置到表格中
            self.ratio_table.setItem(row, 2, indicator_item)
            
            # 在最近波段列中顯示最近波段價格
            recent_lines = []
            for name, value, is_recent_ratio in sorted_prices:
                if is_recent_ratio:
                    recent_lines.append(format_price_text(name, value))
                else:
                    recent_lines.append("")  # 指標價格的位置用空行表示
            
            recent_item = QTableWidgetItem('\n'.join(recent_lines))
            recent_item.setBackground(QBrush(color))
            self.ratio_table.setItem(row, 3, recent_item)

        # 首先設置基本欄位
        setup_basic_columns()

        # 收集所有價格數據
        def collect_all_prices():
            all_prices = []
            
            # 添加指標數據
            for name, value in indicator_prices.items():
                all_prices.append((name, value, False))
            
            # 添加均線數據
            ma_types = {'日均線': '日', '週均線': '周', '月均線': '月', '15分鐘均線': '15K'}
            for ma_key, prefix in ma_types.items():
                ma_data = organized_ma_data[ma_key]
                for ma_period in ['5MA', '10MA', '20MA', '60MA', '120MA', 'strong', 'weak', '5MA_DIFF', '10MA_DIFF', '20MA_DIFF', '60MA_DIFF', '120MA_DIFF']:
                    if ma_period in ma_data and ma_data[ma_period] != 'N/A':
                        value = ma_data[ma_period]
                        period_num = ma_period.replace('MA', '')
                        name = f"{prefix}({period_num})"
                        now_price = organized_ma_data['latest_close_price']
                        if 'DIFF' in ma_period:
                            diff_ratio = Math.calculate_price_diff_ratio(value, now_price)
                            period_num = ma_period.replace('_DIFF', '')
                            name = f"{prefix}({period_num}) 扣抵值[{diff_ratio}%]"
                        # if value != 'N/A' and (float(value) <= Math.calculate_up_limit_price_1_15(now_price) and float(value) >= Math.calculate_down_limit_price_1_15(now_price)):
                        #     all_prices.append((name, value, False))
                        all_prices.append((name, value, False))
            
            # 添加最近波段數據
            if recent_ratio_prices:
                for ratio, value in recent_ratio_prices.items():
                    name = f"【{ratio}】"
                    all_prices.append((name, value, True))

            if gap_df is not None and gap_checkbox_state:
                for index, row in gap_df.iterrows():
                    gap_type = '↑' if row['gap_type'] == '向上跳空' else '↓'
                    gap_price = row['previous_close'] if row['gap_type'] == '向上跳空' else row['current_open']
                    if (float(gap_price) <= Math.calculate_up_limit_price_1_15(now_price) and float(gap_price) >= Math.calculate_down_limit_price_1_15(now_price)):
                        all_prices.append((f"({row['previous_close']}~{row['current_open']})  [{row['date'].strftime('%Y-%m-%d')}] {gap_type}", gap_price, False))
            
            return all_prices

        # 按價格分組到對應的行
        row_prices = {}
        for name, value, is_recent_ratio in collect_all_prices():
            if hasattr(value, 'item'):
                value = value.item()
            row = find_row_for_value(value)
            
            if row not in row_prices:
                row_prices[row] = []
            row_prices[row].append((name, value, is_recent_ratio))

        # 填充價格數據
        for row, prices in row_prices.items():
            add_sorted_prices_to_cell(row, prices)

        # 調整表格外觀
        self.ratio_table.resizeColumnsToContents()
        self.ratio_table.resizeRowsToContents()

        return self.ratio_table

    def show_sma_data(self, stock_id, stock_name, organized_ma_data, ratio_prices, additional_data, indicator_prices, recent_ratio_prices, gap_df, now_price, latest_close_price_by_date, next_open_price):
        self.detail_window = QWidget()
        self.detail_window.setWindowTitle(f"詳細資料 - {stock_id} ({stock_name})")
        self.detail_window.setGeometry(100, 100, 1000, 750)

        # 创建分页控件
        self.tab_widget = QTabWidget()
        
        # 创建各个分页
        self.daily_tab = QWidget()
        self.weekly_tab = QWidget()
        self.monthly_tab = QWidget()
        self.ratio_tab = QWidget()
        
        # 将分页添加到tab widget
        self.tab_widget.addTab(self.ratio_tab, "比例價格")
        self.tab_widget.addTab(self.daily_tab, "均價")
        
        # 在日均价分页中创建网格布局
        daily_layout = QGridLayout()
        
        # 创建标签和表格的辅助函数
        def create_labeled_table(title, table):
            container = QWidget()
            layout = QVBoxLayout(container)
            
            # 创建标签
            label = QLabel(title)
            font = QFont()
            font.setFamily("Microsoft JhengHei")  # 设置字体为 Microsoft JhengHei
            font.setPointSize(13)
            font.setBold(True)
            label.setFont(font)
            
            # 添加标签和表格到垂直布局
            layout.addWidget(label)
            layout.addWidget(table)
            layout.setSpacing(5)  # 设置标签和表格之间的间距
            layout.setContentsMargins(0, 0, 0, 0)  # 设置边距
            
            return container
        
        # 创建最近收盘价的表格（左上）
        recent_price_table = QTableWidget()
        recent_price_table.setColumnCount(2)
        recent_price_table.setRowCount(5)
        recent_price_table.setHorizontalHeaderLabels(["日期", "收盤價"])
        
        # 设置字体
        font = QFont()
        font.setFamily("Microsoft JhengHei")  # 设置字体为 Microsoft JhengHei
        font.setPointSize(13)
        recent_price_table.setFont(font)
        recent_price_table.horizontalHeader().setFont(font)
        
        # 获取并填充最近5筆收盤價
        recent_prices = additional_data.get('latest_close_prices', [])[:5]
        recent_dates = additional_data.get('latest_dates', [])[:5]
        
        for i, (date, price) in enumerate(zip(recent_dates, recent_prices)):
            # 设置日期
            date_item = QTableWidgetItem(str(date))
            date_item.setFont(font)
            recent_price_table.setItem(i, 0, date_item)
            
            # 设置价格
            if hasattr(price, 'item'):
                price = f"{price.item():.2f}"
            price_item = QTableWidgetItem(str(price))
            price_item.setFont(font)
            recent_price_table.setItem(i, 1, price_item)
        
        recent_price_table.resizeColumnsToContents()
        recent_price_table.resizeRowsToContents()
        
        # 创建三个均线表格
        daily_table = self.create_ma_table(organized_ma_data, '日均線')
        weekly_table = self.create_ma_table(organized_ma_data, '週均線')
        monthly_table = self.create_ma_table(organized_ma_data, '月均線')

        daily_table.setFont(font)
        daily_table.horizontalHeader().setFont(font)
        weekly_table.setFont(font)
        weekly_table.horizontalHeader().setFont(font)
        monthly_table.setFont(font)
        monthly_table.horizontalHeader().setFont(font)

        daily_table.resizeColumnsToContents()
        daily_table.resizeRowsToContents()
        weekly_table.resizeColumnsToContents()
        weekly_table.resizeRowsToContents()
        monthly_table.resizeColumnsToContents()
        monthly_table.resizeRowsToContents()
        
        # 创建带标签的表格容器
        recent_container = create_labeled_table("近五日價格", recent_price_table)
        daily_container = create_labeled_table("日均價", daily_table)
        weekly_container = create_labeled_table("周均價", weekly_table)
        monthly_container = create_labeled_table("月均價", monthly_table)
        
        # 将带标签的容器添加到网格布局中
        daily_layout.addWidget(recent_container, 0, 0)  # 左上
        daily_layout.addWidget(daily_container, 0, 1)   # 右上
        daily_layout.addWidget(weekly_container, 1, 0)  # 左下
        daily_layout.addWidget(monthly_container, 1, 1) # 右下
        
        # 设置列和行的拉伸因子
        daily_layout.setColumnStretch(0, 1)
        daily_layout.setColumnStretch(1, 1)
        daily_layout.setRowStretch(0, 1)
        daily_layout.setRowStretch(1, 1)
        
        # 设置布局
        self.daily_tab.setLayout(daily_layout)
        
        
        # 比例价格表格
        self.ratio_layout = QVBoxLayout()
        
        # 添加日期信息标签
        # stock_name = stock_name if stock_name is not None else "--"
        stock_info = f"股票代碼(名稱): {stock_id} ({stock_name})\n"
        date_info = QLabel(
            f"{stock_info}\n"
            f"最高價日期: {additional_data['最近波段最高價日期']}   總波段最高價日期: {additional_data['總波段最高價日期']}\n"
            f"最低價日期: {additional_data['最近波段最低價日期']}   總波段最低價日期: {additional_data['總波段最低價日期']}"
        )
        date_info.setFont(font)
        self.ratio_layout.addWidget(date_info)
        
        # 當沖交易checkbox
        day_trading_checkbox = QCheckBox("當沖")
        day_trading_checkbox.setChecked(True)
        day_trading_checkbox.setFont(font)
        self.ratio_layout.addWidget(day_trading_checkbox)

        # 创建一个水平布局
        fee_layout = QHBoxLayout()

        # 手續費折讓輸入框，預設為1.6%
        fee_discount_label = QLabel("手續費折讓:")
        fee_discount_label.setFont(font)
        fee_discount_label.setFixedWidth(100)
        fee_layout.addWidget(fee_discount_label)

        fee_discount_input = QLineEdit()
        fee_discount_input.setFont(font)
        fee_discount_input.setText("1.6")
        fee_discount_input.setFixedWidth(75)
        fee_discount_input.setPlaceholderText("請輸入")
        fee_discount_input.setAlignment(Qt.AlignCenter)
        fee_layout.addWidget(fee_discount_input)

        fee_discount_unit_label = QLabel("折")
        fee_discount_unit_label.setFont(font)
        fee_layout.addWidget(fee_discount_unit_label)
       
        self.ratio_layout.addLayout(fee_layout)

        export_layout = QHBoxLayout()

        gap_checkbox = QCheckBox("顯示跳空指標")
        gap_checkbox.setChecked(True)
        gap_checkbox.setFont(font)
        export_layout.addWidget(gap_checkbox)
        gap_checkbox.stateChanged.connect(lambda: self.create_ratio_table(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox.isChecked()))
        # 匯出json檔案按鈕
        export_json_button = QPushButton("匯出json檔案")
        export_json_button.setFont(font)
        export_json_button.clicked.connect(lambda: self.export_json(stock_id, ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox.isChecked(), now_price, latest_close_price_by_date, next_open_price))
        export_layout.addWidget(export_json_button) 

        # 重新計算按鈕
        recalculate_button = QPushButton("重新計算")
        recalculate_button.setFont(font)
        recalculate_button.clicked.connect(lambda: self.recalculate(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox.isChecked()))
        export_layout.addWidget(recalculate_button)

        self.ratio_layout.addLayout(export_layout)

        # # 創建比例表格
        # ratio_table = self.create_ratio_table(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df)
        # ratio_layout.addWidget(ratio_table)
        # self.ratio_tab.setLayout(ratio_layout)
        self.ratio_table = QTableWidget()
        self.ratio_table.setColumnCount(5)  # 比例、最近波段、總波段、指標, 獲利
        self.ratio_layout.addWidget(self.ratio_table)
        self.ratio_tab.setLayout(self.ratio_layout)
        self.update_table(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox.isChecked())
        

        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)

        # 添加1分K、3分K、5分K資料匯出按鈕
        export_kbars_layout = QHBoxLayout()
        export_1min_button = QPushButton("匯出1分K資料")
        export_1min_button.setFont(font)
        export_1min_button.clicked.connect(lambda: self.controller.export_1min_data(stock_id, stock_name, self.end_date.get_date()))
        export_kbars_layout.addWidget(export_1min_button)

        export_3min_button = QPushButton("匯出3分K資料")
        export_3min_button.setFont(font)
        export_3min_button.clicked.connect(lambda: self.controller.export_3min_data(stock_id, stock_name, self.end_date.get_date()))
        export_kbars_layout.addWidget(export_3min_button)

        export_5min_button = QPushButton("匯出5分K資料")
        export_5min_button.setFont(font)
        export_5min_button.clicked.connect(lambda: self.controller.export_5min_data(stock_id, stock_name, self.end_date.get_date()))
        export_kbars_layout.addWidget(export_5min_button)
        main_layout.addLayout(export_kbars_layout)

        # 添加截圖按鈕
        screenshot_button = QPushButton("截圖另存圖片")
        screenshot_button.setFont(font)
        screenshot_button.clicked.connect(partial(self.save_screenshot, stock_id, stock_name))
        main_layout.addWidget(screenshot_button)

        

        self.detail_window.setLayout(main_layout)
        
        self.detail_window.show()

    def update_table(self, ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox_state):
        # 創建比例表格
        self.create_ratio_table(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox_state)

    def insert_table_row(self, table, row, values):
        """輔助函數：插一行數據到表格中"""
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            
            # 設置交替行背景色
            if row % 2 == 0:
                item.setBackground(QColor(240, 240, 240))
                
            # 設置為不可編輯
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            table.setItem(row, col, item)

    def toggle_all(self, ma_type):
        state = self.select_all_vars[ma_type].get()
        for period in self.ma_selections[ma_type]:
            self.ma_selections[ma_type][period].set(state)

    def update_select_all(self, ma_type):
        all_checked = all(self.ma_selections[ma_type][period].get() for period in self.ma_selections[ma_type])
        self.select_all_vars[ma_type].set(all_checked)

    def get_ma_selections(self):
        return {ma_type: {period: var.get() for period, var in periods.items()}
                for ma_type, periods in self.ma_selections.items()}

    def find_closest_ratios_for_indicators(self, indicator_prices, total_ratio_prices):
        """
        為每個指標價格找出最接近的比例價格，並保存所有指標信息
        """
        assignments = {}
        ratio_values = {ratio: float(value) for ratio, value in total_ratio_prices.items() 
                       if value != 'N/A'}
        
        if not ratio_values:
            return {}

        # 按固定順序處理指標，確保顯示順序一致
        indicator_types = ['AH', 'AL', 'CDP', 'NH', 'NL']
        
        for indicator_type in indicator_types:
            price = indicator_prices.get(indicator_type, 'N/A')
            if price == 'N/A':
                continue
                
            try:
                price_value = float(price)
                closest_ratio = min(ratio_values.keys(), 
                                  key=lambda x: abs(ratio_values[x] - price_value))
                
                if closest_ratio not in assignments:
                    assignments[closest_ratio] = []
                
                adjusted_ratio = Math.adjust_ratio_price(price_value)
                assignments[closest_ratio].append({
                    'type': indicator_type,
                    'price': price,
                    'adjusted': adjusted_ratio
                })
                
            except (ValueError, TypeError):
                continue
        
        return assignments

    def format_indicators_for_ratio(self, ratio, indicator_assignments):
        """
        格式化顯示指定比例對應的所有指標，確保所有指標都顯示
        """
        if ratio not in indicator_assignments:
            return ''
        
        indicators = indicator_assignments[ratio]
        # 按指標類型排序，確保顯示順序一致
        indicators.sort(key=lambda x: x['type'])
        
        formatted_indicators = []
        for indicator in indicators:
            formatted_indicators.append(
                f"{indicator['type']}:{indicator['price']}({indicator['adjusted']})"
            )
        
        # 使用換行符連接所有指標
        return '\n'.join(formatted_indicators)

        
    def find_closest_ratio(self, price_value, total_ratio_prices):
        """
        找出與給定價格最接近的比例
        """
        try:
            ratio_values = {ratio: float(value) for ratio, value in total_ratio_prices.items() 
                           if value != 'N/A'}
        
            if not ratio_values:
                return None
            
            return min(ratio_values.keys(), 
                      key=lambda x: abs(ratio_values[x] - price_value))
                  
        except (ValueError, TypeError):
            return None

    def find_price_interval(self, price, ratio_values):
        """
        找出價格所在的區間或確切的比例
        返回特殊值：
        - ('min', first_ratio) 表示小於最小比例價格
        - (last_ratio, 'max') 表示大於最大比例價格
        - (ratio, ratio) 表示確切匹配
        - (ratio1, ratio2) 表示在兩個比例價格之間
        """
        try:
            # 將所有比例價格排序
            ratios = sorted(ratio_values.keys(), key=lambda x: float(ratio_values[x]))
            min_ratio = ratios[0]
            max_ratio = ratios[-1]
            
            # 檢查是否小於最小比例價格
            if price < float(ratio_values[min_ratio]):
                return ('min', min_ratio)
                
            # 檢查是否大於最大比例價格
            if price > float(ratio_values[max_ratio]):
                return (max_ratio, 'max')

            # 檢查是否與某個比例價格完全相等
            for ratio, value in ratio_values.items():
                if abs(price - float(value)) < 0.01:
                    return (ratio, ratio)

            # 找出價格所在的區間
            for i in range(len(ratios) - 1):
                ratio1, ratio2 = ratios[i], ratios[i + 1]
                if float(ratio_values[ratio1]) < price < float(ratio_values[ratio2]):
                    return (ratio1, ratio2)

            return None
        
        except (ValueError, TypeError) as e:
            print(f"Error in find_price_interval: {e}")
            return None

    def create_qt_table(self):
        table = QTableWidget()
        table.setColumnCount(6)
            
        # 設置表頭
        headers = ['比例', '總波段', '指標', '日均', '周均', '月均']
        table.setHorizontalHeaderLabels(headers)
            
        # 設置表頭樣式
        header_font = QFont('Microsoft JhengHei', 12, QFont.Bold)
        table.horizontalHeader().setFont(header_font)
            
        # 設置列寬
        table.setColumnWidth(0, 80)   # 比例
        table.setColumnWidth(1, 100)  # 總波段
        table.setColumnWidth(2, 200)  # 指標
        table.setColumnWidth(3, 150)  # 日均
        table.setColumnWidth(4, 150)  # 周均
        table.setColumnWidth(5, 150)  # 月均
            
        # 設置自動調整行高
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
        # 設置文字自動換行
        table.setWordWrap(True)
            
        # 設置表格樣式
        table.setFrameStyle(QFrame.Box | QFrame.Plain)
        table.setShowGrid(True)
        table.setFont(QFont('Microsoft JhengHei', 12))
            
        return table    

    def start_update_thread(self):
        """启动更新UI的线程"""
        self.update_thread = threading.Thread(target=self.process_data_queue, daemon=True)
        self.update_thread.start()
    
    def process_data_queue(self):
        """处理数据队列的线程"""
        while True:
            try:
                stock_segment = self.data_queue.get()
                if stock_segment is None:  # 结束信号
                    break
                    
                # 在主线程中更新UI
                self.notebook.after(0, self._update_tree_safe, stock_segment)
                self.data_queue.task_done()
            except Exception as e:
                print(f"Error in process_data_queue: {e}")
            
    def print_stock_list(self, stock_segment):
        """接收股票数据并放入队列"""
        try:
            # 将数据放入队列
            self.data_queue.put(stock_segment)
        except Exception as e:
            print(f"Error in print_stock_list: {e}")
            # print(f"Stock segment data: {stock_segment}")

    def _update_tree_safe(self, stock_segment):
        """在主線程中安全地更新樹形視圖"""
        try:
            matched_ratios = stock_segment['matched_ratios']
            
            # 檢查是否已經存在該比例的頁面
            for ratio in matched_ratios:
                tab_name = f"比例 {ratio}"
                
                # 檢查是否已存在該分頁
                existing_tree = None
                for tab_id in range(self.notebook.index('end')):
                    if self.notebook.tab(tab_id, "text") == tab_name:
                        existing_tree = self.notebook.winfo_children()[tab_id].winfo_children()[0]
                        break
                
                if existing_tree is None:
                    # 如果分頁不存在，創建新分頁
                    page = ttk.Frame(self.notebook)
                    tree = self.create_page(page)
                    self.notebook.add(page, text=tab_name)
                    existing_tree = tree
                
                # 更新TreeView的數據
                self._update_tree_data(existing_tree, stock_segment)
            
        except Exception as e:
            print(f"Error in _update_tree_safe: {e}")

    def create_page(self, page):
        """創建TreeView的頁面"""
        # 創建TreeView並添加到分頁中
        tree = ttk.Treeview(page, columns=("stock_id", "name", "latest_close_price", "wave_type", 
                                          "spread_ratio", "latest_close_price-0.191_ratio", 
                                          "Ratio_0.191", "Ratio_0.382", "Ratio_0.5", 
                                          "Ratio_0.618", "Ratio_0.809", "Ratio_1", 
                                          "Max_Value", "Max_Date", "Min_Value", "Min_Date", "Download"))
        
        # 設置TreeView的列寬和標題
        self._setup_tree_columns(tree)
        
        # 添加事件綁定
        tree.bind("<Button-1>", self.on_click)  # 添加點擊事件綁定
        tree.bind("<Double-1>", self.on_double_click)  # 添加雙擊事件綁定
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # 使用grid布局管理器
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 配置grid權重
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)

        return tree

    def _setup_tree_columns(self, tree):
        """設置TreeView的列寬和標題"""
        columns = {
            "#0": ("", 0),
            "stock_id": ("股票代號", 100),
            "name": ("股票名稱", 100),
            "latest_close_price": ("最新收盤價", 100),
            "wave_type": ("波段類型", 100),
            "spread_ratio": ("波段比例", 100),
            "latest_close_price-0.191_ratio": ("最新收盤價-0.191比例", 100),
            "Ratio_0.191": ("0.191比例", 100),
            "Ratio_0.382": ("0.382比例", 100),
            "Ratio_0.5": ("0.5比例", 100),
            "Ratio_0.618": ("0.618比例", 100),
            "Ratio_0.809": ("0.809比例", 100),
            "Ratio_1": ("1比例", 100),
            "Max_Value": ("最高價", 100),
            "Max_Date": ("最高價日期", 100),
            "Min_Value": ("最低價", 100),
            "Min_Date": ("最低價日期", 100),
            "Download": ("下載", 100)
        }
        
        for col, (text, width) in columns.items():
            tree.column(col, width=width)
            if col != "#0":
                tree.heading(col, text=text)

    def _update_tree_data(self, tree, stock_segment):
        """更新TreeView的數據"""
        try:
            # 為每個新的股票組合創建一個新的標籤組
            group_tag = f"group_{len(tree.get_children()) // 3}"
            
            # 設置兩種不同的底色標籤
            if int(group_tag.split('_')[1]) % 2 == 0:
                tree.tag_configure(f"{group_tag}_even", background="#B8DBCA")  # 淺灰色
            else:
                tree.tag_configure(f"{group_tag}_odd", background="#E8E8E8")   # 更淺的灰色
            
            # 准备并插入所有波段数据
            segments = [
                (stock_segment['stock_data']['recent_segment'], '最近波段'),
                (stock_segment['stock_data']['highest_segment'], '最高波段'),
                (stock_segment['stock_data']['total_segment'], '總波段')
            ]
            
            for segment_data, wave_type in segments:
                values = self._prepare_tree_values(segment_data, wave_type)
                if values:
                    # 使用對應的標籤
                    tag = f"{group_tag}_even" if int(group_tag.split('_')[1]) % 2 == 0 else f"{group_tag}_odd"
                    self._insert_tree_item(tree, values, tag)

        except Exception as e:
            print(f"Error in _update_tree_data: {e}")

    def _prepare_tree_values(self, segment_data, wave_type):
        """准备树形视图的数据"""
        try:
            button_text = ""
            if wave_type == '最高波段':
                button_text = "下載"
            elif wave_type == '最近波段':
                # 將last_day_volume是股，轉換成張，不要小數點
                if segment_data['last_day_volume'] is not None:
                    last_day_volume = int(segment_data['last_day_volume'])
                    button_text = f"{last_day_volume / 1000:.0f}張"
                else:
                    button_text = "N/A"
            else:
                button_text = "詳細資料"

            return (
                segment_data['stock_id'],
                segment_data['name'],
                segment_data['latest_close_price'],
                wave_type,
                round(float(segment_data['spread_ratio']), 3),
                round(float(segment_data['latest_close_price-0.191_ratio']), 3),
                round(float(segment_data['Ratio_0.191']), 2),
                round(float(segment_data['Ratio_0.382']), 2),
                round(float(segment_data['Ratio_0.5']), 2),
                round(float(segment_data['Ratio_0.618']), 2),
                round(float(segment_data['Ratio_0.809']), 2),
                round(float(segment_data['Ratio_1']), 2),
                segment_data['Max_Value'],
                segment_data['Max_Date'],
                segment_data['Min_Value'],
                segment_data['Min_Date'],
                button_text
            )
        except Exception as e:
            print(f"Error in _prepare_tree_values: {e}")
            return None

    def _insert_tree_item(self, tree, values, tag):
        """插入数据到TreeView"""
        try:
            # 插入數據並使用指定的標籤
            tree.insert('', 'end', values=values, tags=(tag,))
            
            # 確保視圖滾動到最新項目
            tree.yview_moveto(1)
        except Exception as e:
            print(f"Error in _insert_tree_item: {e}")
    def setup_ratio_tabs(self):
        """初始化所有比例分頁"""
        # 預設的比例列表（從小到大排序）
        ratios = ['0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                '1.191', '1.382', '1.5', '1.618', '1.809', '2']
        
        # 為每個比例創建分頁和表格
        for ratio in ratios:
            tab = ttk.Frame(self.notebook)
            tree = self.create_empty_tree(tab)
            
            # 設置網格布局
            tree.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=tree.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            tree.configure(yscrollcommand=scrollbar.set)
            
            # 配置網格權重
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            
            # 添加分頁
            self.notebook.add(tab, text=f"比例 {ratio}")

    def create_empty_tree(self, parent):
        """創建空的表格"""
        tree = ttk.Treeview(parent, columns=("stock_id", "name", "latest_close_price", "wave_type", 
                                        "spread_ratio", "latest_close_price-0.191_ratio", 
                                        "Ratio_0.191", "Ratio_0.382", "Ratio_0.5", 
                                        "Ratio_0.618", "Ratio_0.809", "Ratio_1", 
                                        "Max_Value", "Max_Date", "Min_Value", "Min_Date", "Download"))
        
        # 設置列寬和標題
        self._setup_tree_columns(tree)
        
        # 添加事件綁定
        tree.bind("<Button-1>", self.on_click)
        tree.bind("<Double-1>", self.on_double_click)
        
        return tree

    def save_screenshot(self, stock_id, stock_name):
        # 獲取當前視窗的幾何信息
        x = self.detail_window.geometry().x()
        y = self.detail_window.geometry().y()
        width = self.detail_window.geometry().width()
        height = self.detail_window.geometry().height()

        # 截圖
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        # 打開文件保存對話框
        # default file name: 截圖 - {stock_name} ({stock_id})
        # default path: Downloads
        default_path = os.path.join(self.downloads_path, f"截圖 - {stock_name} ({stock_id}).png")
        file_path, _ = QFileDialog.getSaveFileName(self.detail_window, f"保存截圖", default_path, "PNG Files (*.png);;All Files (*)")

        if file_path:
            # 保存截圖
            screenshot.save(file_path, "PNG")

    def recalculate(self, ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox_state):
        # 分別取得ratio比例為0和2的價格，並轉為float
        # 取得table中ratio比例為0和2的價格
        ratio_0_price = float(self.ratio_table.item(1, 1).text())
        ratio_2_price = float(self.ratio_table.item(25, 1).text())
        
        # 確保 max_value 和 min_value 的順序正確
        max_value = max(ratio_2_price, ratio_0_price)
        min_value = min(ratio_2_price, ratio_0_price)
        
        # 重新計算各比例價格
        ratios = list(ratio_prices.keys())
        for ratio in ratios:
            if ratio == '0':
                ratio_prices[ratio] = ratio_0_price
            elif ratio == '2':
                ratio_prices[ratio] = ratio_2_price
            else:
                # 修正參數順序：max_value, min_value, ratio
                ratio_prices[ratio] = Math.calculate_ratio_value(max_value, min_value, float(ratio))
        
        # 清空指標、總波段及獲利列
        for r in range(self.ratio_table.rowCount()):
            self.ratio_table.setItem(r, 2, QTableWidgetItem(""))
            self.ratio_table.setItem(r, 3, QTableWidgetItem(""))
            self.ratio_table.setItem(r, 4, QTableWidgetItem(""))

        self.update_table(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox_state)

    def save_kbars_data(self, event):
        # 儲存1分K資料為txt檔案，檔名為{stock_id}_{end_date}.txt
        # 資料格式為"序號(流水號),開盤價,最高價,最低價,收盤價,時間"
        df = event.data['df']
        # 在資料df中第一列插入標頭
        # 
        df['序號'] = range(1, len(df) + 1)
        df = df[['序號', 'Open_Price', 'High', 'Low', 'Close_Price', '時間']]
        
        # 創建標頭行
        header_df = pd.DataFrame([['// 序號(流水號),開盤價,最高價,最低價,收盤價,時間']], columns=['序號'])
        
        # 合併標頭和數據
        df = pd.concat([header_df, df], ignore_index=True)

        
        kbar_type = event.data['kbar_type']
        stock_id = event.data['stock_id']
        end_date = event.data['end_date']
        # 儲存分K資料為txt檔案，檔名為{stock_id}_{kbar_type}_{end_date}.txt
        file_path, _ = QFileDialog.getSaveFileName(self.detail_window, f"儲存{kbar_type}K資料", os.path.join(self.downloads_path, f"{stock_id}_{kbar_type}_{end_date}.txt"), "Text Files (*.txt);;All Files (*)")
        
        if file_path:
            df.to_csv(file_path, index=False, header=False)
            QMessageBox.information(self.detail_window, "提示", f"{kbar_type}K資料已儲存")
        else:
            QMessageBox.warning(self.detail_window, "提示", f"{kbar_type}K資料儲存失敗")

    def export_json(self, stock_id, recent_ratio_prices, indicator_prices, organized_ma_data, ratio_prices, day_trading_checkbox, fee_discount_input, gap_df, gap_checkbox_state, now_price, latest_close_price_by_date, next_open_price):
        import json
        # 準備數據字典
        data = {}
        
        # 添加當前價格
        if latest_close_price_by_date is not None:
            data['NOW PRICE'] = f"{latest_close_price_by_date:.2f}"
        else:
            data['NOW PRICE'] = "nan"
        
        # 定義固定的比例序列
        ratio_sequence = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                         '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                         '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                         '3.191', '3.382', '3.5', '3.618', '3.809', '4',
                         '4.191', '4.382', '4.5', '4.618', '4.809', '5']
        
        # 添加最近波段比例價格 (N[ratio])
        for ratio in ratio_sequence:
            if recent_ratio_prices and ratio in recent_ratio_prices:
                price = recent_ratio_prices[ratio]
                if hasattr(price, 'item'):
                    price = price.item()
                data[f"N[{ratio}]"] = f"{price:.2f}"
            else:
                data[f"N[{ratio}]"] = "nan"
        
        # 添加總波段比例價格 ([ratio])
        for ratio in ratio_sequence:
            if ratio in ratio_prices:
                price = ratio_prices[ratio]
                if hasattr(price, 'item'):
                    price = price.item()
                data[f"[{ratio}]"] = f"{price:.2f}"
            else:
                data[f"[{ratio}]"] = "nan"
        
        # 按照固定順序添加均線和指標數據
        indicator_order = [
            ('日', '120'), ('周', '60'), ('周', '20'), ('日', '60'),
            ('周', '120'), ('月', '5'), ('周', '10'), ('日', '20'),
            'AL', ('周', '5'), 'NL', ('15K', '20'), 'CDP', ('15K', '10'),
            ('15K', '5'), ('15K', 'strong'), ('15K', 'weak'), ('日', '10'), ('日', '5'), 'NH', 'AH',
            ('月', '10'), ('月', '20'), ('月', '60'), ('月', '120'),
            ('日', '5MA_DIFF'), ('日', '10MA_DIFF'), ('日', '20MA_DIFF'), ('日', '60MA_DIFF'), ('日', '120MA_DIFF'),
            ('周', '5MA_DIFF'), ('周', '10MA_DIFF'), ('周', '20MA_DIFF'), ('周', '60MA_DIFF'), ('周', '120MA_DIFF'),
            ('月', '5MA_DIFF'), ('月', '10MA_DIFF'), ('月', '20MA_DIFF'), ('月', '60MA_DIFF'), ('月', '120MA_DIFF')
        ]
        
        # 添加均線和指標數據
        for item in indicator_order:
            if isinstance(item, tuple):
                prefix, period = item
                key = f"{prefix}({period})_DC"
                if prefix in {'日': '日均線', '周': '週均線', '月': '月均線', '15K': '15分鐘均線'}:
                    ma_type = {'日': '日均線', '周': '週均線', '月': '月均線', '15K': '15分鐘均線'}[prefix]
                    # 處理扣抵值
                    if period.endswith('MA_DIFF'):
                        ma_period = period.replace('MA_DIFF', 'MA_DIFF')
                    # 對於15分鐘均線，需要特殊處理strong和weak
                    elif prefix != '月' and period in ['strong', 'weak']:
                        ma_period = period
                    else:
                        ma_period = f"{period}MA"
                    if (ma_type in organized_ma_data and 
                        ma_period in organized_ma_data[ma_type] and 
                        organized_ma_data[ma_type][ma_period] != 'N/A'):
                        value = organized_ma_data[ma_type][ma_period]
                        if hasattr(value, 'item'):
                            value = value.item()
                        data[key] = f"{value:.2f}"
                    else:
                        data[key] = "nan"
            else:
                # 處理指標數據
                key = f"{item}_DC"
                if item in indicator_prices:
                    value = indicator_prices[item]
                    if hasattr(value, 'item'):
                        value = value.item()
                    data[key] = f"{value:.2f}"
                else:
                    data[key] = "nan"
        
        # 獲取最近波段結束日期並格式化
        recent_end_date = self.end_date.get_date()
        # next_day = recent_end_date + timedelta(days=1)
        next_day = next_open_price['date'] if next_open_price else None
        formatted_date = next_day.strftime('%Y-%m-%d') if next_day else "nan"

        # 讀取JSON模板
        with open('resource/export_json_templete.json', 'r') as f:
            json_template = json.load(f)
        
        # 更新JSON模板中的數據
        json_template['stock_code'] = stock_id
        json_template['base'] = f"{next_open_price['open_price']}" if next_open_price else "nan"
        json_template['date'] = formatted_date
        json_template['data'] = data
        
        

        # # 創建完整的JSON結構
        # json_data ={
        #     "stock_code": self.entry_stock_id.get(),
        #     "base": f"{next_open_price['open_price']}" if next_open_price else "nan",
        #     "date": formatted_date,
        #     "data": data,
        #     "over_ratio_dont_buy": "0.03",
        #     "extend_over_ratio_dont_buy": "0.03",
        #     "no_buy_after": "10:00:00",
        #     "final_buy": "12:00:00",
        #     "extend_time": "00:30:00",
        #     "enable_15k20ma": True,
        #     "enable_15k10ma": True,
        #     "before_n": 2,
        # }
        
        # 總波段的結束日期
        total_segment_date = self.end_date.get_date()
        formatted_total_segment_date = total_segment_date.strftime('%Y-%m-%d')
        # 打開檔案儲存對話框，預設儲存路徑為"Downloads"
        
        default_path = os.path.join(self.downloads_path, f"{stock_id}_data_{formatted_total_segment_date}.json")
        file_path, _ = QFileDialog.getSaveFileName(
            self.detail_window,
            "儲存JSON檔案",
            default_path,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # 寫入JSON檔案
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_template, f, ensure_ascii=False, indent=4)
