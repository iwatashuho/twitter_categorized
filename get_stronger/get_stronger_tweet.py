# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys, calendar
import codecs
import csv
import glob
import os
import urllib.parse
import pandas as pd
from abc import ABCMeta, abstractmethod
from sub.empty_remove import EMPTY_REMOVE
from sub.get_follower import TweetsGetter_sub

base_path = os.path.dirname(os.path.abspath(__file__))
get_tweets_dir = os.path.normpath(os.path.join(base_path, './get_tweets/'))
filterling_dir = os.path.normpath(os.path.join(base_path, '../filterling/'))

def YmdHMS(created_at):
    '''
    create_atの日付を年-月-日 時:日のフォーマットに変換
    '''
    time_utc = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    unix_time = calendar.timegm(time_utc)
    time_local = time.localtime(unix_time)
    return str(time.strftime("%Y-%m-%d %H:%M", time_local))

def remove_csv(dir_path):
    all_files = glob.glob('{}*.csv'.format(dir_path))
    for file in all_files:
        print("{} 削除されました。".format(file))
        os.remove(file)

if __name__ == '__main__':
    remove_csv(get_tweets_dir + "/stronger_tweets/")
    fr = open(filterling_dir + "/filterling_output_beauty.csv", 'r', encoding="utf-8")
    csvreader = csv.reader(fr)
    header = next(csvreader)
    for row in csvreader:
        user_id = row[5]
        user_sname = row[1]
        user_name = row[6]
        print(user_name,user_sname)
        getter = TweetsGetter_sub.byUser(user_sname)
        fw = open(get_tweets_dir + "/stronger_tweets/" + user_sname + ".csv", 'w', encoding="utf-8")
        csvwriter = csv.writer(fw)
        write_header = ["ユーザーid","スクリーンネーム","ユーザー名","フォロワー数","Tweet_id","投稿日時","ツイート内容"]
        csvwriter.writerow(write_header)
        for tweet in getter.collect(total = 5000):
            write_contents = [
                str(tweet['user']['id_str']),
                str(tweet['user']['screen_name']),
                str(tweet['user']['name']),
                str(tweet['user']['followers_count']),
                str(tweet['id_str']),
                str(YmdHMS(tweet['created_at'])),
                tweet['text']
                ]
            csvwriter.writerow(write_contents)
        fw.close()
    fr.close()
    stronger_path = os.path.join(os.path.join(base_path, 'get_tweets/stronger_tweets/'))
    empty_remove = EMPTY_REMOVE(stronger_path)
    empty_remove.main()
