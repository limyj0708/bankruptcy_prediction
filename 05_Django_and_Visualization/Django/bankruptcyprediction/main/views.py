from django.shortcuts import render
from django.views.generic import TemplateView, FormView
from django.db import connections
from main.forms import searchForm

import datetime
import json
import pickle
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import os
import logging
logger = logging.getLogger('django')

# Create your views here.
class search_window(FormView):
    template_name = 'search_window.html'
    form_class = searchForm
    #def form_valid(self,form):
    #    return super(search_window, self).form_valid(form)
        

class search_result(TemplateView):
    template_name = 'search_result.html'
    template_name_no_such = 'no_such_company.html'
    company_name = ''
    
    def post(self, request):
        self.company_name = request.POST.get('company_name')
        stock_data_closing_price = self.get_stock_data_closing_price()
        
        if stock_data_closing_price == None:
            return render(request, self.template_name_no_such, {'company_name':self.company_name})

        stock_data_trading_num_daily = self.get_stock_data_trading_num_daily()
        stock_data_trading_ratio_sell_montly = self.get_stock_data_trading_ratio_sell_monthly()
        stock_data_trading_ratio_buy_monthly = self.get_stock_data_trading_ratio_buy_monthly()
        news_data_news_num_and_bankruptcy_ratio = self.get_news_num_and_bankruptcy_ratio()
        finance_data_5years = self.get_finance_data()
        audit_report_last_3 = self.get_audit_report()
        predict_result = self.model_prediction(year=2)

        return render(request,
        self.template_name, 
        {'company_name':self.company_name
        ,'stock_data_closing_price':stock_data_closing_price
        ,'stock_data_trading_num_daily':stock_data_trading_num_daily
        ,'stock_data_trading_ratio_sell_montly':stock_data_trading_ratio_sell_montly
        ,'stock_data_trading_ratio_buy_monthly':stock_data_trading_ratio_buy_monthly
        ,'news_data_news_num_and_bankruptcy_ratio':news_data_news_num_and_bankruptcy_ratio
        ,'finance_data_5years':finance_data_5years
        ,'audit_report_last_3':audit_report_last_3
        ,'predict_result':predict_result}
        )

    def get_stock_data_closing_price(self):
        query="""
        SELECT date, "종가(원)"
        FROM stock_data_2000_2020_raw
        WHERE stock_code = (
            SELECT stock_code
            FROM target_company_list
            WHERE (company_name = %s)
            AND (delisted_check = False)
        ) AND EXTRACT(DOW FROM "date") NOT IN (0,6)
        ORDER BY date DESC
        LIMIT 365;
        """
        #start_date = datetime.datetime(2019, 10, 12)
        #end_date = start_date - datetime.timedelta(days=30)
        data = {"x":[],"y":[],"type":"scatter","name":"종가"}

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            #end_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')
            for each_row in cur: # 쿼리 실행 결과가 없다면, for loop에 들어가지지조차 않음
                data["x"].append(each_row[0].strftime('%Y-%m-%d'))
                data["y"].append(each_row[1])
        if data["x"] == []:
            return None
        return data

    def get_stock_data_trading_ratio_sell_daily(self):
        query="""
        select "date"
        ,("매도수량(외국인계)(주)")/("매도수량(개인)(주)"+"매도수량(기관계)(주)"+"매도수량(외국인계)(주)") as "외국인매도비율"
        ,("매도수량(기관계)(주)")/("매도수량(개인)(주)"+"매도수량(기관계)(주)"+"매도수량(외국인계)(주)") as "기관매도비율"
        ,("매도수량(개인)(주)")/("매도수량(개인)(주)"+"매도수량(기관계)(주)"+"매도수량(외국인계)(주)") as "개인매도비율"
        from stock_data_2000_2020_raw
        where stock_code = (
            SELECT stock_code
            FROM target_company_list
            WHERE (company_name = %s)
            AND (delisted_check = False)
        ) AND EXTRACT(DOW FROM "date") NOT IN (0,6)
        order by "date" DESC
        limit 365;
        """

        #start_date = datetime.datetime(2019, 10, 12)
        #end_date = start_date - datetime.timedelta(days=30)
        data_f = {"x":[],"y":[],"type":"scatter", "name":"외국인매도비율"}
        data_inv = {"x":[],"y":[],"type":"scatter", "name":"기관매도비율"}
        data_indi = {"x":[],"y":[],"type":"scatter", "name":"개인매도비율"}
        data_list = []

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            #end_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')
            for each_row in cur: # 쿼리 실행 결과가 없다면, for loop에 들어가지지조차 않음
                data_f["x"].append(each_row[0].strftime('%Y-%m-%d'))
                data_f["y"].append(round(each_row[1],3))
                data_inv["x"].append(each_row[0].strftime('%Y-%m-%d'))
                data_inv["y"].append(round(each_row[2],3))
                data_indi["x"].append(each_row[0].strftime('%Y-%m-%d'))
                data_indi["y"].append(round(each_row[3],3))
        
        data_list.append(data_f)
        data_list.append(data_inv)
        data_list.append(data_indi)

        return data_list

    def get_stock_data_trading_ratio_sell_monthly(self):
        query="""
        select date_trunc('month', date) as mon
        ,to_char(date_trunc('month', date), 'YYYY-MM') as mon_for_chart
        ,sum("매도수량(외국인계)(주)")/(sum("매도수량(개인)(주)")+sum("매도수량(기관계)(주)")+sum("매도수량(외국인계)(주)")) as "외국인매도비율_1m"
        ,sum("매도수량(기관계)(주)")/(sum("매도수량(개인)(주)")+sum("매도수량(기관계)(주)")+sum("매도수량(외국인계)(주)")) as "기관매도비율_1m"
        ,sum("매도수량(개인)(주)")/(sum("매도수량(개인)(주)")+sum("매도수량(기관계)(주)")+sum("매도수량(외국인계)(주)")) as "개인매도비율_1m"
        from stock_data_2000_2020_raw
        where stock_code = (
            SELECT stock_code
            FROM target_company_list
            WHERE (company_name = %s)
            AND (delisted_check = False)
        ) AND EXTRACT(DOW FROM "date") NOT IN (0,6)
        GROUP BY mon
        ORDER BY mon DESC
        LIMIT 13;
        """

        #start_date = datetime.datetime(2019, 10, 12)
        #end_date = start_date - datetime.timedelta(days=30)
        data_f = {"x":[],"y":[],"type":"bar", "name":"외국인매도비율_1m"}
        data_inv = {"x":[],"y":[],"type":"bar", "name":"기관매도비율_1m"}
        data_indi = {"x":[],"y":[],"type":"bar", "name":"개인매도비율_1m"}
        data_list = []

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            #end_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')
            for each_row in cur: # 쿼리 실행 결과가 없다면, for loop에 들어가지지조차 않음
                data_f["x"].append(each_row[1])
                data_f["y"].append(round(each_row[2],3))
                data_inv["x"].append(each_row[1])
                data_inv["y"].append(round(each_row[3],3))
                data_indi["x"].append(each_row[1])
                data_indi["y"].append(round(each_row[4],3))
        
        data_list.append(data_f)
        data_list.append(data_inv)
        data_list.append(data_indi)

        return data_list

    def get_stock_data_trading_ratio_buy_monthly(self):
        query="""
        select date_trunc('month', date) as mon
        ,to_char(date_trunc('month', date), 'YYYY-MM') as mon_for_chart
        ,sum("매수수량(외국인계)(주)")/(sum("매수수량(개인)(주)")+sum("매수수량(기관계)(주)")+sum("매수수량(외국인계)(주)")) as "외국인매수비율_1m"
        ,sum("매수수량(기관계)(주)")/(sum("매수수량(개인)(주)")+sum("매수수량(기관계)(주)")+sum("매수수량(외국인계)(주)")) as "기관매수비율_1m"
        ,sum("매수수량(개인)(주)")/(sum("매수수량(개인)(주)")+sum("매수수량(기관계)(주)")+sum("매수수량(외국인계)(주)")) as "개인매수비율_1m"
        from stock_data_2000_2020_raw
        where stock_code = (
            SELECT stock_code
            FROM target_company_list
            WHERE (company_name = %s)
            AND (delisted_check = False)
        ) AND EXTRACT(DOW FROM "date") NOT IN (0,6)
        GROUP BY mon
        ORDER BY mon DESC
        LIMIT 13;
        """
        #start_date = datetime.datetime(2019, 10, 12)
        #end_date = start_date - datetime.timedelta(days=30)
        data_f = {"x":[],"y":[],"type":"bar", "name":"외국인매수비율_1m"}
        data_inv = {"x":[],"y":[],"type":"bar", "name":"기관매수비율_1m"}
        data_indi = {"x":[],"y":[],"type":"bar", "name":"개인매수비율_1m"}
        data_list = []

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            #end_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')
            for each_row in cur: # 쿼리 실행 결과가 없다면, for loop에 들어가지지조차 않음
                data_f["x"].append(each_row[1])
                data_f["y"].append(round(each_row[2],3))
                data_inv["x"].append(each_row[1])
                data_inv["y"].append(round(each_row[3],3))
                data_indi["x"].append(each_row[1])
                data_indi["y"].append(round(each_row[4],3))
        
        data_list.append(data_f)
        data_list.append(data_inv)
        data_list.append(data_indi)
        return data_list

    def get_stock_data_trading_num_daily(self):
        query="""
        select date, "거래량(주)"
        from stock_data_2000_2020_raw
        where stock_code = (
            SELECT stock_code
            FROM target_company_list
            WHERE (company_name = %s)
            AND (delisted_check = False)
        ) AND EXTRACT(DOW FROM "date") NOT IN (0,6)
        ORDER BY date DESC
        LIMIT 365;
        """

        #start_date = datetime.datetime(2019, 10, 12)
        #end_date = start_date - datetime.timedelta(days=30)
        data = {"x":[],"y":[],"type":"bar","yaxis":"y2","name":"거래량"}

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            #end_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')
            for each_row in cur: # 쿼리 실행 결과가 없다면, for loop에 들어가지지조차 않음
                data["x"].append(each_row[0].strftime('%Y-%m-%d'))
                data["y"].append(each_row[1])
        if data["x"] == []:
            return None
        return data

    def get_news_num_and_bankruptcy_ratio(self):
        query_ratio="""
        select * from bankruptcy_article_ratio_table_live
        where stock_code = (
                    SELECT stock_code
                    FROM target_company_list
                    WHERE (company_name = %s)
                    AND (delisted_check = False)
                );
        """

        table_name = ['bankruptcy_article_ratio_table_3m', 'bankruptcy_article_ratio_table_6m', 'bankruptcy_article_ratio_table_1y']
        data_ratio_3m_live = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","legendgroup": '3개월 전 예측',"mode": 'lines', "visible": 'legendonly',"line":{"dash":"dot"}}
        data_ratio_6m_live = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","legendgroup": '6개월 전 예측',"mode": 'lines',"line":{"dash":"dot"}}
        data_ratio_1y_live = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","legendgroup": '12개월 전 예측',"mode": 'lines', "visible": 'legendonly',"line":{"dash":"dot"}}
        data_ratio_live_list = [data_ratio_3m_live, data_ratio_6m_live, data_ratio_1y_live]
        data_ratio_3m_delisted = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","legendgroup": '3개월 전 예측',"mode": 'lines', "visible": 'legendonly',"line":{"dash":"dot"}}
        data_ratio_6m_delisted = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","legendgroup": '6개월 전 예측',"mode": 'lines',"line":{"dash":"dot"}}
        data_ratio_1y_delisted = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","legendgroup": '12개월 전 예측',"mode": 'lines', "visible": 'legendonly',"line":{"dash":"dot"}}
        data_ratio_delisted_list = [data_ratio_3m_delisted, data_ratio_6m_delisted, data_ratio_1y_delisted]

        for idx, each_table_name in enumerate(table_name):
            query_num_Nm_live_or_delisted = """
            select 
                (cast(sum(article.m1_bankruptcy_related_num) as decimal) / (sum(article.m1_bankruptcy_related_num) + sum(article.m1_normal_num))) as m1_ratio
                ,(cast(sum(article.m2_bankruptcy_related_num) as decimal) / (sum(article.m2_bankruptcy_related_num) + sum(article.m2_normal_num))) as m2_ratio
                ,(cast(sum(article.m3_bankruptcy_related_num) as decimal) / (sum(article.m3_bankruptcy_related_num) + sum(article.m3_normal_num))) as m3_ratio
                ,(cast(sum(article.m4_bankruptcy_related_num) as decimal) / (sum(article.m4_bankruptcy_related_num) + sum(article.m4_normal_num))) as m4_ratio
                ,(cast(sum(article.m5_bankruptcy_related_num) as decimal) / (sum(article.m5_bankruptcy_related_num) + sum(article.m5_normal_num))) as m5_ratio
                ,(cast(sum(article.m6_bankruptcy_related_num) as decimal) / (sum(article.m6_bankruptcy_related_num) + sum(article.m6_normal_num))) as m6_ratio
                ,(cast(sum(article.m7_bankruptcy_related_num) as decimal) / (sum(article.m7_bankruptcy_related_num) + sum(article.m7_normal_num))) as m7_ratio
                ,(cast(sum(article.m8_bankruptcy_related_num) as decimal) / (sum(article.m8_bankruptcy_related_num) + sum(article.m8_normal_num))) as m8_ratio
                ,(cast(sum(article.m9_bankruptcy_related_num) as decimal) / (sum(article.m9_bankruptcy_related_num) + sum(article.m9_normal_num))) as m9_ratio
                ,(cast(sum(article.m10_bankruptcy_related_num) as decimal) / (sum(article.m10_bankruptcy_related_num) + sum(article.m10_normal_num))) as m10_ratio
                ,(cast(sum(article.m11_bankruptcy_related_num) as decimal) / (sum(article.m11_bankruptcy_related_num) + sum(article.m11_normal_num))) as m11_ratio
                ,(cast(sum(article.m12_bankruptcy_related_num) as decimal) / (sum(article.m12_bankruptcy_related_num) + sum(article.m12_normal_num))) as m12_ratio
            from """ + each_table_name + """ article INNER JOIN target_company_list target ON article.stock_code = target.stock_code
            WHERE target.bankruptcy = %s;"""
            with connections['redshift'].cursor() as cur:
                cur.execute(query_num_Nm_live_or_delisted, ['0'])
                for each_row in cur:
                    for each_element in each_row:
                        data_ratio_live_list[idx]["y"].append(float(round(each_element,3)))
                cur.execute(query_num_Nm_live_or_delisted, ['1'])
                for each_row in cur:
                    for each_element in each_row:
                        data_ratio_delisted_list[idx]["y"].append(float(round(each_element,3)))
    
        #start_date = datetime.datetime(2019, 10, 12)
        #end_date = start_date - datetime.timedelta(days=30)
        data_num = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"bar","name":"전체 기사 수","yaxis":"y2"}
        data_ratio = {"x":["1개월 전","2개월 전","3개월 전","4개월 전","5개월 전","6개월 전","7개월 전","8개월 전","9개월 전","10개월 전","11개월 전","12개월 전"],"y":[],"type":"scatter","name":"부도기사비율"}
        data_list = []
        with connections['redshift'].cursor() as cur:
            cur.execute(query_ratio, [self.company_name])
            #end_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')
            for each_row in cur: # 쿼리 실행 결과가 없다면, for loop에 들어가지지조차 않음
                for idx in range(1,13):
                    data_ratio["y"].append(round(each_row[idx],3))
                for idx_2 in range(13,25):
                    data_num["y"].append(round(each_row[idx_2],3))
        data_list.append(data_ratio)
        data_list.append(data_num)
        return [data_list, data_ratio_live_list, data_ratio_delisted_list]

    def get_finance_data(self):
        query="""
            SELECT "회계년"
            ,ROUND("매출액(천원)"/100000,2) as "매출액(억원)"
            ,ROUND("당기순이익(천원)"/100000,2) as "당기순이익(억원)"  
            ,ROUND("영업이익(천원)"/100000,2) as "영업이익(억원)"
            ,"당기순이익률(p)"
            ,"영업이익률(p)"
            ,ROUND("총자산(천원)"/100000,2) as "총자산(억원)"
            ,ROUND("총부채(천원)"/100000,2) as "총부채(억원)"
            ,"부채비율(p)"
            ,ROUND("총부채(천원)"/"총자산(천원)",2) as "총자산부채비율(p)"
            FROM finance_data_1999_2020_raw
            WHERE stock_code = (
                SELECT stock_code
                FROM target_company_list
                WHERE (company_name = %s)
                AND (delisted_check = False)
            )
            ORDER BY "회계년" DESC
            LIMIT 4;
        """
        data = {"회계년":[]
            ,"매출액(억원)":[]
            ,"당기순이익(억원)":[]
            ,"영업이익(억원)":[]
            ,"당기순이익률(%)":[]
            ,"영업이익률(%)":[]
            ,"총자산(억원)":[]
            ,"총부채(억원)":[]
            ,"부채비율(%)":[]
            ,"총자산부채비율(%)":[]}

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            for each_row in cur:
                for idx, each_key in enumerate(data):
                    data[each_key].append(each_row[idx])
        return data

    def get_audit_report(self):
        query="""
            SELECT COALESCE((EXTRACT(YEAR FROM report_date) || '-' || EXTRACT(MONTH FROM report_date)),'-') AS YEAR_MONTH
                    ,CASE WHEN n_opinion THEN '예' ELSE '아니오' END	
            FROM dart_audit_report_data
            WHERE stock_code = (
                SELECT stock_code
                FROM target_company_list
                WHERE (company_name = %s)
                AND (delisted_check = False)
            )
            ORDER BY report_date DESC NULLS LAST
            LIMIT 3;
        """

        data = {"year_month":[]
                ,"n_opinion":[]}

        with connections['redshift'].cursor() as cur:
            cur.execute(query, [self.company_name])
            for each_row in cur:
                data["year_month"].append(each_row[0])
                data["n_opinion"].append(each_row[1])
        return data

    def model_prediction(self, year=2):
        column_for_table_onlyX_2 = [
            'stock_code'
            ,'Y-1_총자산(천원)'
            ,'Y-1_현금및현금성자산(천원)'
            ,'Y-1_총부채(천원)'
            ,'Y-1_총자본(천원)'
            ,'Y-1_매출액(천원)'
            ,'Y-1_당기순이익(천원)'
            ,'Y-1_세전계속사업이익(천원)'
            ,'Y-1_영업이익(천원)'
            ,'Y-1_매출총이익(천원)'
            ,'Y-1_차입금의존도(p)'
            ,'Y-1_당기순이익률(p)'
            ,'Y-1_세전계속사업이익률(p)'
            ,'Y-1_영업이익률(p)'
            ,'Y-1_매출총이익률(p)'
            ,'Y-1_총자산회전율(회)'
            ,'Y-1_총자산증가율(p)'
            ,'Y-1_총자산부채비율(p)'
            ,'Y-2_총자산(천원)'
            ,'Y-2_현금및현금성자산(천원)'
            ,'Y-2_총부채(천원)'
            ,'Y-2_총자본(천원)'
            ,'Y-2_매출액(천원)'
            ,'Y-2_당기순이익(천원)'
            ,'Y-2_세전계속사업이익(천원)'
            ,'Y-2_영업이익(천원)'
            ,'Y-2_매출총이익(천원)'
            ,'Y-2_차입금의존도(p)'
            ,'Y-2_당기순이익률(p)'
            ,'Y-2_세전계속사업이익률(p)'
            ,'Y-2_영업이익률(p)'
            ,'Y-2_매출총이익률(p)'
            ,'Y-2_총자산회전율(회)'
            ,'Y-2_총자산증가율(p)'
            ,'Y-2_총자산부채비율(p)'
            ,'R1-R2_외국인계매도비율변화'
            ,'R2-R3_외국인계매도비율변화'
            ,'R3-R4_외국인계매도비율변화'
            ,'R1-R2_외국인계매수비율변화'
            ,'R2-R3_외국인계매수비율변화'
            ,'R3-R4_외국인계매수비율변화'
            ,'R1-R2_기관계매도비율변화'
            ,'R2-R3_기관계매도비율변화'
            ,'R3-R4_기관계매도비율변화'
            ,'R1-R2_기관계매수비율변화'
            ,'R2-R3_기관계매수비율변화'
            ,'R3-R4_기관계매수비율변화'
            ,'수익률 (1개월)(p)'
            ,'수익률 (3개월)(p)'
            ,'수익률 (6개월)(p)'
            ,'부도기사비율_m1'
            ,'부도기사비율_m2'
            ,'부도기사비율_m3'
            ,'부도기사비율_m4'
            ,'부도기사비율_m5'
            ,'부도기사비율_m6'
            ,'부도기사비율_m7'
            ,'부도기사비율_m8'
            ,'부도기사비율_m9'
            ,'부도기사비율_m10'
            ,'부도기사비율_m11'
            ,'부도기사비율_m12'
            ,'n_opinion_in_r3'
            ,'m1_oil_price'
            ,'m2_oil_price'
            ,'m3_oil_price'
            ,'m4_oil_price'
            ,'m5_oil_price'
            ,'m6_oil_price'
            ,'m7_oil_price'
            ,'m8_oil_price'
            ,'m9_oil_price'
            ,'m10_oil_price'
            ,'m11_oil_price'
            ,'m12_oil_price'
            ,'m1_oil_price_roc_from_month_year_earlier'
            ,'m2_oil_price_roc_from_month_year_earlier'
            ,'m3_oil_price_roc_from_month_year_earlier'
            ,'m4_oil_price_roc_from_month_year_earlier'
            ,'m5_oil_price_roc_from_month_year_earlier'
            ,'m6_oil_price_roc_from_month_year_earlier'
            ,'m7_oil_price_roc_from_month_year_earlier'
            ,'m8_oil_price_roc_from_month_year_earlier'
            ,'m9_oil_price_roc_from_month_year_earlier'
            ,'m10_oil_price_roc_from_month_year_earlier'
            ,'m11_oil_price_roc_from_month_year_earlier'
            ,'m12_oil_price_roc_from_month_year_earlier'
            ,'m1_CD유통수익률(91일)(p)'
            ,'m2_CD유통수익률(91일)(p)'
            ,'m3_CD유통수익률(91일)(p)'
            ,'m4_CD유통수익률(91일)(p)'
            ,'m5_CD유통수익률(91일)(p)'
            ,'m6_CD유통수익률(91일)(p)'
            ,'m7_CD유통수익률(91일)(p)'
            ,'m8_CD유통수익률(91일)(p)'
            ,'m9_CD유통수익률(91일)(p)'
            ,'m10_CD유통수익률(91일)(p)'
            ,'m11_CD유통수익률(91일)(p)'
            ,'m12_CD유통수익률(91일)(p)'
            ,'m1_국고채(3년)(p)'
            ,'m2_국고채(3년)(p)'
            ,'m3_국고채(3년)(p)'
            ,'m4_국고채(3년)(p)'
            ,'m5_국고채(3년)(p)'
            ,'m6_국고채(3년)(p)'
            ,'m7_국고채(3년)(p)'
            ,'m8_국고채(3년)(p)'
            ,'m9_국고채(3년)(p)'
            ,'m10_국고채(3년)(p)'
            ,'m11_국고채(3년)(p)'
            ,'m12_국고채(3년)(p)'
            ,'m1_원달러환율(매매기준율)'
            ,'m2_원달러환율(매매기준율)'
            ,'m3_원달러환율(매매기준율)'
            ,'m4_원달러환율(매매기준율)'
            ,'m5_원달러환율(매매기준율)'
            ,'m6_원달러환율(매매기준율)'
            ,'m7_원달러환율(매매기준율)'
            ,'m8_원달러환율(매매기준율)'
            ,'m9_원달러환율(매매기준율)'
            ,'m10_원달러환율(매매기준율)'
            ,'m11_원달러환율(매매기준율)'
            ,'m12_원달러환율(매매기준율)'
            ,'y1_gdp_growth_rate'
            ,'y2_gdp_growth_rate'
            ,'y3_gdp_growth_rate'
        ]

        column_for_table_onlyX_3 = [
            'stock_code'
            ,'Y-1_총자산(천원)'
            ,'Y-1_현금및현금성자산(천원)'
            ,'Y-1_총부채(천원)'
            ,'Y-1_총자본(천원)'
            ,'Y-1_매출액(천원)'
            ,'Y-1_당기순이익(천원)'
            ,'Y-1_세전계속사업이익(천원)'
            ,'Y-1_영업이익(천원)'
            ,'Y-1_매출총이익(천원)'
            ,'Y-1_차입금의존도(p)'
            ,'Y-1_당기순이익률(p)'
            ,'Y-1_세전계속사업이익률(p)'
            ,'Y-1_영업이익률(p)'
            ,'Y-1_매출총이익률(p)'
            ,'Y-1_총자산회전율(회)'
            ,'Y-1_총자산증가율(p)'
            ,'Y-1_총자산부채비율(p)'
            ,'Y-2_총자산(천원)'
            ,'Y-2_현금및현금성자산(천원)'
            ,'Y-2_총부채(천원)'
            ,'Y-2_총자본(천원)'
            ,'Y-2_매출액(천원)'
            ,'Y-2_당기순이익(천원)'
            ,'Y-2_세전계속사업이익(천원)'
            ,'Y-2_영업이익(천원)'
            ,'Y-2_매출총이익(천원)'
            ,'Y-2_차입금의존도(p)'
            ,'Y-2_당기순이익률(p)'
            ,'Y-2_세전계속사업이익률(p)'
            ,'Y-2_영업이익률(p)'
            ,'Y-2_매출총이익률(p)'
            ,'Y-2_총자산회전율(회)'
            ,'Y-2_총자산증가율(p)'
            ,'Y-2_총자산부채비율(p)'
            ,'Y-3_총자산(천원)'
            ,'Y-3_현금및현금성자산(천원)'
            ,'Y-3_총부채(천원)'
            ,'Y-3_총자본(천원)'
            ,'Y-3_매출액(천원)'
            ,'Y-3_당기순이익(천원)'
            ,'Y-3_세전계속사업이익(천원)'
            ,'Y-3_영업이익(천원)'
            ,'Y-3_매출총이익(천원)'
            ,'Y-3_차입금의존도(p)'
            ,'Y-3_당기순이익률(p)'
            ,'Y-3_세전계속사업이익률(p)'
            ,'Y-3_영업이익률(p)'
            ,'Y-3_매출총이익률(p)'
            ,'Y-3_총자산회전율(회)'
            ,'Y-3_총자산증가율(p)'
            ,'Y-3_총자산부채비율(p)'
            ,'R1-R2_외국인계매도비율변화'
            ,'R2-R3_외국인계매도비율변화'
            ,'R3-R4_외국인계매도비율변화'
            ,'R1-R2_외국인계매수비율변화'
            ,'R2-R3_외국인계매수비율변화'
            ,'R3-R4_외국인계매수비율변화'
            ,'R1-R2_기관계매도비율변화'
            ,'R2-R3_기관계매도비율변화'
            ,'R3-R4_기관계매도비율변화'
            ,'R1-R2_기관계매수비율변화'
            ,'R2-R3_기관계매수비율변화'
            ,'R3-R4_기관계매수비율변화'
            ,'수익률 (1개월)(p)'
            ,'수익률 (3개월)(p)'
            ,'수익률 (6개월)(p)'
            ,'부도기사비율_m1'
            ,'부도기사비율_m2'
            ,'부도기사비율_m3'
            ,'부도기사비율_m4'
            ,'부도기사비율_m5'
            ,'부도기사비율_m6'
            ,'부도기사비율_m7'
            ,'부도기사비율_m8'
            ,'부도기사비율_m9'
            ,'부도기사비율_m10'
            ,'부도기사비율_m11'
            ,'부도기사비율_m12'
            ,'n_opinion_in_r3'
            ,'m1_oil_price'
            ,'m2_oil_price'
            ,'m3_oil_price'
            ,'m4_oil_price'
            ,'m5_oil_price'
            ,'m6_oil_price'
            ,'m7_oil_price'
            ,'m8_oil_price'
            ,'m9_oil_price'
            ,'m10_oil_price'
            ,'m11_oil_price'
            ,'m12_oil_price'
            ,'m1_oil_price_roc_from_month_year_earlier'
            ,'m2_oil_price_roc_from_month_year_earlier'
            ,'m3_oil_price_roc_from_month_year_earlier'
            ,'m4_oil_price_roc_from_month_year_earlier'
            ,'m5_oil_price_roc_from_month_year_earlier'
            ,'m6_oil_price_roc_from_month_year_earlier'
            ,'m7_oil_price_roc_from_month_year_earlier'
            ,'m8_oil_price_roc_from_month_year_earlier'
            ,'m9_oil_price_roc_from_month_year_earlier'
            ,'m10_oil_price_roc_from_month_year_earlier'
            ,'m11_oil_price_roc_from_month_year_earlier'
            ,'m12_oil_price_roc_from_month_year_earlier'
            ,'m1_CD유통수익률(91일)(p)'
            ,'m2_CD유통수익률(91일)(p)'
            ,'m3_CD유통수익률(91일)(p)'
            ,'m4_CD유통수익률(91일)(p)'
            ,'m5_CD유통수익률(91일)(p)'
            ,'m6_CD유통수익률(91일)(p)'
            ,'m7_CD유통수익률(91일)(p)'
            ,'m8_CD유통수익률(91일)(p)'
            ,'m9_CD유통수익률(91일)(p)'
            ,'m10_CD유통수익률(91일)(p)'
            ,'m11_CD유통수익률(91일)(p)'
            ,'m12_CD유통수익률(91일)(p)'
            ,'m1_국고채(3년)(p)'
            ,'m2_국고채(3년)(p)'
            ,'m3_국고채(3년)(p)'
            ,'m4_국고채(3년)(p)'
            ,'m5_국고채(3년)(p)'
            ,'m6_국고채(3년)(p)'
            ,'m7_국고채(3년)(p)'
            ,'m8_국고채(3년)(p)'
            ,'m9_국고채(3년)(p)'
            ,'m10_국고채(3년)(p)'
            ,'m11_국고채(3년)(p)'
            ,'m12_국고채(3년)(p)'
            ,'m1_원달러환율(매매기준율)'
            ,'m2_원달러환율(매매기준율)'
            ,'m3_원달러환율(매매기준율)'
            ,'m4_원달러환율(매매기준율)'
            ,'m5_원달러환율(매매기준율)'
            ,'m6_원달러환율(매매기준율)'
            ,'m7_원달러환율(매매기준율)'
            ,'m8_원달러환율(매매기준율)'
            ,'m9_원달러환율(매매기준율)'
            ,'m10_원달러환율(매매기준율)'
            ,'m11_원달러환율(매매기준율)'
            ,'m12_원달러환율(매매기준율)'
            ,'y1_gdp_growth_rate'
            ,'y2_gdp_growth_rate'
            ,'y3_gdp_growth_rate'
        ]

        dict_for_insert_into_dataframe = {}

        if year == 3:
            column_for_table_onlyX = column_for_table_onlyX_3
        elif year == 2:
            column_for_table_onlyX = column_for_table_onlyX_2
        
        for each_key in column_for_table_onlyX:
            dict_for_insert_into_dataframe[each_key] = ''


        query_finance_live = """
            SELECT
            stock_code
            ,"총자산(천원)"
            ,"현금및현금성자산(천원)"
            ,"총부채(천원)"
            ,"총자본(천원)"
            ,"매출액(천원)"
            ,"당기순이익(천원)"
            ,"세전계속사업이익(천원)"
            ,"영업이익(천원)"
            ,"매출총이익(천원)"
            ,"차입금의존도(p)"
            ,"당기순이익률(p)"
            ,"세전계속사업이익률(p)"
            ,"영업이익률(p)"
            ,"매출총이익률(p)"
            ,"총자산회전율(회)"
            ,"총자산증가율(전년동기)(p)"
            ,"총부채(천원)"/"총자산(천원)" AS "총자산부채비율(p)"
            FROM finance_data_1999_2020_raw
            WHERE stock_code = (
                SELECT stock_code
                FROM target_company_list
                WHERE (company_name = %s)
                AND (delisted_check = False)
            )
            ORDER BY "회계년" DESC
            LIMIT %s;
        """

        query_sell = """
            SELECT r1.stock_code
                    ,r1.R1_외국인계매도비율 - r2.R2_외국인계매도비율 AS "R1-R2_외국인계매도비율변화"
                    ,r2.R2_외국인계매도비율 - r3.R3_외국인계매도비율 AS "R2-R3_외국인계매도비율변화"
                    ,r3.R3_외국인계매도비율 - r4.R4_외국인계매도비율 AS "R3-R4_외국인계매도비율변화"
                    ,r1.R1_기관계매도비율 - r2.R2_기관계매도비율 AS "R1-R2_기관계매도비율변화"
                    ,r2.R2_기관계매도비율 - r3.R3_기관계매도비율 AS "R2-R3_기관계매도비율변화"
                    ,r3.R3_기관계매도비율 - r4.R4_기관계매도비율 AS "R3-R4_기관계매도비율변화"
            FROM (
                SELECT stock_data.stock_code
                ,COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R1_외국인계매도비율"
                ,COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R1_기관계매도비율"
                FROM stock_data_2000_2020_raw stock_data
                WHERE stock_code = (SELECT stock_code
                                    FROM target_company_list
                                    WHERE company_name = %s
                                    AND (delisted_check = False))
                AND stock_data."종가(원)" IS NOT NULL
                AND stock_data.date BETWEEN ('2019-12-31'-30) AND '2019-12-31'
                GROUP BY stock_data.stock_code
            ) r1 INNER JOIN (
                SELECT stock_data.stock_code
                    ,COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R2_외국인계매도비율"
                    ,COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R2_기관계매도비율"
                    FROM stock_data_2000_2020_raw stock_data
                    WHERE stock_code = (SELECT stock_code
                                        FROM target_company_list
                                        WHERE company_name = %s
                                        AND (delisted_check = False))
                    AND stock_data."종가(원)" IS NOT NULL
                    AND stock_data.date BETWEEN ('2019-12-31'-60) AND ('2019-12-31'-31)
                    GROUP BY stock_data.stock_code
            ) r2 ON r1.stock_code = r2.stock_code
            INNER JOIN (
                SELECT stock_data.stock_code
                    ,COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R3_외국인계매도비율"
                    ,COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R3_기관계매도비율"
                    FROM stock_data_2000_2020_raw stock_data
                    WHERE stock_code = (SELECT stock_code
                                        FROM target_company_list
                                        WHERE company_name = %s
                                        AND (delisted_check = False))
                    AND stock_data."종가(원)" IS NOT NULL
                    AND stock_data.date BETWEEN ('2019-12-31'-90) AND ('2019-12-31'-61)
                    GROUP BY stock_data.stock_code
            ) r3 ON r1.stock_code = r3.stock_code
            INNER JOIN (
                SELECT stock_data.stock_code
                    ,COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R4_외국인계매도비율"
                    ,COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매도수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매도수량(개인)(주)"),0)+COALESCE(sum(stock_data."매도수량(기관계)(주)"),0)) as "R4_기관계매도비율"
                    FROM stock_data_2000_2020_raw stock_data
                    WHERE stock_code = (SELECT stock_code
                                        FROM target_company_list
                                        WHERE company_name = %s
                                        AND (delisted_check = False))
                    AND stock_data."종가(원)" IS NOT NULL
                    AND stock_data.date BETWEEN ('2019-12-31'-120) AND ('2019-12-31'-91)
                    GROUP BY stock_data.stock_code
            ) r4 ON r1.stock_code = r4.stock_code;
        """

        query_buy = """
            SELECT r1.stock_code
                ,r1.R1_외국인계매수비율 - r2.R2_외국인계매수비율 AS "R1-R2_외국인계매수비율변화"
                ,r2.R2_외국인계매수비율 - r3.R3_외국인계매수비율 AS "R2-R3_외국인계매수비율변화"
                ,r3.R3_외국인계매수비율 - r4.R4_외국인계매수비율 AS "R3-R4_외국인계매수비율변화"
                ,r1.R1_기관계매수비율 - r2.R2_기관계매수비율 AS "R1-R2_기관계매수비율변화"
                ,r2.R2_기관계매수비율 - r3.R3_기관계매수비율 AS "R2-R3_기관계매수비율변화"
                ,r3.R3_기관계매수비율 - r4.R4_기관계매수비율 AS "R3-R4_기관계매수비율변화"
            FROM (
                SELECT stock_data.stock_code
                ,COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R1_외국인계매수비율"
                ,COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R1_기관계매수비율"
                FROM stock_data_2000_2020_raw stock_data
                WHERE stock_code = (SELECT stock_code
                                    FROM target_company_list
                                    WHERE company_name = %s
                                    AND (delisted_check = False))
                AND stock_data."종가(원)" IS NOT NULL
                AND stock_data.date BETWEEN ('2019-12-31'-30) AND '2019-12-31'
                GROUP BY stock_data.stock_code
            ) r1 INNER JOIN (
                SELECT stock_data.stock_code
                    ,COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R2_외국인계매수비율"
                    ,COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R2_기관계매수비율"
                    FROM stock_data_2000_2020_raw stock_data
                    WHERE stock_code = (SELECT stock_code
                                        FROM target_company_list
                                        WHERE company_name = %s
                                        AND (delisted_check = False))
                    AND stock_data."종가(원)" IS NOT NULL
                    AND stock_data.date BETWEEN ('2019-12-31'-60) AND ('2019-12-31'-31)
                    GROUP BY stock_data.stock_code
            ) r2 ON r1.stock_code = r2.stock_code
            INNER JOIN (
                SELECT stock_data.stock_code
                    ,COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R3_외국인계매수비율"
                    ,COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R3_기관계매수비율"
                    FROM stock_data_2000_2020_raw stock_data
                    WHERE stock_code = (SELECT stock_code
                                        FROM target_company_list
                                        WHERE company_name = %s
                                        AND (delisted_check = False))
                    AND stock_data."종가(원)" IS NOT NULL
                    AND stock_data.date BETWEEN ('2019-12-31'-90) AND ('2019-12-31'-61)
                    GROUP BY stock_data.stock_code
            ) r3 ON r1.stock_code = r3.stock_code
            INNER JOIN (
                SELECT stock_data.stock_code
                    ,COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R4_외국인계매수비율"
                    ,COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)/(COALESCE(sum(stock_data."매수수량(외국인계)(주)"),0)+COALESCE(sum(stock_data."매수수량(개인)(주)"),0)+COALESCE(sum(stock_data."매수수량(기관계)(주)"),0)) as "R4_기관계매수비율"
                    FROM stock_data_2000_2020_raw stock_data
                    WHERE stock_code = (SELECT stock_code
                                        FROM target_company_list
                                        WHERE company_name = %s
                                        AND (delisted_check = False))
                    AND stock_data."종가(원)" IS NOT NULL
                    AND stock_data.date BETWEEN ('2019-12-31'-120) AND ('2019-12-31'-91)
                    GROUP BY stock_data.stock_code
            ) r4 ON r1.stock_code = r4.stock_code;
        """

        query_earnings_rate = """
            SELECT stock_code, "수익률 (1개월)(p)", "수익률 (3개월)(p)", "수익률 (6개월)(p)"
            FROM stock_data_2000_2020_raw
            WHERE stock_code = (SELECT stock_code
                                FROM target_company_list
                                WHERE company_name = %s
                                AND (delisted_check = False))
            AND date = '2019-12-31';
        """

        query_article_ratio = """
            SELECT *
            FROM bankruptcy_article_ratio_table_live
            WHERE stock_code = (
                SELECT stock_code
                FROM target_company_list
                WHERE (company_name = %s)
                AND (delisted_check = False)
            );
        """
        
        query_audit_report = """
            SELECT n_opinion FROM dart_audit_report_data
            WHERE stock_code = (
                SELECT stock_code
                FROM target_company_list
                WHERE (company_name = %s)
                AND (delisted_check = False))
            ORDER BY report_date DESC NULLS LAST
            LIMIT 3;
        """

        query_oil = """
            SELECT "Dubai(dollar)"
            FROM oil_price_dubai_month
            WHERE ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date <= add_months(%s,%s))
            AND ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date > add_months(%s,%s));
        """

        query_oil_price_roc = """
            SELECT "전년동월대비_가격증감율"
            FROM oil_price_dubai_month
            WHERE ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date <= add_months(%s,%s))
            AND ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date > add_months(%s,%s));
        """
        
        query_cd = """
            SELECT "CD유통수익률(91일)(p)"
            FROM marcoeco_data_from_bok
            WHERE ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date <= add_months(%s,%s))
            AND ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date > add_months(%s,%s));
        """
        
        query_bond = """
            SELECT "국고채(3년)(p)"
            FROM marcoeco_data_from_bok
            WHERE ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date <= add_months(%s,%s))
            AND ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date > add_months(%s,%s));
        """
        
        query_exchange_rate = """
            SELECT "원달러환율(매매기준율)"
            FROM marcoeco_data_from_bok
            WHERE ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date <= add_months(%s,%s))
            AND ((date_trunc('month', DATEADD(week,1,DATEADD(month,1,TO_DATE(year_month, 'YYYY-MM')))))::date > add_months(%s,%s));
        """
        
        query_gdp_growth_rate = """
            SELECT gdp_growth_rate
            FROM gdp_growth_rate
            WHERE year = TO_CHAR(DATEADD(year,%s,%s), 'YYYY');
        """
   
        with connections['redshift'].cursor() as cur:
            cur.execute(query_finance_live, [self.company_name, year])
            for idx, each_row in enumerate(cur):
                if idx == 0:
                    dict_for_insert_into_dataframe['stock_code'] = each_row[0]
                    dict_for_insert_into_dataframe["Y-1_총자산(천원)"] = each_row[1]
                    dict_for_insert_into_dataframe["Y-1_현금및현금성자산(천원)"] = each_row[2]
                    dict_for_insert_into_dataframe["Y-1_총부채(천원)"] = each_row[3]
                    dict_for_insert_into_dataframe["Y-1_총자본(천원)"] = each_row[4]
                    dict_for_insert_into_dataframe["Y-1_매출액(천원)"] = each_row[5]
                    dict_for_insert_into_dataframe["Y-1_당기순이익(천원)"] = each_row[6]
                    dict_for_insert_into_dataframe["Y-1_세전계속사업이익(천원)"] = each_row[7]
                    dict_for_insert_into_dataframe["Y-1_영업이익(천원)"] = each_row[8]
                    dict_for_insert_into_dataframe["Y-1_매출총이익(천원)"] = each_row[9]
                    dict_for_insert_into_dataframe["Y-1_차입금의존도(p)"] = each_row[10]
                    dict_for_insert_into_dataframe["Y-1_당기순이익률(p)"] = each_row[11]
                    dict_for_insert_into_dataframe["Y-1_세전계속사업이익률(p)"] = each_row[12]
                    dict_for_insert_into_dataframe["Y-1_영업이익률(p)"] = each_row[13]
                    dict_for_insert_into_dataframe["Y-1_매출총이익률(p)"] = each_row[14]
                    dict_for_insert_into_dataframe["Y-1_총자산회전율(회)"] = each_row[15]
                    dict_for_insert_into_dataframe["Y-1_총자산증가율(p)"] = each_row[16]
                    dict_for_insert_into_dataframe["Y-1_총자산부채비율(p)"] = each_row[17]
                elif idx == 1:
                    dict_for_insert_into_dataframe["Y-2_총자산(천원)"] = each_row[1]
                    dict_for_insert_into_dataframe["Y-2_현금및현금성자산(천원)"] = each_row[2]
                    dict_for_insert_into_dataframe["Y-2_총부채(천원)"] = each_row[3]
                    dict_for_insert_into_dataframe["Y-2_총자본(천원)"] = each_row[4]
                    dict_for_insert_into_dataframe["Y-2_매출액(천원)"] = each_row[5]
                    dict_for_insert_into_dataframe["Y-2_당기순이익(천원)"] = each_row[6]
                    dict_for_insert_into_dataframe["Y-2_세전계속사업이익(천원)"] = each_row[7]
                    dict_for_insert_into_dataframe["Y-2_영업이익(천원)"] = each_row[8]
                    dict_for_insert_into_dataframe["Y-2_매출총이익(천원)"] = each_row[9]
                    dict_for_insert_into_dataframe["Y-2_차입금의존도(p)"] = each_row[10]
                    dict_for_insert_into_dataframe["Y-2_당기순이익률(p)"] = each_row[11]
                    dict_for_insert_into_dataframe["Y-2_세전계속사업이익률(p)"] = each_row[12]
                    dict_for_insert_into_dataframe["Y-2_영업이익률(p)"] = each_row[13]
                    dict_for_insert_into_dataframe["Y-2_매출총이익률(p)"] = each_row[14]
                    dict_for_insert_into_dataframe["Y-2_총자산회전율(회)"] = each_row[15]
                    dict_for_insert_into_dataframe["Y-2_총자산증가율(p)"] = each_row[16]
                    dict_for_insert_into_dataframe["Y-2_총자산부채비율(p)"] = each_row[17]
                elif idx == 2:
                    dict_for_insert_into_dataframe["Y-3_총자산(천원)"] = each_row[1]
                    dict_for_insert_into_dataframe["Y-3_현금및현금성자산(천원)"] = each_row[2]
                    dict_for_insert_into_dataframe["Y-3_총부채(천원)"] = each_row[3]
                    dict_for_insert_into_dataframe["Y-3_총자본(천원)"] = each_row[4]
                    dict_for_insert_into_dataframe["Y-3_매출액(천원)"] = each_row[5]
                    dict_for_insert_into_dataframe["Y-3_당기순이익(천원)"] = each_row[6]
                    dict_for_insert_into_dataframe["Y-3_세전계속사업이익(천원)"] = each_row[7]
                    dict_for_insert_into_dataframe["Y-3_영업이익(천원)"] = each_row[8]
                    dict_for_insert_into_dataframe["Y-3_매출총이익(천원)"] = each_row[9]
                    dict_for_insert_into_dataframe["Y-3_차입금의존도(p)"] = each_row[10]
                    dict_for_insert_into_dataframe["Y-3_당기순이익률(p)"] = each_row[11]
                    dict_for_insert_into_dataframe["Y-3_세전계속사업이익률(p)"] = each_row[12]
                    dict_for_insert_into_dataframe["Y-3_영업이익률(p)"] = each_row[13]
                    dict_for_insert_into_dataframe["Y-3_매출총이익률(p)"] = each_row[14]
                    dict_for_insert_into_dataframe["Y-3_총자산회전율(회)"] = each_row[15]
                    dict_for_insert_into_dataframe["Y-3_총자산증가율(p)"] = each_row[16]
                    dict_for_insert_into_dataframe["Y-3_총자산부채비율(p)"] = each_row[17]

        with connections['redshift'].cursor() as cur:
            cur.execute(query_sell, [self.company_name, self.company_name, self.company_name, self.company_name])
            for each in cur:
                dict_for_insert_into_dataframe["R1-R2_외국인계매도비율변화"] = each[1]
                dict_for_insert_into_dataframe["R2-R3_외국인계매도비율변화"] = each[2]
                dict_for_insert_into_dataframe["R3-R4_외국인계매도비율변화"] = each[3]
                dict_for_insert_into_dataframe["R1-R2_기관계매도비율변화"] = each[4]
                dict_for_insert_into_dataframe["R2-R3_기관계매도비율변화"] = each[5]
                dict_for_insert_into_dataframe["R3-R4_기관계매도비율변화"] = each[6]

        with connections['redshift'].cursor() as cur:           
            cur.execute(query_buy, [self.company_name, self.company_name, self.company_name, self.company_name])
            for each in cur:
                dict_for_insert_into_dataframe["R1-R2_외국인계매수비율변화"] = each[1]
                dict_for_insert_into_dataframe["R2-R3_외국인계매수비율변화"] = each[2]
                dict_for_insert_into_dataframe["R3-R4_외국인계매수비율변화"] = each[3]
                dict_for_insert_into_dataframe["R1-R2_기관계매수비율변화"] = each[4]
                dict_for_insert_into_dataframe["R2-R3_기관계매수비율변화"] = each[5]
                dict_for_insert_into_dataframe["R3-R4_기관계매수비율변화"] = each[6]

        with connections['redshift'].cursor() as cur:       
            cur.execute(query_earnings_rate, [self.company_name])
            for each in cur:
                dict_for_insert_into_dataframe['수익률 (1개월)(p)'] = each[1]
                dict_for_insert_into_dataframe['수익률 (3개월)(p)'] = each[2]
                dict_for_insert_into_dataframe['수익률 (6개월)(p)'] = each[3]

        with connections['redshift'].cursor() as cur:      
            cur.execute(query_article_ratio, [self.company_name])
            for each in cur:
                dict_for_insert_into_dataframe['부도기사비율_m1'] = each[1]
                dict_for_insert_into_dataframe['부도기사비율_m2'] = each[2]
                dict_for_insert_into_dataframe['부도기사비율_m3'] = each[3]
                dict_for_insert_into_dataframe['부도기사비율_m4'] = each[4]
                dict_for_insert_into_dataframe['부도기사비율_m5'] = each[5]
                dict_for_insert_into_dataframe['부도기사비율_m6'] = each[6]
                dict_for_insert_into_dataframe['부도기사비율_m7'] = each[7]
                dict_for_insert_into_dataframe['부도기사비율_m8'] = each[8]
                dict_for_insert_into_dataframe['부도기사비율_m9'] = each[9]
                dict_for_insert_into_dataframe['부도기사비율_m10'] = each[10]
                dict_for_insert_into_dataframe['부도기사비율_m11'] = each[11]
                dict_for_insert_into_dataframe['부도기사비율_m12'] = each[12]

        with connections['redshift'].cursor() as cur:    
            cur.execute(query_audit_report, [self.company_name])
            list_for_audit_check = []
            for each in cur:
                list_for_audit_check.append(each[0])
            dict_for_insert_into_dataframe['n_opinion_in_r3'] = True in list_for_audit_check 

        for each_idx in range(0,12):
            with connections['redshift'].cursor() as cur:
                cur.execute(query_oil, ('2019-12-31', 0-each_idx, '2019-12-31', -1-each_idx))
                for each in cur:
                    dict_for_insert_into_dataframe[column_for_table_onlyX[63 + 17*(year-2) + each_idx]] = each[0]
            with connections['redshift'].cursor() as cur:                    
                cur.execute(query_oil_price_roc, ('2019-12-31', 0-each_idx, '2019-12-31', -1-each_idx))
                for each in cur:
                    dict_for_insert_into_dataframe[column_for_table_onlyX[75 + 17*(year-2) + each_idx]] = each[0]
            with connections['redshift'].cursor() as cur:                
                cur.execute(query_cd, ('2019-12-31', 0-each_idx, '2019-12-31', -1-each_idx))
                for each in cur:
                    dict_for_insert_into_dataframe[column_for_table_onlyX[87 + 17*(year-2) + each_idx]] = each[0]
            with connections['redshift'].cursor() as cur:                    
                cur.execute(query_bond, ('2019-12-31', 0-each_idx, '2019-12-31', -1-each_idx))
                for each in cur:
                    dict_for_insert_into_dataframe[column_for_table_onlyX[99 + 17*(year-2) + each_idx]] = each[0]
            with connections['redshift'].cursor() as cur:                    
                cur.execute(query_exchange_rate, ('2019-12-31', 0-each_idx, '2019-12-31', -1-each_idx))
                for each in cur:
                    dict_for_insert_into_dataframe[column_for_table_onlyX[111 + 17*(year-2) + each_idx]] = each[0]
                    
            for each_idx in range(0,3):
                with connections['redshift'].cursor() as cur:
                    cur.execute(query_gdp_growth_rate, (-1-each_idx, '2019-12-31'))
                    for each in cur:
                        dict_for_insert_into_dataframe[column_for_table_onlyX[123 + 17*(year-2) + each_idx]] = each[0]


        live_dataframe = pd.DataFrame(dict_for_insert_into_dataframe, index = [0])
        live_dataframe.set_index('stock_code', inplace=True)

        none_check = 0
        for each in live_dataframe.columns:
            if live_dataframe[each][0] == None:
                none_check = 1
        
        if none_check == 1:
            return None

        with open('./main/static/main/best_hp_tuned_model_6m.pickle', 'rb') as f:
            best_model_6m = pickle.load(f)

        with open('./main/static/main/best_hp_tuned_model_3m.pickle', 'rb') as f:
            best_model_3m = pickle.load(f)

        with open('./main/static/main/best_hp_tuned_model_1y.pickle', 'rb') as f:
            best_model_1y = pickle.load(f)

        result_6m = best_model_6m.predict(live_dataframe)
        proba_6m = best_model_6m.predict_proba(live_dataframe)

        result_3m = best_model_3m.predict(live_dataframe)
        proba_3m = best_model_3m.predict_proba(live_dataframe)
        
        result_1y = best_model_1y.predict(live_dataframe)
        proba_1y = best_model_1y.predict_proba(live_dataframe)
        
        data = {'result_6m':str(result_6m[0]), 'proba_6m_false':round(proba_6m[0][0]*100,2), 'proba_6m_true':round(proba_6m[0][1]*100,2)
                ,'result_3m':str(result_3m[0]), 'proba_3m_false':round(proba_3m[0][0]*100,2), 'proba_3m_true':round(proba_3m[0][1]*100,2)
                ,'result_1y':str(result_1y[0]), 'proba_1y_false':round(proba_1y[0][0]*100,2), 'proba_1y_true':round(proba_1y[0][1]*100,2)
        }

        return data


        

