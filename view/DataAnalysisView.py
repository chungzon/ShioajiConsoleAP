from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import os
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from common.Math import Math


class DataAnalysisView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.init_ui()

    def init_ui(self):
         # 股票代碼
        ttk.Label(self, text="股票代碼:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.entry_stock_id = ttk.Entry(self)
        self.entry_stock_id.grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(self, text="檢查資料", command=self.check_stock_data).grid(row=0, column=2, padx=10, pady=5)

        # 起始日期
        ttk.Label(self, text="起始日期 (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_start_date = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_start_date.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # 結束日期
        ttk.Label(self, text="結束日期 (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_end_date = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_end_date.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # 設置默認日期（例如：最近一年）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        self.entry_start_date.set_date(start_date)
        self.entry_end_date.set_date(end_date)

      # 獲取下載資料夾路徑
        self.downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # 儲存路徑
        ttk.Label(self, text="儲存路徑:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.entry_file_path = ttk.Entry(self)
        self.entry_file_path.grid(row=3, column=1, padx=10, pady=5)
        self.entry_file_path.insert(0, self.downloads_path)  # 設置預設路徑
        ttk.Button(self, text="瀏覽", command=self.browse_file).grid(row=3, column=2, padx=10, pady=5)

        # Ticks 更新日期
        self.label_update_date_ticks = ttk.Label(self, text="Ticks 更新日期: 未知")
        self.label_update_date_ticks.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        # self.button_update_ticks = ttk.Button(self, text="更新 Ticks", command=self.controller.update_data_ticks)
        # self.button_update_ticks.grid(row=4, column=2, padx=10, pady=5)

        # Kbars 更新日期
        self.label_update_date_kbars = ttk.Label(self, text="Kbars 更新日期: 未知")
        self.label_update_date_kbars.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        # self.button_update_kbars = ttk.Button(self, text="更新 Kbars", command=self.controller.update_data_kbars)
        # self.button_update_kbars.grid(row=5, column=2, padx=10, pady=5)

        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        # 狀態標籤
        self.status_label = ttk.Label(self, text="狀態: ")
        self.status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

        # 確認和分析資料按鈕
        ttk.Button(self, text="分析資料", command=self.analyze_data).grid(row=9, column=0, columnspan=3, pady=20)

        ttk.Button(self, text="詳細資料", command=self.show_detail_data).grid(row=9, column=2, columnspan=3, pady=20)
        


    def check_stock_data(self):
        self.controller.check_stock_data()
        
    def browse_file(self):
        self.controller.browse_file()
        
    def set_status(self, status):
        self.status_label.config(text=f"狀態: {status}")
        
    def analyze_data(self):
        self.controller.analyze_data()

    def show_detail_data(self):
        self.controller.show_detail_data()

    def create_ma_table(self, ma_data, ma_type):
        # 创建通用的均价表格
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(5)
        table.setHorizontalHeaderLabels(["週期", "價格"])
                # 設置表頭樣式
        header_font = QFont('Microsoft JhengHei', 12, QFont.Bold)
        table.horizontalHeader().setFont(header_font)
        
        ma_periods = ['5MA', '10MA', '20MA', '60MA', '120MA']
        for row, period in enumerate(ma_periods):
            # 设置周期
            period_item = QTableWidgetItem(period)
            table.setItem(row, 0, period_item)
            
            # 设置价格
            price = ma_data[ma_type].get(period, 'N/A')
            if hasattr(price, 'item'):
                price = f"{price.item():.2f}"
            price_item = QTableWidgetItem(str(price))
            table.setItem(row, 1, price_item)
        
        table.resizeColumnsToContents()
        return table

    def create_ratio_table(self, ratio_prices, indicator_prices, organized_ma_data):
        table = QTableWidget()
        table.setColumnCount(3)  # 改为3列：比例、總波段、指標
        
        # 设置固定的比例序列
        ratios = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                 '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                 '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                 '3.191', '3.382', '3.5', '3.618', '3.809', '4']
        
        # 计算总行数（包括前后和中间的空白行）
        total_rows = (len(ratios) * 2 - 1) + 2  # 加2是为了前后的空白行
        table.setRowCount(total_rows)
        table.setHorizontalHeaderLabels(["比例", "總波段", "指標"])

        font = QFont()
        font.setPointSize(13)
        table.setFont(font)
        table.horizontalHeader().setFont(font)
        
        # 辅助函数：添加数据到单元格并按价格排序
        def add_to_cell(row, col, new_text, is_daily_ma=False):
            current_item = table.item(row, col)
            current_text = current_item.text() if current_item else ""
            
            # 收集所有价格项及其属性（是否为日均价）
            all_items = []
            if current_text:
                lines = current_text.split('\n')
                for line in lines:
                    is_daily = line.startswith('日')
                    all_items.append((line, is_daily))
            if new_text:
                all_items.append((new_text, is_daily_ma))
            
            # 提取价格进行排序
            def extract_price(item_tuple):
                text = item_tuple[0]
                try:
                    # 提取价格，支持多种格式
                    if '：' in text:
                        price = float(text.split('：')[-1].split('(')[0])
                    elif ':' in text:
                        price = float(text.split(':')[-1].split('(')[0])
                    else:
                        price = float(text.split()[-1])
                    return price  # 直接返回价格，实现从小到大排序
                except:
                    return float('inf')  # 无法提取价格的项放到最后
            
            # 按价格从小到大排序
            all_items.sort(key=extract_price)
            
            # 创建最终的表格项
            text_lines = []
            for text, is_daily in all_items:
                # 为每一行创建新的表格项
                item = QTableWidgetItem(text)
                if is_daily:
                    item.setForeground(QBrush(QColor("red")))
                else:
                    item.setForeground(QBrush(QColor("black")))
                text_lines.append(item)
            
            # 合并所有文本
            final_text = '\n'.join(item.text() for item in text_lines)
            new_item = QTableWidgetItem(final_text)
            
            # 设置背景色
            if current_item:
                new_item.setBackground(current_item.background())
            else:
                is_alternate = (row % 2) == 0
                color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
                new_item.setBackground(QBrush(color))
            
            # 设置文本颜色
            if is_daily_ma:
                new_item.setForeground(QBrush(QColor("red")))
            
            table.setItem(row, col, new_item)
        
        # 设置交替行颜色
        def set_row_color(table, row, is_alternate):
            color = QColor("#FFFFFF") if is_alternate else QColor("#E6F3FF")  # 淺灰色 : 淺藍色
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                item.setBackground(QBrush(color))
                table.setItem(row, col, item)
        
        # 首先创建所有单元格并设置颜色
        for row in range(total_rows):
            # 第一行和最后一行是浅灰色
            if row == 0 or row == total_rows - 1:
                set_row_color(table, row, True)
            # 其他行交替设置颜色
            else:
                is_alternate = (row % 2) == 0  # 偶数行使用浅灰色
                set_row_color(table, row, is_alternate)
        
        # 填充比例和总波段数据（向下偏移一行）
        for i, ratio in enumerate(ratios):
            row = (i * 2) + 1  # 偏移一行
            
            # 设置比例行的颜色（奇数行）
            set_row_color(table, row, False)
            
            # 设置比例
            ratio_item = QTableWidgetItem(ratio)
            is_alternate = (row % 2) == 0
            color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
            ratio_item.setBackground(QBrush(color))
            table.setItem(row, 0, ratio_item)
            
            # 设置总波段价格
            price = ratio_prices['總波段'].get(ratio, 'N/A')
            if hasattr(price, 'item'):
                price = f"{price.item():.2f}"
            price_item = QTableWidgetItem(str(price))
            price_item.setBackground(QBrush(color))
            table.setItem(row, 1, price_item)
            
            # 添加空白行并设置颜色（偶数行）
            if i < len(ratios) - 1:
                row_between = row + 1
                set_row_color(table, row_between, True)
                for col in range(table.columnCount()):
                    table.setItem(row_between, col, QTableWidgetItem(""))
        
        # 设置第一行（0之前的空白行）和最后一行的颜色
        set_row_color(table, 0, True)  # 第一个空白行
        set_row_color(table, total_rows - 1, True)  # 最后一个空白行
        
        # 辅助函数：确定值应该填入哪一行
        def find_row_for_value(value):
            min_price = float(ratio_prices['總波段']['0'])
            max_price = float(ratio_prices['總波段']['4'])
            
            # 如果价格小于最小比例价格
            if value < min_price:
                return 0  # 第一个空白行
            
            # 如果价格大于最大比例价
            if value > max_price:
                return total_rows - 1  # 最后一个空白行
            
            # 在比例价格之间查找位置
            for i, ratio in enumerate(ratios[:-1]):
                current_price = float(ratio_prices['總波段'][ratio])
                next_price = float(ratio_prices['總波段'][ratios[i + 1]])
                
                row = (i * 2) + 1  # 考虑偏移
                
                if abs(value - current_price) < 0.01:
                    return row
                elif current_price < value < next_price or next_price < value < current_price:
                    return row + 1
            
            return total_rows - 1  # 如果没找到合适的位置，放在最后

        # 处理均线数据 - 现在添加到指标列
        ma_types = {
            '日均線': '日',
            '週均線': '周',
            '月均線': '月'
        }
        
        for ma_key, prefix in ma_types.items():
            ma_data = organized_ma_data[ma_key]
            for ma_period in ['5MA', '10MA', '20MA', '60MA', '120MA']:
                if ma_period not in ma_data or ma_data[ma_period] == 'N/A':
                    continue
                    
                value = ma_data[ma_period]
                if hasattr(value, 'item'):
                    value = value.item()
                
                period_num = ma_period.replace('MA', '')
                ma_text = f"{prefix}({period_num})：{value:.2f}"
                
                # 找到应该填入的行
                row = find_row_for_value(value)
                add_to_cell(row, 2, ma_text)  # 现在添加到指标列(列索引2)
        
        # 处理指标数据
        for indicator_name, value in indicator_prices.items():
            if hasattr(value, 'item'):
                value = value.item()
            
            # 找到应该填入的行
            row = find_row_for_value(value)
            indicator_text = f"{indicator_name}：{value:.2f}"
            add_to_cell(row, 2, indicator_text)  # 添加到指标列
        
        # 调整行高和列宽
        for row in range(table.rowCount()):
            table.resizeRowToContents(row)
        table.resizeColumnsToContents()
        
        return table

    def show_sma_data(self, stock_id, stock_name, organized_ma_data, ratio_prices, additional_data, indicator_prices):
        self.detail_window = QWidget()
        self.detail_window.setWindowTitle(f"詳細資料 - {stock_id} ({stock_name})")
        self.detail_window.setGeometry(100, 100, 1000, 750)

        # 创建分页控件
        self.tab_widget = QTabWidget()
        
        # 创建各个分页
        self.daily_tab = QWidget()
        self.weekly_tab = QWidget()
        self.monthly_tab = QWidget()
        self.ratio_tab = QWidget()
        
        # 将分页添加到tab widget
        self.tab_widget.addTab(self.ratio_tab, "比例價格")
        self.tab_widget.addTab(self.daily_tab, "均價")
        
        # 在日均价分页中创建网格布局
        daily_layout = QGridLayout()
        
        # 创建标签和表格的辅助函数
        def create_labeled_table(title, table):
            container = QWidget()
            layout = QVBoxLayout(container)
            
            # 创建标签
            label = QLabel(title)
            font = QFont()
            font.setPointSize(13)
            font.setBold(True)
            label.setFont(font)
            
            # 添加标签和表格到垂直布局
            layout.addWidget(label)
            layout.addWidget(table)
            layout.setSpacing(5)  # 设置标签和表格之间的间距
            layout.setContentsMargins(0, 0, 0, 0)  # 设置边距
            
            return container
        
        # 创建最近收盘价的表格（左上）
        recent_price_table = QTableWidget()
        recent_price_table.setColumnCount(2)
        recent_price_table.setRowCount(5)
        recent_price_table.setHorizontalHeaderLabels(["日期", "收盤價"])
        
        # 设置字体
        font = QFont()
        font.setPointSize(13)
        recent_price_table.setFont(font)
        recent_price_table.horizontalHeader().setFont(font)
        
        # 获取并填充最近5筆收盤價
        recent_prices = additional_data.get('latest_close_prices', [])[:5]
        recent_dates = additional_data.get('latest_dates', [])[:5]
        
        for i, (date, price) in enumerate(zip(recent_dates, recent_prices)):
            # 设置日期
            date_item = QTableWidgetItem(str(date))
            date_item.setFont(font)
            recent_price_table.setItem(i, 0, date_item)
            
            # 设置价格
            if hasattr(price, 'item'):
                price = f"{price.item():.2f}"
            price_item = QTableWidgetItem(str(price))
            price_item.setFont(font)
            recent_price_table.setItem(i, 1, price_item)
        
        recent_price_table.resizeColumnsToContents()
        recent_price_table.resizeRowsToContents()
        
        # 创建三个均线表格
        daily_table = self.create_ma_table(organized_ma_data, '日均線')
        weekly_table = self.create_ma_table(organized_ma_data, '週均線')
        monthly_table = self.create_ma_table(organized_ma_data, '月均線')

        daily_table.setFont(font)
        daily_table.horizontalHeader().setFont(font)
        weekly_table.setFont(font)
        weekly_table.horizontalHeader().setFont(font)
        monthly_table.setFont(font)
        monthly_table.horizontalHeader().setFont(font)

        daily_table.resizeColumnsToContents()
        daily_table.resizeRowsToContents()
        weekly_table.resizeColumnsToContents()
        weekly_table.resizeRowsToContents()
        monthly_table.resizeColumnsToContents()
        monthly_table.resizeRowsToContents()
        
        # 创建带标签的表格容器
        recent_container = create_labeled_table("近五日價格", recent_price_table)
        daily_container = create_labeled_table("日均價", daily_table)
        weekly_container = create_labeled_table("周均價", weekly_table)
        monthly_container = create_labeled_table("月均價", monthly_table)
        
        # 将带标签的容器添加到网格布局中
        daily_layout.addWidget(recent_container, 0, 0)  # 左上
        daily_layout.addWidget(daily_container, 0, 1)   # 右上
        daily_layout.addWidget(weekly_container, 1, 0)  # 左下
        daily_layout.addWidget(monthly_container, 1, 1) # 右下
        
        # 设置列和行的拉伸因子
        daily_layout.setColumnStretch(0, 1)
        daily_layout.setColumnStretch(1, 1)
        daily_layout.setRowStretch(0, 1)
        daily_layout.setRowStretch(1, 1)
        
        # 设置布局
        self.daily_tab.setLayout(daily_layout)
        
        
        # 比例价格表格
        ratio_layout = QVBoxLayout()
        ratio_table = self.create_ratio_table(ratio_prices, indicator_prices, organized_ma_data)
        ratio_layout.addWidget(ratio_table)
        self.ratio_tab.setLayout(ratio_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.detail_window.setLayout(main_layout)
        
        self.detail_window.show()

    def insert_table_row(self, table, row, values):
        """輔助函數：插��一行數據到表格中"""
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            
            # 設置交替行背景色
            if row % 2 == 0:
                item.setBackground(QColor(240, 240, 240))
                
            # 設置為不可編輯
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            table.setItem(row, col, item)

    def toggle_all(self, ma_type):
        state = self.select_all_vars[ma_type].get()
        for period in self.ma_selections[ma_type]:
            self.ma_selections[ma_type][period].set(state)

    def update_select_all(self, ma_type):
        all_checked = all(self.ma_selections[ma_type][period].get() for period in self.ma_selections[ma_type])
        self.select_all_vars[ma_type].set(all_checked)

    def get_ma_selections(self):
        return {ma_type: {period: var.get() for period, var in periods.items()}
                for ma_type, periods in self.ma_selections.items()}

    def find_closest_ratios_for_indicators(self, indicator_prices, total_ratio_prices):
        """
        為每個指標價格找出最接近的比例價格，並保存所有指標信息
        """
        assignments = {}
        ratio_values = {ratio: float(value) for ratio, value in total_ratio_prices.items() 
                       if value != 'N/A'}
        
        if not ratio_values:
            return {}

        # 按固定順序處理指標，確保顯示順序一致
        indicator_types = ['AH', 'AL', 'CDP', 'NH', 'NL']
        
        for indicator_type in indicator_types:
            price = indicator_prices.get(indicator_type, 'N/A')
            if price == 'N/A':
                continue
                
            try:
                price_value = float(price)
                closest_ratio = min(ratio_values.keys(), 
                                  key=lambda x: abs(ratio_values[x] - price_value))
                
                if closest_ratio not in assignments:
                    assignments[closest_ratio] = []
                
                adjusted_ratio = Math.adjust_ratio_price(price_value)
                assignments[closest_ratio].append({
                    'type': indicator_type,
                    'price': price,
                    'adjusted': adjusted_ratio
                })
                
            except (ValueError, TypeError):
                continue
        
        return assignments

    def format_indicators_for_ratio(self, ratio, indicator_assignments):
        """
        格式化顯示指定比例對應的所有指標，確保所有指標都顯示
        """
        if ratio not in indicator_assignments:
            return ''
        
        indicators = indicator_assignments[ratio]
        # 按指標類型排序，確保顯示順序一致
        indicators.sort(key=lambda x: x['type'])
        
        formatted_indicators = []
        for indicator in indicators:
            formatted_indicators.append(
                f"{indicator['type']}:{indicator['price']}({indicator['adjusted']})"
            )
        
        # 使用換行符連接所有指標
        return '\n'.join(formatted_indicators)

        
    def find_closest_ratio(self, price_value, total_ratio_prices):
        """
        找出與給定價格最接近的比例
        """
        try:
            ratio_values = {ratio: float(value) for ratio, value in total_ratio_prices.items() 
                           if value != 'N/A'}
        
            if not ratio_values:
                return None
            
            return min(ratio_values.keys(), 
                      key=lambda x: abs(ratio_values[x] - price_value))
                  
        except (ValueError, TypeError):
            return None

    def find_price_interval(self, price, ratio_values):
        """
        找出價格所在的區間或確切的比例
        返回特殊值：
        - ('min', first_ratio) 表示小於最小比例價格
        - (last_ratio, 'max') 表示大於最大比例價格
        - (ratio, ratio) 表示確切匹配
        - (ratio1, ratio2) 表示在兩個比例價格之間
        """
        try:
            # 將所有比例價格排序
            ratios = sorted(ratio_values.keys(), key=lambda x: float(ratio_values[x]))
            min_ratio = ratios[0]
            max_ratio = ratios[-1]
            
            # 檢查是否小於最小比例價格
            if price < float(ratio_values[min_ratio]):
                return ('min', min_ratio)
                
            # 檢查是否大於最大比例價格
            if price > float(ratio_values[max_ratio]):
                return (max_ratio, 'max')

            # 檢查是否與某個比例價格完全相等
            for ratio, value in ratio_values.items():
                if abs(price - float(value)) < 0.01:
                    return (ratio, ratio)

            # 找出價格所在的區間
            for i in range(len(ratios) - 1):
                ratio1, ratio2 = ratios[i], ratios[i + 1]
                if float(ratio_values[ratio1]) < price < float(ratio_values[ratio2]):
                    return (ratio1, ratio2)

            return None
        
        except (ValueError, TypeError) as e:
            print(f"Error in find_price_interval: {e}")
            return None

    def create_qt_table(self):
        table = QTableWidget()
        table.setColumnCount(6)
            
        # 設置表頭
        headers = ['比例', '總波段', '指標', '日均', '周均', '月均']
        table.setHorizontalHeaderLabels(headers)
            
        # 設置表頭樣式
        header_font = QFont('Microsoft JhengHei', 12, QFont.Bold)
        table.horizontalHeader().setFont(header_font)
            
        # 設置列寬
        table.setColumnWidth(0, 80)   # 比例
        table.setColumnWidth(1, 100)  # 總波段
        table.setColumnWidth(2, 200)  # 指標
        table.setColumnWidth(3, 150)  # 日均
        table.setColumnWidth(4, 150)  # 周均
        table.setColumnWidth(5, 150)  # 月均
            
        # 設置自動調整行高
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
        # 設置文字自動換行
        table.setWordWrap(True)
            
        # 設置表格樣式
        table.setFrameStyle(QFrame.Box | QFrame.Plain)
        table.setShowGrid(True)
        table.setFont(QFont('Microsoft JhengHei', 12))
            
        return table   
        
    # def start_download(self):
    #     stock_id = self.stock_id_entry.get()
    #     start_date = self.start_date_ticks_entry.get()
    #     end_date = self.end_date_ticks_entry.get()

    #     start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    #     end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    #     # 重置進度條
    #     self.update_progress(0)
    #     self.update_kbars(stock_id, start_date, end_date)

    # def update_ticks(self, stock_id, start_date, end_date):
    #     self.controller.update_data("Ticks", stock_id, start_date, end_date)

    # def update_kbars(self, stock_id, start_date, end_date):
    #     self.controller.update_data("Kbars", stock_id, start_date, end_date)
        
    # def update_progress(self, value):
    #     self.progress_var.set(value)
    #     self.update_idletasks()
        
    # def set_progress_config(self, dates):
    #     self.progress.config(maximum=dates)
