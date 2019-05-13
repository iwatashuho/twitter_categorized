# -*- coding: utf-8 -*-
import os
import glob
import csv
import pandas as pd

# フォルダ中のパスを取得
# DATA_PATH = "./strongers/エンタメ/"

class CSV_CONCAT(object):

    def __init__(self,file_dir_path):
        self.DIR_PATH = file_dir_path
        self.All_Files = glob.glob('{}*.csv'.format(self.DIR_PATH))

    # フォルダ中の全csvをマージ
    def concat_and_dump_csv(self,csv_name):
        list = []
        for file in self.All_Files:
            list.append(pd.read_csv(file, engine='python'))
        df = pd.concat(list)
        file_path_fordir = os.path.dirname(csv_name)
        if not os.path.exists(file_path_fordir):
            os.makedirs(file_path_fordir)
        df.to_csv(csv_name, encoding='utf_8')

### usage ###
# csv_concater = CSV_CONCAT("./strongers/エンタメ/")
# csv_concater.concat_and_dump_csv("./strongers/エンタメ/label_1.csv")
### usage ###

if __name__ == '__main__':
    csv_concater = CSV_CONCAT("/Users/iwata/my_drive/twitter_api/use_fasttext/get_tweets/美容/")
    csv_concater.concat_and_dump_csv("/Users/iwata/my_drive/twitter_api/use_fasttext/get_tweets/Integration/label_美容.csv")
