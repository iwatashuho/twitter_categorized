# # -*- coding: utf-8 -*-
import re
import datetime, time, sys
import os
import pandas as pd
import codecs
import subprocess
import unicodedata
import csv
import glob
import json
import emoji
import MeCab
import fasttext as ft


class STRONGER_FILTER:

    def __init__(self,csv_path,dir_path):
        self.model_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../models/tweetcategory_model_ver_0.14.bin'))
        self.classifier = ft.load_model(self.model_path)
        self.CSV_PATH = csv_path
        self.DIR_PATH = dir_path

    def get_texts(self):
        """
        csvからテキストを抜き出す。
        """
        csv_file,csv_reader = self.set_csv_open(self.CSV_PATH)
        results = []
        for row in csv_reader:
            tweet_text = row[2]
            results.append(tweet_text)
        csv_file.close()
        return results

    def get_surfaces(self, tweets):
        """
        文書を分かち書きし単語単位に分割
        """
        results = []
        mecab = MeCab.Tagger('-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
        for row in tweets:
            tweets = self.format_text(row)
            mecab.parse('')
            surf = []
            node = mecab.parseToNode(tweets)
            while node:
                #基本形に変換
                base_txt = node.feature.split(",")[6]
                #助詞を取り除く
                hinshi = node.feature.split(",")[0]
                if hinshi in ["名詞","形容詞","動詞","記号","助詞"]:
                    if base_txt == "*":
                        surf.append(node.surface)
                    else:
                        surf.append(base_txt)
                node = node.next
            results.append(surf)
        return results

    def filtering_class(self, sentences):
        """
        ツイートを解析して分類を行う
        """
        df = pd.read_csv(self.CSV_PATH)
        append_pred = []
        print(str(self.CSV_PATH))
        for i,sentence in enumerate(sentences):
            words = " ".join(sentence)

            if len(words) <= 4:
                append_pred.append(str("測定不能"))
                continue
            estimate = self.classifier.predict_proba([words], k=3)[0][0]
            append_pred.append(str(estimate[0]))
        df["予想"] = append_pred
        file_path_fordir = os.path.dirname(self.DIR_PATH)
        if not os.path.exists(file_path_fordir):
            os.makedirs(file_path_fordir)
        csvname_split = str(self.CSV_PATH).split("/")
        beauty_name = csvname_split[-1]
        beauty_name = re.sub("\.csv","",beauty_name)
        df_beauty = df[ df["予想"].str.contains('美容') ]
        df_enable = df[ df["予想"].str.contains('__label__') ]
        av = df_beauty["予想"].count()/df_enable["Tweet_id"].count()
        df.to_csv( self.DIR_PATH + "/" + beauty_name + ".csv", index=False )
        csv_file = open(self.DIR_PATH + "/get_av.csv", mode="a")
        csvwriter = csv.writer(csv_file)
        csvwriter.writerow([beauty_name,av])
        csv_file.close()
        print(beauty_name,av)
        # df_beauty.to_csv( self.DIR_PATH + "/output_beauty.csv", index=False )
        # df_other.to_csv( self.DIR_PATH + "/output_other.csv", index=False )

    def main(self):
        get_texts = self.get_texts()#csv 配列化
        wakati_tweets = self.get_surfaces(get_texts) #csvテキスト分かち化して再び配列化
        filtering = self.filtering_class(wakati_tweets)

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

    def set_csv_open(self,file_path):
        f = codecs.open(file_path, 'r', 'utf-8')
        csvreader = csv.reader(f)
        header = next(csvreader)
        return f,csvreader

if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    beautys_path = os.path.join(os.path.join(base_path, '../get_stronger/get_tweets/beauty_user/'))
    all_files = glob.glob('{}*.csv'.format(beautys_path))
    output_dir = os.path.normpath(os.path.join(base_path, './output/beauty/'))
    for file in all_files:
        stronger_filter = STRONGER_FILTER(file, output_dir)
        stronger_filter.main()

    beautys_path = os.path.join(os.path.join(base_path, './output/beauty/get_av.csv'))
    df_av = pd.read_csv(beautys_path)
    df_av = df_av.iloc[:, [1]]
    print("平均値",df_av.mean())
    print("中央値",df_av.median())
    print("標準偏差",df_av.std())
