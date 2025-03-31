import tkinter as tk
from tkinter import ttk
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

class MainApplication(tk.Tk):
    
    @staticmethod
    def initialize_api():
        api = sj.Shioaji(simulation=True)
        api.login(
            api_key="9o7ruXLDR2psg46JJF1s9eK3W79PduD1skFfNQF5948A",
            secret_key="FitCPzfFjQCRd3cabRSD7QpovDVsVWNxh4MgwygshCBK"
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

        self.tab_control.add(self.data_analysis_view, text="資料分析")
        self.tab_control.add(self.data_download_view, text="資料下載")
        self.tab_control.add(self.realtime_monitor_view, text="即時監控")
        self.tab_control.add(self.backtest_view, text="資料回測")
        self.tab_control.add(self.daily_close_view, text="年度交易量下載")
        self.tab_control.add(self.select_stock_view, text="選股策略")
        self.tab_control.pack(expand=1, fill="both")

        self.scheduler = start_scheduler()
        # self.scheduler.run()


    

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
