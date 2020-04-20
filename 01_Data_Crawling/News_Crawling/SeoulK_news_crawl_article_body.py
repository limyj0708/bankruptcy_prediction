#!/usr/bin/env python
# coding: utf-8

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import datetime
import time
import os
import csv
import pickle
import socket
import re
import concurrent

hostname = socket.gethostname()
df_article_list_gen = pd.read_csv('seoulK.csv', encoding='utf-8', chunksize=10000, dtype={'종목코드': object}) # url 리스트 불러옴
all_kind_of_blank = re.compile(r'\s+')
news_comp_name = re.compile(r'<.*> D')
google_cmd = re.compile(r'googletag.*\}\);')

async def get_article_body(article_url):
    timeout = aiohttp.ClientTimeout(total=30)
    if article_url == None:
        return None
    async with aiohttp.ClientSession() as session:
        print(article_url,'session')
        try:
            async with session.get(article_url, headers={'user-agent': 'AppleWebKit/537.36'}, timeout=timeout) as req:
                print(article_url,'session.get')
                if req.status == 404:
                    print('그런 페이지가 없다')
                    return None # 없는 페이지라면 반환값은 None이 된다.
                html = await req.text()
                print(article_url,'session.html')
                soup = BeautifulSoup(html, 'lxml')
                print(article_url,'session.soup')

                if '등록된 기사가 없습니다' in soup.find('head').get_text():
                    print('등록된 기사가 없습니다')
                    return '등록된 기사가 없습니다'

                article_body = soup.find('div', {"itemprop" : "articleBody"}).get_text()
                first = all_kind_of_blank.sub(' ',article_body)
                second = news_comp_name.sub('',first)
                third = google_cmd.sub('',second)
                forth = third.replace('◆', '').replace('■','').replace('저작권자 ⓒ 서울경제, 무단 전재 및 재배포 금지','')
                return forth
        except concurrent.futures._base.TimeoutError:
            print('timeout')
            return 'timeout'
        except AttributeError:
            print('No article')
            return 'noarticle'


def save_to_csv_one_article(one_dict, header_list):
    if os.path.isfile(hostname + '_seoulK_with_body.csv'): # 파일이 있는지 확인
        open_param = 'a' # 있으면 수정(뒤에 내용 추가) 모드
    else:
        open_param = 'w' # 없으면 파일 생성함
    with open(hostname + '_seoulK_with_body.csv', open_param, encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        if open_param == 'w':
            wr.writerow(header_list)
        writerow_pa_list = []
        for each_key in one_dict:
            writerow_pa_list.append(one_dict[each_key])
        wr.writerow(writerow_pa_list)

async def get_article_body_run(df_article_list_gen):
    try: # pickle 파일 있는지 없는지 확인. 크롤링이 모종의 이유로 중단되었을 때를 대비한 진행상태 저장 pickle
        with open('progress_getbody.pickle', 'rb') as f:
            last_progress_getbody = pickle.load(f)
    except FileNotFoundError:
        last_progress_getbody = [0,0]
        # 몇 번째 chunk인지, chunk 내에서 몇 번째인지 설정

    header = ['언론사명', '회사명', '종목코드', '기사_URL', '기사_업로드_날짜', '기사_제목', '기사_내용']

    progress_check_chunk = 0
    for each_chunk in df_article_list_gen:
        os.system('cls' if os.name == 'nt' else 'clear')
        if last_progress_getbody[0] > progress_check_chunk:
            progress_check_chunk += 1
            continue
        
        df_idx = 0
        loop_check = 1
        progress_inside_chunk = 0

        while loop_check == 1:
            os.system('cls' if os.name == 'nt' else 'clear')
            print('loop start')
            get_article_body_ins_list = []
            article_dict_list = []
            for run_idx in range(1,8):
                try:
                    if last_progress_getbody[1] > progress_inside_chunk:
                        progress_inside_chunk += 1
                        df_idx += 1
                        continue
                    print(each_chunk.iloc[df_idx]['종목코드'],'|',progress_check_chunk ,'/',last_progress_getbody[0],'|',progress_inside_chunk,'/',last_progress_getbody[1])
                    article_dict = {}
                    for each_key in header:
                        if each_key != '기사_내용':
                            article_dict[each_key] = each_chunk.iloc[df_idx][each_key]
                        else:
                            article_dict[each_key] = None

                    article_dict_list.append(article_dict)
                    get_article_body_ins_list.append(get_article_body(article_dict['기사_URL']))
                    df_idx += 1
                    print(run_idx)
                except IndexError:
                    print('=====Out of Index=======')
                    loop_check=0
                    break

            body_bunch = await asyncio.gather(*get_article_body_ins_list)

            for dict_idx, each in enumerate(article_dict_list):
                each['기사_내용'] = body_bunch[dict_idx]
                save_to_csv_one_article(each, header)
                
            last_progress_getbody[1] = last_progress_getbody[1] + len(body_bunch)
            progress_inside_chunk = progress_inside_chunk + len(body_bunch)
            with open('progress_getbody.pickle', 'wb') as f:
                pickle.dump(last_progress_getbody, f)

        last_progress_getbody[0] += 1
        last_progress_getbody[1] = 0
        with open('progress_getbody.pickle', 'wb') as f:
            pickle.dump(last_progress_getbody, f)


asyncio.run(get_article_body_run(df_article_list_gen))
print('>>>>>DONE<<<<<')