# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys, calendar
import os
import codecs
import csv
import urllib.parse
import pandas as pd
from abc import ABCMeta, abstractmethod
from sub.concat_csv import CSV_CONCAT
from sub.shaping_for_fasttext import SHAPING_FOR_FASTTEXT
from sub.pwd import *

base_path = os.path.dirname(os.path.abspath(__file__))
get_tweets_dir = os.path.normpath(os.path.join(base_path, './get_tweets/'))

#tweetをgetしまくる関数。親クラスです。
class TweetsGetter(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.session = OAuth1Session(CK, CS, AT, AS)

    #子クラスによるオーバーライドを前提とした関数 abstractmethod
    @abstractmethod
    def specifyUrlAndParams(self, keyword):
        '''
        呼出し先 URL、パラメータを返す
        '''
    #子クラスによるオーバーライドを前提とした関数 abstractmethod
    @abstractmethod
    def pickupTweet(self, res_text, includeRetweet):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
    #子クラスによるオーバーライドを前提とした関数 abstractmethod
    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''

    def collect(self, total = -1, onlyText = False, includeRetweet = False):
        '''
        ツイート取得を開始する
        '''
        #----------------
        # 回数制限を確認
        #----------------
        self.checkLimit()

        #----------------
        # URL、パラメータ
        #----------------
        url, params = self.specifyUrlAndParams()
        params['include_rts'] = str(includeRetweet).lower()
        # include_rts は statuses/user_timeline のパラメータ。search/tweets には無効

        #----------------
        # ツイート取得
        #----------------
        cnt = 0
        unavailableCnt = 0
        while True:
            res = self.session.get(url, params = params)
            #api取得エラーだったら以下
            if res.status_code == 503:
                # 503 : Service Unavailable
                if unavailableCnt > 10:
                    #10回以上リピートしてしまったらエラー
                    raise Exception('Twitter API error %d' % res.status_code)
                unavailableCnt += 1
                print ('Service Unavailable 503')
                #30秒待機
                self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
                continue
            # 503でなければカウントを0にします。
            unavailableCnt = 0

            #api取得エラー以外のガチエラーだったらこちら
            if res.status_code != 200:
                raise Exception('Twitter API error %d' % res.status_code)
            #上記クリアならばtweet用jsonを取得
            tweets = self.pickupTweet(json.loads(res.text))
            #tweetが0ならループから抜けます。
            if len(tweets) == 0:
                # len(tweets) != params['count'] としたいが
                # count は最大値らしいので判定に使えない。
                # ⇒  "== 0" にする
                # https://dev.twitter.com/discussions/7513
                break

            for tweet in tweets:
                #リツイートだったら出力しない。
                if (('retweeted_status' in tweet) and (includeRetweet is False)):
                    pass
                else:
                    #textオプションが入ってたらtextを出力
                    if onlyText is True:
                        yield tweet['text']
                    else:
                        yield tweet

                    cnt += 1
                    # 100件のリクエストごとに件数を表示
                    if cnt % 100 == 0:
                        print ('%d件 ' % cnt)
                    # totalを超えたら出力せずforを抜け出す。
                    if total > 0 and cnt >= total:
                        return
            #以下のmax_id以下ツイートから取得していく。
            #http://nonbiri-tereka.hatenablog.com/entry/2014/03/06/220015
            params['max_id'] = tweet['id'] - 1

            # ヘッダ確認 （回数制限）
            # X-Rate-Limit-Remaining が入ってないことが稀にあるのでチェック
            if ('X-Rate-Limit-Remaining' in res.headers and 'X-Rate-Limit-Reset' in res.headers):
                if (int(res.headers['X-Rate-Limit-Remaining']) == 0):
                    #残り回数が0だったら次の制限解除時間まで待機させる
                    self.waitUntilReset(int(res.headers['X-Rate-Limit-Reset']))
                    #念の為残回数チェック
                    self.checkLimit()
            else:
                #上記のヘッダーが取れなかったらとりあえず残回数を取得
                print ('not found  -  X-Rate-Limit-Remaining or X-Rate-Limit-Reset')
                # 残回数チェック。上記のifで拾えなかった場合こちらで残回数0の場合にリミットまで待機させる。
                self.checkLimit()

    #残回数をチェックし、0だったら待機させる関数
    def checkLimit(self):
        '''
        回数制限を問合せ、アクセス可能になるまで wait する
        '''
        unavailableCnt = 0
        while True:
            url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
            res = self.session.get(url)
            #取れなくなった且つ、残回数取得のapiすら503だったら10回リピートさして、トライさせる
            if res.status_code == 503:
                # 503 : Service Unavailable
                if unavailableCnt > 10:
                    raise Exception('Twitter API error %d' % res.status_code)

                unavailableCnt += 1
                print ('Service Unavailable 503')
                #30秒待機
                self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
                continue

            unavailableCnt = 0
            # 上記のエラー以外だったら単純にエラーを出力
            if res.status_code != 200:
                raise Exception('Twitter API error %d' % res.status_code)

            #こちらで残り回数と、次までのリセット秒数を拾って、残回数0なら次のリミットまで待機さす
            remaining, reset = self.getLimitContext(json.loads(res.text))
            if (remaining == 0):
                self.waitUntilReset(reset)
            else:
                break

    #残回数をチェックし、0だったら待機させる関数
    def waitUntilReset(self, reset):
        '''
        reset 時刻まで sleep
        '''
        seconds = reset - time.mktime(datetime.datetime.now().timetuple())
        seconds = max(seconds, 0)
        print ('\n     =====================')
        print ('     == waiting %d sec ==' % seconds)
        print ('     =====================')
        #flushは即時実行の関数
        sys.stdout.flush()
        #指定した秒数待機させる
        time.sleep(seconds + 10)  # 念のため + 10 秒

    #staticメソッドにすると、インスタンス化せずともメソッドを呼び出すことができる。
    #そしてclassメソッドと違って最初のself用引数がいらない&ない。 selfがないため、継承して子クラスになっても親クラスのプロパティを参照する。
    @staticmethod
    def bySearch(keyword):
        return TweetsGetterBySearch(keyword)

    @staticmethod
    def byUser(screen_name):
        return TweetsGetterByUser(screen_name)

#上記のクラスの子クラス。サーチ用にゲットする関数やね
class TweetsGetterBySearch(TweetsGetter):
    '''
    キーワードでツイートを検索
    '''
    def __init__(self, keyword):
        #親クラスのinitを呼び出します。 https://www.lifewithpython.com/2014/01/python-super-function.html
        #多分ここで__init__をオーバーライドしているのは self.keywordを作りたかったからでしょう。
        super(TweetsGetterBySearch, self).__init__()
        self.keyword = keyword


    #検索用のパラメータを設定する search tweetsでツイートを取得
    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        params = {'q':self.keyword, 'count':200, 'tweet_mode':'extended', 'result_type':'mixed'}
        return url, params

    #collect関数で取得したjson
    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text['statuses']:
            results.append(tweet)

        return results

    #残回数とリセットまでの時間を取得しreturnするマン
    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['search']['/search/tweets']['remaining']
        reset     = res_text['resources']['search']['/search/tweets']['reset']
        return int(remaining), int(reset)

def YmdHMS(created_at):
    '''
    create_atの日付を年-月-日 時:日のフォーマットに変換
    '''
    time_utc = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    unix_time = calendar.timegm(time_utc)
    time_local = time.localtime(unix_time)
    return str(time.strftime("%Y-%m-%d %H:%M", time_local))

#そのうちpathを実行スクリプトからの相対パスに変更しようね https://qiita.com/FGtatsuro/items/52ad08640df6bfad5c2a
def dest_tweet(dict, min_faves="0", since_day="2019-01-01"):
    '''
    dictで指定したカテゴリのワードからツイートを拾ってくる。
    '''
    for ct,sw in dict.items():
        since_day = "2018-01-01"
        for kw in sw:
            start_string = """
カテゴリ: {0}
キーワード: {1}
書き込み開始
            """.format(ct,kw)
            print(start_string)
            getter = TweetsGetter.bySearch(u'{0} min_faves:{1} since:{2} lang:ja OR @999999999'.format(kw,min_faves,since_day))
            create_csv_file = get_tweets_dir + "/" + ct + "/" + kw + ".csv"
            file_path_fordir = os.path.dirname(create_csv_file)
            if not os.path.exists(file_path_fordir):
                os.makedirs(file_path_fordir)
            fw = open(create_csv_file, 'w', encoding="utf-8")
            csvwriter = csv.writer(fw)
            write_header = ["ユーザーid","スクリーンネーム","ユーザー名","フォロワー数","リツイート数","ファボ数","投稿日時","ツイート内容"]
            csvwriter.writerow(write_header)
            for tweet in getter.collect(total = 3000):
                write_contents = [
                    str(tweet['user']['id_str']),
                    str(tweet['user']['screen_name']),
                    str(tweet['user']['name']),
                    str(tweet['user']['followers_count']),
                    str(tweet['retweet_count']),
                    str(tweet['favorite_count']),
                    str(YmdHMS(tweet['created_at'])),
                    tweet['full_text']
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
    df.drop_duplicates(subset=["ユーザーid","ユーザー名"], inplace=True)
    df.to_csv(filepath,index=False)


if __name__ == '__main__':

    serch_dict = {
        "IT":[
            "テスト駆動",
            "講演",
            "dev",
            "参考書",
            "GKE",
            "パターンマッチ",
            "メモリ",
        ],
        "美容":[
            "アクアレーベル",
            "雪肌精",
            "透明肌"
        ],
        "暮らし":[
            "猫",
            "酒場",
            "英国式パブ",
            "一杯",
            "カクテル",
        ],
        "エンタメ":[
            "プラチナメダル",
            "勝った",
            "ワタナベ楽器",
            "ストラップ",
            "ケーブル",
            "ステッカー",
            "アンデッド",
            "パスカット",
            "ドリブル",
            "キャプテン",
            "ユニフォーム",
            "禁忌",
            "猫耳",
            "ティターン",
            "OPTIWEB",
        ]
    }

    # dest_tweet(serch_dict)

    argvs = sys.argv
    is_wakati = argvs[1]
    if is_wakati == "True":
        for k in serch_dict:
            csv_concater = CSV_CONCAT(get_tweets_dir + "/" + k + "/")
            csv_concater.concat_and_dump_csv(get_tweets_dir + "/Integration/label_" + k + ".csv")
        for k in serch_dict:
            shaping_for_fasttext = SHAPING_FOR_FASTTEXT(k, get_tweets_dir + "/Integration/label_" + k + ".csv", get_tweets_dir + "/wakati_txt/")
            shaping_for_fasttext.main()
        shaping_for_fasttext.integrate_txt("Integrate.txt")
