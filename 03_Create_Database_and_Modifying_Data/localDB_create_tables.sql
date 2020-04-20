-- 뉴스 기사에, 해당 뉴스 기사에 관련된 기업의 종목코드를 태그로 붙임
CREATE OR REPLACE PROCEDURE sp_add_tags_on_news()
AS $$
DECLARE
	url_row record;
	tag_array_stock_code text[];
	counter integer := 0;
BEGIN
	FOR url_row IN (select article_url from news_data_deduplicated_main) LOOP
		IF counter % 10000 = 0 THEN
			RAISE NOTICE 'NOTICE : %',counter; -- 진척도 확인용
		END IF;
		tag_array_stock_code := (SELECT ARRAY(SELECT stock_code FROM news_data_total_url_for_tag
		WHERE article_url = url_row.article_url) AS tags);

		UPDATE news_data_deduplicated_main 
		SET tag_stock_code = tag_array_stock_code
		WHERE article_url = url_row.article_url;

		counter := counter + 1;
	END LOOP;
END; $$
LANGUAGE plpgsql;

ALTER TABLE news_data_deduplicated_main ADD COLUMN tag_stock_code char(6) ARRAY; -- 태그 컬럼 추가
CALL sp_add_tags_on_news(); -- 프로시져 실행


-- Redshift에서는 ARRAY 형식을 지원하지 않기 때문에, Redshift에 업로드하기 전에 ARRAY를 JSON 배열 형태로 바꾸어 주어야 함
SELECT 
article_url
,published_date
,bankruptcy_article_check
,TRANSLATE(CAST(tag_stock_code AS TEXT), '{}','[]')
INTO TEMPORARY news_data_deduplicated_main_cache_tag_json
FROM news_data_deduplicated_main;

COPY news_data_deduplicated_main_cache_tag_json
TO '/Users/youngjinlim/Documents/news_data_deduplicated_minimal_main_tag_json.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);


-- 기업 별, 월별 부도기사비율, 기사 수 테이블 제작
-- 3개월 예측용 테이블을 만드는 함수로, 6개월, 1년 예측 테이블은 pre_3m_q 항목만 pre_6m, pre_1y로 바꾸어서 진행하면 됨
-- 웹 페이지에 출력시킬 최신 뉴스 데이터는, 'pre_3m_q date;' 항목을 2019-12-31로 맞춰 주면 생성됨 (bankruptcy_article_ratio_table_live 테이블)
DROP FUNCTION sp_get_article_list_have_certain_stock_tag();
CREATE OR REPLACE FUNCTION sp_get_article_list_have_certain_stock_tag()
RETURNS void AS $$
DECLARE
	pre_3m_q date;
	each_code char(6);
	one_ratio_for_inserting real;
	m_cache real;
	m_cache_normal_num integer;
	m_cache_bankruptcy_related integer;
	m1_cache real;
	m2_cache real;
	m3_cache real;
	m4_cache real;
	m5_cache real;
	m6_cache real;
	m7_cache real;
	m8_cache real;
	m9_cache real;
	m10_cache real;
	m11_cache real;
	m12_cache real;
    m1_normal_num_cache integer;
    m2_normal_num_cache integer;
    m3_normal_num_cache integer;
    m4_normal_num_cache integer;
    m5_normal_num_cache integer;
    m6_normal_num_cache integer;
    m7_normal_num_cache integer;
    m8_normal_num_cache integer;
    m9_normal_num_cache integer;
    m10_normal_num_cache integer;
    m11_normal_num_cache integer;
    m12_normal_num_cache integer;
    m1_bankruptcy_related_num_cache integer;
    m2_bankruptcy_related_num_cache integer;
    m3_bankruptcy_related_num_cache integer;
    m4_bankruptcy_related_num_cache integer;
    m5_bankruptcy_related_num_cache integer;
    m6_bankruptcy_related_num_cache integer;
    m7_bankruptcy_related_num_cache integer;
    m8_bankruptcy_related_num_cache integer;
    m9_bankruptcy_related_num_cache integer;
    m10_bankruptcy_related_num_cache integer;
    m11_bankruptcy_related_num_cache integer;
    m12_bankruptcy_related_num_cache integer;
	-- limit_val integer := 1;
