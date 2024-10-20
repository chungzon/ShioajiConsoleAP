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
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        # 第一行
        row1_frame = ttk.Frame(main_frame)
        row1_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # 添加日期選擇元件
        date_frame = ttk.Frame(row1_frame)
        date_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(date_frame, text="開始日期:").pack(side=tk.LEFT)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(date_frame, text="結束日期:").pack(side=tk.LEFT)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.pack(side=tk.LEFT)

        # 設置默認日期（例如：最近一年）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        self.start_date.set_date(start_date)
        self.end_date.set_date(end_date)

        ttk.Label(row1_frame, text="0618與Head價差比例").pack(side=tk.LEFT, padx=(10,5))
        ttk.Label(row1_frame, text="±").pack(side=tk.LEFT)
        self.ratio_entry = ttk.Entry(row1_frame, width=10)
        self.ratio_entry.pack(side=tk.LEFT, padx=(0,5))
        # 現價-0618比例
        ttk.Label(row1_frame, text="現價-0618比例").pack(side=tk.LEFT, padx=5)
        ttk.Label(row1_frame, text="+").pack(side=tk.LEFT)
        self.ratio_positive_entry = ttk.Entry(row1_frame, width=5)
        self.ratio_positive_entry.insert(0, "0.03")  # 設置預設值為 0.03    
        self.ratio_positive_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(row1_frame, text="~").pack(side=tk.LEFT)
        ttk.Label(row1_frame, text="-").pack(side=tk.LEFT)
        self.ratio_native_entry = ttk.Entry(row1_frame, width=5)
        self.ratio_native_entry.insert(0, "0.05")  # 設置預設值為 0.05
        self.ratio_native_entry.pack(side=tk.LEFT, padx=(0,5))


        self.recent_wave_var = tk.BooleanVar()
        self.highest_wave_var = tk.BooleanVar()
        self.total_wave_var = tk.BooleanVar()

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
        # 添加日均線的 checkbox
        ttk.Label(row2_frame, text="日均線:").pack(side=tk.LEFT, padx=(0, 5))
        self.daily_ma_vars = {}
        for period in [5, 10, 20, 60, 120]:
            var = tk.BooleanVar(value=False)  # 預設為選中
            self.daily_ma_vars[period] = var
            ttk.Checkbutton(row2_frame, text=f"{period}", variable=var).pack(side=tk.LEFT, padx=(0, 5))

        # 添加周均線的 checkbox
        ttk.Label(row2_frame, text="周均線:").pack(side=tk.LEFT, padx=(20, 5))
        self.weekly_ma_vars = {}
        for period in [5, 10, 20, 60, 120]:
            var = tk.BooleanVar(value=False)  # 預設為選中
            self.weekly_ma_vars[period] = var
            ttk.Checkbutton(row2_frame, text=f"{period}", variable=var).pack(side=tk.LEFT, padx=(0, 5))

        # 添加月均線的 checkbox
        ttk.Label(row2_frame, text="月均線:").pack(side=tk.LEFT, padx=(20, 5))
        self.monthly_ma_vars = {}
        for period in [5, 10, 20, 60, 120]:
            var = tk.BooleanVar(value=False)  # 預設為選中
            self.monthly_ma_vars[period] = var
            ttk.Checkbutton(row2_frame, text=f"{period}", variable=var).pack(side=tk.LEFT, padx=(0, 5))


        # 設置 LabelFrame 來包含 Treeview
        self.table_frame = ttk.LabelFrame(self, text="股票資訊")
        self.table_frame.grid(row=2, column=0, pady=10, sticky="nsew")

        # 定義欄位名稱
        columns = ['股票代碼', '股票名稱', '現價','波段', 'Head-0618價差比例', '現價-0618比例', '買點', '頸線', 'Head', 'Max_Date', 'Max_Value', 'Min_Date', 'Min_Value', '下載']

        # 設置 Treeview 並定義列
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        self.tree.tag_configure('Blue', background="lightblue")
        self.tree.tag_configure('White', background="white")

        # 定義每個欄位的標題和寬度
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')

        self.tree.heading("下載", text="下載")
        self.tree.column("下載", width=60, anchor="center")  # 設置下載列的寬度和對齊方式

        # 將 Treeview 放置在 LabelFrame 中
        self.tree.grid(row=0, column=0, sticky="nsew")

        # 綁定雙擊事件
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click)

        # 添加垂直滾動條
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        # 添加水平滾動條
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=hsb.set)

        # 設置框架的網格配置，使其能夠隨著窗口調整大小
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
    def calculate(self):
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
            'daily': {period: var.get() for period, var in self.daily_ma_vars.items()},
            'weekly': {period: var.get() for period, var in self.weekly_ma_vars.items()},
            'monthly': {period: var.get() for period, var in self.monthly_ma_vars.items()}
        }

        # 清空 TreeView 中的現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        all_wave_extremes = self.controller.calculate(start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections)

        # 設置標籤樣式
        self.tree.tag_configure('blue_text', foreground='blue')
        self.tree.tag_configure('red_text', foreground='red')
        
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
            spread_ratio = round(segment['spread_ratio'], 3)  # 價差比例
            ratio_0618_ratio = round(segment['latest_close_price-0.618_ratio'], 3)
            # 修改這裡：每三行為一組，組間交替顏色
            group_number = index // 3
            tag = 'Blue' if group_number % 2 == 0 else 'White'
            
            values = (stock_id, stock_name, latest_close_price, wave_type, spread_ratio, ratio_0618_ratio, ratio_0618, ratio_1, max_value, max_date, max_value, min_date, min_value, '')
            
            if wave_type == '最高波段':
                values = values[:-1] + ('下載',)
            elif wave_type == '最近波段':
                values = values[:-1] + ('詳細資料',)

            item = self.tree.insert('', 'end', values=values, tags=(tag,))
            
            # 為現價和買點設置特定的顏色
            # self.tree.set(item, column='現價', value=latest_close_price)
            # self.tree.item(item, tags=(tag, 'blue_text'), values=values)
            
            # self.tree.set(item, column='買點', value=ratio_0618)
            # self.tree.item(item, tags=(tag, 'red_text'), values=values)


    def show_error(self, message):
        messagebox.showerror("錯誤", message)

    def on_double_click(self, event):
        item = self.tree.selection()[0]  # 獲取選中的項目
        stock_code = self.tree.item(item, "values")[0]  # 獲取第一列（股票代碼）
        pyperclip.copy(stock_code)  # 複製到剪貼板
        self.show_copy_message(stock_code)

    def on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if column == f"#{len(self.tree['columns'])}" and self.tree.item(item, "values")[13] == '下載':  # 最後一列
                stock_id = self.tree.item(item, "values")[0]  # 假設股票代碼是第一列
                max_date = self.tree.item(item, "values")[9]  # 最高價波段日期
                self.download_detail_data(stock_id, max_date)
            elif column == f"#{len(self.tree['columns'])}" and self.tree.item(item, "values")[13] == '詳細資料':  # 最後一列
                stock_id = self.tree.item(item, "values")[0]  # 假設股票代碼是第一列
                # 點擊詳細資料，顯示詳細資料，會彈跳出一個視窗以顯示詳細資料
                self.show_detail_data(stock_id)

    def show_copy_message(self, stock_code):
        # 創建一個臨時標籤來顯示複製成功的消息
        msg = ttk.Label(self, text=f"已複製股票代碼: {stock_code}", foreground="green")
        msg.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 設置定時器，2秒後刪除消息
        self.after(2000, msg.destroy)

    def export_stock_codes(self):
        # 獲取所有股票代碼，保持原始順序
        stock_codes = OrderedDict()
        for item in self.tree.get_children():
            stock_code = self.tree.item(item, "values")[0]
            if stock_code not in stock_codes:
                stock_codes[stock_code] = None

        # 將股票代碼分組，每組最多60個
        stock_codes = list(stock_codes.keys())
        lines = ["\t".join(stock_codes[i:i+60]) for i in range(0, len(stock_codes), 60)]

        # 獲取下載資料夾路徑
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # 設置默認文件名
        default_filename = "stock_codes.txt"
        
        # 選擇文件保存位置，設置初始目錄為下載資料夾
        file_path = filedialog.asksaveasfilename(
            initialdir=downloads_path,
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))
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
        
    def show_detail_data(self, stock_id):
        # 彈跳出一個視窗以顯示詳細資料
        self.controller.show_detail_data(stock_id)
        

    def show_sma_data(self, stock_id, sma_data):
        detail_window = tk.Toplevel(self)
        detail_window.title(f"詳細資料 - {stock_id}")
        # 在這視窗內顯示sma_data
        sma_text = f"日均線: {sma_data[0]}\n周均線: {sma_data[1]}\n月均線: {sma_data[2]}"
        sma_label = tk.Label(detail_window, text=sma_text)
        sma_label.pack()

