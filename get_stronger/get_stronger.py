# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys, calendar
import os
import codecs
import csv
import urllib.parse
import pandas as pd
import datetime
from abc import ABCMeta, abstractmethod
from sub.get_follower import TweetsGetter_sub

base_path = os.path.dirname(os.path.abspath(__file__))
get_tweets_dir = os.path.normpath(os.path.join(base_path, './get_tweets/'))

def YmdHMS(created_at):
    '''
    create_atの日付を年-月-日 時:日のフォーマットに変換
    '''
    time_utc = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    unix_time = calendar.timegm(time_utc)
    time_local = time.localtime(unix_time)
    return str(time.strftime("%Y-%m-%d %H:%M", time_local))

def dest_tweet(sw, min_faves="10", since_day="2019-01-01"):
    '''
    ワードからツイートを拾ってくる。
    '''
    getter = TweetsGetter_sub.bySearch(u'{0} min_faves:{1} since:{2} lang:ja OR @99999'.format(sw,min_faves,since_day))
    create_csv_file = get_tweets_dir + "/stronger/" + sw + "_" + str(datetime.date.today()) + ".csv"
    file_path_fordir = os.path.dirname(create_csv_file)
    if not os.path.exists(file_path_fordir):
        os.makedirs(file_path_fordir)
    fw = open(create_csv_file, 'w', encoding="utf-8")
    csvwriter = csv.writer(fw)
    write_header = ["ユーザーid","スクリーンネーム","ユーザー名","フォロワー数","リツイート数","ファボ数","投稿日時","ツイート内容","Tweet_id",]
    csvwriter.writerow(write_header)
    for tweet in getter.collect(total = 10000):
        write_contents = [
            str(tweet['user']['id_str']),
            str(tweet['user']['screen_name']),
            str(tweet['user']['name']),
            str(tweet['user']['followers_count']),
            str(tweet['retweet_count']),
            str(tweet['favorite_count']),
            str(YmdHMS(tweet['created_at'])),
            tweet['full_text'],
            str(tweet['id_str']),
            ]
        csvwriter.writerow(write_contents)
    fw.close()
    drop_duplicate(create_csv_file)
    print("書き込み完了\n")

def drop_duplicate(filepath):
    '''
    ユーザーの重複を削除する
    '''
    df = pd.read_csv(filepath)
    df.drop_duplicates(subset=["ユーザーid"], inplace=True)
    df.to_csv(filepath,index=False)

if __name__ == '__main__':
    # dest_tweet("keyword")
