-- 뉴스 기사 테이블 만들기
DROP TABLE IF EXISTS news_data_deduplicated_main CASCADE;
CREATE TABLE news_data_deduplicated_main(
	article_url VARCHAR NOT NULL PRIMARY KEY
	,published_date DATE NOT NULL
	,bankruptcy_article_check Boolean
	,tag_stock_code VARCHAR(10000)
);

COPY news_data_deduplicated_main
from 's3://for-bankruptcy-prediction/news_data_deduplicated_minimal_main_tag_json.csv'
credentials 'aws_access_key_id=(적절한 키 입력);aws_secret_access_key=(적절한 키 입력))'
IGNOREHEADER 1
CSV;

-- 학습용 뉴스 기사 부도비율 테이블들(3개월 예측, 6개월 예측, 1년 예측) 만들기
DROP TABLE IF EXISTS bankruptcy_article_ratio_table_3m;
CREATE TABLE bankruptcy_article_ratio_table_3m(
		stock_code char(6) NOT NULL
        ,FOREIGN KEY (stock_code) REFERENCES target_company_list(stock_code)
        ,m1 real
        ,m2 real
        ,m3 real
        ,m4 real
        ,m5 real
        ,m6 real
        ,m7 real
        ,m8 real
        ,m9 real
        ,m10 real
        ,m11 real
        ,m12 real
        ,m1_normal_num integer
        ,m2_normal_num integer
        ,m3_normal_num integer
        ,m4_normal_num integer
        ,m5_normal_num integer
        ,m6_normal_num integer
        ,m7_normal_num integer
        ,m8_normal_num integer
        ,m9_normal_num integer
        ,m10_normal_num integer
        ,m11_normal_num integer
        ,m12_normal_num integer
        ,m1_bankruptcy_related_num integer
        ,m2_bankruptcy_related_num integer
        ,m3_bankruptcy_related_num integer
        ,m4_bankruptcy_related_num integer
        ,m5_bankruptcy_related_num integer
        ,m6_bankruptcy_related_num integer
        ,m7_bankruptcy_related_num integer
        ,m8_bankruptcy_related_num integer
        ,m9_bankruptcy_related_num integer
        ,m10_bankruptcy_related_num integer
        ,m11_bankruptcy_related_num integer
        ,m12_bankruptcy_related_num integer
	);

DROP TABLE IF EXISTS bankruptcy_article_ratio_table_6m;
CREATE TABLE bankruptcy_article_ratio_table_6m(
		stock_code char(6) NOT NULL
        ,FOREIGN KEY (stock_code) REFERENCES target_company_list(stock_code)
        ,m1 real
        ,m2 real
        ,m3 real
        ,m4 real
        ,m5 real
        ,m6 real
        ,m7 real
        ,m8 real
        ,m9 real
        ,m10 real
        ,m11 real
        ,m12 real
        ,m1_normal_num integer
        ,m2_normal_num integer
        ,m3_normal_num integer
        ,m4_normal_num integer
        ,m5_normal_num integer
        ,m6_normal_num integer
        ,m7_normal_num integer
        ,m8_normal_num integer
        ,m9_normal_num integer
        ,m10_normal_num integer
        ,m11_normal_num integer
        ,m12_normal_num integer
        ,m1_bankruptcy_related_num integer
        ,m2_bankruptcy_related_num integer
        ,m3_bankruptcy_related_num integer
        ,m4_bankruptcy_related_num integer
        ,m5_bankruptcy_related_num integer
        ,m6_bankruptcy_related_num integer
        ,m7_bankruptcy_related_num integer
        ,m8_bankruptcy_related_num integer
        ,m9_bankruptcy_related_num integer
        ,m10_bankruptcy_related_num integer
        ,m11_bankruptcy_related_num integer
        ,m12_bankruptcy_related_num integer
	);

DROP TABLE IF EXISTS bankruptcy_article_ratio_table_1y;
CREATE TABLE bankruptcy_article_ratio_table_1y(
		stock_code char(6) NOT NULL
        ,FOREIGN KEY (stock_code) REFERENCES target_company_list(stock_code)
        ,m1 real
        ,m2 real
        ,m3 real
        ,m4 real
        ,m5 real
        ,m6 real
        ,m7 real
        ,m8 real
        ,m9 real
        ,m10 real
        ,m11 real
        ,m12 real
        ,m1_normal_num integer
        ,m2_normal_num integer
        ,m3_normal_num integer
        ,m4_normal_num integer
        ,m5_normal_num integer
        ,m6_normal_num integer
        ,m7_normal_num integer
        ,m8_normal_num integer
        ,m9_normal_num integer
        ,m10_normal_num integer
        ,m11_normal_num integer
        ,m12_normal_num integer
        ,m1_bankruptcy_related_num integer
        ,m2_bankruptcy_related_num integer
        ,m3_bankruptcy_related_num integer
        ,m4_bankruptcy_related_num integer
        ,m5_bankruptcy_related_num integer
        ,m6_bankruptcy_related_num integer
        ,m7_bankruptcy_related_num integer
        ,m8_bankruptcy_related_num integer
        ,m9_bankruptcy_related_num integer
        ,m10_bankruptcy_related_num integer
        ,m11_bankruptcy_related_num integer
        ,m12_bankruptcy_related_num integer
	);

