# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys
import codecs
import csv
import os
import urllib.parse
import pandas as pd
from abc import ABCMeta, abstractmethod
from sub.get_follower import TweetsGetter_sub

base_path = os.path.dirname(os.path.abspath(__file__))
get_tweets_dir = os.path.normpath(os.path.join(base_path, './get_tweets/'))

if __name__ == '__main__':
    fr = open(get_tweets_dir + "/beauty_list/beauty.csv", 'r', encoding="utf-8")
    csvreader = csv.reader(fr)
    header = next(csvreader)
    for row in csvreader:
        user_id = row[0]
        user_sname = row[1]
        user_name = row[2]
        getter = TweetsGetter_sub.byUser(user_sname)
        fw = open(get_tweets_dir + "/beauty_user/" + user_sname + ".csv", 'w', encoding="utf-8")
        csvwriter = csv.writer(fw)
        write_header = ["Tweet_id","時間","ツイート内容"]
        csvwriter.writerow(write_header)
        for tweet in getter.collect(total = 5000):
            write_contents = [str(tweet['id']),str(tweet['created_at']),tweet['text']]
            csvwriter.writerow(write_contents)
        fw.close()
    fr.close()


