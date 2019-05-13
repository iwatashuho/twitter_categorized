import sys
import fasttext as ft

argvs = sys.argv
input_file = argvs[1]
output_file = argvs[2]
#次元数はdim エポック数(繰り返し学習させること)はepoch 最低出現頻度のカウントはmin_count
#https://pypi.org/project/fasttext/
classifier = ft.supervised(input_file, output_file, dim=350, min_count=10, epoch=25, lr=1.0, word_ngrams=3, ws=14, bucket=2000000)