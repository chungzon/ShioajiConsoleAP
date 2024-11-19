import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import datetime
import threading

class DataDownloadView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        ttk.Label(self, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.stock_id_entry = ttk.Entry(self)
        self.stock_id_entry.grid(row=0, column=1, padx=10, pady=5, sticky='e')

        ttk.Label(self, text="開始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.start_date_ticks_entry = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.start_date_ticks_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')

        ttk.Label(self, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.end_date_ticks_entry = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.end_date_ticks_entry.grid(row=2, column=1, padx=10, pady=5, sticky='w')

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self, orient='horizontal', length=200, mode='determinate', variable=self.progress_var, maximum=100)
        self.progress.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        ttk.Button(self, text="下載", command=self.start_download).grid(row=4, column=0, columnspan=2, pady=10)

        # 下載全部股票KBar
        ttk.Button(self, text="下載全部股票分K資料", command=self.start_download_all).grid(row=4, column=2, pady=10)

    def start_download(self):
        stock_id = self.stock_id_entry.get()
        start_date = self.start_date_ticks_entry.get()
        end_date = self.end_date_ticks_entry.get()

        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        # 重置進度條
        self.update_progress(0)
        self.update_kbars(stock_id, start_date, end_date)

    def update_ticks(self, stock_id, start_date, end_date):
        self.controller.update_data("Ticks", stock_id, start_date, end_date)

    def update_kbars(self, stock_id, start_date, end_date):
        self.controller.update_data("Kbars", stock_id, start_date, end_date)
        
    def update_progress(self, value):
        self.progress_var.set(value)
        self.update_idletasks()
        
    def set_progress_config(self, dates):
        self.progress.config(maximum=dates)

    # 下載全部股票KBar
    def start_download_all(self):
        start_date = self.start_date_ticks_entry.get()
        end_date = self.end_date_ticks_entry.get()
        self.controller.start_download_all(start_date, end_date)

    def handle_log_message(self, event):
        # 使用 after 方法確保在主線程中更新 GUI
        self.after(0, lambda: self.append_log(event.data))

    def append_log(self, message):
        print(message)