from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import os
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QMessageBox, QCheckBox, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from common.Math import Math
# SelectStockView
from common.enum.StockType import StockType
from view.SelectStockView import SelectStockView


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

        # 最近波段起始日期
        ttk.Label(self, text="最近波段起始日期 (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.entry_recent_start_date = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_recent_start_date.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # 最近波段結束日期
        ttk.Label(self, text="最近波段結束日期 (YYYY-MM-DD):").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.entry_recent_end_date = DateEntry(self, background='white', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', locale='zh_TW')
        self.entry_recent_end_date.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # 設置最近波段起始日期默認日期（例如：最近一個月）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        self.entry_recent_start_date.set_date(start_date)
        self.entry_recent_end_date.set_date(end_date)

        # 獲取下載資料夾路徑
        self.downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # 儲存路徑
        ttk.Label(self, text="儲存路徑:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.entry_file_path = ttk.Entry(self)
        self.entry_file_path.grid(row=6, column=1, padx=10, pady=5)
        self.entry_file_path.insert(0, self.downloads_path)  # 設置預設路徑
        ttk.Button(self, text="瀏覽", command=self.browse_file).grid(row=6, column=2, padx=10, pady=5)

        # Ticks 更新日期
        self.label_update_date_ticks = ttk.Label(self, text="Ticks 更新日期: 未知")
        self.label_update_date_ticks.grid(row=7, column=0, columnspan=2, padx=10, pady=5)
        # self.button_update_ticks = ttk.Button(self, text="更新 Ticks", command=self.controller.update_data_ticks)
        # self.button_update_ticks.grid(row=4, column=2, padx=10, pady=5)

        # Kbars 更新日期
        self.label_update_date_kbars = ttk.Label(self, text="Kbars 更新日期: 未知")
        self.label_update_date_kbars.grid(row=8, column=0, columnspan=2, padx=10, pady=5)
        # self.button_update_kbars = ttk.Button(self, text="更新 Kbars", command=self.controller.update_data_kbars)
        # self.button_update_kbars.grid(row=5, column=2, padx=10, pady=5)

        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=9, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        # 狀態標籤
        self.status_label = ttk.Label(self, text="狀態: ")
        self.status_label.grid(row=10, column=0, columnspan=3, padx=10, pady=5)

        # 確認和分析資料按鈕
        ttk.Button(self, text="分析資料", command=self.analyze_data).grid(row=11, column=0, columnspan=3, pady=20)

        ttk.Button(self, text="詳細資料", command=self.show_detail_data).grid(row=12, column=0, columnspan=3, pady=20)
        


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

    def create_ratio_table(self, ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input):
        table = QTableWidget()
        table.setColumnCount(5)  # 比例、最近波段、總波段、指標, 獲利
        
        # 设置固定的比例序列
        ratios = ['0', '0.191', '0.382', '0.5', '0.618', '0.809', '1', 
                 '1.191', '1.382', '1.5', '1.618', '1.809', '2',
                 '2.191', '2.382', '2.5', '2.618', '2.809', '3',
                 '3.191', '3.382', '3.5', '3.618', '3.809', '4',
                 '4.191', '4.382', '4.5', '4.618', '4.809', '5']
        
        # 計算總行
        total_rows = (len(ratios) * 2 - 1) + 2
        table.setRowCount(total_rows)
        table.setHorizontalHeaderLabels(["比例", "最近波段", "指標", "總波段", "獲利"])
        header_font = QFont('Microsoft JhengHei', 12, QFont.Bold)
        table.horizontalHeader().setFont(header_font)
        font = QFont()
        font.setFamily("Microsoft JhengHei")  # 设置字体为 Microsoft JhengHei
        font.setPointSize(13)
        table.setFont(font)
      
        # 加入選擇cell的事件
        def on_cell_clicked(row, col):
            # 如果選擇的是當沖checkbox
            stock_type = StockType.DAY_TRADING
            if not day_trading_checkbox.isChecked():
                stock_type = StockType.LONG_TERM

            # 如果選擇的是最近波段列
            if col == 1:  # 最近波段列
                fee_discount = fee_discount_input.text()
                # 判斷fee_discount是否為數字
                try:
                    float(fee_discount)
                except ValueError:
                    QMessageBox.warning(None, "警告", "手續費折讓必須為數字")
                    return
                fee_discount = float(fee_discount)

                # 清空獲利列
                for r in range(table.rowCount()):
                    table.setItem(r, 4, QTableWidgetItem(""))
                cell = table.item(row, col)
                if cell and cell.text():
                    for line in cell.text().split('\n'):
                        # line轉為數字
                        try:
                            price = float(line)
                            print(f"選擇的買入價格: {price:.2f}")
                            # 找出指標和總波段資料，並依據價格排序，並顯示
                            # 找出table中，colunm 1和colunm 3的資料，並依據價格排序，並顯示
                            for table_row in range(table.rowCount()):                                      
                                indicator_prices_cell = table.item(table_row, 2)
                                indicator_prices = []
                                if indicator_prices_cell is not None:
                                    indicator_prices_cell_text = indicator_prices_cell.text().strip()
                                    if indicator_prices_cell_text != "":
                                        indicator_prices = indicator_prices_cell_text.split('\n')
                                        # 排序，除了資料為''的資料，其他資料依據價格排序
                                        indicator_prices = [price for price in indicator_prices if price != '']
                                        indicator_prices = sorted(indicator_prices, key=lambda x: float(x.split('：')[1]))
                                        
                                total_wave_prices = []
                                total_wave_prices_cell = table.item(table_row, 3)
                                if total_wave_prices_cell is not None:
                                    total_wave_prices_cell_text = total_wave_prices_cell.text().strip()
                                    if total_wave_prices_cell_text != "":
                                        total_wave_prices = total_wave_prices_cell_text.split('\n')  
                                        # 排序，除了資料為''的資料，其他資料依據價格排序 
                                        total_wave_prices = [price for price in total_wave_prices if price != '']
                                        total_wave_prices = sorted(total_wave_prices, key=lambda x: float(x.split('：')[1]))
                                
                                # 將指標和總波段資料合併
                                indicator_prices.extend(total_wave_prices)
                                # 排序，除了資料為''的資料，其他資料依據價格排序
                                indicator_prices = [price for price in indicator_prices if price != '']
                                indicator_prices = sorted(indicator_prices, key=lambda x: float(x.split('：')[1]))
                                print(f"合併後的資料: {indicator_prices}")

                                # 將指標和總波段資料合併後，顯示在table中
                                for indicator_price in indicator_prices:
                                    # 取出價格
                                    indicator_price = indicator_price.split('：')[1]
                                    # 計算獲利
                                    profit = Math.calculate_profit(price, indicator_price, stock_type, fee_discount)

                                    # 如果資料已存在，則附加上去
                                    if table.item(table_row, 4) is not None and table.item(table_row, 4).text().strip() != "":
                                        table.setItem(table_row, 4, QTableWidgetItem(table.item(table_row, 4).text() + '\n' + str(profit) + '元'))
                                    else:
                                        table.setItem(table_row, 4, QTableWidgetItem(str(profit) + '元'))


                                if (table.item(table_row, 4) is None or table.item(table_row, 4).text().strip() == ""):
                                    #最近波段欄位資料
                                    recent_ratio_prices_cell = table.item(table_row, 1)
                                    if recent_ratio_prices_cell is not None:
                                        recent_ratio_prices_cell_text = recent_ratio_prices_cell.text().strip()
                                        if recent_ratio_prices_cell_text != "":
                                            profit = Math.calculate_profit(price, float(recent_ratio_prices_cell_text), stock_type, fee_discount)
                                            table.setItem(table_row, 4, QTableWidgetItem(str(profit) + '元'))

                            break
                        except ValueError:
                            continue
                            # 調整表格外觀
                table.resizeColumnsToContents()
                table.resizeRowsToContents()

        table.cellClicked.connect(on_cell_clicked)


        def find_row_for_value(value):
            min_price = float(ratio_prices['0'])
            max_price = float(ratio_prices['5'])
            
            # 如果value是字串，轉換為浮點數
            if isinstance(value, str):
                value = float(value)

            # 如果价格小于最小比例价格
            if value < min_price:
                return 0  # 第一个空白行
            
            # 如果价格大于最大比例价
            if value > max_price:
                return total_rows - 1  # 最后一个空白行
            
            # 在比例价格之间查找位置
            for i, ratio in enumerate(ratios[:-1]):
                current_price = float(ratio_prices[ratio])
                next_price = float(ratio_prices[ratios[i + 1]])
                
                row = (i * 2) + 1  # 考虑偏移
                
                if abs(value - current_price) < 0.01:
                    return row
                elif current_price < value < next_price or next_price < value < current_price:
                    return row + 1
            
            return total_rows - 1  # 如果没找到合适的位置，放在最后

        def format_price_text(name, value, is_recent_ratio=False):
            if hasattr(value, 'item'):
                value = value.item()

            if isinstance(value, float):
                return f"{name}：{value:.2f}"
            else:
                return f"{name}：{value}"

        # 設置比例欄位和總波段欄位
        def setup_basic_columns():
            # 設置交替行顏色
            for row in range(total_rows):
                is_alternate = (row % 2) == 0
                color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
                
                # 第一行和最後一行是空白行
                if row == 0 or row == total_rows - 1:
                    for col in range(4):
                        item = QTableWidgetItem("")
                        item.setBackground(QBrush(color))
                        table.setItem(row, col, item)
                    continue
                
                # 比例行
                if (row - 1) % 2 == 0 and (row - 1) // 2 < len(ratios):
                    ratio_idx = (row - 1) // 2
                    
                    # 比例欄位
                    ratio_item = QTableWidgetItem(ratios[ratio_idx])
                    ratio_item.setBackground(QBrush(color))
                    table.setItem(row, 0, ratio_item)
                    
                    # 總波段欄位
                    wave_price = ratio_prices[ratios[ratio_idx]]
                    if hasattr(wave_price, 'item'):
                        wave_price = wave_price.item()
                    price_item = QTableWidgetItem(f"{wave_price:.2f}")
                    price_item.setBackground(QBrush(color))
                    table.setItem(row, 1, price_item)
                
                # 中間的空白行
                else:
                    for col in range(4):
                        item = QTableWidgetItem("")
                        item.setBackground(QBrush(color))
                        table.setItem(row, col, item)

        def add_sorted_prices_to_cell(row, prices_list):
            """將所有價格一起排序後添加到指標列"""
            # 按價格排序所有價格
            sorted_prices = sorted(prices_list, key=lambda x: float(x[1]))
            
            # 生成顯示文本
            text_lines = []
            for name, value, is_recent_ratio in sorted_prices:
                if is_recent_ratio:
                    text_lines.append("")  # 最近波段價格的位置用空行表示
                else:
                    text_lines.append(format_price_text(name, value))
            
            # 創建表格項並設置文本
            indicator_item = QTableWidgetItem('\n'.join(text_lines))
            
            # 設置背景色
            is_alternate = (row % 2) == 0
            color = QColor("#F0F0F0") if is_alternate else QColor("#E6F3FF")
            indicator_item.setBackground(QBrush(color))
            
            # 設置到表格中
            table.setItem(row, 2, indicator_item)
            
            # 在最近波段列中顯示最近波段價格
            recent_lines = []
            for name, value, is_recent_ratio in sorted_prices:
                if is_recent_ratio:
                    recent_lines.append(format_price_text(name, value))
                else:
                    recent_lines.append("")  # 指標價格的位置用空行表示
            
            recent_item = QTableWidgetItem('\n'.join(recent_lines))
            recent_item.setBackground(QBrush(color))
            table.setItem(row, 3, recent_item)

        # 首先設置基本欄位
        setup_basic_columns()

        # 收集所有價格數據
        def collect_all_prices():
            all_prices = []
            
            # 添加指標數據
            for name, value in indicator_prices.items():
                all_prices.append((name, value, False))
            
            # 添加均線數據
            ma_types = {'日均線': '日', '週均線': '周', '月均線': '月', '15分鐘均線': '15K'}
            for ma_key, prefix in ma_types.items():
                ma_data = organized_ma_data[ma_key]
                for ma_period in ['5MA', '10MA', '20MA', '60MA', '120MA']:
                    if ma_period in ma_data and ma_data[ma_period] != 'N/A':
                        value = ma_data[ma_period]
                        period_num = ma_period.replace('MA', '')
                        name = f"{prefix}({period_num})"
                        all_prices.append((name, value, False))
            
            # 添加最近波段數據
            if recent_ratio_prices:
                for ratio, value in recent_ratio_prices.items():
                    name = f"【{ratio}】"
                    all_prices.append((name, value, True))
            
            return all_prices

        # 按價格分組到對應的行
        row_prices = {}
        for name, value, is_recent_ratio in collect_all_prices():
            if hasattr(value, 'item'):
                value = value.item()
            row = find_row_for_value(value)
            
            if row not in row_prices:
                row_prices[row] = []
            row_prices[row].append((name, value, is_recent_ratio))

        # 填充價格數據
        for row, prices in row_prices.items():
            add_sorted_prices_to_cell(row, prices)

        # 調整表格外觀
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

        return table

    def show_sma_data(self, stock_id, stock_name, organized_ma_data, ratio_prices, additional_data, indicator_prices, recent_ratio_prices):
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
            font.setFamily("Microsoft JhengHei")  # 设置字体为 Microsoft JhengHei
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
        font.setFamily("Microsoft JhengHei")  # 设置字体为 Microsoft JhengHei
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
        
        # 添加日期信息标签
        date_info = QLabel(
            # f"最近波段期間: {additional_data['Start_Date']} ~ {additional_data['End_Date']}\n"
            f"最高價日期: {additional_data['最近波段最高價日期']} \n"
            f"最低價日期: {additional_data['最近波段最低價日期']} "
        )
        date_info.setFont(font)
        ratio_layout.addWidget(date_info)
        
        # 當沖交易checkbox
        day_trading_checkbox = QCheckBox("當沖")
        day_trading_checkbox.setChecked(True)
        day_trading_checkbox.setFont(font)
        ratio_layout.addWidget(day_trading_checkbox)

        # 创建一个水平布局
        fee_layout = QHBoxLayout()

        # 手續費折讓輸入框，預設為1.6%
        fee_discount_label = QLabel("手續費折讓:")
        fee_discount_label.setFont(font)
        fee_discount_label.setFixedWidth(100)
        fee_layout.addWidget(fee_discount_label)

        fee_discount_input = QLineEdit()
        fee_discount_input.setFont(font)
        fee_discount_input.setText("1.6")
        fee_discount_input.setFixedWidth(75)
        fee_discount_input.setPlaceholderText("請輸入")
        fee_discount_input.setAlignment(Qt.AlignCenter)
        fee_layout.addWidget(fee_discount_input)

        fee_discount_unit_label = QLabel("折")
        fee_discount_unit_label.setFont(font)
        fee_layout.addWidget(fee_discount_unit_label)
       
        ratio_layout.addLayout(fee_layout)

        # 創建比例表格
        ratio_table = self.create_ratio_table(ratio_prices, indicator_prices, organized_ma_data, recent_ratio_prices, day_trading_checkbox, fee_discount_input)
        ratio_layout.addWidget(ratio_table)
        self.ratio_tab.setLayout(ratio_layout)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.detail_window.setLayout(main_layout)
        
        self.detail_window.show()

    def insert_table_row(self, table, row, values):
        """輔助函數：插一行數據到表格中"""
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