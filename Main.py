import tkinter as tk
from tkinter import ttk

from flask import Response
from DailyKbarsDownloadScheduler import start_daily_kbars_scheduler
from model.RealtimeMonitorModel import RealtimeMonitorModel
from view.DataAnalysisView import DataAnalysisView
from model.DataAnalysisModel import DataAnalysisModel
from controller.DataAnalysisController import DataAnalysisController
from view.DataDownloadView import DataDownloadView
from model.DataDownloadModel import DataDownloadModel
from controller.DataDownloadController import DataDownloadController
from view.RealtimeMonitorView import RealtimeMonitorView
from model.RealtimeMonitorModel import RealtimeMonitorModel
from controller.RealtimeMonitorController import RealtimeMonitorController
from view.BacktestView import BacktestView
from model.BacktestModel import BacktestModel
from controller.BacktestController import BacktestController
from view.DailyClosePriceDownloadView import DailyClosePriceDownloadView
from model.DailyClosePriceDownloadModel import DailyClosePriceDownloadModel
from controller.DailyClosePriceDownloadController import DailyClosePriceDownloadController
from view.SelectStockView import SelectStockView
from model.SelectStockModel import SelectStockModel
from controller.SelectStockController import SelectStockController
import shioaji as sj
import tkinter.font as tkfont
from DataDownloadScheduler import start_scheduler