BEGIN
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
	
	FOR each_code IN (SELECT * FROM target_company_list) LOOP
		pre_3m_q := (SELECT pre_3m FROM target_company_list WHERE stock_code = each_code);
		FOR each_month IN 1..12 LOOP
			m_cache := (
				SELECT
					CASE WHEN (count(*) = 0) THEN 0
					ELSE (COALESCE(sum(CASE WHEN bankruptcy_article_check THEN 1 ELSE 0 END),0) / count(*)::real)
					END AS bankruptcy_article_ratio
				FROM news_data_deduplicated_main
				WHERE (each_code = ANY(tag_stock_code)) AND
				(published_date BETWEEN (pre_3m_q - interval '1 month'*each_month) AND (pre_3m_q - interval '1 month'*(each_month-1)))
			);
			m_cache_normal_num := (
				SELECT count(*)
				FROM news_data_deduplicated_main
				WHERE (each_code = ANY(tag_stock_code))
					AND (published_date BETWEEN (pre_3m_q - interval '1 month'*each_month) AND (pre_3m_q - interval '1 month'*(each_month-1)))
					AND bankruptcy_article_check = False
			);
			m_cache_bankruptcy_related := (
				SELECT count(*)
				FROM news_data_deduplicated_main
				WHERE (each_code = ANY(tag_stock_code)) 
				AND (published_date BETWEEN (pre_3m_q - interval '1 month'*each_month) AND (pre_3m_q - interval '1 month'*(each_month-1)))
				AND bankruptcy_article_check = True
			);
			CASE each_month
				WHEN 1 THEN 
					m1_cache := m_cache;
					m1_normal_num_cache := m_cache_normal_num;
					m1_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 2 THEN 
					m2_cache := m_cache;
					m2_normal_num_cache := m_cache_normal_num; 
					m2_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 3 THEN 
					m3_cache := m_cache; 
					m3_normal_num_cache := m_cache_normal_num; 
					m3_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 4 THEN 
					m4_cache := m_cache; 
					m4_normal_num_cache := m_cache_normal_num; 
					m4_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 5 THEN 
					m5_cache := m_cache; 
					m5_normal_num_cache := m_cache_normal_num; 
					m5_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 6 THEN 
					m6_cache := m_cache; 
					m6_normal_num_cache := m_cache_normal_num; 
					m6_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 7 THEN 
					m7_cache := m_cache; 
					m7_normal_num_cache := m_cache_normal_num; 
					m7_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 8 THEN 
					m8_cache := m_cache; 
					m8_normal_num_cache := m_cache_normal_num; 
					m8_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 9 THEN 
					m9_cache := m_cache; 
					m9_normal_num_cache := m_cache_normal_num; 
					m9_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 10 THEN 
					m10_cache := m_cache; 
					m10_normal_num_cache := m_cache_normal_num;
					m10_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 11 THEN 
					m11_cache := m_cache; 
					m11_normal_num_cache := m_cache_normal_num;
					m11_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
				WHEN 12 THEN 
					m12_cache := m_cache; 
					m12_normal_num_cache := m_cache_normal_num;
					m12_bankruptcy_related_num_cache := m_cache_bankruptcy_related;
			END CASE;
		END LOOP;
		INSERT INTO bankruptcy_article_ratio_table_3m 
		VALUES (each_code,
					m1_cache,m2_cache,m3_cache,m4_cache,m5_cache,m6_cache,m7_cache,m8_cache,m9_cache,m10_cache,m11_cache,m12_cache,
					m1_normal_num_cache,m2_normal_num_cache,m3_normal_num_cache,m4_normal_num_cache,m5_normal_num_cache,m6_normal_num_cache,m7_normal_num_cache,m8_normal_num_cache,m9_normal_num_cache,m10_normal_num_cache,m11_normal_num_cache,m12_normal_num_cache,
					m1_bankruptcy_related_num_cache,m2_bankruptcy_related_num_cache,m3_bankruptcy_related_num_cache,m4_bankruptcy_related_num_cache,m5_bankruptcy_related_num_cache,m6_bankruptcy_related_num_cache,m7_bankruptcy_related_num_cache,m8_bankruptcy_related_num_cache,m9_bankruptcy_related_num_cache,m10_bankruptcy_related_num_cache,m11_bankruptcy_related_num_cache,m12_bankruptcy_related_num_cache);
		-- limit_val := limit_val + 1;
		-- RAISE NOTICE '%', each_code;
	END LOOP;
