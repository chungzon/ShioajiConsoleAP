import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import datetime
import threading
import AutoDownloadDailyClosePrice

class DailyClosePriceDownloadView(tk.Frame):
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

        self.log_text = tk.Text(self, wrap="word", height=10, state="disabled")
        self.log_text.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        ttk.Button(self, text="下載", command=self.start_download_thread).grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(self, text="下載當日收盤價", command=self.start_download_all_thread).grid(row=5, column=1, pady=10)

    def start_download_thread(self):
        # 開始一個新線程來處理下載，以防止卡住GUI
        thread = threading.Thread(target=self.start_download)
        thread.start()

    def start_download(self):
        stock_id = self.stock_id_entry.get()
        start_date = self.start_date_ticks_entry.get()
        end_date = self.end_date_ticks_entry.get()

        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        # 重置進度條
        self.update_progress(0)
        if stock_id:
            self.controller.download_daily_close_price(start_date, end_date, stock_id)
        else:
            self.controller.download_daily_close_price(start_date, end_date)

    def download_daily_close_price(self, start_date, end_date):
        self.model.download_daily_close_top30_stock(start_date, end_date)

    def update_progress(self, value):
        self.progress_var.set(value)
        self.update_idletasks()

    def set_progress_config(self, dates):
        self.progress.config(maximum=dates)

    def append_log(self, message):
        # 解鎖text，插入新消息後鎖定
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)  # 自動滾動到最後一行
        self.log_text.config(state="disabled")
        self.update_idletasks()

    def start_download_all_thread(self):
        # 创建一个新线程来运行自动下载
        thread = threading.Thread(target=self.run_auto_download)
        thread.start()

    def run_auto_download(self):
        # 创建 AutoDownloadDailyClosePrice 类的实例
        auto_downloader = AutoDownloadDailyClosePrice.AutoDownloadDailyClosePrice()
        auto_downloader.run()