# # -*- coding: utf-8 -*-
import re
import datetime, time, sys
import os
import codecs
import subprocess
import unicodedata
import csv
import json
import emoji
import MeCab


class SHAPING_FOR_FASTTEXT(object):

    def __init__(self,class_label,csv_path,dir_path):
        self.CLASS_LABEL = "__label__" + class_label
        self.CSV_PATH = csv_path
        self.DIR_PATH = dir_path

    def get_texts(self):
        """
        csvからテキストを抜き出す。
        """
        csv_file,csv_reader = self.set_csv_open(self.CSV_PATH)
        results = []
        for row in csv_reader:
            tweet_text = row[3]
            results.append(tweet_text)
        csv_file.close()
        return results

    def get_surfaces(self,tweets):
        """
        文書を分かち書きし単語単位に分割
        """
        results = []
        mecab = MeCab.Tagger('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
        for row in tweets:
            content = self.format_text(row)
            #バグ対応です。これをしないとparseToNodeのsurfaceが読み取れません。
            mecab.parse('')
            surf = []
            #parseToNodeでやるとsafaceとfeatureで情報が分けられたものを返してくれます。
            #副詞とか助詞とかを取り除きたい場合はこちらこちらを利用してやると便利ですよ。（普通のparseの方がその分処理速度は早いですがね...）
            node = mecab.parseToNode(content)
            while node:
                #surfのイメージ: ["私","それ","は","ない","と","思う"]
                #基本形に変換
                base_txt = node.feature.split(",")[6]
                # #助詞を取り除く
                hinshi = node.feature.split(",")[0]
                if hinshi in ["名詞","形容詞","動詞","記号","助詞"]:
                    if base_txt == "*":
                        surf.append(node.surface)
                    else:
                        surf.append(base_txt)
                #nextというメソッドがついているので次の形態素にwhile用の変数を更新してセンテンスの形態素解析が終わるまでループしてます。
                node = node.next
            results.append(surf)
        return results

    def write_txt(self,wakati_tweets):
        """
        評価モデル用のテキストファイルを作成する
        """
        try:
            if(len(wakati_tweets) > 0):
                fileName = self.DIR_PATH + self.CLASS_LABEL + "_wakati.txt"
                file_path_fordir = os.path.dirname(fileName)
                if not os.path.exists(file_path_fordir):
                    os.makedirs(file_path_fordir)
                labelText = self.CLASS_LABEL + ", "
                f = open(fileName, 'w')
                for row in wakati_tweets:
                    # 空行区切りの文字列に変換
                    # イメージ: ["私","それ","は","ない","と","思う"] => 私 それ は ない と 思う
                    spaceTokens = " ".join(row);
                    # イメージ:  私 それ は ない と 思う => __label__1, 私 それ は ない と 思う\n
                    result = labelText + spaceTokens + "\n"
                    # 書き込み
                    f.write(result)
                f.close()
            print(str(len(wakati_tweets))+"行を書き込み")
        except Exception as e:
            print("テキストへの書き込みに失敗")
            print(e)

    def format_text(self,text):
        '''
        ツイートから不要な情報を削除
        '''
        # def remove_emoji(src_str):
        #     return ''.join(c for c in src_str if c not in emoji.UNICODE_EMOJI)
        text=re.sub('<[^<]+?>', "", text)
        text=re.sub(r"pic\.twitter\.com\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+", "", text)
        text=re.sub(r"instagram\.com\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+", "", text)
        text=re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+)", "", text)
        text=re.sub(r'@[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
        text=re.sub(r'&[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
        text=re.sub(';', "", text)
        text=re.sub('RT', "", text)
        text=re.sub('#', "", text)
        text=re.sub('\?', "", text)
        text=re.sub('？', "", text)
        text=re.sub('！', "", text)
        text=re.sub('\!', "", text)
        text=re.sub('\(', "", text)
        text=re.sub('\)', "", text)
        text=re.sub('（', "", text)
        text=re.sub('）', "", text)
        text=re.sub('\n', "", text)
        text=re.sub('\d+', '0', text)
        text=re.sub('、', ',', text)
        text=re.sub('\・', '', text)
        text=re.sub('\...', '', text)
        text=re.sub('，', ',', text)
        text=re.sub('．', '。', text)
        text=re.sub('\.', '。', text)
        text=re.sub('\[', '', text)
        text=re.sub('\]', '', text)
        text=re.sub('\「', '', text)
        text=re.sub('\」', '', text)
        text=re.sub('\【', '', text)
        text=re.sub('\】', '', text)
        text=re.sub('\/', '', text)
        text=text.lower()
        text=text.strip()
        text=unicodedata.normalize("NFKC", text)
        return text

    def main(self):
        get_texts = self.get_texts()
        wakati_tweets = self.get_surfaces(get_texts)
        self.write_txt(wakati_tweets)

    def integrate_txt(self,filename):
        base = os.path.dirname(os.path.abspath(__file__))
        base_dirname = os.path.normpath(os.path.join(base, '../get_tweets/wakati_txt'))
        try:
            input_f = base_dirname + "/*.txt"
            output_f = base_dirname + "/" + filename
            cmd = "cat %s > %s" % (input_f, output_f )
            proc = subprocess.Popen(
            cmd,
            shell  = True,                #シェル経由($ sh -c "command")で実行。
            stdin  = subprocess.PIPE,     #1
            stdout = subprocess.PIPE,     #2
            stderr = subprocess.PIPE)
            stdout_data, stderr_data = proc.communicate()
            print(stdout_data)
            print(stderr_data)
        except:
            print("Error.")

    def set_csv_open(self,file_path):
        f = codecs.open(file_path, 'r', 'utf-8')
        csvreader = csv.reader(f)
        header = next(csvreader)
        return f,csvreader