END; $$
LANGUAGE plpgsql;

SELECT * FROM sp_get_article_list_have_certain_stock_tag(); -- 함수 실행


-- 거시 데이터들 보관용 테이블 제작 및 데이터 적재
-- 한국은행 데이터
DROP TABLE IF EXISTS marcoeco_data_from_bok;
CREATE TABLE marcoeco_data_from_bok (
	"year_month" char(7)
	,"CD유통수익률(91일)(p)" real
	,"국고채(3년)(p)" real
	,"원달러환율(매매기준율)" real
);

COPY marcoeco_data_from_bok
FROM '/Users/youngjinlim/OneDrive/Coding/BigData_Study/Final_project/AWS/COPY용 데이터/marcoeco_data_from_bok.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

-- 두바이유 가격
DROP TABLE IF EXISTS oil_price_dubai_month;
CREATE TABLE oil_price_dubai_month (
	"year_month" char(7)
	,"Dubai(dollar)" real
	,"전년동월대비_가격증감율" real
);

COPY oil_price_dubai_month
FROM '/Users/youngjinlim/OneDrive/Coding/BigData_Study/Final_project/AWS/COPY용 데이터/oil_price_dubai_month.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

-- GDP 성장율
DROP TABLE IF EXISTS gdp_growth_rate;
CREATE TABLE gdp_growth_rate (
	"year" char(4)
	,"gdp_growth_rate" real
);

COPY gdp_growth_rate
FROM '/Users/youngjinlim/OneDrive/Coding/BigData_Study/Final_project/AWS/COPY용 데이터/gdp_growth_rate_2000_2020.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);


-- 학습용 거시지표 테이블 제작
-- 아래 코드들은 1년 예측용 테이블을 만드는 함수로, 3개월, 6개월 예측 테이블은 1y 을 3m, 6m으로 바꿔서 진행하면 됨
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


-- 2004년 1월의 데이터라면, 2004년 2월 8일에 발표되었을 것이라고 가정. (1 month + 1 week)
-- (예측일 > 2004-02-08 > 예측일 - 1 month) 의 조건을 만족하면, 2004년 1월의 데이터를 m1으로 칭한다.
-- m1 ~ m12까지 예측에 사용

-- 석유가격 - m1 추출 예시
SELECT "Dubai(dollar)" AS "oil_price"
	FROM oil_price_dubai_month
	WHERE ((date_trunc('month', TO_DATE(year_month, 'YYYY-MM')) + interval '1 month' + interval '1 week')::date < '2004-02-20'::date - interval '1 month'*0)
	AND ((date_trunc('month', TO_DATE(year_month, 'YYYY-MM')) + interval '1 month' + interval '1 week')::date > '2004-02-20'::date - interval '1 month'*1);

-- 금리, 환율 - m1 추출 예시
SELECT "CD유통수익률(91일)(p)" AS 
	,"국고채(3년)(p)"
	,"원달러환율(매매기준율)"
FROM marcoeco_data_from_bok
WHERE 
	((date_trunc('month', TO_DATE(year_month, 'YYYY-MM')) + interval '1 month' + interval '1 week')::date < '2004-02-20'::date - interval '1 month'*0)
	AND ((date_trunc('month', TO_DATE(year_month, 'YYYY-MM')) + interval '1 month' + interval '1 week')::date > '2004-02-20'::date - interval '1 month'*1);

-- 해당 년도 전년도(y1) GDP 성장율 추출
SELECT * FROM gdp_growth_rate WHERE year = TO_CHAR(('2004-02-20'::date - interval '1 year'*1), 'YYYY');


-- 텅 빈 table_for_dt_based_model_1y_macroeco 테이블의 stock_code 컬럼에 target_company_list의 stock_code를 넣음
INSERT INTO table_for_dt_based_model_1y_macroeco
SELECT stock_code FROM target_company_list;

