# -*- coding: utf-8 -*-
import re
import os
import pandas as pd
import csv
import glob

class EMPTY_REMOVE:

    def __init__(self,dir_path):
        self.DIR_PATH = dir_path

    def remove_empty(self,dir_path):
        all_files = glob.glob('{}*.csv'.format(dir_path))
        for file in all_files:
            df = pd.read_csv(file)
            if df["スクリーンネーム"].count() <= 5:
                print("{} 削除されました。".format(file))
                os.remove(file)

    def main(self):
        self.remove_empty(self.DIR_PATH)

if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    stronger_path = os.path.join(os.path.join(base_path, '../get_tweets/stronger_tweets/'))
    empty_remove = EMPTY_REMOVE(stronger_path)
    empty_remove.main()
