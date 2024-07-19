import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pymssql
import pandas as pd
import shioaji as sj
from datetime import datetime, timedelta
import concurrent.futures
import time

# 初始化 Shioaji API
api = sj.Shioaji(simulation=True)
api.login(
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

def connect_db():
    conn = pymssql.connect(
        server='127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn

def get_latest_dates(stock_id):
    conn = connect_db()
    query_ticks = f"""
    SELECT MAX(ts) as latest_date
    FROM Ticks
    WHERE stock_id = '{stock_id}'
    """
    query_kbars = f"""
    SELECT MAX(ts) as latest_date
    FROM Kbars
    WHERE stock_id = '{stock_id}'
    """
    df_ticks = pd.read_sql(query_ticks, conn)
    df_kbars = pd.read_sql(query_kbars, conn)
    conn.close()

    latest_date_ticks = df_ticks['latest_date'].iloc[0]
    latest_date_kbars = df_kbars['latest_date'].iloc[0]

    return latest_date_ticks, latest_date_kbars

def get_kbars(stock_code, start_date, end_date):
    contract = api.Contracts.Stocks[stock_code]
    kbars = api.kbars(contract, start=start_date, end=end_date)
    
    df = pd.DataFrame({**kbars})
    df.ts = pd.to_datetime(df.ts)  # 將時間戳轉換為datetime
    return df

def insert_kbars(df, stock_code):
    conn = connect_db()
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO Kbars (stock_id, ts, Open_Price, High, Low, Close_Price, Volume) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (stock_code, row.ts, row.Open, row.High, row.Low, row.Close, row.Volume)
        )
    
    conn.commit()
    cursor.close()
    conn.close()

def process_kbars(stock_code, start_date, end_date, progress_var, status_label):
    start_time = time.time()
    
    # 獲取Kbars數據
    kbars_df = get_kbars(stock_code, start_date, end_date)
    
    # 插入數據到資料庫
    insert_kbars(kbars_df, stock_code)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 更新進度條和狀態標籤
    progress_var.set(progress_var.get() + 1)
    status_label.config(text=f"單個任務花費時間: {elapsed_time:.2f}秒")
    
    return elapsed_time

def confirm_stock():
    stock_id = entry_stock_id.get()
    if not stock_id:
        messagebox.showerror("錯誤", "股票代碼為必填")
        return

    latest_date_ticks, latest_date_kbars = get_latest_dates(stock_id)
    label_update_date_ticks.config(text=latest_date_ticks.strftime('%Y-%m-%d'))
    label_update_date_kbars.config(text=latest_date_kbars.strftime('%Y-%m-%d'))
    messagebox.showinfo("確認", f"股票代碼: {stock_id}")

def browse_file():
    file_selected = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
    if file_selected:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_selected)

def update_data():
    stock_id = entry_stock_id.get()
    if not stock_id:
        messagebox.showerror("錯誤", "股票代碼為必填")
        return

    latest_date_ticks, latest_date_kbars = get_latest_dates(stock_id)
    start_date = (latest_date_kbars + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    
    total_start_time = time.time()
    
    # 設置進度條
    progress_var.set(0)
    progress_bar.config(maximum=1)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_kbars, stock_id, start_date, end_date, progress_var, status_label)]
        for future in concurrent.futures.as_completed(futures):
            elapsed_time = future.result()
            status_label.config(text=f"單個任務花費時間: {elapsed_time:.2f}秒")
    
    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time
    
    label_update_date_kbars.config(text=end_date)
    messagebox.showinfo("更新", f"資料更新成功，總花費時間: {total_elapsed_time:.2f}秒")

def analyze_data():
    stock_id = entry_stock_id.get()
    file_path = entry_file_path.get()
    if not stock_id or not file_path:
        messagebox.showerror("錯誤", "股票代碼和資料儲存路徑均為必填")
        return
    # 添加分析資料的邏輯
    messagebox.showinfo("分析", f"開始分析資料，股票代碼: {stock_id}, 資料儲存路徑: {file_path}")

# 建立主窗口
root = tk.Tk()
root.title("股票資料分析器")

# 設置網格布局的列和行的權重，使其在窗口調整大小時自適應
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=2)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(3, weight=1)
root.rowconfigure(4, weight=1)
root.rowconfigure(5, weight=1)
root.rowconfigure(6, weight=1)

# 股票代碼
tk.Label(root, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
entry_stock_id = tk.Entry(root)
entry_stock_id.grid(row=0, column=1, padx=10, pady=5, sticky="we")
tk.Button(root, text="確認", command=confirm_stock).grid(row=0, column=2, padx=10, pady=5)

# Ticks 資料更新時間
tk.Label(root, text="Ticks 資料更新時間:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
label_update_date_ticks = tk.Label(root, text="2024-07-16")
label_update_date_ticks.grid(row=1, column=1, padx=10, pady=5, sticky="we")
tk.Button(root, text="更新", command=update_data).grid(row=1, column=2, padx=10, pady=5)

# Kbars 資料更新時間
tk.Label(root, text="Kbars 資料更新時間:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
label_update_date_kbars = tk.Label(root, text="2024-07-16")
label_update_date_kbars.grid(row=2, column=1, padx=10, pady=5, sticky="we")
tk.Button(root, text="更新", command=update_data).grid(row=2, column=2, padx=10, pady=5)

# 資料儲存路徑
tk.Label(root, text="資料儲存路徑:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
entry_file_path = tk.Entry(root, width=50)
entry_file_path.grid(row=3, column=1, padx=10, pady=5, sticky="we")
tk.Button(root, text="瀏覽", command=browse_file).grid(row=3, column=2, padx=10, pady=5)

# 進度條和狀態標籤
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="we")
status_label = tk.Label(root, text="等待更新...")
status_label.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="we")

# 開始分析按鈕
tk.Button(root, text="開始分析", command=analyze_data).grid(row=6, column=0, columnspan=3, pady=20)

# 啟動主循環
root.mainloop()
