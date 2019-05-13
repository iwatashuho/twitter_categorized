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


class ALLOCATE_STRONGER:

    def __init__(self,csv_path,dir_path):
        self.model_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../models/tweetcategory_model_ver_0.15.bin'))
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
            tweet_text = row[6]
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
        df = pd.read_csv(self.CSV_PATH, engine='python')
        df["ツイート内容"] = df["ツイート内容"].apply(lambda d: str(d).strip().replace("\r","") )
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
        file_path_fordir = os.path.dirname(self.DIR_PATH + "/user_data/")
        if not os.path.exists(file_path_fordir):
            os.makedirs(file_path_fordir)
        csvname_split = str(self.CSV_PATH).split("/")
        beauty_name = csvname_split[-1]
        beauty_name = re.sub("\.csv","",beauty_name)
        df_beauty = df[ df["予想"].str.contains('美容') ]
        df_enable = df[ df["予想"].str.contains('__label__') ]
        av = df_beauty["予想"].count()/df_enable["Tweet_id"].count()
        df.to_csv( self.DIR_PATH + "/user_data/" + beauty_name + ".csv", index=False )
        print(df["フォロワー数"][0])
        print(av)
        if av >= 0.42:
            if df["フォロワー数"][0] >= 5000:
                csv_file = open(self.DIR_PATH + "/beauty_infulencer.csv", mode="a")
                csvwriter = csv.writer(csv_file)
                csvwriter.writerow([df["ユーザーid"][0],beauty_name,df["ユーザー名"][0],str(av),df["フォロワー数"][0]])
                csv_file.close()
            else:
                csv_file = open(self.DIR_PATH + "/beauty_account.csv", mode="a")
                csvwriter = csv.writer(csv_file)
                csvwriter.writerow([df["ユーザーid"][0],beauty_name,df["ユーザー名"][0],str(av),df["フォロワー数"][0]])
                csv_file.close()
        else:
            if df["フォロワー数"][0] >= 3000:
                csv_file = open(self.DIR_PATH + "/lifestyle_account.csv", mode="a")
                csvwriter = csv.writer(csv_file)
                csvwriter.writerow([df["ユーザーid"][0],beauty_name,df["ユーザー名"][0],str(av),df["フォロワー数"][0]])
                csv_file.close()
            else:
                csv_file = open(self.DIR_PATH + "/ordinaly_account.csv", mode="a")
                csvwriter = csv.writer(csv_file)
                csvwriter.writerow([df["ユーザーid"][0],beauty_name,df["ユーザー名"][0],str(av),df["フォロワー数"][0]])
                csv_file.close()

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

def create_csv(path,headrow):
    csv_file = open(path, mode="w")
    csvwriter = csv.writer(csv_file)
    csvwriter.writerow(headrow)
    csv_file.close()

def remove_csv(dir_path):
    all_files = glob.glob('{}*.csv'.format(dir_path))
    for file in all_files:
        print("{} 削除されました。".format(file))
        os.remove(file)

if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    beautys_path = os.path.join(os.path.join(base_path, '../get_stronger/get_tweets/stronger_tweets/'))
    all_files = glob.glob('{}*.csv'.format(beautys_path))
    write_header = ["ユーザーid","スクリーンネーム","ユーザー名","美容系ツイート率","フォロワー数"]
    output_dir = os.path.normpath(os.path.join(base_path, './output/claster/'))

    #振り分け用csvファイル作成
    create_csv(output_dir + "/beauty_infulencer.csv", write_header)
    create_csv(output_dir + "/beauty_account.csv", write_header)
    create_csv(output_dir + "/lifestyle_account.csv", write_header)
    create_csv(output_dir + "/ordinaly_account.csv", write_header)

    remove_csv(output_dir + "/user_data/")
    #クラスタ振り分け処理
    for file in all_files:
        allocate_stronger = ALLOCATE_STRONGER(file, output_dir)
        allocate_stronger.main()
