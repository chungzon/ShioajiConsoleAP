import tkinter as tk
from tkinter import ttk
from view.DataAnalysisView import DataAnalysisView
from model.DataAnalysisModel import DataAnalysisModel
from controller.DataAnalysisController import DataAnalysisController
from view.DataDownloadView import DataDownloadView
from model.DataDownloadModel import DataDownloadModel
from controller.DataDownloadController import DataDownloadController
import shioaji as sj

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
        self.api = self.initialize_api()

        self.title("Stock Application")

        self.tab_control = ttk.Notebook(self)

        self.data_analysis_model = DataAnalysisModel(self.api)
        self.data_analysis_view = DataAnalysisView(self.tab_control, None)
        self.data_analysis_controller = DataAnalysisController(self.data_analysis_model, self.data_analysis_view)

        self.data_download_model = DataDownloadModel(self.api)
        self.data_download_view = DataDownloadView(self.tab_control, None)
        self.data_download_controller = DataDownloadController(self.data_download_model, self.data_download_view)

        self.tab_control.add(self.data_analysis_view, text="資料分析")
        self.tab_control.add(self.data_download_view, text="資料下載")
        self.tab_control.pack(expand=1, fill="both")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
