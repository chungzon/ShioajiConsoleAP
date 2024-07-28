import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import datetime
import threading

class DataAnalysisView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
         # 股票代碼
        ttk.Label(self, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.entry_stock_id = ttk.Entry(self)
        self.entry_stock_id.grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(self, text="檢查資料", command=self.check_stock_data).grid(row=0, column=2, padx=10, pady=5)

        # 起始日期
        ttk.Label(self, text="起始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_start_date = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_start_date.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # 結束日期
        ttk.Label(self, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_end_date = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_end_date.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # 儲存路徑
        ttk.Label(self, text="儲存路徑:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.entry_file_path = ttk.Entry(self)
        self.entry_file_path.grid(row=3, column=1, padx=10, pady=5)
        ttk.Button(self, text="瀏覽", command=self.browse_file).grid(row=3, column=2, padx=10, pady=5)

        # Ticks 更新日期
        self.label_update_date_ticks = ttk.Label(self, text="Ticks 更新日期: 未知")
        self.label_update_date_ticks.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        # self.button_update_ticks = ttk.Button(self, text="更新 Ticks", command=self.controller.update_data_ticks)
        # self.button_update_ticks.grid(row=4, column=2, padx=10, pady=5)

        # Kbars 更新日期
        self.label_update_date_kbars = ttk.Label(self, text="Kbars 更新日期: 未知")
        self.label_update_date_kbars.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        # self.button_update_kbars = ttk.Button(self, text="更新 Kbars", command=self.controller.update_data_kbars)
        # self.button_update_kbars.grid(row=5, column=2, padx=10, pady=5)

        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        # 狀態標籤
        self.status_label = ttk.Label(self, text="狀態: ")
        self.status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

        # 確認和分析資料按鈕
        ttk.Button(self, text="分析資料", command=self.analyze_data).grid(row=9, column=0, columnspan=3, pady=20)
        


    def check_stock_data(self):
        self.controller.check_stock_data()
        
    def browse_file(self):
        self.controller.browse_file()
        
    def set_status(self, status):
        self.status_label.config(text=f"狀態: {status}")
        
    def analyze_data(self):
        self.controller.analyze_data()

        
    # def start_download(self):
    #     stock_id = self.stock_id_entry.get()
    #     start_date = self.start_date_ticks_entry.get()
    #     end_date = self.end_date_ticks_entry.get()

    #     start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    #     end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    #     # 重置進度條
    #     self.update_progress(0)
    #     self.update_kbars(stock_id, start_date, end_date)

    # def update_ticks(self, stock_id, start_date, end_date):
    #     self.controller.update_data("Ticks", stock_id, start_date, end_date)

    # def update_kbars(self, stock_id, start_date, end_date):
    #     self.controller.update_data("Kbars", stock_id, start_date, end_date)
        
    # def update_progress(self, value):
    #     self.progress_var.set(value)
    #     self.update_idletasks()
        
    # def set_progress_config(self, dates):
    #     self.progress.config(maximum=dates)
