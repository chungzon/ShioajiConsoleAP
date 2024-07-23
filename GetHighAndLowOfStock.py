# import shioaji as sj
# import pandas as pd
# import os

# # 初始化 Shioaji API
# api = sj.Shioaji(simulation=True)
# api.login(
#     api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
#     secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
# )

# # 取得股票歷史價格資料
# def get_stock_data(stock_id, start_date, end_date):
#     kbars = api.kbars(api.Contracts.Stocks[stock_id], start=start_date, end=end_date)
#     df = pd.DataFrame({**kbars})
#     df.ts = pd.to_datetime(df.ts)
#     df['date'] = df['ts'].dt.date
#     return df

# # 儲存資料到Excel
# def save_to_excel(df, stock_id, start_date, end_date):
#     # 設定儲存路徑和檔名
#     save_path = "D:\\TradingData"
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)
    
#     file_name = f"{stock_id}_{start_date}_to_{end_date}.xlsx"
#     file_path = os.path.join(save_path, file_name)
    
#     # 將資料儲存為Excel檔案
#     df.to_excel(file_path, index=False)
#     print(f"資料已儲存到: {file_path}")

# # 主函數
# def main():
#     stock_id = "1325"  # 替換成你想要分析的股票ID
#     start_date = "2020-06-01"
#     end_date = "2024-06-27"

#     # 取得股票數據
#     df = get_stock_data(stock_id, start_date, end_date)

#     # 計算每日最高價和最低價
#     daily_high_low = df.groupby('date').agg({'High': 'max', 'Low': 'min'}).reset_index()

#     # 儲存資料到Excel
#     save_to_excel(daily_high_low, stock_id, start_date, end_date)

# # 執行主函數
# if __name__ == "__main__":
#     main()


import shioaji as sj
import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

# 初始化 Shioaji API
api = sj.Shioaji(simulation=True)
api.login(
    # api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    # secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
    api_key="6GWV7gnxYXaEomoyLuTFRe29BnoAyEohVpbSZQYHdY66",
    secret_key="F6PJrruho4pRpC9KefgKeqReFQ2nhLV34uXe2RmMZFow"
)

# 取得股票歷史價格資料
def get_stock_data(stock_id, start_date, end_date):
    kbars = api.kbars(api.Contracts.Stocks[stock_id], start=start_date, end=end_date)
    df = pd.DataFrame({**kbars})
    df.ts = pd.to_datetime(df.ts)
    df['date'] = df['ts'].dt.date
    return df

# 儲存資料到Excel
def save_to_excel(df, stock_id, start_date, end_date, save_path):
    # 設定儲存路徑和檔名
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    file_name = f"{stock_id}_{start_date}_to_{end_date}.xlsx"
    file_path = os.path.join(save_path, file_name)
    
    # 將資料儲存為Excel檔案
    df.to_excel(file_path, index=False)
    messagebox.showinfo("完成", f"資料已儲存到: {file_path}")

# 主函數
def main(stock_id, start_date, end_date, save_path):
    # 取得股票數據
    df = get_stock_data(stock_id, start_date, end_date)

    # 計算每日最高價和最低價
    daily_high_low = df.groupby('date').agg({'High': 'max', 'Low': 'min'}).reset_index()

    # 儲存資料到Excel
    save_to_excel(daily_high_low, stock_id, start_date, end_date, save_path)

# 建立GUI
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

    # 建立主窗口
    root = tk.Tk()
    root.title("股票資料下載器")

    # 股票代碼
    tk.Label(root, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5)
    entry_stock_id = tk.Entry(root)
    entry_stock_id.grid(row=0, column=1, padx=10, pady=5)

    # 起始日期
    tk.Label(root, text="起始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
    entry_start_date = tk.Entry(root)
    entry_start_date.grid(row=1, column=1, padx=10, pady=5)

    # 結束日期
    tk.Label(root, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5)
    entry_end_date = tk.Entry(root)
    entry_end_date.grid(row=2, column=1, padx=10, pady=5)

    # 儲存路徑
    tk.Label(root, text="儲存路徑:").grid(row=3, column=0, padx=10, pady=5)
    entry_save_path = tk.Entry(root)
    entry_save_path.grid(row=3, column=1, padx=10, pady=5)
    tk.Button(root, text="瀏覽", command=browse_directory).grid(row=3, column=2, padx=10, pady=5)

    # 執行按鈕
    tk.Button(root, text="下載資料", command=run).grid(row=4, column=0, columnspan=3, pady=20)

    # 啟動主循環
    root.mainloop()

# 執行GUI
if __name__ == "__main__":
    create_gui()

