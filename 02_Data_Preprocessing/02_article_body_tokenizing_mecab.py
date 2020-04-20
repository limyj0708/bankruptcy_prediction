import pandas as pd
from IPython.display import clear_output
from konlpy.tag import Okt, Komoran, Mecab, Hannanum, Kkma

def get_tokenizer(tokenizer_name):
    if tokenizer_name == "komoran":
        tokenizer = Komoran()
    elif tokenizer_name == "okt":
        tokenizer = Okt()
    elif tokenizer_name == "mecab":
        tokenizer = Mecab()
    elif tokenizer_name == "hannanum":
        tokenizer = Hannanum()
    elif tokenizer_name == "kkma":
        tokenizer = Kkma()
    else:
        tokenizer = Mecab()
    return tokenizer


total_df = pd.read_csv('news_data_deduplicated_cleansed.csv')
tokenizer = get_tokenizer("mecab")

progress_check = 1
for each_line in total_df['article_body']:
    token_str = " ".join(tokenizer.morphs(each_line))
    with open('article_body_tokenized.txt', mode='a', encoding='utf-8') as f:
        f.writelines(token_str + '\n')
    print(progress_check)
    progress_check += 1




