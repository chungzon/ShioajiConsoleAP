import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import datetime
import threading
from tkcalendar import DateEntry

class StockView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("股票分析系統")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=1, fill='both')

        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='股票資料分析')

        self.download_ticks_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_ticks_frame, text='下載Ticks及KBar數據')

        self.create_main_tab()
        self.create_download_ticks_tab()

    def create_main_tab(self):
        # 股票代碼
        ttk.Label(self.main_frame, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.entry_stock_id = ttk.Entry(self.main_frame)
        self.entry_stock_id.grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(self.main_frame, text="檢查資料", command=self.controller.check_stock_data).grid(row=0, column=2, padx=10, pady=5)

        # 起始日期
        ttk.Label(self.main_frame, text="起始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_start_date = DateEntry(self.main_frame, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_start_date.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # 結束日期
        ttk.Label(self.main_frame, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_end_date = DateEntry(self.main_frame, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_end_date.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # 儲存路徑
        ttk.Label(self.main_frame, text="儲存路徑:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.entry_file_path = ttk.Entry(self.main_frame)
        self.entry_file_path.grid(row=3, column=1, padx=10, pady=5)
        ttk.Button(self.main_frame, text="瀏覽", command=self.controller.browse_file).grid(row=3, column=2, padx=10, pady=5)

        # Ticks 更新日期
        self.label_update_date_ticks = ttk.Label(self.main_frame, text="Ticks 更新日期: 未知")
        self.label_update_date_ticks.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        self.button_update_ticks = ttk.Button(self.main_frame, text="更新 Ticks", command=self.controller.update_data_ticks)
        self.button_update_ticks.grid(row=4, column=2, padx=10, pady=5)

        # Kbars 更新日期
        self.label_update_date_kbars = ttk.Label(self.main_frame, text="Kbars 更新日期: 未知")
        self.label_update_date_kbars.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        self.button_update_kbars = ttk.Button(self.main_frame, text="更新 Kbars", command=self.controller.update_data_kbars)
        self.button_update_kbars.grid(row=5, column=2, padx=10, pady=5)

        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        # 狀態標籤
        self.status_label = ttk.Label(self.main_frame, text="狀態: ")
        self.status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

        # 確認和分析資料按鈕
        ttk.Button(self.main_frame, text="分析資料", command=self.controller.analyze_data).grid(row=9, column=0, columnspan=3, pady=20)
        
    def create_download_ticks_tab(self):
        ttk.Label(self.download_ticks_frame, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.stock_id_ticks_entry = ttk.Entry(self.download_ticks_frame)
        self.stock_id_ticks_entry.grid(row=0, column=1, padx=10, pady=5, sticky='e')

        ttk.Label(self.download_ticks_frame, text="開始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.start_date_ticks_entry = DateEntry(self.download_ticks_frame, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.start_date_ticks_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')

        ttk.Label(self.download_ticks_frame, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.end_date_ticks_entry = DateEntry(self.download_ticks_frame, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.end_date_ticks_entry.grid(row=2, column=1, padx=10, pady=5, sticky='w')
        
        self.progress = ttk.Progressbar(self.download_ticks_frame, orient='horizontal', length=200, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        ttk.Button(self.download_ticks_frame, text="下載", command=self.start_download).grid(row=4, column=0, columnspan=2, pady=10)
        

    def start_download(self):
        stock_id = self.stock_id_ticks_entry.get()
        start_date = self.start_date_ticks_entry.get()
        end_date = self.end_date_ticks_entry.get()

        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        # 重置進度條
        self.progress['value'] = 0

        # 創建執行序
        ticks_thread = threading.Thread(target=self.update_ticks, args=(stock_id, start_date, end_date))
        kbars_thread = threading.Thread(target=self.update_kbars, args=(stock_id, start_date, end_date))

        # 啟動執行序
        ticks_thread.start()
        kbars_thread.start()

        # 等待所有執行序完成後更新進度條
        self.monitor_threads([ticks_thread, kbars_thread])

    def monitor_threads(self, threads):
        if any(thread.is_alive() for thread in threads):
            self.progress['value'] += 50 / len(threads)
            self.download_ticks_frame.after(100, self.monitor_threads, threads)
        else:
            self.progress['value'] = 100

    def update_ticks(self, stock_id, start_date, end_date):
        self.controller.update_data("Ticks", stock_id, start_date, end_date)

    def update_kbars(self, stock_id, start_date, end_date):
        self.controller.update_data("Kbars", stock_id, start_date, end_date)
    def download_ticks_and_kbar(self):
        stock_id = self.stock_id_ticks_entry.get()
        start_date = datetime.datetime.strptime(self.start_date_ticks_entry.get(), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(self.end_date_ticks_entry.get(), "%Y-%m-%d")
        self.controller.update_data("Ticks", stock_id, start_date, end_date)
        self.controller.update_data("Kbars", stock_id, start_date, end_date)

    def set_status(self, status):
        self.status_label.config(text=f"狀態: {status}")

    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def mainloop(self):
        self.root.mainloop()

