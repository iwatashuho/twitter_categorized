# # -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys
import codecs
import csv
from sub.define_client import define_client_proc

class GET_RETWEETER(object):

    def __init__(self,file_path):
        self.csv_file,self.csv_reader = self.set_csv_open(file_path)

    def get_tweets_proc(self,tweet_id):
        nnx = 100
        url = "https://api.twitter.com/1.1/statuses/retweets/"+str(tweet_id)+".json"
        session = define_client_proc()
        response = session.get(url, params = {'count':nnx})
        if response.status_code == 200:
            print ('アクセス可能回数: %s' % response.headers['X-Rate-Limit-Remaining'])
            retweet_usr = json.loads(response.text)
            return retweet_usr
        else:
            print(response.status_code)
            # X-Rate-Limit-Remaining が入ってないことが稀にあるのでチェック
            if ('X-Rate-Limit-Remaining' in response.headers and 'X-Rate-Limit-Reset' in response.headers):
                if (int(response.headers['X-Rate-Limit-Remaining']) == 0):
                    print("action: 残回数0 待機処理へ")
                    self.waitUntilReset(int(response.headers['X-Rate-Limit-Reset']))
            else:
                #上記のヘッダーが取れなかったらとりあえず残回数を取得
                print ('not found  -  X-Rate-Limit-Remaining or X-Rate-Limit-Reset')
            sys.stderr.write("**** 待機処理完了\n")
            sys.stderr.write("status code: %d\n" % response.status_code)

    def waitUntilReset(self,reset):
        seconds = reset - time.mktime(datetime.datetime.now().timetuple())
        seconds = max(seconds, 0)
        print ('\n     =====================')
        print ('     == waiting %d sec ==' % seconds)
        print ('     =====================')
        sys.stdout.flush()
        time.sleep(seconds + 30)

    def get_retweet(self,parent_name):
        sys.stderr.write("*** 開始 ***\n")
        fw = codecs.open("./Influencers_data/" + parent_name + "_retweeter.csv", 'w', 'utf-8')
        csvwriter = csv.writer(fw)
        write_header = ["ユーザーid","ユーザーネーム","スクリーンネーム","リツイート元url"]
        csvwriter.writerow(write_header)
        for row in self.csv_reader:
            parent_tweet_id = row[1]
            retweeters = self.get_tweets_proc(parent_tweet_id)
            tweet_link = "https://twitter.com/" + parent_name +  "/status/" + str(parent_tweet_id)
            print("==================================")
            print("親ツイートのid: " + parent_tweet_id)
            if retweeters is None:
                print("action: continue")
                continue
            for retweeter in retweeters:
                write_contents = [retweeter['user']['id_str'],str(retweeter['user']['name']),str(retweeter['user']['screen_name']),tweet_link]
                csvwriter.writerow(write_contents)
            print("==================================\n\n")
        self.csv_file.close()
        fw.close()
        sys.stderr.write("*** 終了 ***\n")

    def set_csv_open(self,file_path):
        f = codecs.open(file_path, 'r', 'utf-8')
        csvreader = csv.reader(f)
        header = next(csvreader)
        return f,csvreader

### usage ###
# get_retweeter = GET_RETWEETER("./Influencers_data/wada_saan.csv")
# get_retweeter.get_retweet()
### usage ###
