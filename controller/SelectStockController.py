from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class SelectStockController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.controller = self

    def calculate(self, start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections):
        # all_wave_extremes = self.model.process_all_stocks(ratio, ratio2, top_n)
        result = self.model.process_all_stocks(start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections)
        if isinstance(result, str) and result.startswith("錯誤："):
            self.view.show_error(result)
        else:
            # 處理正常的结果
            return result
        
    def download_detail_data(self, stock_id, start_date, end_date, file_path):
        self.model.analyze_data(stock_id, start_date, end_date, file_path)

    def show_detail_data(self, stock_id):
        recent_segment, total_segment = self.model.get_stock_data_from_all_wave_extremes(stock_id)
        if total_segment is None:
            print(f"沒有找到股票 {stock_id} 的數據")
            return

        # 整理均線數據（使用最近波段數據）
        organized_ma_data = {
            "日均線": {
                "5日": recent_segment.get('sma_5', 'N/A'),
                "10日": recent_segment.get('sma_10', 'N/A'),
                "20日": recent_segment.get('sma_20', 'N/A'),
                "60日": recent_segment.get('sma_60', 'N/A'),
                "120日": recent_segment.get('sma_120', 'N/A')
            },
            "週均線": {
                "5週": recent_segment.get('weekly_sma_5', 'N/A'),
                "10週": recent_segment.get('weekly_sma_10', 'N/A'),
                "20週": recent_segment.get('weekly_sma_20', 'N/A'),
                "60週": recent_segment.get('weekly_sma_60', 'N/A'),
                "120週": recent_segment.get('weekly_sma_120', 'N/A')
            },
            "月均線": {
                "5月": recent_segment.get('monthly_sma_5', 'N/A'),
                "10月": recent_segment.get('monthly_sma_10', 'N/A'),
                "20月": recent_segment.get('monthly_sma_20', 'N/A'),
                "60月": recent_segment.get('monthly_sma_60', 'N/A'),
                "120月": recent_segment.get('monthly_sma_120', 'N/A')
            }
        }

        # 整理比例價格數據（包括最近波段和總波段）
        ratio_prices = {
            "最近波段": {
                '0.191': recent_segment.get('Ratio_0.191', 'N/A'),
                '0.382': recent_segment.get('Ratio_0.382', 'N/A'),
                '0.5': recent_segment.get('Ratio_0.5', 'N/A'),
                '0.618': recent_segment.get('Ratio_0.618', 'N/A'),
                '0.809': recent_segment.get('Ratio_0.809', 'N/A'),
                '1': recent_segment.get('Ratio_1', 'N/A'),
                '1.191': recent_segment.get('Ratio_1.191', 'N/A'),
                '1.382': recent_segment.get('Ratio_1.382', 'N/A'),
                '1.5': recent_segment.get('Ratio_1.5', 'N/A'),
                '1.618': recent_segment.get('Ratio_1.618', 'N/A'),
                '1.809': recent_segment.get('Ratio_1.809', 'N/A'),
                '2': recent_segment.get('Ratio_2', 'N/A'),
                '2.191': recent_segment.get('Ratio_2.191', 'N/A'),
                '2.382': recent_segment.get('Ratio_2.382', 'N/A'),
                '2.5': recent_segment.get('Ratio_2.5', 'N/A'),
                '2.618': recent_segment.get('Ratio_2.618', 'N/A'),
                '2.809': recent_segment.get('Ratio_2.809', 'N/A'),
                '3': recent_segment.get('Ratio_3', 'N/A'),
                '3.191': recent_segment.get('Ratio_3.191', 'N/A'),
                '3.382': recent_segment.get('Ratio_3.382', 'N/A'),
                '3.5': recent_segment.get('Ratio_3.5', 'N/A'),
                '3.618': recent_segment.get('Ratio_3.618', 'N/A'),
                '3.809': recent_segment.get('Ratio_3.809', 'N/A'),
                '4': recent_segment.get('Ratio_4', 'N/A')
            },
            "總波段": {
                '0.191': total_segment.get('Ratio_0.191', 'N/A'),
                '0.382': total_segment.get('Ratio_0.382', 'N/A'),
                '0.5': total_segment.get('Ratio_0.5', 'N/A'),
                '0.618': total_segment.get('Ratio_0.618', 'N/A'),
                '0.809': total_segment.get('Ratio_0.809', 'N/A'),
                '1': total_segment.get('Ratio_1', 'N/A'),
                '1.191': total_segment.get('Ratio_1.191', 'N/A'),
                '1.382': total_segment.get('Ratio_1.382', 'N/A'),
                '1.5': total_segment.get('Ratio_1.5', 'N/A'),
                '1.618': total_segment.get('Ratio_1.618', 'N/A'),
                '1.809': total_segment.get('Ratio_1.809', 'N/A'),
                '2': total_segment.get('Ratio_2', 'N/A'),
                '2.191': total_segment.get('Ratio_2.191', 'N/A'),
                '2.382': total_segment.get('Ratio_2.382', 'N/A'),
                '2.5': total_segment.get('Ratio_2.5', 'N/A'),
                '2.618': total_segment.get('Ratio_2.618', 'N/A'),
                '2.809': total_segment.get('Ratio_2.809', 'N/A'),
                '3': total_segment.get('Ratio_3', 'N/A'),
                '3.191': total_segment.get('Ratio_3.191', 'N/A'),
                '3.382': total_segment.get('Ratio_3.382', 'N/A'),
                '3.5': total_segment.get('Ratio_3.5', 'N/A'),
                '3.618': total_segment.get('Ratio_3.618', 'N/A'),
                '3.809': total_segment.get('Ratio_3.809', 'N/A'),
                '4': total_segment.get('Ratio_4', 'N/A')
            }
        }

        # 添加其他可能需要的數據（使用總波段數據）
        additional_data = {
            '最高價': total_segment.get('Max_Value', 'N/A'),
            '最低價': total_segment.get('Min_Value', 'N/A'),
            '最新收盤價': total_segment.get('latest_close_price', 'N/A'),
            '價差比例': total_segment.get('spread_ratio', 'N/A'),
            '最新收盤價-0.618比例': total_segment.get('latest_close_price-0.618_ratio', 'N/A')
        }

        self.view.show_sma_data(stock_id, organized_ma_data, ratio_prices, additional_data)
        