COPY bankruptcy_article_ratio_table_3m
from 's3://for-bankruptcy-prediction/bankruptcy_article_ratio_table_3m.csv'
credentials 'aws_access_key_id=(적절한 키 입력);aws_secret_access_key=(적절한 키 입력))'
IGNOREHEADER 1
CSV;

COPY bankruptcy_article_ratio_table_6m
from 's3://for-bankruptcy-prediction/bankruptcy_article_ratio_table_6m.csv'
credentials 'aws_access_key_id=(적절한 키 입력);aws_secret_access_key=(적절한 키 입력))'
IGNOREHEADER 1
CSV;

COPY bankruptcy_article_ratio_table_1y
from 's3://for-bankruptcy-prediction/bankruptcy_article_ratio_table_1y.csv'
credentials 'aws_access_key_id=(적절한 키 입력);aws_secret_access_key=(적절한 키 입력))'
IGNOREHEADER 1
CSV;


-- 1년 예측 모델 학습용 거시 데이터 테이블 만들기
-- 3개월, 6개월 테이블도 동일한 코드로 생성
DROP TABLE IF EXISTS table_for_dt_based_model_1y_macroeco;
CREATE TABLE table_for_dt_based_model_1y_macroeco(
	stock_code char(6)
    ,FOREIGN KEY (stock_code) REFERENCES target_company_list(stock_code)
	,"m1_oil_price" real
	,"m2_oil_price" real
	,"m3_oil_price" real
	,"m4_oil_price" real
	,"m5_oil_price" real
	,"m6_oil_price" real
	,"m7_oil_price" real
	,"m8_oil_price" real
	,"m9_oil_price" real
	,"m10_oil_price" real
	,"m11_oil_price" real
	,"m12_oil_price" real
    ,"m1_oil_price_roc_from_month_year_earlier" real
	,"m2_oil_price_roc_from_month_year_earlier" real
	,"m3_oil_price_roc_from_month_year_earlier" real
	,"m4_oil_price_roc_from_month_year_earlier" real
	,"m5_oil_price_roc_from_month_year_earlier" real
	,"m6_oil_price_roc_from_month_year_earlier" real
	,"m7_oil_price_roc_from_month_year_earlier" real
	,"m8_oil_price_roc_from_month_year_earlier" real
	,"m9_oil_price_roc_from_month_year_earlier" real
	,"m10_oil_price_roc_from_month_year_earlier" real
	,"m11_oil_price_roc_from_month_year_earlier" real
	,"m12_oil_price_roc_from_month_year_earlier" real
    ,"m1_CD유통수익률(91일)(p)" real
    ,"m2_CD유통수익률(91일)(p)" real
    ,"m3_CD유통수익률(91일)(p)" real
    ,"m4_CD유통수익률(91일)(p)" real
    ,"m5_CD유통수익률(91일)(p)" real
    ,"m6_CD유통수익률(91일)(p)" real
    ,"m7_CD유통수익률(91일)(p)" real
    ,"m8_CD유통수익률(91일)(p)" real
    ,"m9_CD유통수익률(91일)(p)" real
    ,"m10_CD유통수익률(91일)(p)" real
    ,"m11_CD유통수익률(91일)(p)" real
    ,"m12_CD유통수익률(91일)(p)" real
    ,"m1_국고채(3년)(p)" real
    ,"m2_국고채(3년)(p)" real
    ,"m3_국고채(3년)(p)" real
    ,"m4_국고채(3년)(p)" real
    ,"m5_국고채(3년)(p)" real
    ,"m6_국고채(3년)(p)" real
    ,"m7_국고채(3년)(p)" real
    ,"m8_국고채(3년)(p)" real
    ,"m9_국고채(3년)(p)" real
    ,"m10_국고채(3년)(p)" real
    ,"m11_국고채(3년)(p)" real
    ,"m12_국고채(3년)(p)" real
    ,"m1_원달러환율(매매기준율)" real
    ,"m2_원달러환율(매매기준율)" real
    ,"m3_원달러환율(매매기준율)" real
    ,"m4_원달러환율(매매기준율)" real
    ,"m5_원달러환율(매매기준율)" real
    ,"m6_원달러환율(매매기준율)" real
    ,"m7_원달러환율(매매기준율)" real
    ,"m8_원달러환율(매매기준율)" real
    ,"m9_원달러환율(매매기준율)" real
    ,"m10_원달러환율(매매기준율)" real
    ,"m11_원달러환율(매매기준율)" real
    ,"m12_원달러환율(매매기준율)" real
    ,"y1_gdp_growth_rate" real
    ,"y2_gdp_growth_rate" real
    ,"y3_gdp_growth_rate" real
);

COPY table_for_dt_based_model_1y_macroeco
from 's3://for-bankruptcy-prediction/table_for_dt_based_model_1y_macroeco.csv'
credentials 'aws_access_key_id=(적절한 키 입력);aws_secret_access_key=(적절한 키 입력))'
IGNOREHEADER 1
CSV;
--