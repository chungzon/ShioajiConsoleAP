#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票資料匯出API GUI應用程式
提供圖形化界面來控制API服務
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
import requests
from datetime import datetime
import sys
import os

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ExportJson import ExportJson

class StockAPIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("股票資料匯出API服務")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 設定字體樣式
        self.setup_fonts()
        
        # API服務相關變數
        self.api_thread = None
        self.api_running = False
        self.export_json = ExportJson()
        
        # 設定預設值
        self.host = tk.StringVar(value="localhost")
        self.port = tk.StringVar(value="5000")
        
        # 設定文件路徑
        self.config_file = "gui_config.json"
        
        # 載入設定
        self.load_config()
        
        # 創建GUI
        self.create_widgets()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_fonts(self):
        """設定字體樣式"""
        import tkinter.font as tkFont
        
        # 定義字體樣式（再大2pt）
        self.fonts = {
            'title': tkFont.Font(family="Microsoft JhengHei", size=20, weight="bold"),
            'heading': tkFont.Font(family="Microsoft JhengHei", size=14, weight="bold"),
            'normal': tkFont.Font(family="Microsoft JhengHei", size=13),
            'small': tkFont.Font(family="Microsoft JhengHei", size=12),
            'button': tkFont.Font(family="Microsoft JhengHei", size=13),
            'entry': tkFont.Font(family="Microsoft JhengHei", size=13),
            'log': tkFont.Font(family="Microsoft JhengHei", size=12)
        }
        
        # 設定自定義樣式
        style = ttk.Style()
        style.configure('Custom.TButton', font=self.fonts['button'])
        # LabelFrame的字體設定需要不同的方法
        style.configure('TLabelFrame', font=self.fonts['heading'])
        style.configure('TLabelFrame.Label', font=self.fonts['heading'])
    
    def load_config(self):
        """載入設定文件"""
        try:
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
            # 使用預設值
            self.host.set('localhost')
            self.port.set('5000')
            self.config_loaded = False
    
    def save_config(self):
        """保存設定文件"""
        try:
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
    
    def on_setting_changed(self, *args):
        """設定變更時的處理"""
        # 可以在此處添加自動保存邏輯，或者只是提示用戶
        pass
    
    def reset_config(self):
        """重置設定為預設值"""
        self.host.set('localhost')
        self.port.set('5000')
        self.log_message("設定已重置為預設值")
        
        # 刪除設定文件
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                self.log_message("已刪除設定文件")
        except Exception as e:
            self.log_message(f"刪除設定文件失敗: {str(e)}", "ERROR")
    
    def create_widgets(self):
        """創建GUI組件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 標題
        title_label = ttk.Label(main_frame, text="股票資料匯出API服務", font=self.fonts['title'])
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 服務設定區域
        settings_frame = ttk.LabelFrame(main_frame, text="服務設定", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # IP設定
        ip_label = ttk.Label(settings_frame, text="IP地址:", font=self.fonts['normal'])
        ip_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.host_entry = ttk.Entry(settings_frame, textvariable=self.host, width=20, font=self.fonts['entry'])
        self.host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Port設定
        port_label = ttk.Label(settings_frame, text="端口:", font=self.fonts['normal'])
        port_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.port_entry = ttk.Entry(settings_frame, textvariable=self.port, width=10, font=self.fonts['entry'])
        self.port_entry.grid(row=0, column=3, sticky=tk.W)
        
        # 保存設定按鈕
        self.save_config_button = ttk.Button(settings_frame, text="保存設定", command=self.save_config, style='Custom.TButton')
        self.save_config_button.grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        
        # 重置設定按鈕
        self.reset_config_button = ttk.Button(settings_frame, text="重置設定", command=self.reset_config, style='Custom.TButton')
        self.reset_config_button.grid(row=0, column=5, sticky=tk.W, padx=(5, 0))
        
        # 綁定設定變更事件
        self.host.trace('w', self.on_setting_changed)
        self.port.trace('w', self.on_setting_changed)
        
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
        
        # 設定按鈕字體
        for button in [self.start_button, self.stop_button, self.test_button, self.clear_button]:
            button.configure(style='Custom.TButton')
        
        # 狀態顯示區域
        status_frame = ttk.LabelFrame(main_frame, text="服務狀態", padding="10")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="服務未啟動", foreground="red", font=self.fonts['normal'])
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.url_label = ttk.Label(status_frame, text="", font=self.fonts['small'])
        self.url_label.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        # 日誌顯示區域
        log_frame = ttk.LabelFrame(main_frame, text="執行日誌", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 創建滾動文字框
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            width=80,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=self.fonts['log']
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置滾動條
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 顯示載入設定的狀態
        if hasattr(self, 'config_loaded'):
            if self.config_loaded:
                self.log_message("已載入上次的設定")
            else:
                self.log_message("使用預設設定")
    
    def log_message(self, message, level="INFO"):
        """添加日誌訊息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 自動滾動到底部
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
            messagebox.showerror("錯誤", f"無效的端口號: {e}")
            return
        
        if self.api_running:
            messagebox.showwarning("警告", "API服務已在運行中")
            return
        
        # 啟動API服務線程
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
            import sys
            import os
            
            # 創建Flask應用
            app = Flask(__name__)
            
            # 設定日誌回調
            def log_callback(message, level="INFO"):
                self.root.after(0, lambda: self.log_message(message, level))
            
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
                    
                    # 先驗證股票代碼（使用結束日期結束）
                    # df = self.export_json.get_stock_KBars(stock_id, start_date, end_date_end)
                    # if df is None or df.empty:
                    #     log_callback(f"錯誤: 無法取得股票 {stock_id} 的資料", "ERROR")
                    #     return jsonify({
                    #         'success': False,
                    #         'error': f'無法取得股票 {stock_id} 的資料，請檢查股票代碼或日期範圍'
                    #     }), 404
                    
                    # 為每個日期計算指標資料
                    results = []
                    for i, end_date in enumerate(date_list):
                        try:
                            log_callback(f"計算日期 {end_date.strftime('%Y-%m-%d')} ({i+1}/{len(date_list)})")
                            
                            # 計算最近波段日期（使用後半段時間）
                            # date_diff = (end_date - start_date).days
                            # mid_days = date_diff // 2
                            # mid_date = start_date + timedelta(days=mid_days)
                            # recent_start_date = mid_date
                            # recent_end_date = end_date
                            
                            df = self.export_json.get_stock_data(stock_id, start_date, end_date)
                            kbars_df = self.export_json.get_stock_KBars(stock_id, start_date, end_date)
                            daily_df = self.export_json.get_stock_data(stock_id, end_date + timedelta(days=-365*5), end_date)

    
                            # 執行匯出，直接返回資料
                            json_data = self.export_json.export_to_json(
                                stock_id=stock_id,
                                start_date=start_date,
                                end_date=end_date,
                                df=df,
                                kbars_df=kbars_df,
                                daily_df=daily_df,
                                output_path=None,
                                return_data=True
                            )
                            
                            if json_data:
                                # 添加日期資訊到結果中
                                json_data['calculation_date'] = end_date.strftime('%Y-%m-%d')
                                json_data['date_index'] = i + 1
                                json_data['day_of_week'] = end_date.strftime('%A')
                                results.append(json_data)
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
                        return jsonify({
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
                        })
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
            self.root.after(0, lambda: self.status_label.config(text="服務運行中", foreground="green"))
            self.root.after(0, lambda: self.url_label.config(text=f"http://{self.host.get()}:{self.port.get()}"))
            self.root.after(0, lambda: self.log_message("API服務啟動成功"))
            
            # 啟動Flask服務
            app.run(host=self.host.get(), port=int(self.port.get()), debug=False, use_reloader=False)
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"API服務啟動失敗: {str(e)}", "ERROR"))
            self.root.after(0, lambda: self.status_label.config(text="服務啟動失敗", foreground="red"))
            self.api_running = False
    
    def test_api(self):
        """測試API功能"""
        if not self.api_running:
            messagebox.showwarning("警告", "請先啟動API服務")
            return
        
        def test_in_thread():
            try:
                base_url = f"http://{self.host.get()}:{self.port.get()}"
                
                # 測試健康檢查
                self.root.after(0, lambda: self.log_message("開始測試API..."))
                
                response = requests.get(f"{base_url}/api/health", timeout=10)
                if response.status_code == 200:
                    self.root.after(0, lambda: self.log_message("✓ 健康檢查通過"))
                else:
                    self.root.after(0, lambda: self.log_message(f"✗ 健康檢查失敗，狀態碼: {response.status_code}", "ERROR"))
                    return
                
                # 測試股票資料匯出（使用新的日期區間格式）
                test_data = {
                    "stock_id": "6877",
                    "start_date": "2024-01-01",
                    "end_date_start": "2024-12-30",
                    "end_date_end": "2024-12-31"
                }
                
                self.root.after(0, lambda: self.log_message(f"測試股票資料匯出: {json.dumps(test_data, ensure_ascii=False)}"))
                
                response = requests.post(
                    f"{base_url}/api/export-stock-data",
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.root.after(0, lambda: self.log_message("✓ 股票資料匯出測試成功"))
                        data = result.get('data', [])
                        count = result.get('count', 0)
                        successful_count = result.get('successful_count', 0)
                        date_range = result.get('date_range', {})
                        
                        self.root.after(0, lambda: self.log_message(f"總日期數: {count}"))
                        self.root.after(0, lambda: self.log_message(f"成功計算: {successful_count}"))
                        if date_range:
                            self.root.after(0, lambda: self.log_message(f"日期區間: {date_range.get('end_date_start', 'N/A')} 至 {date_range.get('end_date_end', 'N/A')}"))
                        
                        if data:
                            for i, item in enumerate(data[:3]):  # 只顯示前3筆
                                if 'error' in item:
                                    self.root.after(0, lambda item=item: self.log_message(f"日期 {item['calculation_date']} ({item['day_of_week']}): 錯誤 - {item['error']}", "ERROR"))
                                else:
                                    self.root.after(0, lambda item=item: self.log_message(f"日期 {item['calculation_date']} ({item['day_of_week']}): 價格 {item.get('base', 'N/A')}"))
                            
                            if len(data) > 3:
                                self.root.after(0, lambda: self.log_message(f"... 還有 {len(data) - 3} 筆資料"))
                    else:
                        self.root.after(0, lambda: self.log_message(f"✗ 股票資料匯出失敗: {result.get('error', '未知錯誤')}", "ERROR"))
                else:
                    self.root.after(0, lambda: self.log_message(f"✗ 股票資料匯出失敗，狀態碼: {response.status_code}", "ERROR"))
                    self.root.after(0, lambda: self.log_message(f"錯誤訊息: {response.text}", "ERROR"))
                
                # 測試5分K資料匯出
                kbar_test_data = {
                    "stock_id": "6877",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
                
                self.root.after(0, lambda: self.log_message(f"測試5分K資料匯出: {json.dumps(kbar_test_data, ensure_ascii=False)}"))
                
                response = requests.post(
                    f"{base_url}/api/export-5min-kbar",
                    json=kbar_test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.root.after(0, lambda: self.log_message("✓ 5分K資料匯出測試成功"))
                        data = result.get('data', [])
                        count = result.get('count', 0)
                        self.root.after(0, lambda: self.log_message(f"5分K資料筆數: {count}"))
                        if data:
                            first_kbar = data[0]
                            self.root.after(0, lambda: self.log_message(f"第一筆資料: {first_kbar['datetime']} - 開:{first_kbar['open_price']} 收:{first_kbar['close_price']}"))
                    else:
                        self.root.after(0, lambda: self.log_message(f"✗ 5分K資料匯出失敗: {result.get('error', '未知錯誤')}", "ERROR"))
                else:
                    self.root.after(0, lambda: self.log_message(f"✗ 5分K資料匯出失敗，狀態碼: {response.status_code}", "ERROR"))
                    self.root.after(0, lambda: self.log_message(f"錯誤訊息: {response.text}", "ERROR"))
                
                self.root.after(0, lambda: self.log_message("API測試完成"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"API測試失敗: {str(e)}", "ERROR"))
        
        # 在背景線程中執行測試
        test_thread = threading.Thread(target=test_in_thread, daemon=True)
        test_thread.start()
    
    def on_closing(self):
        """關閉應用程式時的處理"""
        if self.api_running:
            self.stop_api()
        
        # 保存設定
        self.save_config()
        
        self.root.destroy()

def main():
    """主函數"""
    root = tk.Tk()
    app = StockAPIGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
