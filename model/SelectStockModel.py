import os
import pandas as pd
import shioaji as sj
import time
from datetime import datetime, timedelta
from model.BaseModel import BaseModel
from common.Math import Math
from common.Event import Event

class SelectStockModel(BaseModel):
        # 創建log資料夾和檔案
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f"log_select_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    def __init__(self, api):
        super().__init__(api)  # 繼承父類的初始化
        self.all_wave_extremes = []
        self.event = Event()

    def get_stock_data(self, stock_id, start_date, end_date):
        try:
            # 建立資料庫連接
            conn = self.connect_db()

            # 查詢語句
            query = f"""
                SELECT distinct date, open_price, high_price, low_price, close_price
                FROM stock_data
                WHERE stock_id = '{stock_id}' AND date >= '{start_date}' AND date <= '{end_date}' ORDER BY date ASC
            """
            df = pd.read_sql(query, conn)
            df['date'] = pd.to_datetime(df['date'])
            # 關閉連接
            conn.close()

            return df

        except Exception as e:
            print(f"讀取資料時發生錯誤: {e}")
            return None
    
    # 取得股票區間最後一天的成交量
    def get_last_day_volume(self, stock_id, date):
        try:
            # 建立資料庫連接
            conn = self.connect_db()

            # 查詢語句
            query = f"""
                SELECT volume
                FROM stock_data
                WHERE stock_id = '{stock_id}' AND date = '{date}'
            """
            df = pd.read_sql(query, conn)
            return df['volume'].iloc[0]
        
        except Exception as e:
            print(f"取得股票區間最後一天的成交量時發生錯誤: {e}")
            return None

    def calculate_wave_extremes(self, df, stock_id):
        # 初始化波段列表
        waves = []
        wave_start_idx = 0
        is_upward = None

        for i in range(1, len(df)):
            if is_upward is None:
                is_upward = df['close_price'].iloc[i] > df['close_price'].iloc[i-1]
                continue

            current_trend = df['close_price'].iloc[i] > df['close_price'].iloc[i-1]

            # 檢查趨勢是否改變
            if current_trend != is_upward:
                wave_end_idx = i - 1
                wave_data = df.iloc[wave_start_idx:wave_end_idx + 1]
                wave_max = wave_data['close_price'].max()
                wave_min = wave_data['close_price'].min()
                waves.append({
                    'start_date': df['date'].iloc[wave_start_idx],
                    'end_date': df['date'].iloc[wave_end_idx],
                    'max_price': wave_max,
                    'min_price': wave_min
                })
                # 重置波段開始索引和趨勢
                wave_start_idx = i - 1
                is_upward = current_trend

        # 最後一個波段
        wave_data = df.iloc[wave_start_idx:]
        wave_max = wave_data['close_price'].max()
        wave_min = wave_data['close_price'].min()
        wave_618 = (wave_max - wave_min) / 2 * 0.618 + wave_min
        wave_head = (wave_max - wave_min) / 2 * 1 + wave_min
        waves.append({
            'start_date': df['date'].iloc[wave_start_idx],
            'end_date': df['date'].iloc[-1],
            'max_price': wave_max,
            'min_price': wave_min,
            '618': wave_618,
            'head': wave_head
        })
        
        latest_close_price = self.get_latest_close_price(stock_id)
        df = pd.DataFrame(waves)
        print(df)
        if latest_close_price and latest_close_price < wave_618:
            return df
        else:
            return None    

    def organize_ma_data(self, sma_values, weekly_sma_values, monthly_sma_values):
        """
        整理均線數據為易讀格式
        
        :param sma_values: 日均線數據列表
        :param weekly_sma_values: 週均線數據列表
        :param monthly_sma_values: 月���線數據列表
        :return: 整理後的均線數據字典
        """
        ma_data = {
            "日均線": {},
            "週均線": {},
            "月均線": {}
        }
        
        ma_periods = [5, 10, 20, 60, 120]
        
        # 處理日均線數據
        for i, period in enumerate(ma_periods):
            ma_data["日均線"][f"{period}日"] = sma_values[i] if i < len(sma_values) else "N/A"
        
        # 處理週均線數據
        for i, period in enumerate(ma_periods):
            ma_data["週均線"][f"{period}週"] = weekly_sma_values[i] if i < len(weekly_sma_values) else "N/A"
        
        # 處理月均線數據
        for i, period in enumerate(ma_periods):
            ma_data["月均線"][f"{period}月"] = monthly_sma_values[i] if i < len(monthly_sma_values) else "N/A"

        return ma_data

    def process_all_stocks(self, start_date, end_date, ratio, positive_ratio, native_ratio, top_n, recent_wave_var, highest_wave_var, total_wave_var, ma_selections, ratio_all_vars, ratio_type_vars):
        top_50_stocks = self.get_top_volumn_stocks(top_n)
        if isinstance(top_50_stocks, str) and top_50_stocks.startswith("錯誤："):
            return top_50_stocks
        else:
            # 處理正常的结果
            self.all_wave_extremes = []

            # 收集均線選擇
            # ma_selections = {
            #     'daily': {period: var.get() for period, var in self.daily_ma_vars.items()},
            #     'weekly': {period: var.get() for period, var in self.weekly_ma_vars.items()},
            #     'monthly': {period: var.get() for period, var in self.monthly_ma_vars.items()}
            # }

            count = 0
            for stock_id in top_50_stocks:
                try:
                    count += 1
                    print(f"正在處理股票: {stock_id} {count} / {len(top_50_stocks)}")
                    stock_segment = []
                    stock_data_df = self.get_stock_data(stock_id, start_date, end_date)
                    last_day_volume = None
                    latest_close_price = None
                    if stock_data_df is not None and not stock_data_df.empty:
                        try:
                            latest_close_price = self.get_latest_close_price(stock_id)
                        except Exception as e:
                            latest_close_price = stock_data_df['close_price'].iloc[-1]
                            print(f"取得最新收盤價時發生錯誤: {e}；以區間最後一天的收盤價: {latest_close_price} 代替")
                        last_day_volume = self.get_last_day_volume(stock_id, end_date)

                    wave_extremes_df = self.find_peaks_troughs_v34_small(stock_id, stock_data_df, latest_close_price, end_date)
                    if wave_extremes_df is not None and not wave_extremes_df.empty:
                        wave_extremes_df['stock_id'] = stock_id  # 加入股票代號
                        wave_extremes_df['name'] = self.get_stock_name(stock_id)
                        recent_segment, highest_segment = self.evaluate_segment(wave_extremes_df)
                        max_value_of_all_waves = wave_extremes_df['Max_Value'].max()
                        max_value_index = wave_extremes_df['Max_Value'].idxmax()

                        # 獲取最高價的日期
                        # max_value_date = wave_extremes_df.loc[max_value_index, 'Max_Date']
                        # # 在最高價之後找最低價
                        # # min_after_max_series = wave_extremes_df.loc[max_value_index:, 'Min_Value']
                        # # min_value_after_max = min_after_max_series.min()
                        # # min_after_max_index = min_after_max_series.idxmin()
                        # min_value_of_all_waves = wave_extremes_df['Min_Value'].min()
                        # min_value_index = wave_extremes_df['Min_Value'].idxmin()
                        # min_value_date = wave_extremes_df.loc[min_value_index, 'Min_Date']

                        # 獲取最高價的日期
                        max_value_date = wave_extremes_df.loc[max_value_index, 'Max_Date']
                        # 在最高價之後找最低價
                        min_after_max_series = wave_extremes_df.loc[max_value_index:, 'Min_Value']
                        min_value_after_max = min_after_max_series.min()
                        # min_value_of_all_waves = wave_extremes_df['Min_Value'].min()
                        min_after_max_index = min_after_max_series.idxmin()
                        # 獲取最低價的日期
                        min_value_date = wave_extremes_df.loc[min_after_max_index, 'Min_Date']

                        # 計算現價分別減去最高波段的 ratio_0.191、ratio_0.382、ratio_0.5、ratio_0.618、ratio_0.809、ratio_1、ratio_1.191、ratio_1.382、ratio_1.5、ratio_1.618、ratio_1.809、ratio_2
                        highest_segment['current_0191'] = latest_close_price - highest_segment['Ratio_0.191']
                        highest_segment['current_0382'] = latest_close_price - highest_segment['Ratio_0.382']
                        highest_segment['current_0500'] = latest_close_price - highest_segment['Ratio_0.5']
                        highest_segment['current_0618'] = latest_close_price - highest_segment['Ratio_0.618']
                        highest_segment['current_0809'] = latest_close_price - highest_segment['Ratio_0.809']
                        highest_segment['current_1'] = latest_close_price - highest_segment['Ratio_1']
                        highest_segment['current_1191'] = latest_close_price - highest_segment['Ratio_1.191']
                        highest_segment['current_1382'] = latest_close_price - highest_segment['Ratio_1.382']
                        highest_segment['current_1500'] = latest_close_price - highest_segment['Ratio_1.5']
                        highest_segment['current_1618'] = latest_close_price - highest_segment['Ratio_1.618']
                        highest_segment['current_1809'] = latest_close_price - highest_segment['Ratio_1.809']
                        highest_segment['current_2'] = latest_close_price - highest_segment['Ratio_2']

                        # 計算買點分別減去最高波段的 ratio_0.191、ratio_0.382、ratio_0.5、ratio_0.618、ratio_0.809、ratio_1、ratio_1.191、ratio_1.382、ratio_1.5、ratio_1.618、ratio_1.809、ratio_2
                        highest_segment['buy_0191'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_0.191']
                        highest_segment['buy_0382'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_0.382']
                        highest_segment['buy_0500'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_0.5']
                        highest_segment['buy_0618'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_0.618']
                        highest_segment['buy_0809'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_0.809']
                        highest_segment['buy_1'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_1']
                        highest_segment['buy_1191'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_1.191']
                        highest_segment['buy_1382'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_1.382']
                        highest_segment['buy_1500'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_1.5']
                        highest_segment['buy_1618'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_1.618']
                        highest_segment['buy_1809'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_1.809']
                        highest_segment['buy_2'] = highest_segment['Ratio_0.618'] - highest_segment['Ratio_2']

                        # 計算現價分別減去最近波段的 ratio_0.191、ratio_0.382、ratio_0.5、ratio_0.618、ratio_0.809、ratio_1、ratio_1.191、ratio_1.382、ratio_1.5、ratio_1.618、ratio_1.809、ratio_2
                        recent_segment['current_0191'] = round((latest_close_price - recent_segment['Ratio_0.191'].copy()) / latest_close_price, 3)
                        recent_segment['current_0382'] = round((latest_close_price - recent_segment['Ratio_0.382'].copy()) / latest_close_price, 3)
                        recent_segment['current_0500'] = round((latest_close_price - recent_segment['Ratio_0.5'].copy()) / latest_close_price, 3)
                        recent_segment['current_0618'] = round((latest_close_price - recent_segment['Ratio_0.618'].copy()) / latest_close_price, 3)
                        recent_segment['current_0809'] = round((latest_close_price - recent_segment['Ratio_0.809'].copy()) / latest_close_price, 3)
                        recent_segment['current_1'] = round((latest_close_price - recent_segment['Ratio_1'].copy()) / latest_close_price, 3)
                        recent_segment['current_1191'] = round((latest_close_price - recent_segment['Ratio_1.191'].copy()) / latest_close_price, 3)
                        recent_segment['current_1382'] = round((latest_close_price - recent_segment['Ratio_1.382'].copy()) / latest_close_price, 3)
                        recent_segment['current_1500'] = round((latest_close_price - recent_segment['Ratio_1.5'].copy()) / latest_close_price, 3)
                        recent_segment['current_1618'] = round((latest_close_price - recent_segment['Ratio_1.618'].copy()) / latest_close_price, 3)
                        recent_segment['current_1809'] = round((latest_close_price - recent_segment['Ratio_1.809'].copy()) / latest_close_price, 3)
                        recent_segment['current_2'] = round((latest_close_price - recent_segment['Ratio_2'].copy()) / latest_close_price, 3)

                        # 計算買點分別減去最近波段的 ratio_0.191、ratio_0.382、ratio_0.5、ratio_0.618、ratio_0.809、ratio_1、ratio_1.191、ratio_1.382、ratio_1.5、ratio_1.618、ratio_1.809、ratio_2
                        recent_segment['buy_0191'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_0.191'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_0382'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_0.382'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_0500'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_0.5'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_0618'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_0.618'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_0809'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_0.809'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_1'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_1'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_1191'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_1.191'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_1382'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_1.382'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_1500'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_1.5'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_1618'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_1.618'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_1809'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_1.809'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['buy_2'] = round((recent_segment['Ratio_0.618'].copy() - recent_segment['Ratio_2'].copy()) / recent_segment['Ratio_0.618'].copy(), 3)
                        recent_segment['last_day_volume'] = last_day_volume

                        # 計算 ratio_0.191、ratio_0.382、ratio_0.5、ratio_0.618、ratio_0.809、ratio_1
                        ratio_0 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0)
                        ratio_0191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.191)
                        ratio_0382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.382)
                        ratio_0500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.5)
                        ratio_0809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.809)
                        ratio_1191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.191)
                        ratio_1382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.382)
                        ratio_1500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.5)
                        ratio_1618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.618)
                        ratio_1809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 1.809)
                        ratio_2 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2)
                        ratio_2191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.191)
                        ratio_2382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.382)
                        ratio_2500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.5)
                        ratio_2618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.618)
                        ratio_2809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 2.809)
                        ratio_3 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3)
                        ratio_3191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.191)
                        ratio_3382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.382)
                        ratio_3500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.5)
                        ratio_3618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.618)
                        ratio_3809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 3.809)
                        ratio_4 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4)
                        ratio_4191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.191)
                        ratio_4382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.382)
                        ratio_4500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.5)
                        ratio_4618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.618)
                        ratio_4809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 4.809)
                        ratio_5 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5)
                        ratio_5191 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.191)
                        ratio_5382 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.382)
                        ratio_5500 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.5)
                        ratio_5618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.618)
                        ratio_5809 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 5.809)
                        ratio_6 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 6)


                        # 計算 ratio_0.618 和 ratio_1
                        ratio_0618 = Math.calculate_ratio_value(max_value_of_all_waves, min_value_after_max, 0.618)
                        ratio_1 = Math.calculate_ratio_1(max_value_of_all_waves, min_value_after_max)

                        # 計算 Head-0.618 價差比例
                        head_0618_spread_ratio = round((max_value_of_all_waves - ratio_0618) / ratio_0618, 3)

                        # 計算現價-0.191 價差比例
                        current_0191_spread_ratio = round((latest_close_price - ratio_0191) / latest_close_price, 3)

                        # 計算現價分別減去0.191、0.382、0.5、0.618、0.809、1、1.191、1.382、1.5、1.618、1.809、2
                        current_0191_spread_ratio = round((latest_close_price - ratio_0191) / latest_close_price, 3)
                        current_0382_spread_ratio = round((latest_close_price - ratio_0382) / latest_close_price, 3)
                        current_0500_spread_ratio = round((latest_close_price - ratio_0500) / latest_close_price, 3)
                        current_0618_spread_ratio = round((latest_close_price - ratio_0618) / latest_close_price, 3)
                        current_0809_spread_ratio = round((latest_close_price - ratio_0809) / latest_close_price, 3)
                        current_1_spread_ratio = round((latest_close_price - ratio_1) / latest_close_price, 3)
                        current_1191_spread_ratio = round((latest_close_price - ratio_1191) / latest_close_price, 3)
                        current_1382_spread_ratio = round((latest_close_price - ratio_1382) / latest_close_price, 3)
                        current_1500_spread_ratio = round((latest_close_price - ratio_1500) / latest_close_price, 3)
                        current_1618_spread_ratio = round((latest_close_price - ratio_1618) / latest_close_price, 3)
                        current_1809_spread_ratio = round((latest_close_price - ratio_1809) / latest_close_price, 3)
                        current_2_spread_ratio = round((latest_close_price - ratio_2) / latest_close_price, 3)

                        # 計算買點分別減去0.191、0.382、0.5、0.618、0.809、1、1.191、1.382、1.5、1.618、1.809、2
                        buy_0191_spread_ratio = round((latest_close_price - ratio_0191) / latest_close_price, 3)
                        buy_0382_spread_ratio = round((latest_close_price - ratio_0382) / latest_close_price, 3)
                        buy_0500_spread_ratio = round((latest_close_price - ratio_0500) / latest_close_price, 3)
                        buy_0618_spread_ratio = round((latest_close_price - ratio_0618) / latest_close_price, 3)
                        buy_0809_spread_ratio = round((latest_close_price - ratio_0809) / latest_close_price, 3)
                        buy_1_spread_ratio = round((latest_close_price - ratio_1) / latest_close_price, 3)
                        buy_1191_spread_ratio = round((latest_close_price - ratio_1191) / latest_close_price, 3)
                        buy_1382_spread_ratio = round((latest_close_price - ratio_1382) / latest_close_price, 3)
                        buy_1500_spread_ratio = round((latest_close_price - ratio_1500) / latest_close_price, 3)
                        buy_1618_spread_ratio = round((latest_close_price - ratio_1618) / latest_close_price, 3)
                        buy_1809_spread_ratio = round((latest_close_price - ratio_1809) / latest_close_price, 3)
                        buy_2_spread_ratio = round((latest_close_price - ratio_2) / latest_close_price, 3)
                        
                        # 計算CDP
                        CDP = highest_segment['CDP']
                        NH = highest_segment['NH']
                        NL = highest_segment['NL']
                        AH = highest_segment['AH']
                        AL = highest_segment['AL']

                        stock_name = highest_segment.get('name', '')

                        latest_close_prices = recent_segment['latest_close_prices']
                        latest_dates = recent_segment['latest_dates']

                        gap_df = self.get_gap_stocks(stock_data_df)
                        try:
                            now_price = self.get_latest_close_price(stock_id)
                        except Exception as e:
                            now_price = latest_close_price
                            print(f"取得現價時發生錯誤: {e}；以最新收盤價: {latest_close_price} 代替")
                        next_open_price = self.get_next_open_price_date(stock_id, end_date)
                        latest_close_price_date = stock_data_df[stock_data_df['date'] == pd.to_datetime(end_date)]
                        latest_close_price_by_date = None
                        if latest_close_price_date.empty:
                            latest_close_price_by_date = None;
                        else:
                            latest_close_price_by_date = latest_close_price_date['close_price'].iloc[-1]
                        

                        segment = {
                            'stock_id': stock_id,
                            'name': stock_name,
                            'latest_close_price': latest_close_price,
                            'wave_type': [None],
                            'Max_Date': max_value_date,
                            'Min_Date': min_value_date,
                            'Max_Value': max_value_of_all_waves,
                            'Min_Value': min_value_after_max,
                            'Ratio_0': ratio_0,
                            'Ratio_0.191': ratio_0191,
                            'Ratio_0.382': ratio_0382,
                            'Ratio_0.5': ratio_0500,
                            'Ratio_0.618': ratio_0618,
                            'Ratio_0.809': ratio_0809,
                            'Ratio_1': ratio_1,
                            'Ratio_1.191': ratio_1191,
                            'Ratio_1.382': ratio_1382,
                            'Ratio_1.5': ratio_1500,
                            'Ratio_1.618': ratio_1618,
                            'Ratio_1.809': ratio_1809,
                            'Ratio_2': ratio_2,
                            'Ratio_2.191': ratio_2191,
                            'Ratio_2.382': ratio_2382,
                            'Ratio_2.5': ratio_2500,
                            'Ratio_2.618': ratio_2618,
                            'Ratio_2.809': ratio_2809,
                            'Ratio_3': ratio_3,
                            'Ratio_3.191': ratio_3191,
                            'Ratio_3.382': ratio_3382,
                            'Ratio_3.5': ratio_3500,
                            'Ratio_3.618': ratio_3618,
                            'Ratio_3.809': ratio_3809,
                            'Ratio_4': ratio_4,
                            'Ratio_4.191': ratio_4191,
                            'Ratio_4.382': ratio_4382,
                            'Ratio_4.5': ratio_4500,
                            'Ratio_4.618': ratio_4618,
                            'Ratio_4.809': ratio_4809,
                            'Ratio_5': ratio_5,
                            'Ratio_5.191': ratio_5191,
                            'Ratio_5.382': ratio_5382,
                            'Ratio_5.5': ratio_5500,
                            'Ratio_5.618': ratio_5618,
                            'Ratio_5.809': ratio_5809,
                            'Ratio_6': ratio_6,
                            'spread_ratio': head_0618_spread_ratio,
                            'latest_close_price-0.191_ratio': current_0191_spread_ratio,
                            'max_value_of_all_waves': max_value_of_all_waves,
                            'min_value_after_max': min_value_after_max,
                            'wave_type': '',
                            'CDP': CDP,
                            'NH': NH,
                            'NL': NL,
                            'AH': AH,
                            'AL': AL,
                            'latest_close_prices': latest_close_prices,
                            'latest_dates': latest_dates,
                            'current_0191': current_0191_spread_ratio,
                            'current_0382': current_0382_spread_ratio,
                            'current_0500': current_0500_spread_ratio,
                            'current_0618': current_0618_spread_ratio,
                            'current_0809': current_0809_spread_ratio,
                            'current_1': current_1_spread_ratio,
                            'current_1191': current_1191_spread_ratio,
                            'current_1382': current_1382_spread_ratio,
                            'current_1500': current_1500_spread_ratio,
                            'current_1618': current_1618_spread_ratio,
                            'current_1809': current_1809_spread_ratio,
                            'current_2': current_2_spread_ratio,
                            'buy_0191': buy_0191_spread_ratio,
                            'buy_0382': buy_0382_spread_ratio,
                            'buy_0500': buy_0500_spread_ratio,
                            'buy_0618': buy_0618_spread_ratio,
                            'buy_0809': buy_0809_spread_ratio,
                            'buy_1': buy_1_spread_ratio,
                            'buy_1191': buy_1191_spread_ratio,
                            'buy_1382': buy_1382_spread_ratio,
                            'buy_1500': buy_1500_spread_ratio,
                            'buy_1618': buy_1618_spread_ratio,
                            'buy_1809': buy_1809_spread_ratio,
                            'buy_2': buy_2_spread_ratio,
                            'gap_df': gap_df,
                            'now_price': now_price,
                            'next_open_price': next_open_price,
                            'latest_close_price_by_date': latest_close_price_by_date,
                            'last_day_volume': last_day_volume
                        }

                        is_ma_selected, is_more_than_ma = self.check_price_above_selected_ma(latest_close_price, recent_segment, ma_selections)
                        if not is_ma_selected:
                            # if ((float(ratio) < recent_segment['spread_ratio'] or float(ratio) * -1 > recent_segment['spread_ratio'])\
                            #     and (recent_wave_var and (float(positive_ratio) >= recent_segment['latest_close_price-0.191_ratio'] \
                            #     and float(native_ratio) * -1 <= recent_segment['latest_close_price-0.191_ratio'])))\
                            #     or ((float(ratio) < highest_segment['spread_ratio'] or float(ratio) * -1 > highest_segment['spread_ratio'])\
                            #     and (highest_wave_var and (float(positive_ratio) >= highest_segment['latest_close_price-0.191_ratio'] \
                            #     and float(native_ratio) * -1 <= highest_segment['latest_close_price-0.191_ratio'])))\
                            #     or ((float(ratio) < head_0618_spread_ratio or float(ratio) * -1 > head_0618_spread_ratio)\
                            #     and (total_wave_var and (float(positive_ratio) >= current_0191_spread_ratio \
                            #     and float(native_ratio) * -1 <= current_0191_spread_ratio))):
                            #     self.add_wave_segment(recent_segment, '最近波段', max_value_of_all_waves, min_value_after_max)
                            #     self.add_wave_segment(highest_segment, '最高波段', max_value_of_all_waves, min_value_after_max)
                            #     self.add_wave_segment(segment, '總波段', max_value_of_all_waves, min_value_after_max)
                            if (float(ratio) <= recent_segment['spread_ratio'] or float(ratio) * -1 >= recent_segment['spread_ratio'])\
                                and (recent_wave_var):
                                # 判斷是否為買價，如果是，則逐一檢查recent_segment['buy_ratio']的價格是否在positive_ratio和native_ratio之間
                                if ratio_type_vars['buy']:
                                    ratios_to_check = {
                                        '0.191': recent_segment['buy_0191'],
                                        '0.382': recent_segment['buy_0382'],
                                        '0.500': recent_segment['buy_0500'],
                                        '0.618': recent_segment['buy_0618'],
                                        '0.809': recent_segment['buy_0809'],
                                        '1.000': recent_segment['buy_1'],
                                        '1.191': recent_segment['buy_1191'],
                                        '1.382': recent_segment['buy_1382'],
                                        '1.500': recent_segment['buy_1500'],
                                        '1.618': recent_segment['buy_1618'],
                                        '1.809': recent_segment['buy_1809'],
                                        '2.000': recent_segment['buy_2']
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue

                                if ratio_type_vars['current']:
                                        ratios_to_check = {
                                            '0.191': recent_segment['current_0191'],
                                            '0.382': recent_segment['current_0382'],
                                            '0.500': recent_segment['current_0500'],
                                            '0.618': recent_segment['current_0618'],
                                            '0.809': recent_segment['current_0809'],
                                            '1.000': recent_segment['current_1'],
                                            '1.191': recent_segment['current_1191'],
                                            '1.382': recent_segment['current_1382'],
                                            '1.500': recent_segment['current_1500'],
                                            '1.618': recent_segment['current_1618'],
                                            '1.809': recent_segment['current_1809'],
                                            '2.000': recent_segment['current_2']
                                        }
                                        matched_ratios = {}
                                        closest_ratio_key = None
                                        closest_ratio_value = float('inf')
                                        for ratio_key, ratio_value in ratios_to_check.items():
                                            if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                    float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                    float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                                
                                                # 计算接近程度
                                                proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                                
                                                # 更新最接近的比例
                                                if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                    closest_ratio_key = ratio_key
                                                    closest_ratio_value = proximity

                                        # 将最接近的比例添加到匹配结果中
                                        if closest_ratio_key is not None:
                                            matched_ratios[closest_ratio_key] = {
                                                'stock_id': stock_id,
                                                'matched_ratios': [closest_ratio_key],
                                                'stock_data': {
                                                    'recent_segment': recent_segment,
                                                    'highest_segment': highest_segment,
                                                    'total_segment': segment
                                                }
                                            }

                                        if matched_ratios and closest_ratio_key is not None:
                                            stock_segment = {
                                                'stock_id': stock_id,
                                                'matched_ratios': matched_ratios,
                                                'stock_data': {
                                                    'recent_segment': recent_segment,
                                                    'highest_segment': highest_segment,
                                                    'total_segment': segment
                                                }
                                            }
                                            self.event.notify(stock_segment)
                                            self.all_wave_extremes.append(recent_segment)
                                            self.all_wave_extremes.append(highest_segment)
                                            self.all_wave_extremes.append(segment)
                                            continue
                            elif (float(ratio) <= highest_segment['spread_ratio'] or float(ratio) * -1 >= highest_segment['spread_ratio'])\
                                and (highest_wave_var):
                                # 判斷是否為買價，如果是，則逐一檢查highest_segment['buy_ratio']的價格是否在positive_ratio和native_ratio之間
                                if ratio_type_vars['buy']:
                                    ratios_to_check = {
                                        '0.191': recent_segment['buy_0191'],
                                        '0.382': recent_segment['buy_0382'],
                                        '0.500': recent_segment['buy_0500'],
                                        '0.618': recent_segment['buy_0618'],
                                        '0.809': recent_segment['buy_0809'],
                                        '1.000': recent_segment['buy_1'],
                                        '1.191': recent_segment['buy_1191'],
                                        '1.382': recent_segment['buy_1382'],
                                        '1.500': recent_segment['buy_1500'],
                                        '1.618': recent_segment['buy_1618'],
                                        '1.809': recent_segment['buy_1809'],
                                        '2.000': recent_segment['buy_2']
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue

                            elif (float(ratio) <= head_0618_spread_ratio or float(ratio) * -1 >= head_0618_spread_ratio)\
                                and (total_wave_var):
                                if ratio_type_vars['buy']:
                                    ratios_to_check = {
                                        '0.191': recent_segment['buy_0191'],
                                        '0.382': recent_segment['buy_0382'],
                                        '0.500': recent_segment['buy_0500'],
                                        '0.618': recent_segment['buy_0618'],
                                        '0.809': recent_segment['buy_0809'],
                                        '1.000': recent_segment['buy_1'],
                                        '1.191': recent_segment['buy_1191'],
                                        '1.382': recent_segment['buy_1382'],
                                        '1.500': recent_segment['buy_1500'],
                                        '1.618': recent_segment['buy_1618'],
                                        '1.809': recent_segment['buy_1809'],
                                        '2.000': recent_segment['buy_2']
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue
                        elif is_more_than_ma:
                            if (float(ratio) <= recent_segment['spread_ratio'] or float(ratio) * -1 >= recent_segment['spread_ratio'])\
                                and (recent_wave_var):
                                # 判斷是否為買價，如果是，則逐一檢查recent_segment['buy_ratio']的價格是否在positive_ratio和native_ratio之間
                                if ratio_type_vars['buy']:
                                    ratios_to_check = {
                                        '0.191': recent_segment['buy_0191'],
                                        '0.382': recent_segment['buy_0382'],
                                        '0.500': recent_segment['buy_0500'],
                                        '0.618': recent_segment['buy_0618'],
                                        '0.809': recent_segment['buy_0809'],
                                        '1.000': recent_segment['buy_1'],
                                        '1.191': recent_segment['buy_1191'],
                                        '1.382': recent_segment['buy_1382'],
                                        '1.500': recent_segment['buy_1500'],
                                        '1.618': recent_segment['buy_1618'],
                                        '1.809': recent_segment['buy_1809'],
                                        '2.000': recent_segment['buy_2']
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue

                                if ratio_type_vars['current']:
                                        ratios_to_check = {
                                            '0.191': recent_segment['current_0191'],
                                            '0.382': recent_segment['current_0382'],
                                            '0.500': recent_segment['current_0500'],
                                            '0.618': recent_segment['current_0618'],
                                            '0.809': recent_segment['current_0809'],
                                            '1.000': recent_segment['current_1'],
                                            '1.191': recent_segment['current_1191'],
                                            '1.382': recent_segment['current_1382'],
                                            '1.500': recent_segment['current_1500'],
                                            '1.618': recent_segment['current_1618'],
                                            '1.809': recent_segment['current_1809'],
                                            '2.000': recent_segment['current_2']
                                        }

                                        # 记录每个比例区间的匹配情况
                                        matched_ratios = {}
                                        closest_ratio_key = None
                                        closest_ratio_value = float('inf')
                                        for ratio_key, ratio_value in ratios_to_check.items():
                                            if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                    float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                    float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                                
                                                # 计算接近程度
                                                proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                                
                                                # 更新最接近的比例
                                                if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                    closest_ratio_key = ratio_key
                                                    closest_ratio_value = proximity

                                        # 将最接近的比例添加到匹配结果中
                                        if closest_ratio_key is not None:
                                            matched_ratios[closest_ratio_key] = {
                                                'stock_id': stock_id,
                                                'matched_ratios': [closest_ratio_key],
                                                'stock_data': {
                                                    'recent_segment': recent_segment,
                                                    'highest_segment': highest_segment,
                                                    'total_segment': segment
                                                }
                                            }

                                        if matched_ratios and closest_ratio_key is not None:
                                            stock_segment = {
                                                'stock_id': stock_id,
                                                'matched_ratios': matched_ratios,
                                                'stock_data': {
                                                    'recent_segment': recent_segment,
                                                    'highest_segment': highest_segment,
                                                    'total_segment': segment
                                                }
                                            }
                                            self.event.notify(stock_segment)
                                            self.all_wave_extremes.append(recent_segment)
                                            self.all_wave_extremes.append(highest_segment)
                                            self.all_wave_extremes.append(segment)
                                            continue
                            elif (float(ratio) <= highest_segment['spread_ratio'] or float(ratio) * -1 >= highest_segment['spread_ratio'])\
                                and (highest_wave_var):
                                # 判斷是否為買價，如果是，則逐一檢查highest_segment['buy_ratio']的價格是否在positive_ratio和native_ratio之間
                                if ratio_type_vars['buy']:
                                    ratios_to_check = {
                                        '0.191': highest_segment['buy_0191'],
                                        '0.382': highest_segment['buy_0382'],
                                        '0.500': highest_segment['buy_0500'],
                                        '0.618': highest_segment['buy_0618'],
                                        '0.809': highest_segment['buy_0809'],
                                        '1.000': highest_segment['buy_1'],
                                        '1.191': highest_segment['buy_1191'],
                                        '1.382': highest_segment['buy_1382'],
                                        '1.500': highest_segment['buy_1500'],
                                        '1.618': highest_segment['buy_1618'],
                                        '1.809': highest_segment['buy_1809'],
                                        '2.000': highest_segment['buy_2']
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue

                                if ratio_type_vars['current']:
                                    ratios_to_check = {
                                        '0.191': highest_segment['current_0191'],
                                        '0.382': highest_segment['current_0382'],
                                        '0.500': highest_segment['current_0500'],
                                        '0.618': highest_segment['current_0618'],
                                        '0.809': highest_segment['current_0809'],
                                        '1.000': highest_segment['current_1'],
                                        '1.191': highest_segment['current_1191'],
                                        '1.382': highest_segment['current_1382'],
                                        '1.500': highest_segment['current_1500'],
                                        '1.618': highest_segment['current_1618'],
                                        '1.809': highest_segment['current_1809'],
                                        '2.000': highest_segment['current_2']
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue

                            elif (float(ratio) <= head_0618_spread_ratio or float(ratio) * -1 >= head_0618_spread_ratio)\
                                and (total_wave_var):
                                if ratio_type_vars['buy']:
                                    ratios_to_check = {
                                        '0.191': buy_0191_spread_ratio,
                                        '0.382': buy_0382_spread_ratio,
                                        '0.500': buy_0500_spread_ratio,
                                        '0.618': buy_0618_spread_ratio,
                                        '0.809': buy_0809_spread_ratio,
                                        '1.000': buy_1_spread_ratio,
                                        '1.191': buy_1191_spread_ratio,
                                        '1.382': buy_1382_spread_ratio,
                                        '1.500': buy_1500_spread_ratio,
                                        '1.618': buy_1618_spread_ratio,
                                        '1.809': buy_1809_spread_ratio,
                                        '2.000': buy_2_spread_ratio
                                    }
                                    matched_ratios = {}
                                    closest_ratio_key = None
                                    closest_ratio_value = float('inf')
                                    for ratio_key, ratio_value in ratios_to_check.items():
                                        if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                            
                                            # 计算接近程度
                                            proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                            
                                            # 更新最接近的比例
                                            if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                closest_ratio_key = ratio_key
                                                closest_ratio_value = proximity

                                    # 将最接近的比例添加到匹配结果中
                                    if closest_ratio_key is not None:
                                        matched_ratios[closest_ratio_key] = {
                                            'stock_id': stock_id,
                                            'matched_ratios': [closest_ratio_key],
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }

                                    if matched_ratios and closest_ratio_key is not None:
                                        stock_segment = {
                                            'stock_id': stock_id,
                                            'matched_ratios': matched_ratios,
                                            'stock_data': {
                                                'recent_segment': recent_segment,
                                                'highest_segment': highest_segment,
                                                'total_segment': segment
                                            }
                                        }
                                        self.event.notify(stock_segment)
                                        self.all_wave_extremes.append(recent_segment)
                                        self.all_wave_extremes.append(highest_segment)
                                        self.all_wave_extremes.append(segment)
                                        continue
                                if ratio_type_vars['current']:
                                        ratios_to_check = {
                                            '0.191': current_0191_spread_ratio,
                                            '0.382': current_0382_spread_ratio,
                                            '0.500': current_0500_spread_ratio,
                                            '0.618': current_0618_spread_ratio,
                                            '0.809': current_0809_spread_ratio,
                                            '1.000': current_1_spread_ratio,
                                            '1.191': current_1191_spread_ratio,
                                            '1.382': current_1382_spread_ratio,
                                            '1.500': current_1500_spread_ratio,
                                            '1.618': current_1618_spread_ratio,
                                            '1.809': current_1809_spread_ratio,
                                            '2.000': current_2_spread_ratio
                                        }
                                        matched_ratios = {}
                                        closest_ratio_key = None
                                        closest_ratio_value = float('inf')
                                        for ratio_key, ratio_value in ratios_to_check.items():
                                            if (ratio_all_vars.get(ratio_key, False) and  # 该比例被选中
                                                    float(positive_ratio) >= ratio_value and  # 在正比例范围内
                                                    float(native_ratio) * -1 <= ratio_value): # 在负比例范围内
                                                
                                                # 计算接近程度
                                                proximity = min(abs(float(positive_ratio) - ratio_value), abs(float(native_ratio) * -1 - ratio_value))
                                                
                                                # 更新最接近的比例
                                                if proximity < closest_ratio_value or (proximity == closest_ratio_value and float(ratio_key) < float(closest_ratio_key)):
                                                    closest_ratio_key = ratio_key
                                                    closest_ratio_value = proximity

                                        # 将最接近的比例添加到匹配结果中
                                        if closest_ratio_key is not None:
                                            matched_ratios[closest_ratio_key] = {
                                                'stock_id': stock_id,
                                                'matched_ratios': [closest_ratio_key],
                                                'stock_data': {
                                                    'recent_segment': recent_segment,
                                                    'highest_segment': highest_segment,
                                                    'total_segment': segment
                                                }
                                            }

                                        if matched_ratios and closest_ratio_key is not None:
                                            stock_segment = {
                                                'stock_id': stock_id,
                                                'matched_ratios': matched_ratios,
                                                'stock_data': {
                                                    'recent_segment': recent_segment,
                                                    'highest_segment': highest_segment,
                                                    'total_segment': segment
                                                }
                                            }
                                            self.event.notify(stock_segment)
                                            self.all_wave_extremes.append(recent_segment)
                                            self.all_wave_extremes.append(highest_segment)
                                            self.all_wave_extremes.append(segment)
                                            continue
                            # 如果选择了现价，检查每个比例区间
                            
                except Exception as e:
                    print(f"無法獲取股票 {stock_id} 的數據: {str(e)}")
                    self.write_log(f"無法分析股票 {stock_id} 的數據: {str(e)}")
                    continue
                    
            # if self.all_wave_extremes is not None:
            #     return self.all_wave_extremes

            # return pd.DataFrame()
        
    def get_recent_segment(self, segments_df):
        # 获取最近一次波段数据
        if not segments_df.empty:
            return segments_df.iloc[-1].copy()  # 最近一次波段数据在最后一行
        else:
            return None

    def get_highest_segment(self, segments_df):
        # 获取最高点波段数据
        if not segments_df.empty:
            max_value_idx = segments_df['Max_Value'].idxmax()  # 找到最高点波段的索引
            return segments_df.iloc[max_value_idx].copy()
        else:
            return None
        
    def evaluate_segment(self, segments_df):
        recent_segment = self.get_recent_segment(segments_df)
        highest_segment = self.get_highest_segment(segments_df)
        
        return recent_segment, highest_segment
    
    def add_wave_segment(self, segment_data, wave_type, max_value_of_all_waves, min_value_after_max):
        """
        添加波段信息到 all_wave_extremes 列表中。

        :param all_wave_extremes: 存儲所有波段信息的列表
        :param segment_data: 要添加的波段信息字典
        :param wave_type: 波段類型（'最近波段', '最高波段', 或 '總波段'）
        :param max_value_of_all_waves: 所有波段中的最高值
        :param min_value_after_max: 最高點之後的最低值
        """
        stock_segment = {}
        new_segment = segment_data.copy()  # 創建一個新的字典，避免修改原始數據
        new_segment['wave_type'] = wave_type
        new_segment['max_value_of_all_waves'] = max_value_of_all_waves
        new_segment['min_value_after_max'] = min_value_after_max
        self.all_wave_extremes.append(new_segment)
        self.event.notify(new_segment)
                
        # 如果需要,可以在這裡打印整理後的均線數據
        if 'organized_ma_data' in segment_data:
            print(f"{wave_type} 均線數據:")
            for ma_type, ma_values in segment_data['organized_ma_data'].items():
                print(f"  {ma_type}:")
                for period, value in ma_values.items():
                    print(f"    {period}: {value}")
    
    def check_price_above_selected_ma(self, current_price, segment_data, ma_selections):
        """
        檢查現價是否同時大於或等於所有選擇的均線價格。

        :param current_price: 股票當前價格
        :param segment_data: 包含均線數據的字典
        :param ma_selections: 用戶選擇的均線
        :return: 元組 (是否有選擇均線, 是否大於等於所有選擇的均線)
        """
        is_any_ma_selected = False
        is_above_all_selected_ma = True

        for ma_type in ['daily', 'weekly', 'monthly', '15min']:
            for period, is_selected in ma_selections[ma_type].items():
                if is_selected:
                    is_any_ma_selected = True
                    ma_column = f"{ma_type}_sma_{period}" if ma_type != 'daily' else f"sma_{period}"
                    if ma_column in segment_data:
                        if current_price < segment_data[ma_column]:
                            is_above_all_selected_ma = False
                            return is_any_ma_selected, is_above_all_selected_ma
                    else:
                        print(f"警告: {ma_column} 不在 segment_data 中")
                        is_above_all_selected_ma = False
                        return is_any_ma_selected, is_above_all_selected_ma

        return is_any_ma_selected, is_above_all_selected_ma
    
    def get_ratio_prices(self, stock_id):
        # 獲取股票的基準價格（例如最新收盤價）
        base_price = self.get_base_price(stock_id)
        
        ratios = [0.191, 0.382, 0.5, 0.618, 0.809, 1, 1.382, 1.5, 1.618, 1.809, 2, 2.191, 2.382, 2.5, 2.618, 2.809, 3, 
                  3.191, 3.382, 3.5, 3.618, 3.809, 4]
        ratio_prices = {}
        
        for ratio in ratios:
            price = base_price * ratio
            ratio_prices[f"{ratio:.3f}"] = f"{price:.2f}"
        
        return ratio_prices

    def get_stock_data_from_all_wave_extremes(self, stock_id):
        matching_segments = []
        for segment in self.all_wave_extremes:
            if str(segment['stock_id']) == str(stock_id):
                matching_segments.append(segment)
                if len(matching_segments) == 3:
                    return matching_segments[0], matching_segments[2]  # 返回最近波段和總波段
        
        if matching_segments:
            print(f"警告：股票 {stock_id} 沒有找到足夠的波段數據")
            return matching_segments[0], matching_segments[-1] if len(matching_segments) > 1 else matching_segments[0]
        
        return None, None  # 如果完全沒有找到匹配的股票數據

    def write_log(self, message):
        with open(self.log_filename, "a") as log_file:
            log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            
    # 取得日期的下一個交易日開盤價格
    def get_next_open_price_date(self, stock_code, date):
        # 取得下一個交易日
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # 查詢下一個交易日的開盤價格
            query = """
                SELECT TOP 1 date, open_price
                FROM stock_data
                WHERE stock_id = %s AND date > %s
                ORDER BY date ASC
            """
            cursor.execute(query, (stock_code, date))
            result = cursor.fetchone()
            
            if result:
                return {
                    'date': result[0],
                    'open_price': result[1]
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error in get_next_open_price_date: {e}")
            return None
            
        finally:
            cursor.close()
            conn.close()