class StockAPIGUIView(ttk.Frame):
    """股票API服務分頁視圖"""
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        self.export_json = None
        self.api_thread = None
        self.api_running = False
        
        # 設定預設值
        self.host = tk.StringVar(value="localhost")
        self.port = tk.StringVar(value="5000")
        
        # 設定文件路徑
        self.config_file = "gui_config.json"
        
        # 載入設定
        self.load_config()
        
        # 創建GUI
        self.create_widgets()
    
    def load_config(self):
        """載入設定文件"""
        try:
            import json
            import os
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.host.set(config.get('host', 'localhost'))
                    self.port.set(config.get('port', '5000'))
                    self.config_loaded = True
            else:
                self.config_loaded = False
        except Exception as e:
            print(f"載入設定失敗: {str(e)}")
            self.host.set('localhost')
            self.port.set('5000')
            self.config_loaded = False
    
    def save_config(self):
        """保存設定文件"""
        try:
            import json
            from datetime import datetime
            config = {
                'host': self.host.get(),
                'port': self.port.get(),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.log_message("設定已保存")
        except Exception as e:
            self.log_message(f"保存設定失敗: {str(e)}", "ERROR")
    
    def reset_config(self):
        """重置設定為預設值"""
        self.host.set('localhost')
        self.port.set('5000')
        self.log_message("設定已重置為預設值")
        
        # 刪除設定文件
        try:
            import os
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                self.log_message("已刪除設定文件")
        except Exception as e:
            self.log_message(f"刪除設定文件失敗: {str(e)}", "ERROR")
    
    def create_widgets(self):
        """創建GUI組件"""
        # 主框架
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 標題
        title_label = ttk.Label(main_frame, text="股票資料匯出API服務", font=('Microsoft JhengHei', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 服務設定區域
        settings_frame = ttk.LabelFrame(main_frame, text="服務設定", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # IP設定
        ip_label = ttk.Label(settings_frame, text="IP地址:", font=('Microsoft JhengHei', 13))
        ip_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.host_entry = ttk.Entry(settings_frame, textvariable=self.host, width=20, font=('Microsoft JhengHei', 13))
        self.host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Port設定
        port_label = ttk.Label(settings_frame, text="端口:", font=('Microsoft JhengHei', 13))
        port_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.port_entry = ttk.Entry(settings_frame, textvariable=self.port, width=10, font=('Microsoft JhengHei', 13))
        self.port_entry.grid(row=0, column=3, sticky=tk.W)
        
        # 保存設定按鈕
        self.save_config_button = ttk.Button(settings_frame, text="保存設定", command=self.save_config)
        self.save_config_button.grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        
        # 重置設定按鈕
        self.reset_config_button = ttk.Button(settings_frame, text="重置設定", command=self.reset_config)
        self.reset_config_button.grid(row=0, column=5, sticky=tk.W, padx=(5, 0))
        
        # 控制按鈕區域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="啟動服務", command=self.start_api)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止服務", command=self.stop_api, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_button = ttk.Button(control_frame, text="測試API", command=self.test_api)
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(control_frame, text="清除日誌", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT)
        
        # 狀態顯示區域
        status_frame = ttk.LabelFrame(main_frame, text="服務狀態", padding="10")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="服務未啟動", foreground="red", font=('Microsoft JhengHei', 13))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.url_label = ttk.Label(status_frame, text="", font=('Microsoft JhengHei', 12))
        self.url_label.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        # 日誌顯示區域
        log_frame = ttk.LabelFrame(main_frame, text="執行日誌", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 創建滾動文字框
        from tkinter import scrolledtext
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            width=80,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Microsoft JhengHei', 12)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 顯示載入設定的狀態
        if hasattr(self, 'config_loaded'):
            if self.config_loaded:
                self.log_message("已載入上次的設定")
            else:
                self.log_message("使用預設設定")
    
    def log_message(self, message, level="INFO"):
        """添加日誌訊息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.update()
    
    def clear_log(self):
        """清除日誌"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("日誌已清除")
    
    def start_api(self):
        """啟動API服務"""
        try:
            port = int(self.port.get())
            if port < 1 or port > 65535:
                raise ValueError("端口號必須在1-65535之間")
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"無效的端口號: {e}")
            return
        
        if self.api_running:
            from tkinter import messagebox
            messagebox.showwarning("警告", "API服務已在運行中")
            return
        
        # 初始化 ExportJson 和 DataAnalysisModel
        if self.export_json is None:
            from api.ExportJson import ExportJson
            from model.DataAnalysisModel import DataAnalysisModel
            self.export_json = ExportJson()
            self.data_analysis_model = DataAnalysisModel(self.api)
        
        # 啟動API服務線程
        import threading
        self.api_thread = threading.Thread(target=self.run_api_server, daemon=True)
        self.api_thread.start()
        
        # 更新UI狀態
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.host_entry.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)
        
        self.log_message("正在啟動API服務...")
    
    def stop_api(self):
        """停止API服務"""
        if not self.api_running:
            from tkinter import messagebox
            messagebox.showwarning("警告", "API服務未在運行")
            return
        
        self.api_running = False
        
        # 更新UI狀態
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.host_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        
        self.status_label.config(text="服務已停止", foreground="red")
        self.url_label.config(text="")
        
        self.log_message("API服務已停止")
    
    def run_api_server(self):
        """運行API服務器"""
        try:
            from flask import Flask, request, jsonify
            from datetime import datetime
            import threading
            import json
            
            # 創建Flask應用
            app = Flask(__name__)
            
            # 設定日誌回調
            def log_callback(message, level="INFO"):
                self.after(0, lambda: self.log_message(message, level))
            
            @app.route('/api/export-stock-data', methods=['POST'])
            def export_stock_data():
                try:
                    log_callback("收到股票資料匯出請求")
                    
                    # 獲取請求資料
                    data = request.get_json()
                    log_callback(f"請求資料: {json.dumps(data, ensure_ascii=False)}")
                    
                    # 驗證必要參數
                    if not data:
                        log_callback("錯誤: 請提供JSON格式的請求資料", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '請提供JSON格式的請求資料'
                        }), 400
                    
                    required_fields = ['stock_id', 'start_date', 'end_date_start', 'end_date_end']
                    for field in required_fields:
                        if field not in data:
                            log_callback(f"錯誤: 缺少必要參數: {field}", "ERROR")
                            return jsonify({
                                'success': False,
                                'error': f'缺少必要參數: {field}'
                            }), 400
                    
                    # 解析參數
                    stock_id = data['stock_id']
                    start_date_str = data['start_date']
                    end_date_start_str = data['end_date_start']
                    end_date_end_str = data['end_date_end']
                    
                    log_callback(f"處理股票代碼: {stock_id}, 日期區間: {start_date_str} 到 {end_date_start_str}-{end_date_end_str}")
                    
                    # 解析日期
                    try:
                        from datetime import datetime, timedelta
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        end_date_start = datetime.strptime(end_date_start_str, '%Y-%m-%d').date()
                        end_date_end = datetime.strptime(end_date_end_str, '%Y-%m-%d').date()
                    except ValueError as e:
                        log_callback(f"錯誤: 日期格式錯誤: {e}", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': f'日期格式錯誤: {e}。請使用 YYYY-MM-DD 格式'
                        }), 400
                    
                    # 驗證日期範圍
                    if start_date >= end_date_start:
                        log_callback("錯誤: 起始日期必須早於結束日期開始", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '起始日期必須早於結束日期開始'
                        }), 400
                    
                    if end_date_start > end_date_end:
                        log_callback("錯誤: 結束日期開始必須早於或等於結束日期結束", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '結束日期開始必須早於或等於結束日期結束'
                        }), 400
                    
                    # 生成日期區間內的所有日期
                    current_date = end_date_start
                    date_list = []
                    while current_date <= end_date_end:
                        date_list.append(current_date)
                        current_date += timedelta(days=1)
                    
                    log_callback(f"將計算 {len(date_list)} 個日期的指標資料")
                    
                    # 為每個日期計算指標資料
                    results = []
                    for i, end_date in enumerate(date_list):
                        try:
                            log_callback(f"計算日期 {end_date.strftime('%Y-%m-%d')} ({i+1}/{len(date_list)})")
                            
                            # 使用 DataAnalysisModel 的 get_stock_data_from_all_wave_extremes 方法
                            # 計算最近波段日期（使用後半段時間）
                            date_diff = (end_date - start_date).days
                            mid_days = date_diff // 2
                            mid_date = start_date + timedelta(days=mid_days)
                            recent_start_date = mid_date
                            recent_end_date = end_date
                            
                            start_date_str = start_date.strftime('%Y-%m-%d')
                            end_date_str = end_date.strftime('%Y-%m-%d')
                            recent_start_date_str = recent_start_date.strftime('%Y-%m-%d')
                            recent_end_date_str = recent_end_date.strftime('%Y-%m-%d')

                            result = self.data_analysis_model.get_stock_data_from_all_wave_extremes(
                                stock_id, start_date_str, end_date_str, recent_start_date_str, recent_end_date_str
                            )
                            next_open_price = None
                            if result is not None:
                                segment, recent_segment, gap_df, now_price, latest_close_price_by_date, next_open_price = result
                                
                                # 整理比例價格資料
                                ratio_data = {}
                                ratio_columns = ['Ratio_0', 'Ratio_0.191', 'Ratio_0.382', 'Ratio_0.5', 'Ratio_0.618', 'Ratio_0.809', 
                                               'Ratio_1', 'Ratio_1.191', 'Ratio_1.382', 'Ratio_1.5', 'Ratio_1.618', 'Ratio_1.809',
                                               'Ratio_2', 'Ratio_2.191', 'Ratio_2.382', 'Ratio_2.5', 'Ratio_2.618', 'Ratio_2.809',
                                               'Ratio_3', 'Ratio_3.191', 'Ratio_3.382', 'Ratio_3.5', 'Ratio_3.618', 'Ratio_3.809',
                                               'Ratio_4', 'Ratio_4.191', 'Ratio_4.382', 'Ratio_4.5', 'Ratio_4.618', 'Ratio_4.809',
                                               'Ratio_5', 'Ratio_5.191', 'Ratio_5.382', 'Ratio_5.5', 'Ratio_5.618', 'Ratio_5.809', 'Ratio_6']
                                
                                for col in ratio_columns:
                                    if col in segment:
                                        value = segment[col]
                                        if value is not None and str(value) != 'nan':
                                            # 提取比例數字
                                            ratio_num = col.replace('Ratio_', '')
                                            ratio_data[f'[{ratio_num}]'] = f"{float(value):.2f}"
                                        else:
                                            ratio_num = col.replace('Ratio_', '')
                                            ratio_data[f'[{ratio_num}]'] = "nan"
                                
                                sma_data = {}
                                # 整理15K資料
                                for period in [10, 20, 60]:
                                    col_name = f'15min_sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            sma_data[f'15K({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            sma_data[f'15K({period})_DIFF'] = "nan"

                                # 整理SMA資料
                                
                                # 日線SMA
                                for period in [5, 10, 20, 60, 120]:
                                    col_name = f'sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            sma_data[f'日({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            sma_data[f'日({period})_DIFF'] = "nan"
                                
                                # 週線SMA
                                for period in [5, 10, 20, 60, 120]:
                                    col_name = f'weekly_sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            sma_data[f'週({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            sma_data[f'週({period})_DIFF'] = "nan"
                                
                                # 月線SMA
                                for period in [5, 10, 20, 60, 120]:
                                    col_name = f'monthly_sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            sma_data[f'月({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            sma_data[f'月({period})_DIFF'] = "nan"
                                
                                # 整理CDP資料
                                cdp_data = {}
                                cdp_columns = ['AL', 'NL', 'CDP', 'NH', 'AH']
                                for col in cdp_columns:
                                    if col in segment:
                                        value = segment[col]
                                        if value is not None and str(value) != 'nan':
                                            cdp_data[col] = f"{float(value):.2f}"
                                        else:
                                            cdp_data[col] = "nan"
                                
                                # 按照指定順序合併所有資料
                                all_data = {}
                                
                                # 1. 現價資料
                                all_data['NOW PRICE'] = f"{segment.get('latest_close_price', 0):.2f}"
                                
                                # 2. 比例價格資料（按照指定順序）
                                for col in ratio_columns:
                                    if col in segment:
                                        value = segment[col]
                                        if value is not None and str(value) != 'nan':
                                            ratio_num = col.replace('Ratio_', '')
                                            all_data[f'[{ratio_num}]'] = f"{float(value):.2f}"
                                        else:
                                            ratio_num = col.replace('Ratio_', '')
                                            all_data[f'[{ratio_num}]'] = "nan"
                                
                                # 3. CDP資料
                                for col in cdp_columns:
                                    if col in segment:
                                        value = segment[col]
                                        if value is not None and str(value) != 'nan':
                                            all_data[col] = f"{float(value):.2f}"
                                        else:
                                            all_data[col] = "nan"
                                
                                # 4. 15K扣抵值資料
                                for period in [10, 20, 60]:
                                    col_name = f'15min_sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            all_data[f'15K({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            all_data[f'15K({period})_DIFF'] = "nan"
                                
                                # 5. 日線扣抵值資料
                                for period in [5, 10, 20, 60, 120]:
                                    col_name = f'sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            all_data[f'日({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            all_data[f'日({period})_DIFF'] = "nan"
                                
                                # 6. 週線扣抵值資料
                                for period in [5, 10, 20, 60, 120]:
                                    col_name = f'weekly_sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            all_data[f'週({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            all_data[f'週({period})_DIFF'] = "nan"
                                
                                # 7. 月線扣抵值資料
                                for period in [5, 10, 20, 60, 120]:
                                    col_name = f'monthly_sma_{period}_diff'
                                    if col_name in recent_segment:
                                        value = recent_segment[col_name]
                                        if value is not None and str(value) != 'N/A' and str(value) != 'nan':
                                            all_data[f'月({period})_DIFF'] = f"{float(value):.2f}"
                                        else:
                                            all_data[f'月({period})_DIFF'] = "nan"
                                
                                # 讀取JSON模板
                                with open('resource/export_json_templete.json', 'r', encoding='utf-8') as f:
                                    json_template = json.load(f)
                                json_template['stock_code'] = stock_id
                                json_template['base'] = f"{next_open_price['open_price']:.2f}"
                                json_template['date'] = end_date.strftime('%Y-%m-%d')
                                json_template['data'] = all_data

                                results.append(json_template)
                                log_callback(f"✓ 日期 {end_date.strftime('%Y-%m-%d')} 計算成功")
                            else:
                                # 如果某個日期計算失敗，添加錯誤資訊
                                results.append({
                                    'stock_code': stock_id,
                                    'calculation_date': end_date.strftime('%Y-%m-%d'),
                                    'date_index': i + 1,
                                    'day_of_week': end_date.strftime('%A'),
                                    'error': '資料處理失敗',
                                    'success': False
                                })
                                log_callback(f"✗ 日期 {end_date.strftime('%Y-%m-%d')} 計算失敗", "ERROR")
                                
                        except Exception as e:
                            # 如果某個日期計算出現異常，添加錯誤資訊
                            results.append({
                                'stock_code': stock_id,
                                'calculation_date': end_date.strftime('%Y-%m-%d'),
                                'date_index': i + 1,
                                'day_of_week': end_date.strftime('%A'),
                                'error': f'計算錯誤: {str(e)}',
                                'success': False
                            })
                            log_callback(f"✗ 日期 {end_date.strftime('%Y-%m-%d')} 計算異常: {str(e)}", "ERROR")
                    
                    # 檢查是否有任何成功的結果
                    successful_results = [r for r in results if 'error' not in r]
                    
                    if successful_results:
                        log_callback(f"計算完成: 共 {len(results)} 個日期，成功 {len(successful_results)} 個")
                        # result_json = json.dumps(results, ensure_ascii=False)
                        result_json = {
                            'success': True,
                            'data': results,
                            'count': len(results),
                            'successful_count': len(successful_results),
                            'date_range': {
                                'start_date': start_date.strftime('%Y-%m-%d'),
                                'end_date_start': end_date_start.strftime('%Y-%m-%d'),
                                'end_date_end': end_date_end.strftime('%Y-%m-%d'),
                                'total_days': len(date_list)
                            },
                            'message': f'成功取得股票 {stock_id} 的資料，日期區間 {end_date_start.strftime("%Y-%m-%d")} 至 {end_date_end.strftime("%Y-%m-%d")}，共 {len(results)} 個日期，成功 {len(successful_results)} 個'
                        }

                        return Response(json.dumps(result_json, ensure_ascii=False), mimetype='application/json')
                    else:
                        log_callback("錯誤: 所有日期的資料處理都失敗", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '所有日期的資料處理都失敗',
                            'data': results
                        }), 500
                        
                except Exception as e:
                    log_callback(f"錯誤: 伺服器內部錯誤: {str(e)}", "ERROR")
                    return jsonify({
                        'success': False,
                        'error': f'伺服器內部錯誤: {str(e)}'
                    }), 500

            # 5分K資料匯出
            @app.route('/api/export-5min-kbar', methods=['POST'])
            def export_5min_kbar():
                try:
                    log_callback("收到5分K資料匯出請求")
                    
                    # 獲取請求資料
                    data = request.get_json()
                    log_callback(f"請求資料: {json.dumps(data, ensure_ascii=False)}")
                    
                    # 驗證必要參數
                    if not data:
                        log_callback("錯誤: 請提供JSON格式的請求資料", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '請提供JSON格式的請求資料'
                        }), 400
                    
                    required_fields = ['stock_id', 'start_date', 'end_date']
                    for field in required_fields:
                        if field not in data:
                            log_callback(f"錯誤: 缺少必要參數: {field}", "ERROR")
                            return jsonify({
                                'success': False,
                                'error': f'缺少必要參數: {field}'
                            }), 400
                    
                    # 解析參數
                    stock_id = data['stock_id']
                    start_date_str = data['start_date']
                    end_date_str = data['end_date']
                    
                    log_callback(f"處理股票代碼: {stock_id}, 日期範圍: {start_date_str} 到 {end_date_str}")
                    
                    # 解析日期
                    try:
                        from datetime import datetime, timedelta
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    except ValueError as e:
                        log_callback(f"錯誤: 日期格式錯誤: {e}", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': f'日期格式錯誤: {e}。請使用 YYYY-MM-DD 格式'
                        }), 400

                    # df = self.export_json.get_stock_data(stock_id, start_date, end_date)
                    kbars_df = self.export_json.get_stock_KBars(stock_id, start_date, end_date)

                    # if df is None or df.empty:
                    #     log_callback(f"錯誤: 無法取得股票 {stock_id} 的資料", "ERROR")
                    #     return jsonify({
                    #         'success': False,
                    #         'error': f'無法取得股票 {stock_id} 的資料，請檢查股票代碼或日期範圍'
                    #     }), 404
                    # log_callback(f"成功取得 {len(df)} 筆股票資料")

                    if kbars_df is None or kbars_df.empty:
                        log_callback(f"錯誤: 無法取得股票 {stock_id} 的資料", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': f'無法取得股票 {stock_id} 的資料，請檢查股票代碼或日期範圍'
                        }), 404

                    # 生成5分K資料
                    kbar_data = self.export_json.generate_5min_kbar(kbars_df)
                    if kbar_data:
                        log_callback("5分K資料處理完成，返回結果")
                        log_callback(f"返回資料大小: {len(json.dumps(kbar_data, ensure_ascii=False))} 字元")
                        return jsonify({
                            'success': True,
                            'data': kbar_data,
                            'count': len(kbar_data),
                            'message': f'成功取得股票 {stock_id} 的5分K資料，共 {len(kbar_data)} 筆'
                        })
                    else:
                        log_callback("錯誤: 5分K資料處理失敗", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '5分K資料處理失敗'
                        }), 500
                    
                    if kbar_data:
                        log_callback("5分K資料處理完成，返回結果")
                        log_callback(f"返回資料大小: {len(json.dumps(kbar_data, ensure_ascii=False))} 字元")
                        return jsonify({
                            'success': True,
                            'data': kbar_data,
                            'count': len(kbar_data),
                            'message': f'成功取得股票 {stock_id} 的5分K資料，共 {len(kbar_data)} 筆'
                        })
                    else:
                        log_callback("錯誤: 5分K資料處理失敗", "ERROR")
                        return jsonify({
                            'success': False,
                            'error': '5分K資料處理失敗'
                        }), 500
                except Exception as e:
                    log_callback(f"錯誤: 伺服器內部錯誤: {str(e)}", "ERROR")
                    return jsonify({
                        'success': False,
                        'error': f'伺服器內部錯誤: {str(e)}'
                    }), 500

            @app.route('/api/health', methods=['GET'])
            def health_check():
                log_callback("收到健康檢查請求")
                return jsonify({
                    'status': 'healthy',
                    'message': '股票資料匯出API服務正常運行',
                    'timestamp': datetime.now().isoformat()
                })
            
            @app.route('/', methods=['GET'])
            def index():
                log_callback("收到API說明請求")
                return jsonify({
                    'service': '股票資料匯出API',
                    'version': '1.0.0',
                    'endpoints': {
                        'POST /api/export-stock-data': {
                            'description': '匯出股票資料',
                            'parameters': {
                                'stock_id': '股票代碼 (字串)',
                                'start_date': '起始日期 (YYYY-MM-DD)',
                                'end_date_start': '結束日期開始 (YYYY-MM-DD)',
                                'end_date_end': '結束日期結束 (YYYY-MM-DD)'
                            }
                        },
                        'GET /api/health': '健康檢查',
                        'GET /': 'API說明'
                    }
                })
            
            # 更新狀態
            self.api_running = True
            self.after(0, lambda: self.status_label.config(text="服務運行中", foreground="green"))
            self.after(0, lambda: self.url_label.config(text=f"http://{self.host.get()}:{self.port.get()}"))
            self.after(0, lambda: self.log_message("API服務啟動成功"))
            
            # 啟動Flask服務
            app.run(host=self.host.get(), port=int(self.port.get()), debug=False, use_reloader=False)
            
        except Exception as e:
            self.after(0, lambda: self.log_message(f"API服務啟動失敗: {str(e)}", "ERROR"))
            self.after(0, lambda: self.status_label.config(text="服務啟動失敗", foreground="red"))
            self.api_running = False
    
    def test_api(self):
        """測試API功能"""
        if not self.api_running:
            from tkinter import messagebox
            messagebox.showwarning("警告", "請先啟動API服務")
            return
        
        def test_in_thread():
            try:
                import requests
                import json
                base_url = f"http://{self.host.get()}:{self.port.get()}"
                
                # 測試健康檢查
                self.after(0, lambda: self.log_message("開始測試API..."))
                
                response = requests.get(f"{base_url}/api/health", timeout=10)
                if response.status_code == 200:
                    self.after(0, lambda: self.log_message("✓ 健康檢查通過"))
                else:
                    self.after(0, lambda: self.log_message(f"✗ 健康檢查失敗，狀態碼: {response.status_code}", "ERROR"))
                    return
                
                # 測試股票資料匯出
                test_data = {
                    "stock_id": "6877",
                    "start_date": "2024-01-01",
                    "end_date_start": "2024-12-30",
                    "end_date_end": "2024-12-31"
                }
                
                self.after(0, lambda: self.log_message(f"測試股票資料匯出: {json.dumps(test_data, ensure_ascii=False)}"))
                
                response = requests.post(
                    f"{base_url}/api/export-stock-data",
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.after(0, lambda: self.log_message("✓ 股票資料匯出測試成功"))
                        data = result.get('data', [])
                        count = result.get('count', 0)
                        successful_count = result.get('successful_count', 0)
                        
                        self.after(0, lambda: self.log_message(f"總日期數: {count}"))
                        self.after(0, lambda: self.log_message(f"成功計算: {successful_count}"))
                        
                        if data:
                            for i, item in enumerate(data[:3]):  # 只顯示前3筆
                                if 'error' in item:
                                    self.after(0, lambda item=item: self.log_message(f"日期 {item['calculation_date']} ({item['day_of_week']}): 錯誤 - {item['error']}", "ERROR"))
                                else:
                                    self.after(0, lambda item=item: self.log_message(f"日期 {item['calculation_date']} ({item['day_of_week']}): 價格 {item.get('base', 'N/A')}"))
                            
                            if len(data) > 3:
                                self.after(0, lambda: self.log_message(f"... 還有 {len(data) - 3} 筆資料"))
                    else:
                        self.after(0, lambda: self.log_message(f"✗ 股票資料匯出失敗: {result.get('error', '未知錯誤')}", "ERROR"))
                else:
                    self.after(0, lambda: self.log_message(f"✗ 股票資料匯出失敗，狀態碼: {response.status_code}", "ERROR"))
                    self.after(0, lambda: self.log_message(f"錯誤訊息: {response.text}", "ERROR"))
                
                self.after(0, lambda: self.log_message("API測試完成"))
                
            except Exception as e:
                self.after(0, lambda: self.log_message(f"API測試失敗: {str(e)}", "ERROR"))
        
        # 在背景線程中執行測試
        import threading
        test_thread = threading.Thread(target=test_in_thread, daemon=True)
        test_thread.start()

class MainApplication(tk.Tk):
    
    @staticmethod
    def initialize_api():
        api = sj.Shioaji(simulation=True)
        api.login(
            api_key="CV7uuCJ7pB7x2i4T7783dBwiP7NwqhgwNj96J9uPd7PK",
            secret_key="HvDpMQ84VfgsGqBPN4nqfPV1iY9XsoWHst4rd4UimHaf"
        )
        return api

    def __init__(self):
        super().__init__()
        self.api = None
        try:
            self.api = self.initialize_api()
        except Exception as e:
            print(f"Error initializing API: {e}")
                # 設置默認字體大小
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=13)

        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(size=13)

        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_font.configure(size=13)

        # 設置 ttk 控件的字體

        # 設置 ttk 控件的字體
        style = ttk.Style()
        style.configure('.', font=('Microsoft JhengHei', 14))
        style.configure('Treeview', font=('Microsoft JhengHei', 14))
        style.configure('Treeview.Heading', font=('Microsoft JhengHei', 14))

        self.title("Stock Application")

        self.tab_control = ttk.Notebook(self)

        self.data_analysis_model = DataAnalysisModel(self.api)
        self.data_analysis_view = DataAnalysisView(self.tab_control, None)
        self.data_analysis_controller = DataAnalysisController(self.data_analysis_model, self.data_analysis_view)

        self.data_download_model = DataDownloadModel(self.api)
        self.data_download_view = DataDownloadView(self.tab_control, None)
        self.data_download_controller = DataDownloadController(self.data_download_model, self.data_download_view)

        self.realtime_monitor_model = RealtimeMonitorModel(self.api)
        self.realtime_monitor_view = RealtimeMonitorView(self.tab_control, None, self.realtime_monitor_model)
        self.realtime_monitor_controller = RealtimeMonitorController(self.realtime_monitor_model, self.realtime_monitor_view)
        # contract = self.api.Contracts.Stocks["2330"]
        # self.realtime_monitor_model.subscribe_stock(contract, 1)

        self.backtest_model = BacktestModel(self.api)
        self.backtest_view = BacktestView(self.tab_control, None, self.backtest_model)
        self.backtest_controller = BacktestController(self.backtest_model, self.backtest_view)

        self.daily_close_model = DailyClosePriceDownloadModel(self.api)
        self.daily_close_view = DailyClosePriceDownloadView(self.tab_control, None, self.daily_close_model)
        self.daily_close_controller = DailyClosePriceDownloadController(self.daily_close_model, self.daily_close_view)

        self.select_stock_model = SelectStockModel(self.api)
        self.select_stock_view = SelectStockView(self.tab_control, None, self.select_stock_model)
        self.select_stock_controller = SelectStockController(self.select_stock_model, self.select_stock_view)
        # self.select_stock_model.event.register(self.select_stock_view.print_stock_list)

        # 創建股票API服務分頁
        self.stock_api_view = StockAPIGUIView(self.tab_control, self.api)

        self.tab_control.add(self.data_analysis_view, text="資料分析")
        self.tab_control.add(self.data_download_view, text="資料下載")
        self.tab_control.add(self.realtime_monitor_view, text="即時監控")
        self.tab_control.add(self.backtest_view, text="資料回測")
        self.tab_control.add(self.daily_close_view, text="年度交易量下載")
        self.tab_control.add(self.select_stock_view, text="選股策略")
        self.tab_control.add(self.stock_api_view, text="API服務")
        self.tab_control.pack(expand=1, fill="both")

        # 启动调度器
        print("正在启动调度器...")
        self.scheduler = start_scheduler(self.api)
        self.daily_kbars_scheduler = start_daily_kbars_scheduler(self.api)
        print("调度器启动完成")
        
        # self.scheduler.run()


    

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
