# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys
import codecs
import csv
import urllib.parse
import pandas as pd
from abc import ABCMeta, abstractmethod
from sub.pwd import *

#tweetをgetしまくる関数。親クラスです。
class TweetsGetter_sub(object):
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
                if res.status_code == 404 or res.status_code == 401:
                    print("このユーザーは退会した可能性があります。")
                    break
                else:
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

    @staticmethod
    def bylist(listid):
        return TweetsGetterBylist(listid)

#上記のクラスの子クラス。サーチ用にゲットする関数やね
class TweetsGetterBySearch(TweetsGetter_sub):
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
        params = {'q':self.keyword, 'count':200, 'tweet_mode':'extended' }
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


class TweetsGetterByUser(TweetsGetter_sub):
    '''
    ユーザーを指定してツイートを取得
    '''
    def __init__(self, screen_name):
        super(TweetsGetterByUser, self).__init__()
        self.screen_name = screen_name

    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
        params = {'screen_name':self.screen_name, 'count':200, 'exclude_replies':"true" }
        return url, params

    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text:
            results.append(tweet)

        return results

    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['statuses']['/statuses/user_timeline']['remaining']
        reset     = res_text['resources']['statuses']['/statuses/user_timeline']['reset']

        return int(remaining), int(reset)


class TweetsGetterBylist(TweetsGetter_sub):
    '''
    リストからユーザーを抽出
    '''
    def __init__(self, listid):
        super(TweetsGetterBylist, self).__init__()
        self.listid = listid

    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/lists/members.json'
        params = {'list_id':self.listid, 'count':200}
        return url, params

    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text:
            results.append(tweet)

        return results

    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['statuses']['/statuses/user_timeline']['remaining']
        reset     = res_text['resources']['statuses']['/statuses/user_timeline']['reset']

        return int(remaining), int(reset)


    #### インフルエンサーのタイムラインを取得する ####
    #リストゲット
    # getter = TweetsGetter.bylist("809711379401744384")
    # cnt = 0
    # fw = open(get_tweets_dir + "/beaty.csv", 'w', encoding="utf-8")
    # csvwriter = csv.writer(fw)
    # write_header = ["ユーザーid","スクリーンネーム","ユーザー名"]
    # csvwriter.writerow(write_header)
    # for tweet in getter.collect(total = 500):
    #     write_contents = [
    #                 str(tweet['id']),
    #                 str(tweet['screen_name']),
    #                 str(tweet['name']),
    #             ]
    #     csvwriter.writerow(write_contents)
    # fw.close()
