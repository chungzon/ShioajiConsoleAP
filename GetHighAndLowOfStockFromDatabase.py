import pymssql
import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog


def connect_db():
    conn = pymssql.connect(
        server = '127.0.0.1:1433',
        user='TSE_USER',
        password='fuckme',
        database='TSE'
    )
    return conn


def get_stock_data_from_db(stock_id, start_date, end_date):
    conn = connect_db()
    query = f"""
    SELECT ts, Open_Price, High, Low, Close_Price, Volume
    FROM Kbars
    WHERE stock_id = {stock_id} AND ts >= '{start_date}' AND ts <= DATEADD(day, 1, '{end_date}')
    """
    df = pd.read_sql(query, conn)
    df['ts'] = pd.to_datetime(df['ts'])
    df['date'] = df['ts'].dt.date
    conn.close()
    return df


def save_to_excel(df, stock_id, start_date, end_date, save_path):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    file_name = f"{stock_id}_{start_date}_to_{end_date}.xlsx"
    file_path = os.path.join(save_path, file_name)
    
    df.to_excel(file_path, index=False)
    messagebox.showinfo("完成", f"資料已儲存到: {file_path}")


def main(stock_id, start_date, end_date, save_path):
    df = get_stock_data_from_db(stock_id, start_date, end_date)
    daily_high_low = df.groupby('date').agg({'High': 'max', 'Low': 'min'}).reset_index()
    save_to_excel(daily_high_low, stock_id, start_date, end_date, save_path)


def create_gui():
    def run():
        stock_id = entry_stock_id.get()
        start_date = entry_start_date.get()
        end_date = entry_end_date.get()
        save_path = entry_save_path.get()

        if not stock_id or not start_date or not end_date or not save_path:
            messagebox.showerror("錯誤", "所有欄位均為必填")
            return

        main(stock_id, start_date, end_date, save_path)

    def browse_directory():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry_save_path.delete(0, tk.END)
            entry_save_path.insert(0, folder_selected)

    root = tk.Tk()
    root.title("股票資料下載器")

    tk.Label(root, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5)
    entry_stock_id = tk.Entry(root)
    entry_stock_id.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="起始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
    entry_start_date = tk.Entry(root)
    entry_start_date.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(root, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5)
    entry_end_date = tk.Entry(root)
    entry_end_date.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(root, text="儲存路徑:").grid(row=3, column=0, padx=10, pady=5)
    entry_save_path = tk.Entry(root)
    entry_save_path.grid(row=3, column=1, padx=10, pady=5)
    tk.Button(root, text="瀏覽", command=browse_directory).grid(row=3, column=2, padx=10, pady=5)

    tk.Button(root, text="下載資料", command=run).grid(row=4, column=0, columnspan=3, pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
