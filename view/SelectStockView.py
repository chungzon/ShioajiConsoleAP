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
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtCore import Qt

font_path = 'C:/Windows/Fonts/msjh.ttc'  # 微軟正黑體字體路徑
zh_font = font_manager.FontProperties(fname=font_path)

class SelectStockView(tk.Frame):
    
    def __init__(self, parent, controller, model):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.model = model
        self.init_ui()
        self.data_queue = Queue()  # 用于存储待处理的股票数据
        self.processing = False
        self.start_update_thread()

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
        start_date = end_date - timedelta(days=365)
        self.start_date.set_date(start_date)
        self.end_date.set_date(end_date)

        ttk.Label(row1_frame, text="0618與Head價差比例").pack(side=tk.LEFT, padx=(10,5))
        ttk.Label(row1_frame, text="±").pack(side=tk.LEFT)
        self.ratio_entry = ttk.Entry(row1_frame, width=10)
        self.ratio_entry.pack(side=tk.LEFT, padx=(0,5))
        # 現價-0618比例
        ttk.Label(row1_frame, text="現價-0191比例").pack(side=tk.LEFT, padx=5)
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

        self.ma_selections = {
            'daily': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                      20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=True), 
                      120: tk.BooleanVar(value=False)},
            'weekly': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                       20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=True), 
                       120: tk.BooleanVar(value=False)},
            'monthly': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                        20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=True), 
                        120: tk.BooleanVar(value=False)}
        }
        self.select_all_vars = {
            'daily': tk.BooleanVar(value=False),
            'weekly': tk.BooleanVar(value=False),
            'monthly': tk.BooleanVar(value=False)
        }
        ma_types = [("日均線", 'daily'), ("週均線", 'weekly'), ("月均線", 'monthly')]
        ma_types = [("日均線", 'daily'), ("週均線", 'weekly'), ("月均線", 'monthly')]
        for i, (ma_type, ma_key) in enumerate(ma_types):
            frame = ttk.Frame(row2_frame)
            frame.pack(padx=5, pady=5, anchor="w")
            
            ttk.Label(frame, text=ma_type, width=8).pack(side="left")
            
            # 添加全選 checkbox
            select_all_cb = ttk.Checkbutton(frame, text="全選", 
                                            variable=self.select_all_vars[ma_key],
                                            command=lambda k=ma_key: self.toggle_all(k))
            select_all_cb.pack(side="left", padx=(0, 10))

            for period in [5, 10, 20, 60, 120]:
                cb = ttk.Checkbutton(frame, text=f"{period}", 
                                     variable=self.ma_selections[ma_key][period],
                                     command=lambda k=ma_key: self.update_select_all(k))
                cb.pack(side="left", padx=(0, 5))

        # 設置 LabelFrame 來包含 Treeview
        self.table_frame = ttk.LabelFrame(self, text="股票資訊")
        self.table_frame.grid(row=2, column=0, pady=10, sticky="nsew")

        # 定義欄位名稱
        columns = ['股票代碼', '股票名稱', '現價','波段', 'Head-0618價差比例', '現價-0191比例', '0.191', '0.382', '0.5', '0.618', '0.809', '頸線', 'Head', 'Max_Date', 'Max_Value', 'Min_Date', 'Min_Value', '下載']

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

        # 將 Treeview 放置在 LabelFrame 
        self.tree.grid(row=0, column=0, sticky="nsew")

        # 綁定事件
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
        if self.processing:
            messagebox.showinfo("提示", "正在處理中，請稍候...")
            return
            
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
            'monthly': {period: var.get() for period, var in self.ma_selections['monthly'].items()}
        }

        # 清空 TreeView 中的現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.processing = True
        
        # 启动处理线程
        process_thread = threading.Thread(
            target=self.process_calculation,
            args=(start_date, end_date, ratio, positive_ratio, native_ratio,
                  top_n, recent_wave_var, highest_wave_var, total_wave_var,
                  ma_selections)
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
            self.tree.after(0, self._calculation_finished)

    def _calculation_finished(self):
        """计算完成后的处理"""
        if not self.processing:
            messagebox.showinfo("完成", "篩選完成")

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
            if column == f"#{len(self.tree['columns'])}" and self.tree.item(item, "values")[17] == '下載':  # 最後一列
                stock_id = self.tree.item(item, "values")[0]  # 假設股票代碼是第一列
                max_date = self.tree.item(item, "values")[9]  # 最高價波段日期
                self.download_detail_data(stock_id, max_date)
            elif column == f"#{len(self.tree['columns'])}" and self.tree.item(item, "values")[17] == '詳細資料':  # 最後一列
                stock_id = self.tree.item(item, "values")[0]  # 假設股票代碼是第一列
                stock_name = self.tree.item(item, "values")[1]  # 股票名稱
                # 點擊詳細資料，顯示詳細資料會彈跳出一個視窗顯示詳細資料
                self.show_detail_data(stock_id, stock_name)

    def show_copy_message(self, stock_code):
        # 創建一個臨時標來顯示複製成功的消息
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

    def create_ratio_table(self, ratio_prices, indicator_prices, organized_ma_data):
        table = QTableWidget()
        table.setColumnCount(3)  # 改为3列：比例、總波段、指標
        
        # 设置固定的比例序列
        ratios = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                 '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                 '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                 '3.191', '3.382', '3.5', '3.618', '3.809', '4']
        
        # 计算总行数（包括前后和中间的空白行）
        total_rows = (len(ratios) * 2 - 1) + 2  # 加2是为了前后的空白行
        table.setRowCount(total_rows)
        table.setHorizontalHeaderLabels(["比例", "總波段", "指標"])

        font = QFont()
        font.setPointSize(13)
        table.setFont(font)
        table.horizontalHeader().setFont(font)
        
        # 辅助函数：添加数据到单元格并按价格排序
        def add_to_cell(row, col, new_text, is_daily_ma=False):
            current_item = table.item(row, col)
            current_text = current_item.text() if current_item else ""
            
            # 收集所有价格项及其属性（是否为日均价）
            all_items = []
            if current_text:
                lines = current_text.split('\n')
                for line in lines:
                    is_daily = line.startswith('日')
                    all_items.append((line, is_daily))
            if new_text:
                all_items.append((new_text, is_daily_ma))
            
            # 提取价格进行排序
            def extract_price(item_tuple):
                text = item_tuple[0]
                try:
                    # 提取价格，支持多种格式
                    if '：' in text:
                        price = float(text.split('：')[-1].split('(')[0])
                    elif ':' in text:
                        price = float(text.split(':')[-1].split('(')[0])
                    else:
                        price = float(text.split()[-1])
                    return price  # 直接返回价格，实现从小到大排序
                except:
                    return float('inf')  # 无法提取价格的项放到最后
            
            # 按价格从小到大排序
            all_items.sort(key=extract_price)
            
            # 创建最终的表格项
            text_lines = []
            for text, is_daily in all_items:
                # 为每一行创建新的表格项
                item = QTableWidgetItem(text)
                if is_daily:
                    item.setForeground(QBrush(QColor("red")))
                else:
                    item.setForeground(QBrush(QColor("black")))
                text_lines.append(item)
            
            # 合并所有文本
            final_text = '\n'.join(item.text() for item in text_lines)
            new_item = QTableWidgetItem(final_text)
            
            # 设置背景色
            if current_item:
                new_item.setBackground(current_item.background())
            else:
                is_alternate = (row % 2) == 0
                color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
                new_item.setBackground(QBrush(color))
            
            # 设置文本颜色
            if is_daily_ma:
                new_item.setForeground(QBrush(QColor("red")))
            
            table.setItem(row, col, new_item)
        
        # 设置交替行颜色
        def set_row_color(table, row, is_alternate):
            color = QColor("#FFFFFF") if is_alternate else QColor("#E6F3FF")  # 淺灰色 : 淺藍色
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                item.setBackground(QBrush(color))
                table.setItem(row, col, item)
        
        # 首先创建所有单元格并设置颜色
        for row in range(total_rows):
            # 第一行和最后一行是浅灰色
            if row == 0 or row == total_rows - 1:
                set_row_color(table, row, True)
            # 其他行交替设置颜色
            else:
                is_alternate = (row % 2) == 0  # 偶数行使用浅灰色
                set_row_color(table, row, is_alternate)
        
        # 填充比例和总波段数据（向下偏移一行）
        for i, ratio in enumerate(ratios):
            row = (i * 2) + 1  # 偏移一行
            
            # 设置比例行的颜色（奇数行）
            set_row_color(table, row, False)
            
            # 设置比例
            ratio_item = QTableWidgetItem(ratio)
            is_alternate = (row % 2) == 0
            color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
            ratio_item.setBackground(QBrush(color))
            table.setItem(row, 0, ratio_item)
            
            # 设置总波段价格
            price = ratio_prices['總波段'].get(ratio, 'N/A')
            if hasattr(price, 'item'):
                price = f"{price.item():.2f}"
            price_item = QTableWidgetItem(str(price))
            price_item.setBackground(QBrush(color))
            table.setItem(row, 1, price_item)
            
            # 添加空白行并设置颜色（偶数行）
            if i < len(ratios) - 1:
                row_between = row + 1
                set_row_color(table, row_between, True)
                for col in range(table.columnCount()):
                    table.setItem(row_between, col, QTableWidgetItem(""))
        
        # 设置第一行（0之前的空白行）和最后一行的颜色
        set_row_color(table, 0, True)  # 第一个空白行
        set_row_color(table, total_rows - 1, True)  # 最后一个空白行
        
        # 辅助函数：确定值应该填入哪一行
        def find_row_for_value(value):
            min_price = float(ratio_prices['總波段']['0'])
            max_price = float(ratio_prices['總波段']['4'])
            
            # 如果价格小于最小比例价格
            if value < min_price:
                return 0  # 第一个空白行
            
            # 如果价格大于最大比例价
            if value > max_price:
                return total_rows - 1  # 最后一个空白行
            
            # 在比例价格之间查找位置
            for i, ratio in enumerate(ratios[:-1]):
                current_price = float(ratio_prices['總波段'][ratio])
                next_price = float(ratio_prices['總波段'][ratios[i + 1]])
                
                row = (i * 2) + 1  # 考虑偏移
                
                if abs(value - current_price) < 0.01:
                    return row
                elif current_price < value < next_price or next_price < value < current_price:
                    return row + 1
            
            return total_rows - 1  # 如果没找到合适的位置，放在最后

        # 处理均线数据 - 现在添加到指标列
        ma_types = {
            '日均線': '日',
            '週均線': '周',
            '月均線': '月'
        }
        
        for ma_key, prefix in ma_types.items():
            ma_data = organized_ma_data[ma_key]
            for ma_period in ['5MA', '10MA', '20MA', '60MA', '120MA']:
                if ma_period not in ma_data or ma_data[ma_period] == 'N/A':
                    continue
                    
                value = ma_data[ma_period]
                if hasattr(value, 'item'):
                    value = value.item()
                
                period_num = ma_period.replace('MA', '')
                ma_text = f"{prefix}({period_num})：{value:.2f}"
                
                # 找到应该填入的行
                row = find_row_for_value(value)
                add_to_cell(row, 2, ma_text)  # 现在添加到指标列(列索引2)
        
        # 处理指标数据
        for indicator_name, value in indicator_prices.items():
            if hasattr(value, 'item'):
                value = value.item()
            
            # 找到应该填入的行
            row = find_row_for_value(value)
            indicator_text = f"{indicator_name}：{value:.2f}"
            add_to_cell(row, 2, indicator_text)  # 添加到指标列
        
        # 调整行高和列宽
        for row in range(table.rowCount()):
            table.resizeRowToContents(row)
        table.resizeColumnsToContents()
        
        return table

    def show_sma_data(self, stock_id, stock_name, organized_ma_data, ratio_prices, additional_data, indicator_prices):
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
        ratio_layout = QVBoxLayout()
        ratio_table = self.create_ratio_table(ratio_prices, indicator_prices, organized_ma_data)
        ratio_layout.addWidget(ratio_table)
        self.ratio_tab.setLayout(ratio_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.detail_window.setLayout(main_layout)
        
        self.detail_window.show()

    def insert_table_row(self, table, row, values):
        """輔助函數：插��一行數據到表格中"""
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
                self.tree.after(0, self._update_tree_safe, stock_segment)
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
        """在主线程中安全地更新树形视图"""
        try:
            # 获取当前树形视图中的项目数
            current_items = len(self.tree.get_children())
            group_number = current_items // 3
            tag = 'Blue' if group_number % 2 == 0 else 'White'

            # 准备数据
            values = self._prepare_tree_values(stock_segment)
            
            # 插入数据
            self.tree.insert('', 'end', values=values, tags=(tag,))
            
            # 确保视图滚动到最新项目
            self.tree.yview_moveto(1)
            
        except Exception as e:
            print(f"Error in _update_tree_safe: {e}")
            # print(f"Stock segment data: {stock_segment}")

    def _prepare_tree_values(self, stock_segment):
        """准备树形视图的数据"""
        try:
            return (
                stock_segment['stock_id'],
                stock_segment['name'],
                stock_segment['latest_close_price'],
                stock_segment['wave_type'],
                round(stock_segment['spread_ratio'], 3),
                round(stock_segment['latest_close_price-0.191_ratio'], 3),
                round(stock_segment['Ratio_0.191'], 2),
                round(stock_segment['Ratio_0.382'], 2),
                round(stock_segment['Ratio_0.5'], 2),
                round(stock_segment['Ratio_0.618'], 2),
                round(stock_segment['Ratio_0.809'], 2),
                round(stock_segment['Ratio_1'], 2),
                stock_segment['Max_Value'],
                stock_segment['Max_Date'],
                stock_segment['Max_Value'],
                stock_segment['Min_Date'],
                stock_segment['Min_Value'],
                '下載' if stock_segment['wave_type'] == '最高波段' else '詳細資料'
            )
        except Exception as e:
            print(f"Error in _prepare_tree_values: {e}")
            # print(f"Stock segment data: {stock_segment}")
            return None

