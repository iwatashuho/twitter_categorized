# -*- coding: utf-8 -*-
import os
import glob
import csv
import pandas as pd
# import numpy as np

# フォルダ中のパスを取得
# DATA_PATH = "./strongers/エンタメ/"
base_path = os.path.dirname(os.path.abspath(__file__))
get_tweets_dir = os.path.normpath(os.path.join(base_path, './get_tweets/'))

class CSV_CONCAT(object):

    def __init__(self,file_dir_path):
        self.DIR_PATH = file_dir_path
        self.All_Files = glob.glob('{}*.csv'.format(self.DIR_PATH))

    # フォルダ中の全csvをマージ
    def concat_and_dump_csv(self,csv_name,change=False):
        list = []
        # np.set_printoptions(suppress=True)
        for file in self.All_Files:
            if os.path.isdir(file) == True:
                continue
            df = pd.read_csv(file, engine='python')
            if change == True:
                df["ファボ数"] = df["ファボ数"].astype('int64')
                df["リツイート数"] = df["リツイート数"].astype('int64')
                df["フォロワー数"] = df["フォロワー数"].astype('int64')
            df["ファボ数"] = df["ファボ数"].astype('int64')
            df["ユーザーid"] = df["ユーザーid"].astype('int64')
            list.append(df)
        df = pd.concat(list,ignore_index=True)
        file_path_fordir = os.path.dirname(csv_name)
        if not os.path.exists(file_path_fordir):
            os.makedirs(file_path_fordir)
        df.to_csv(csv_name, encoding='utf_8')

    def drop_duplicate_and_filter(self,filepath):
        '''
        ユーザーの重複を削除して、favo数10以下を切り捨てる
        '''
        df = pd.read_csv(filepath)
        df = df.fillna({"Tweet_id": 0,"ファボ数": 0,"リツイート数": 0,"フォロワー数": 0,"ユーザーid": 0,})
        df["Tweet_id"] = df["Tweet_id"].astype('int64')
        df["ファボ数"] = df["ファボ数"].astype('int64')
        df["リツイート数"] = df["リツイート数"].astype('int64')
        df["フォロワー数"] = df["フォロワー数"].astype('int64')
        df["ユーザーid"] = df["ユーザーid"].astype('int64')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.drop_duplicates(subset=["ユーザーid"], inplace=True, keep="last")
        df.to_csv(filepath,index=False)

def remove_csv(dir_path):
    all_files = glob.glob('{}*.csv'.format(dir_path))
    for file in all_files:
        print("{} 削除されました。".format(file))
        os.remove(file)

### usage ###
# csv_concater = CSV_CONCAT("./stronger/エンタメ/")
# csv_concater.concat_and_dump_csv("./stronger/エンタメ/label_1.csv")
### usage ###
if __name__ == '__main__':
    remove_csv(get_tweets_dir + "/")

    csv_concater = CSV_CONCAT(get_tweets_dir + "/stronger/")
    csv_concater.concat_and_dump_csv(get_tweets_dir + "/integrate_1.csv", change=True)

    csv_concater_sele = CSV_CONCAT(get_tweets_dir + "/stronger/selenium/")
    csv_concater_sele.concat_and_dump_csv(get_tweets_dir + "/integrate_2.csv")

    all_concatter = CSV_CONCAT(get_tweets_dir + "/")
    all_concatter.concat_and_dump_csv(get_tweets_dir + "/all_integrate.csv")
    all_concatter.drop_duplicate_and_filter(get_tweets_dir + "/all_integrate.csv")
