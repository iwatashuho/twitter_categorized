# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import time, sys, calendar
import os
import codecs
import csv
import urllib.parse
import pandas as pd
import datetime
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

base_path = os.path.dirname(os.path.abspath(__file__))
get_tweets_dir = os.path.normpath(os.path.join(base_path, './get_tweets/'))

if __name__ == '__main__':

    def get_stronger_selenium(sw):
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(chrome_options=options)
        driver.get('https://twitter.com/search?q=' + sw +' since:2018-01-01 lang:ja OR @99999&src=typd')
        html01=driver.page_source
        while 1:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            html02=driver.page_source
            if html01!=html02:
                html01=html02
            else:
                break
        base_path = os.path.dirname(os.path.abspath(__file__))
        text_file = os.path.join(base_path, './get_source.txt')
        f = open(text_file, mode='w')
        f.write(driver.page_source)
        f.close()
        driver.quit()
        textfile = open(text_file, mode="r")
        soup = BeautifulSoup(textfile, "html5lib")
        list_for_csv = []

        #ユーザーid
        useridbs = soup.find_all("a",{"class":"js-account-group"})
        user_idlists = []
        for userid in useridbs:
            userid_str = str(userid["data-user-id"])
            user_idlists.append(userid_str)
        list_for_csv.append(user_idlists)
        #スクリーンネーム 時間
        screen_namebs = soup.find_all("a",{"class":"js-permalink"})
        screen_names = []
        times = []
        for screen_name in screen_namebs:
            href = str(screen_name["href"])
            r = re.compile("\/([^\/]*)\/")
            sn = r.search(href).group(1)
            screen_names.append(sn)
            timer = str(screen_name["title"])
            times.append(timer)
        list_for_csv.append(screen_names)
        #ユーザー名 ツイートid
        usernamebs = soup.find_all("div",{"class":"js-stream-tweet"})
        username_lists = []
        tweet_id_lists = []
        for username in usernamebs:
            username_str = str(username["data-name"])
            username_str=re.sub('<[^<]+?>', "", username_str)
            username_lists.append(username_str)
            tweet_id_str = str(username["data-conversation-id"])
            tweet_id_str=re.sub('<[^<]+?>', "", tweet_id_str)
            tweet_id_lists.append(tweet_id_str)
        list_for_csv.append(username_lists)
        list_for_csv.append(tweet_id_lists)
        #ファボ数 時間取得
        countlist = soup.find_all("div",{"class":"ProfileTweet-actionCountList"})
        favos = []
        for count in countlist:
            favo = count.find("span", id=re.compile('profile-tweet-action-favorite-count-aria-\w+'))
            favo_str = str(favo)
            favo_str=re.sub('<[^<]+?>', "", favo_str)
            favo_str=re.sub(' いいね', "", favo_str)
            favos.append(favo_str)
        list_for_csv.append(favos)
        list_for_csv.append(times)
        #テキスト取得
        textbs = soup.find_all("p",{"class":"TweetTextSize"})
        texts = []
        for text in textbs:
            text_str = str(text)
            text_str=re.sub('<[^<]+?>', "", text_str)
            text_str=re.sub(r"pic\.twitter\.com\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+", "", text_str)
            text_str=re.sub(r"instagram\.com\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+", "", text_str)
            text_str=re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+)", "", text_str)
            text_str=re.sub(r'@[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text_str)
            text_str=re.sub(r'&[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text_str)
            text_str=re.sub(';', "", text_str)
            text_str=re.sub('RT', "", text_str)
            text_str=re.sub('\n', "", text_str)
            texts.append(text_str)
        list_for_csv.append(texts)
        return list_for_csv,user_idlists

    def drop_duplicate_and_filter(filepath):
        '''
        ユーザーの重複を削除して、favo数10以下を切り捨てる
        '''
        df = pd.read_csv(filepath)
        df.drop_duplicates(subset=["ユーザーid"], inplace=True)
        df["ファボ数"] = df["ファボ数"].astype('int64')
        df = df[ df["ファボ数"] >= 10 ]
        df.to_csv(filepath,index=False)

    def YmdHMS(created_at):
        '''
        create_atの日付を年-月-日 時:日のフォーマットに変換
        '''
        time = datetime.datetime.strptime(created_at, '%H:%M - %Y年%m月%d日')
        return str(time.strftime("%Y-%m-%d %H:%M"))

    def dest_tweet(sw):
        '''
        csvに書き出しを行う
        '''
        create_csv_file = get_tweets_dir + "/stronger/selenium/" + sw + "_" + str(datetime.date.today()) + ".csv"
        file_path_fordir = os.path.dirname(create_csv_file)
        if not os.path.exists(file_path_fordir):
            os.makedirs(file_path_fordir)
        fw = open(create_csv_file, 'w', encoding="utf-8")
        csvwriter = csv.writer(fw)
        list_for_csv,user_idlists = get_stronger_selenium(sw)
        write_header = ["ユーザーid","スクリーンネーム","ユーザー名","ファボ数","投稿日時","ツイート内容","Tweet_id"]
        csvwriter.writerow(write_header)
        for i in range(len(user_idlists)):
            write_contents = [
                    list_for_csv[0][i-1],
                    list_for_csv[1][i-1],
                    list_for_csv[2][i-1],
                    re.sub(",","",list_for_csv[4][i-1]),
                    YmdHMS(list_for_csv[5][i-1]),
                    list_for_csv[6][i-1],
                    list_for_csv[3][i-1],
                ]
            csvwriter.writerow(write_contents)
        fw.close()
        drop_duplicate_and_filter(create_csv_file)
        print("書き込み完了\n")

if __name__ == '__main__':
    #dest_tweet("keyword")
