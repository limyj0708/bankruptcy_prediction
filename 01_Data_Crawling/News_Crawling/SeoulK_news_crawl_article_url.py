#!/usr/bin/env python
# coding: utf-8

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import datetime
import time
import os
import csv
import pickle
# from IPython.display import clear_output # Cell output clear를 위함
import socket
hostname = socket.gethostname()


# In[33]:


df_company_list = pd.read_csv('Target_company_list_for_news_crawling_for_dist.csv', encoding='utf-8', dtype={'종목코드': object, '상장폐지일': object})


# In[34]:


def get_and_create_page_content(url, company_name, stock_code):
    headers = {'user-agent': 'Mozilla/5.0'}
    req = requests.get(url, headers=headers)
    html = req.text
    soup = BeautifulSoup(html, 'lxml')
    
    dl_list = soup.find_all('dl')
    
    if len(dl_list) == 0:
        # 페이지에 기사가 하나도 없으면 None 반환
        return None
    contents_of_one_page = []
    
    for each in dl_list:
        contents_of_each_article = {'news_comp':'서울경제',                                    'target_comp':company_name, 'target_code':stock_code,                                    'article_link':None, 'published_date':None, 'title':None}
        
        title = each.find('dt').find('a').get_text()
        article_link = 'https://www.sedaily.com' + each.find('dt').find('a').get('href')
        published_date = each.find('dd').find('span', class_='letter').get_text()
        
        contents_of_each_article['title'] = title
        contents_of_each_article['article_link'] = article_link
        contents_of_each_article['published_date'] = published_date
        
        contents_of_one_page.append(contents_of_each_article)
    return contents_of_one_page


# In[35]:


def create_six_month_daterange_list(date='20191231'):
    delisted_date_datetime_obj = datetime.datetime.strptime(date, '%Y%m%d')
    start_date = (delisted_date_datetime_obj + datetime.timedelta(days=-1095)).strftime("%Y-%m-%d")
    end_date = delisted_date_datetime_obj.strftime("%Y-%m-%d")

    date_list = []
    for idx in range(1,7):
        end_date = (delisted_date_datetime_obj + datetime.timedelta(days=(-183*(idx-1)))).strftime("%Y-%m-%d")
        start_date = (delisted_date_datetime_obj + datetime.timedelta(days=(-183*idx+1))).strftime("%Y-%m-%d")
        date_list.append((start_date, end_date))
    
    return date_list


# In[36]:


def save_to_csv_by_every_page(list_param, header_list):
    if os.path.isfile(hostname + '_seoulK.csv'): # 파일이 있는지 확인
        open_param = 'a' # 있으면 수정(뒤에 내용 추가) 모드
    else:
        open_param = 'w' # 없으면 파일 생성함
            
    with open(hostname + '_seoulK.csv', open_param, encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        
        if open_param == 'w':
            wr.writerow(header_list)
            
        for each_dic in list_param:
            writerow_pa_list = []
            for each_key in each_dic:
                writerow_pa_list.append(each_dic[each_key])
            wr.writerow(writerow_pa_list)


# In[37]:


def get_seoulk_article_url(df_company_list):
    try: # pickle 파일 있는지 없는지 확인
        with open('progress.pickle', 'rb') as f:
            progress_dict = pickle.load(f)
    except FileNotFoundError:
        progress_dict = {}
    
    for idx in df_company_list.index:
        stock_code = df_company_list.iloc[idx]['종목코드']
        if stock_code not in progress_dict.keys():
            # 진행도 저장 dictionary에 지금 하는 종목코드가 있는지 확인
            progress_dict[stock_code] = [0,0,0]
            # 없으면 종목코드 항목 생성하고 완성 진행도 0, 날짜 진행도 0, 페이지 진행도 0으로 세팅
        elif progress_dict[stock_code][0] == 1:
            #이 종목이 크롤링 완성된 종목이라면, 다음 종목으로 넘어감
            continue

        company_name = df_company_list.iloc[idx]['기업명']
        delisted_check = df_company_list.iloc[idx]['상폐여부']
        delisted_date = df_company_list.iloc[idx]['상장폐지일']
        header = ['언론사명', '회사명', '종목코드', '기사_URL', '기사_업로드_날짜', '기사_제목']

        skip_num_date = progress_dict[stock_code][1] # 이만큼 날짜를 넘길 예정
        
        if delisted_check == 1: # 상폐 종목인지 확인
            date_list = create_six_month_daterange_list(delisted_date)
        else:
            date_list = create_six_month_daterange_list('20191231')

        for idx, each_pair in enumerate(date_list):
            # clear_output(wait=True)
            os.system('cls' if os.name == 'nt' else 'clear')
            page_num = 1
            if skip_num_date >= (idx+1): # 지난 날짜 진행도가 3이면, (idx+1)이 4가 될 때까지 반복문 공회전
                continue
            skip_num_page = progress_dict[stock_code][2] # 이만큼 페이지를 넘길 예정
            while True: # 1페이지씩 탐색함
                if skip_num_page >= page_num: # 지난 진행도가 10이면, pagenum이 11이 될 때까지 반복문 공회전
                    page_num += 1 
                    continue
                
                url='https://www.sedaily.com/Search/Search/SEList?Page=' + str(page_num) +                                      '&scDetail=detail&scOrdBy=0&catView=AL&scText='+ company_name + '&scPeriod=0&scArea=tc&scTextIn=&scTextExt=&scPeriodS=' + each_pair[0] + '&scPeriodE=' + each_pair[1]
                                     # date는 YYYY-MM-DD

                article_list_of_this_page = get_and_create_page_content(url, company_name, stock_code)
                if article_list_of_this_page == None:
                    break # 이 페이지부터는 기사가 없음. 즉 검색 끝난 것. 다음 연도쌍으로 넘어감
                
                print(f'{company_name}, {page_num}, {each_pair[0]}, {each_pair[1]}')
                save_to_csv_by_every_page(article_list_of_this_page, header) # 기사 저장
                page_num += 1
                
                progress_dict[stock_code][2] = progress_dict[stock_code][2] + 1 ## 페이지 진행도 1 더함
                with open('progress.pickle', 'wb') as f:
                    pickle.dump(progress_dict, f)
            
            progress_dict[stock_code][1] = progress_dict[stock_code][1] + 1 ## 날짜 진행도 1 더함
            progress_dict[stock_code][2] = 0 ## 날짜가 다음으로 넘어갔으니, 페이지 진행도는 다시 0이 되어야 함
            with open('progress.pickle', 'wb') as f:
                pickle.dump(progress_dict, f)
        
        progress_dict[stock_code][0] = 1 # 이 종목은 완료되었음
        with open('progress.pickle', 'wb') as f:
            pickle.dump(progress_dict, f)


# In[38]:


get_seoulk_article_url(df_company_list)
print('*****************Done*********************')



