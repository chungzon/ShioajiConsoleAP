import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import tkinter as tk
from tkinter import ttk, messagebox


class StockView:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("股票資料分析器")

        # 股票代碼
        tk.Label(self.root, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_stock_id = tk.Entry(self.root)
        self.entry_stock_id.grid(row=0, column=1, padx=10, pady=5)
        tk.Button(self.root, text="檢查資料", command=self.controller.check_stock_data).grid(row=0, column=2, padx=10, pady=5)

        # 起始日期
        tk.Label(self.root, text="起始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_start_date = tk.Entry(self.root)
        self.entry_start_date.grid(row=1, column=1, padx=10, pady=5)

        # 結束日期
        tk.Label(self.root, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5)
        self.entry_end_date = tk.Entry(self.root)
        self.entry_end_date.grid(row=2, column=1, padx=10, pady=5)

        # 儲存路徑
        tk.Label(self.root, text="儲存路徑:").grid(row=3, column=0, padx=10, pady=5)
        self.entry_file_path = tk.Entry(self.root)
        self.entry_file_path.grid(row=3, column=1, padx=10, pady=5)
        tk.Button(self.root, text="瀏覽", command=self.controller.browse_file).grid(row=3, column=2, padx=10, pady=5)

        # Ticks 更新日期
        self.label_update_date_ticks = tk.Label(self.root, text="Ticks 更新日期: 未知")
        self.label_update_date_ticks.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        self.button_update_ticks = tk.Button(self.root, text="更新 Ticks", command=self.controller.update_data_ticks)
        self.button_update_ticks.grid(row=4, column=2, padx=10, pady=5)

        # Kbars 更新日期
        self.label_update_date_kbars = tk.Label(self.root, text="Kbars 更新日期: 未知")
        self.label_update_date_kbars.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        self.button_update_kbars = tk.Button(self.root, text="更新 Kbars", command=self.controller.update_data_kbars)
        self.button_update_kbars.grid(row=5, column=2, padx=10, pady=5)

        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        # 狀態標籤
        self.status_label = tk.Label(self.root, text="狀態: ")
        self.status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

        # 確認和分析資料按鈕
        # tk.Button(self.root, text="確認", command=self.controller.update_stock_data).grid(row=8, column=0, columnspan=3, pady=20)
        tk.Button(self.root, text="分析資料", command=self.controller.analyze_data).grid(row=9, column=0, columnspan=3, pady=20)

    def set_status(self, status):
        self.status_label.config(text=f"狀態: {status}")

    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def mainloop(self):
        self.root.mainloop()

