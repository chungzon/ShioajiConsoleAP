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

from common.Math import Math

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
                      20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=False), 
                      120: tk.BooleanVar(value=False)},
            'weekly': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                       20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=False), 
                       120: tk.BooleanVar(value=False)},
            'monthly': {5: tk.BooleanVar(value=False), 10: tk.BooleanVar(value=False), 
                        20: tk.BooleanVar(value=False), 60: tk.BooleanVar(value=False), 
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
            'daily': {period: var.get() for period, var in self.ma_selections['daily'].items()},
            'weekly': {period: var.get() for period, var in self.ma_selections['weekly'].items()},
            'monthly': {period: var.get() for period, var in self.ma_selections['monthly'].items()}
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
            ratio_0191 = round(segment['Ratio_0.191'], 2)
            ratio_0382 = round(segment['Ratio_0.382'], 2)
            ratio_0500 = round(segment['Ratio_0.5'], 2)
            ratio_0618 = round(segment['Ratio_0.618'], 2)
            ratio_0809 = round(segment['Ratio_0.809'], 2)
            ratio_1 = round(segment['Ratio_1'], 2) # 頸線
            spread_ratio = round(segment['spread_ratio'], 3)  # 價差比例
            ratio_0191_ratio = round(segment['latest_close_price-0.191_ratio'], 3)
            # 修改這裡：每三行為一組，組間交替顏色
            group_number = index // 3
            tag = 'Blue' if group_number % 2 == 0 else 'White'
            
            values = (stock_id, stock_name, latest_close_price, wave_type, spread_ratio, ratio_0191_ratio, ratio_0191, ratio_0382, ratio_0500, ratio_0618, ratio_0809, ratio_1, max_value, max_date, max_value, min_date, min_value, '')
            
            if wave_type == '最高波段':
                values = values[:-1] + ('下載',)
            elif wave_type == '最近波段':
                values = values[:-1] + ('詳細資料',)

            item = self.tree.insert('', 'end', values=values, tags=(tag,))


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
        

    def show_sma_data(self, stock_id, organized_ma_data, ratio_prices, additional_data, indicator_prices):
        detail_window = tk.Toplevel(self)
        detail_window.title(f"詳細資料 - {stock_id}")
        detail_window.geometry("750x750")  # 視窗大小

        # 創建更大的字體
        # large_font = tkfont.Font(family="Helvetica", size=12)

        notebook = ttk.Notebook(detail_window)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        style = ttk.Style()
        style.configure('.', font=('Microsoft JhengHei', 14))
        style.configure('Treeview', font=('Microsoft JhengHei', 14))
        style.configure('Treeview.Heading', font=('Microsoft JhengHei', 14))

        # 均線數據選項卡
        for ma_type, ma_values in organized_ma_data.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=ma_type)

            tree = ttk.Treeview(frame, columns=('Period', 'Value'), show='headings', style="Treeview")
            tree.heading('Period', text='週期')
            tree.heading('Value', text='值')
            tree.column('Period', width=120, anchor='center')
            tree.column('Value', width=120, anchor='center')

            for period, value in ma_values.items():
                tree.insert('', 'end', values=(period, value))

            tree.pack(expand=True, fill='both')

        # 比例價格選項卡
        ratio_frame = ttk.Frame(notebook)
        notebook.add(ratio_frame, text="比例價格")

        ratio_tree = ttk.Treeview(ratio_frame, columns=('Ratio', 'Recent', 'Total', 'CDP'), 
                                 show='headings', style="Treeview")
        ratio_tree.heading('Ratio', text='比例')
        ratio_tree.heading('Recent', text='最近波段')
        ratio_tree.heading('Total', text='總波段')
        ratio_tree.heading('CDP', text='指標')
        ratio_tree.column('Ratio', width=100, anchor='center')
        ratio_tree.column('Recent', width=100, anchor='center')
        ratio_tree.column('Total', width=100, anchor='center')
        ratio_tree.column('CDP', width=100, anchor='center')

        ratio_tree.tag_configure('oddrow', background='#E8E8E8')
        ratio_tree.tag_configure('evenrow', background='#FFFFFF')

        # 初始化每個比例的指標顯示字典
        indicator_displays = {}
        
        # 依序處理每個指標
        indicator_types = ['AH', 'AL', 'CDP', 'NH', 'NL']
        for indicator_type in indicator_types:
            price = indicator_prices.get(indicator_type, 'N/A')
            if price == 'N/A':
                continue
                
            try:
                price_value = float(price)
                closest_ratio = self.find_closest_ratio(price_value, ratio_prices['總波段'])
                
                if closest_ratio:
                    adjusted_ratio = Math.adjust_ratio_price(price_value)
                    indicator_text = f"{indicator_type}:{price}({adjusted_ratio})\t"
                    
                    # 如果該比例已有指標，則添加到現有文本後面
                    if closest_ratio in indicator_displays:
                        indicator_displays[closest_ratio] += f"{indicator_text}"
                    else:
                        indicator_displays[closest_ratio] = indicator_text
                        
            except (ValueError, TypeError):
                continue

        # 顯示數據
        for i, ratio in enumerate(ratio_prices['最近波段'].keys()):
            tags = ('oddrow',) if i % 2 else ('evenrow',)
            indicator_display = indicator_displays.get(ratio, '')
            
            ratio_tree.insert('', 'end', values=(ratio, 
                                                ratio_prices['最近波段'][ratio], 
                                                ratio_prices['總波段'][ratio],
                                                indicator_display),
                             tags=tags)

        ratio_tree.pack(expand=True, fill='both')

        # 額外數據選項卡
        additional_frame = ttk.Frame(notebook)
        notebook.add(additional_frame, text="其他數據")

        additional_tree = ttk.Treeview(additional_frame, columns=('Item', 'Value'), show='headings', style="Treeview")
        additional_tree.heading('Item', text='項目')
        additional_tree.heading('Value', text='值')
        additional_tree.column('Item', width=180, anchor='center')
        additional_tree.column('Value', width=180, anchor='center')

        for item, value in additional_data.items():
            additional_tree.insert('', 'end', values=(item, value))

        additional_tree.pack(expand=True, fill='both')

        # 添加一個關閉按鈕
        close_button = ttk.Button(detail_window, text="關閉", command=detail_window.destroy)
        close_button.pack(pady=10)

        # 設置按鈕字體
        # close_button.configure(style="TButton")
        # style.configure("TButton", font=large_font)

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

