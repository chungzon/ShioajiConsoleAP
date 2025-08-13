# 資源路徑

import os


'''
取得資源路徑
'''
def get_resource_path(file_name):
    resource_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(resource_dir, file_name)

    # 確保resource目錄存在
    os.makedirs(resource_dir, exist_ok=True)

    return file_path

'''定義列舉'''
class ResourceFileNames:
    TW_ALL_STOCKS_CSV = "tw_all_stocks.csv"