-- 나머지 거시 데이터를 채우는 프로시져
CREATE OR REPLACE PROCEDURE sp_create_macrodata_table()
AS $$
DECLARE
	column_array text[] := (SELECT ARRAY(
						SELECT column_name
	  			   		FROM information_schema.columns
	 			   		WHERE table_schema = 'public'
	   			   		AND table_name   = 'table_for_dt_based_model_1y_macroeco')
				   );
	i integer;
	interval_index integer := 1;
	pre_date date;
	each_stock_code record;
BEGIN
	FOR each_stock_code IN (select stock_code from target_company_list) LOOP
		pre_date := (select pre_1y from target_company_list where stock_code = each_stock_code.stock_code);
		
		FOR i IN 2 .. 13 LOOP -- 석유가격 컬럼
			EXECUTE format(
				'UPDATE table_for_dt_based_model_1y_macroeco
				 SET %I = (
					SELECT "Dubai(dollar)"
					FROM oil_price_dubai_month
					WHERE ((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date <= $1 - interval ''1 month''*($2-1))
					AND ((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date > $3 - interval ''1 month''*$4))
				WHERE stock_code = $5', column_array[i])
			USING pre_date, interval_index, pre_date, interval_index, each_stock_code.stock_code;
			interval_index := interval_index + 1;
			-- RAISE NOTICE '%', i;
		END LOOP;

        interval_index := 1; -- interval_index 초기화

		FOR i IN 14 .. 25 LOOP -- 석유가격 전년동월대비 변동 컬럼
			EXECUTE format(
				'UPDATE table_for_dt_based_model_1y_macroeco
				 SET %I= (
					SELECT "전년동월대비_가격증감율"
					FROM oil_price_dubai_month
					WHERE 
						((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date <= $1 - interval ''1 month''*($2-1))
						AND ((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date > $3 - interval ''1 month''*$4))
				WHERE stock_code = $5', column_array[i])
			USING pre_date, interval_index, pre_date, interval_index, each_stock_code.stock_code;
			interval_index := interval_index + 1;
		END LOOP;
		
		interval_index := 1; -- interval_index 초기화

		FOR i IN 26 .. 37 LOOP -- 한국은행 거시지표 CD유통수익률
			EXECUTE format(
				'UPDATE table_for_dt_based_model_1y_macroeco
				 SET %I= (
					SELECT "CD유통수익률(91일)(p)"
					FROM marcoeco_data_from_bok
					WHERE 
						((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date <= $1 - interval ''1 month''*($2-1))
						AND ((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date > $3 - interval ''1 month''*$4))
					WHERE stock_code = $5', column_array[i])
			USING pre_date, interval_index, pre_date, interval_index, each_stock_code.stock_code;
			interval_index := interval_index + 1;
		END LOOP;
		
		interval_index := 1; -- interval_index 초기화
		
		FOR i IN 38 .. 49 LOOP -- 한국은행 거시지표 국고채 3년
		EXECUTE format(
			'UPDATE table_for_dt_based_model_1y_macroeco
			 SET %I= (
				SELECT "국고채(3년)(p)"
				FROM marcoeco_data_from_bok
				WHERE 
					((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date <= $1 - interval ''1 month''*($2-1))
					AND ((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date > $3 - interval ''1 month''*$4))
					WHERE stock_code = $5', column_array[i])
			USING pre_date, interval_index, pre_date, interval_index, each_stock_code.stock_code;
			interval_index := interval_index + 1;
		END LOOP;
		
		interval_index := 1; -- interval_index 초기화
		
		FOR i IN 50 .. 61 LOOP -- 한국은행 거시지표 원달러환율
			EXECUTE format(
			'UPDATE table_for_dt_based_model_1y_macroeco
			SET %I= (
				SELECT "원달러환율(매매기준율)"
				FROM marcoeco_data_from_bok
				WHERE 
					((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date <= $1 - interval ''1 month''*($2-1))
					AND ((date_trunc(''month'', TO_DATE(year_month, ''YYYY-MM'')) + interval ''1 month'' + interval ''1 week'')::date > $3 - interval ''1 month''*$4))
					WHERE stock_code = $5', column_array[i])
			USING pre_date, interval_index, pre_date, interval_index, each_stock_code.stock_code;
			interval_index := interval_index + 1;
		END LOOP;
		
		interval_index := 1; -- interval_index 초기화
		
		FOR i IN 62 .. 64 LOOP -- 연별 GDP성장율
			EXECUTE format(
				'UPDATE table_for_dt_based_model_1y_macroeco
				SET %I= (
					SELECT gdp_growth_rate
					FROM gdp_growth_rate
					WHERE year = TO_CHAR(($1 - interval ''1 year''*$2), ''YYYY''))
				WHERE stock_code = $3', column_array[i])
			USING pre_date, interval_index, each_stock_code.stock_code;
			interval_index := interval_index + 1;
		END LOOP;
		-- RAISE NOTICE '%', each_stock_code;
	END LOOP;
END; $$
LANGUAGE plpgsql;

call sp_create_macrodata_table(); -- 프로시져 실행


-- %는 psycopg2 사용 시 escape 문자로 사용되기 때문에, 컬럼에서 %를 다 p로 바꾸어 주었음
ALTER TABLE stock_data_3years_raw_3m
RENAME COLUMN "수익률 (1개월)(%)" TO "수익률 (1개월)(p)";

ALTER TABLE stock_data_3years_raw_3m
RENAME COLUMN "수익률 (1주)(%)" TO "수익률 (1주)(p)";

ALTER TABLE stock_data_3years_raw_3m
RENAME COLUMN "수익률 (3개월)(%)" TO "수익률 (3개월)(p)";

ALTER TABLE stock_data_3years_raw_3m
RENAME COLUMN "수익률 (6개월)(%)" TO "수익률 (6개월)(p)";

ALTER TABLE stock_data_3years_raw_3m
RENAME COLUMN "수익률(%)" TO "수익률(p)";

ALTER TABLE stock_data_3years_raw_1y
RENAME COLUMN "수익률 (1개월)(%)" TO "수익률 (1개월)(p)";

ALTER TABLE stock_data_3years_raw_1y
RENAME COLUMN "수익률 (1주)(%)" TO "수익률 (1주)(p)";

ALTER TABLE stock_data_3years_raw_1y
RENAME COLUMN "수익률 (3개월)(%)" TO "수익률 (3개월)(p)";

ALTER TABLE stock_data_3years_raw_1y
RENAME COLUMN "수익률 (6개월)(%)" TO "수익률 (6개월)(p)";

ALTER TABLE stock_data_3years_raw_1y
RENAME COLUMN "수익률(%)" TO "수익률(p)";


-- S3에 업로드 후, Redshift에 올라갈 csv 내보내기
COPY bankruptcy_article_ratio_table_3m
TO '/Users/youngjinlim/Documents/bankruptcy_article_ratio_table_3m.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY bankruptcy_article_ratio_table_6m
TO '/Users/youngjinlim/Documents/bankruptcy_article_ratio_table_6m.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY bankruptcy_article_ratio_table_1y
TO '/Users/youngjinlim/Documents/bankruptcy_article_ratio_table_1y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_3m_macroeco
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_3m_macroeco.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_3m_macroeco
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_6m_macroeco.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_1y_macroeco
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_1y_macroeco.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY bankruptcy_article_ratio_table_live
TO '/Users/youngjinlim/Documents/bankruptcy_article_ratio_table_live.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_3m_finance_2y
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_3m_finance_2y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_3m_finance_3y
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_3m_finance_3y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_6m_finance_2y
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_6m_finance_2y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_6m_finance_3y
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_6m_finance_3y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_1y_finance_2y
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_1y_finance_2y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY table_for_dt_based_model_1y_finance_3y
TO '/Users/youngjinlim/Documents/table_for_dt_based_model_1y_finance_3y.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);

COPY news_data_deduplicated_main
TO '/Users/youngjinlim/Documents/news_data_deduplicated_main.csv'
WITH (FORMAT csv, ENCODING UTF8, HEADER);