# 기업부도예측 with 머신러닝 & 지표 시각화
* **프로젝트 라이브 URL : http://13.124.187.87:8000**
* **만든 사람 : 임영진**
	* [LinkedIn](https://www.linkedin.com/in/young-jin-lim-b499a0111/)
	* [Github_Page](https://limyj0708.github.io/)


## 프로젝트 목표
1. 상장 기업의 3개월, 6개월, 1년 후의 부도 유무와 부도 확률 예측
2. 의사결정에 도움이 되는 지표 시각화
3. 이를 웹 어플리케이션의 형태로 생성


## 프로젝트 진행 개요
![infra](https://raw.githubusercontent.com/limyj0708/bankruptcy_prediction/master/readme_image/infra.gif)
1. **데이터 크롤링**
	* Python 라이브러리를 활용한 경제지 기사, Dart 감사보고서 크롤링
	* 크롤링 속도 향상을 위한 비동기 코드 작성 (4배 정도의 속도 향상)
	* 다수의 크롤링 머신을 조작하기 위한 쉘 스크립트 작성
1. **데이터 전처리**
	* 경제지 기사 데이터 정제 (특수문자 제거 등)
	* 경제지 기사 데이터 토큰화 및 코사인 유사도 기준 "부도" 유사단어 상위 30개 추출
		* "부도" 유사단어가 포함된 기사는 부도관련 기사로 판정
	* 기업 별 감사보고서 본문의 "계속기업으로서의 존속 가능성 부정" 여부 체크
1. **DB 구축**
	* AWS Redshift에 데이터 저장 및 사용
	* AWS Redshift에서는 비효율적인 연산 처리를 위해, 로컬 머신에 PostgreSQL DB를 구축
1. **머신 러닝**
	* RandomForest, GradientBoosting, XGBoost 세 종류의 의사결정나무 기반 모델 사용, 결과 비교
	* 데이터 오버샘플링 방식 별 결과 비교 (RandomOverSampling, ADASYN, SMOTE) 
	* 가장 결과가 좋은 모델에 대한 하이퍼파라미터 튜닝
	* Feature Importance 평가
	* 학습은 Gcloud compute engine에서 진행
1. **데이터 시각화 및 웹 어플리케이션 제작**
	* Django 기반 웹 어플리케이션 제작
	* 시각화 라이브러리 plotly를 사용하여 의사결정에 도움이 되는 데이터 시각화
	* 모델에 최신 기업 데이터를 넣어 부도 여부 예측, 예측 결과를 웹 페이지에 출력
	* AWS EC2 위에서 어플리케이션 작동


## 사용 기술 및 라이브러리
* Python
	* Asyncio, Aiohttp, Requests, Beautifulsoup
	* Pandas, Scikit-learn, imbalanced-learn
	* FastText, konlpy
	* psycopg2
	* Django
* PostgreSQL, AWS Redshift
	* SQL,  PL/pgSQL
* Javascript
	* plotly
* HTML, CSS
* Bash shell script


# 프로젝트 상세
## 목차 - 누르면 이동
1. [사용한 데이터, 참고 리포트](https://github.com/limyj0708/bankruptcy_prediction#1-사용한-데이터-참고-리포트)
1. 프로젝트 개발 과정
	* [2-1. 데이터 크롤링](https://github.com/limyj0708/bankruptcy_prediction#2-1-데이터-크롤링)
	* [2-2. 데이터 전처리](https://github.com/limyj0708/bankruptcy_prediction#2-2-데이터-전처리)
	* [2-3. DB 구축](https://github.com/limyj0708/bankruptcy_prediction#2-3-db-구축)
	* [2-4. 머신 러닝](https://github.com/limyj0708/bankruptcy_prediction#2-4-머신-러닝)
	* [2-5. 데이터 시각화 및 웹 어플리케이션 제작](https://github.com/limyj0708/bankruptcy_prediction#2-5-데이터-시각화-및-웹-어플리케이션-제작)


## 1. 사용한 데이터, 참고 리포트
1. 참고 리포트
	1. 한국금융연구원의 [빅데이터를 이용한 딥러닝 기반의 기업 부도예측 연구](http://www.kcft.or.kr/wp-content/uploads/2018/01/131605558932838295_WP17-08-1.pdf) 리포트에서 방향성을 참고하여 프로젝트 시작
1. 사용한 데이터
	1. 2000 ~ 2019년 기간의 상장되었던 기업의 재무제표, 주가, 거래량 데이터
		* 출처 : [Dataguide](http://www.dataguide.co.kr/DG5Web/index.asp)
	1. 주요 경제지 기업별 기사 최신 3년치 (2708개 기업의 기사 2,380,889건)
		* 대상 언론사 : 한국경제, 서울경제, 헤럴드경제, 머니투데이
		* 언론사 홈페이지에서, 기업명으로 검색하여 출력된 기사들을 크롤링
	1. Dart 전자공시의 기업 별 감사보고서 데이터
		* 각 기업 당 최신 10개의 감사보고서 크롤링
	1. 2000 ~ 2019년 기간의 거시지표
		* 출처 : 한국은행, 한국석유공사
		* 국고채 3년물 금리, CD유통수익률, 원/달러 환율, GDP 성장율, 두바이유 가격


## 2. 프로젝트 개발 과정
### 2-1. 데이터 크롤링
1. Dart 감사보고서 크롤링
	1. [크롤링 코드로 가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/01_Data_Crawling/Dart_audit_report_crawling/dart_audit%20report_crawling.ipynb)
	1. 기업 별 감사보고서 페이지 구조 분석 및 크롤링, 결과를 아래와 같은 csv로 저장
	
	<br>

	| stock_code | company_name | bankruptcy | report_name | url | &nbsp;&nbsp;&nbsp;&nbsp; text &nbsp;&nbsp;&nbsp;&nbsp; | report_date |
	| ---------- | ------------ | ---------- | ----------- | --- | ---- | ----------- |
	| 008670 | 굿모닝신한증권 | 0 | A-1 | http://dart.fss.or.kr/ds... | 외부감사인의 감사보고서본 감사인은 첨부된 굿모닝신한증권주식회사의 2004년 3월 3... | 2004-06-03 |
	| 008670 | 굿모닝신한증권 | 0 | A-2 | http://dart.fss.or.kr/ds... | 외부감사인의 감사보고서본 감사인은 굿모닝신한증권주식회사(구, 굿모닝증권주식회사)의 ... | 2003-06-11 |
	| 008670 | 굿모닝신한증권 | 0 | A-3 | http://dart.fss.or.kr/ds... | 외부감사인의 감사보고서본 감사인은 굿모닝증권주식회사의 2002년 3월 31일과 20... | 2002-06-07 |
	| ...        | ...          | ...        | ...         | ...  | ... | ...         |


1. 경제지 신문 기사 크롤링
	1. [크롤링 코드 모음 폴더로 가기](https://github.com/limyj0708/bankruptcy_prediction/tree/master/01_Data_Crawling/News_Crawling)
	1. [비동기 코드 (서울경제신문 기사 본문 크롤링)](https://github.com/limyj0708/bankruptcy_prediction/blob/master/01_Data_Crawling/News_Crawling/SeoulK_news_crawl_article_body.py)
	1. 언론사 별 기업명 검색 결과 페이지 구조를 분석하여 크롤링 진행
	1. 크롤링 해야 할 양이 많았기 때문에, 시간 단축을 위해 비동기 코드 작성
		1. [Asyncio](https://docs.python.org/3/library/asyncio.html), [Aiohttp](https://docs.aiohttp.org/en/stable/) 라이브러리 사용
	1. gcloud compute engine의 인스턴스 32개를 크롤링 머신으로 사용했으며, 한 번에 여러 머신에 명령을 내리기 위해 쉘 스크립트 사용
		1. [쉘 스크립트 모음 폴더로 가기](https://github.com/limyj0708/bankruptcy_prediction/tree/master/01_Data_Crawling/News_Crawling/shell%20script)
		1. 사용한 쉘 스크립트 예시
	
        ```sh
        # 파일 하나를 gcloud compute instance들에 한 번에 올리는 스크립트.
        # 여기서는 크롤링 코드 py파일을 업로드 했다.
        #!/bin/sh
        start_num=1
        last_num=32
        ((instance_num="${start_num}"))
        machine_prefix=" cw-machine-"
        scp_upload_prefix="gcloud compute scp "
        zone_prefix=" --zone"
        name_tosend="SeoulK/SeoulK_crawl_body.py"
        remote_dir=":~/SeoulK"

        while (("${instance_num}"<=last_num)); do
            if (("${instance_num}"<=(start_num+7) )); then
                zone=" us-east1-b"
            elif (( "${instance_num}">=(start_num+8) && "${instance_num}"<=(start_num+15) )); then
                zone=" us-west1-a"
            elif (( "${instance_num}">=(start_num+16) && "${instance_num}"<=(start_num+23) )); then
                zone=" us-central1-a"
            else
                zone=" northamerica-northeast1-a"
            fi

            machine_name=$machine_prefix$instance_num
            echo $scp_upload_prefix$name_tosend$zone_prefix$zone$machine_name$remote_dir
            $scp_upload_prefix$name_tosend$zone_prefix$zone$machine_name$remote_dir &
            ((instance_num="${instance_num}"+1))
        done

        wait
        echo "All processes are done!"
        ```

### 2-2. 데이터 전처리
1. 기사 데이터 본문 내용 정제
	1. [기사 데이터 정제 코드로 가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/02_Data_Preprocessing/01_article_body_cleansing.ipynb)
	1. 아래와 같은 함수를 만들어서 처리
	
	```python
	def cleansing(text):    
	   pattern = ('googletag.*\}\);') # Google Ad 태그 삭제
	   text = re.sub(pattern=pattern, repl=' ', string=text)
	   pattern = ('\s+') # 모든 종류의 공백을 공백 하나로 변경
	   text = re.sub(pattern=pattern, repl=' ', string=text)
	   pattern = '([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)' # E-mail 주소 제거
	   text = re.sub(pattern=pattern, repl='', string=text)
	   pattern = '(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F]{2}))+' # URL 제거
	   text = re.sub(pattern=pattern, repl='', string=text)
	   pattern = '([ㄱ-ㅎㅏ-ㅣ]+)' # 한글 자음, 모음 제거
	   text = re.sub(pattern=pattern, repl='', string=text)
	   pattern = '<[^>]*>' # HTML 태그 제거
	   text = re.sub(pattern=pattern, repl='', string=text)
	   pattern = '[^\w\s]' # 특수기호 제거
	   text = re.sub(pattern=pattern, repl='', string=text)
	   return text
	```

1. [konlpy](https://konlpy-ko.readthedocs.io/ko/v0.4.3/)의 [mecab(은전한닢)](http://eunjeon.blogspot.com/) 형태소 분석기로 기사 본문 토큰화
	1. [토큰화 코드로 가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/02_Data_Preprocessing/02_article_body_tokenizing_mecab.py)
	1. mecab 사용자 사전에 대상 기업 이름 2708개 추가

1. [fastText](https://fasttext.cc/)로 1,224,734개의 토큰화 한 기사 본문 데이터 학습 후, "부도" 유사단어 코사인 유사도 기준 상위 30개 추출
    1. [학습 및 유사단어 추출 코드로 가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/02_Data_Preprocessing/03_fastText_fitting_and_extract_top30words_of_bankruptcy.ipynb)
    1. "부도" 유사단어 30개는 아래와 같으며, 특정 기업 이름과 의미를 알기 힘든 단어, 
	너무 의미가 광범위한 단어를 제외한 24개 단어 사용

	```python
	model.most_similar('부도', topn=30, restrict_vocab=30000)
	# restrict_vocab을 제한하지 않으면, 결과 값에 이상한 단어가 많이 등장하여 사용이 힘듦

	[('채무불이행', 0.7117146849632263),
	('파산', 0.670993447303772),
	('부실화', 0.6374591588973999),
	('부실', 0.6326149702072144),
	('자금난', 0.6201349496841431),
	('불이행', 0.6112999320030212),
	('디폴트', 0.597563624382019),
	('회생', 0.5880905985832214),
	('매출채권', 0.5860508680343628),
	('위기', 0.5692920684814453),
	('경영난', 0.5686293840408325),
	('법정', 0.5624008178710938),
	('채무', 0.5615006685256958),
	('사태', 0.5613707900047302), # 제외
	('파탄', 0.5370084047317505),
	('연체', 0.536543607711792),
	('기설', 0.535281240940094), # 제외
	('익스포저', 0.5338025093078613),
	('대란', 0.5329005718231201),
	('잠식', 0.5316050052642822),
	('모면', 0.5307774543762207),
	('존폐', 0.5305982828140259),
	('부실기업', 0.5297956466674805),
	('최악', 0.5293768048286438), # 제외
	('워크아웃', 0.5289958119392395),
	('어음', 0.5285745859146118),
	('미지급', 0.5282562971115112),
	('신성건설', 0.5238434076309204), # 제외
	('처했', 0.5231027007102966), # 제외
	('패소', 0.5228811502456665) # 제외
	]
	```

1. (부도 + 부도 유사단어) 총 25개 중 하나라도 포함된 기사는 부도 관련기사로 판정
	1. [부도 관련기사 판정 및 컬럼 추가 코드로 가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/02_Data_Preprocessing/04_article_body_bankruptcy_related_check.ipynb)


### 2-3. DB 구축
1. [DB 구축 관련 코드 모음 폴더로 가기](https://github.com/limyj0708/bankruptcy_prediction/tree/master/03_Create_Database_and_Modifying_Data)
1. 머신 러닝 학습에 필요한 feature들을 정의한 후, 이를 기반으로 구축
   1. 기업들의 최신 2년 분량의 재무 데이터 (부도난 기업의 경우, 부도 전 최신 2년)
   		1. 사용한 재무 항목
			 * 총자산(천원)
			 * 현금및현금성자산(천원)
			 * 총부채(천원)
			 * 총자본(천원)
			 * 매출액(천원)
			 * 당기순이익(천원)
			 * 세전계속사업이익(천원)
			 * 영업이익(천원)
			 * 매출총이익(천원)
			 * 차입금의존도(p)
			 * 당기순이익률(p)
			 * 세전계속사업이익률(p)
			 * 영업이익률(p)
			 * 매출총이익률(p)
			 * 총자산회전율(회)
			 * 총자산증가율(p)
			 * 총자산부채비율(p)
   1. 기업들의 최신 4개월 분량의 주가 데이터 (부도난 기업의 경우, 부도 전 최신 4개월)
   		1. 기간 별, 거래주체별 거래량 비율 (개인, 외국인, 기관)
   1. 기업들의 최신 1년 분량의 기사 데이터 (부도난 기업의 경우, 부도 전 최신 1년)
   		1. 월별 부도기사비율
   1. 최신 1년 분량의 거시 데이터 (부도난 기업의 경우, 부도 전 최신 1년)
   		1. 월별 - 유가, 유가변화율, CD유통수익률(91일), 3년 국고채 이율, 원달러 환율
		2. 연간 GDP 성장율


3. 데이터베이스 ER 다이어그램

    ![Oops, Some network ants ate this pic!](https://raw.githubusercontent.com/limyj0708/bankruptcy_prediction/master/readme_image/bankruptcy_prediction_diagram.gif)
   
   1. [이미지 크게 보기 - 출력된 이미지 클릭 시 커짐](https://raw.githubusercontent.com/limyj0708/bankruptcy_prediction/master/readme_image/bankruptcy_prediction_diagram.gif)
   2. 각 테이블에 대한 설명

      <table>
        <th>테이블명</th>
        <th>설명</th>
        <tr>
          <td>table_company_list</td>
          <td>* 학습 대상 기업들의 기본 정보가 담긴 테이블. 모든 연산의 중심이 되는 테이블이다.</td>
        </tr>
        <tr>
          <td>finance_data_1999_2020_raw</td>
          <td>
            * 대상 기업들의 재무 데이터 원본이 담겨 있는 테이블<br>
            * 대부분의 다른 테이블이 이 테이블의 stock_code 컬럼을 foreign key로 참조하고 있음
          </td>
        </tr>
        <tr>
          <td>
            table_for_dt_based_model_3m_finance_2y<br>
            table_for_dt_based_model_6m_finance_2y<br>
            table_for_dt_based_model_1y_finance_2y
          </td>
          <td>
            * 각각 3개월 뒤, 6개월 뒤, 1년 뒤 부도예측용 재무 테이블.<br>
            * 2년치 데이터만 저장되어 있음
          </td>
        </tr>
        <tr>
          <td>
            table_for_dt_based_model_3m_finance_3y<br>
            table_for_dt_based_model_6m_finance_3y<br>
            table_for_dt_based_model_1y_finance_3y
          </td>
          <td>
            * 최신 3년치 재무 데이터가 저장되어있는 테이블들.<br>
            * 학습 대상 기업의 수를 늘리기 위해 재무 데이터를 2년치만 사용하기로 하면서 사용하지 않게 되었으나, 만일을 위해 남겨 두었다.
          </td>
        </tr>
        <tr>
          <td>stock_data_2000_2020_raw</td>
          <td>* 주가 데이터 원본 테이블</td>
        </tr>
        <tr>
          <td>
            stock_data_3years_raw_3m<br>
            stock_data_3years_raw_6m<br>
            stock_data_3years_raw_1y
          </td>
          <td>
            * 각각 3개월 뒤, 6개월 뒤, 1년 뒤 부도예측용 주가 데이터 테이블.<br>
            * 3년치 데이터가 저장되어 있으나, 최종적으로는 4개월 분량의 데이터만 추출하여 사용하였음.
          </td>
        <tr>
          <td>news_data_total_url_for_tag</td>
          <td>
            * URL 중복 제거를 하지 않은 2,380,889개의 기사를 저장한 테이블<br>
            * 검색 회사명, 종목코드, 기사 URL을 컬럼으로 가지고 있으며, 기사 본문이 담긴 테이블에 태그를 붙이기 위해서 만들어졌다.
          </td>
        </tr>
        <tr>
          <td>news_data_deduplicated_main</td>
          <td>
            * 중복 제거 처리한, 기사 본문이 담긴 테이블.<br>
            * 각 기사마다 관련된 기업의 종목코드들이 담긴 컬럼을 가지고 있다.
          </td>
        </tr>
        <tr>
          <td>
            bankruptcy_article_ratio_table_3m<br>
            bankruptcy_article_ratio_table_6m<br>
            bankruptcy_article_ratio_table_1y
          </td>
          <td>
            * 각각 3개월 뒤, 6개월 뒤, 1년 뒤 부도예측용 부도기사비율 데이터 테이블.<br>
            * 1년 분량의 부도기사비율 데이터가, 월별로 저장되어 있다.
          </td>
        </tr>
        <tr>
          <td>
            bankruptcy_article_ratio_table_live
          </td>
          <td>
            * 기사의 수와 부도기사비율 시각화를 위한 최신 1년치 데이터 테이블
          </td>
        </tr>
        <tr>
          <td>
            table_for_dt_based_model_3m_macroeco<br>
            table_for_dt_based_model_6m_macroeco<br>
            table_for_dt_based_model_1y_macroeco
          </td>
          <td>
            * 각각 3개월 뒤, 6개월 뒤, 1년 뒤 부도예측용 거시 데이터 테이블.<br>
            * 1년 분량의 거시 데이터가, 월별로 저장되어 있다.
          </td>
        </tr>
        <tr>
          <td>
            gdp_growth_rate<br>
            oil_price_dubai_month<br>
            macroeco_data_from_bok
          </td>
          <td>
            * 각각 GDP 성장율, 두바이유 가격, (CD유통수익률/국고채 3년물 이율/원달러 환율) 원본 데이터를 저장한 테이블
          </td>
        </tr>
        <tr>
          <td>
            dart_audit_report_data
          </td>
          <td>
            * Dart 감사 보고서의 계속기업 존속가능의견 여부를 저장한 테이블
          </td>
        </tr>
      </table>

    <br>

1. 쿼리 작성은 두 가지 방법으로 진행하였음
   1. jupyter lab 환경에서 python 라이브러리 psycopg2로 진행
   1. SQL 클라이언트에서 직접 SQL로 진행
   1. 두 방법에 모두 익숙해지기 위해 이렇게 진행하였음
   1. psycopg2을 사용하여 진행한 부분
      1. 대상 회사 테이블 제작 (table_company_list)
      2. 주식 데이터 테이블 제작
      3. Dart 감사보고서 데이터 테이블 제작
      4. 재무 데이터 테이블 제작
      5. 기사 데이터 원본 테이블 제작
      6. 해당되는 파일
         1. [psycopg2_localDB_postgresql.ipynb](https://github.com/limyj0708/bankruptcy_prediction/blob/master/03_Create_Database_and_Modifying_Data/psycopg2_localDB_postgresql.ipynb)
         2. [psycopg2_redshift.ipynb](https://github.com/limyj0708/bankruptcy_prediction/blob/master/03_Create_Database_and_Modifying_Data/psycopg2_redshift.ipynb)
   1. SQL을 사용하여 진행한 부분
      1. 기사 데이터 원본 테이블에 태그 컬럼 추가 및 태그 할당
      2. 학습에 사용할 기사 데이터 테이블 제작
      3. 거시 데이터 원본 테이블 제작
      4. 학습에 사용할 거시 데이터 테이블 제작
      5. 해당되는 파일
         1. [localDB_create_tables.sql](https://github.com/limyj0708/bankruptcy_prediction/blob/master/03_Create_Database_and_Modifying_Data/localDB_create_tables.sql)
         2. [redshift_create_tables.sql](https://github.com/limyj0708/bankruptcy_prediction/blob/master/03_Create_Database_and_Modifying_Data/redshift_create_tables.sql)

   6. SQL에서 복잡한 연산은 PL/pgSQL로 함수나 프로시져를 만들어서 진행
      1. 사용한 프로시져 예시
            ```SQL
                -- 뉴스 기사에, 해당 뉴스 기사에 관련된 기업의 종목코드를 묶어서 할당하는 프로시져
            CREATE OR REPLACE PROCEDURE sp_add_tags_on_news()
            AS $$
            DECLARE -- 변수 선언
                url_row record;
                tag_array_stock_code text[]; -- 태그처럼 사용될 종목코드 묶음
                counter integer := 0;
            BEGIN
                FOR url_row IN (select article_url from news_data_deduplicated_main) LOOP
                    IF counter % 10000 = 0 THEN
                        RAISE NOTICE 'NOTICE : %',counter; -- 진척도 확인을 위한 Raise
                    END IF;
                    tag_array_stock_code := (SELECT ARRAY
                                            (SELECT stock_code 
                                                FROM news_data_total_url_for_tag 
                                -- url 중복제거 하지 않은, 수집한 기사 로우 데이터
                                WHERE article_url = url_row.article_url) 
                            AS tags);
                
                    UPDATE news_data_deduplicated_main 
                    SET tag_stock_code = tag_array_stock_code
                    WHERE article_url = url_row.article_url;
                    counter := counter + 1;
                END LOOP;
            END; $$
            LANGUAGE plpgsql;

            ALTER TABLE news_data_deduplicated_main ADD COLUMN tag_stock_code char(6) ARRAY; 
                -- 태그 컬럼 추가
            CALL sp_add_tags_on_news(); -- 프로시져 실행
            ```


      1. 프로시저 실행 결과, tag_stock_code 컬럼 생성

![컬럼 생성](https://raw.githubusercontent.com/limyj0708/bankruptcy_prediction/master/readme_image/table_example.gif)

### 2-4. 머신 러닝
1. [학습 코드 보러가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/04_Machine_Learning/Machine_learning_DTBased_model.ipynb)
2. 프로젝트 시작 시 참고한  [빅데이터를 이용한 딥러닝 기반의 기업 부도예측 연구](http://www.kcft.or.kr/wp-content/uploads/2018/01/131605558932838295_WP17-08-1.pdf) 리포트에서는 RandomForest 모델이 가장 결과가 좋았기 때문에, 아래 의사결정나무 기반 앙상블 모델 3개 의 결과를 비교하여 가장 좋은 것을 사용하기로 함
   * RandomForest
   * GradientBoosting
   * XGBoost

3. 학습 데이터의 약 15%만이 부도 기업인 비대칭 데이터이기 때문에, 데이터 오버샘플링을 진행하여 학습을 진행하였고, 아래 4가지 경우에 대해 결과를 비교함
   * 오버샘플링 진행하지 않음
   * RandomOverSampling
   * ADASYN (Adaptive Synthetic Sampling Approach for Imbalanced Learning)
   * SMOTE (Synthetic Minority Over-sampling Technique)

4. 데이터의 [층화 무작위 추출](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedShuffleSplit.html) 30회를 진행하여, 30회의 평가점수 평균을 내어 결과를 비교함
5. 위의 학습/샘플링 작업은 별도의 모듈을 만들어서 진행 / [모듈 코드 보러가기](https://github.com/limyj0708/bankruptcy_prediction/blob/master/04_Machine_Learning/ml_Suffle_and_validation.py)
6. AWS Redshift에서 데이터를 불러와서 학습을 진행하였음
   1. 학습 데이터 샘플 - 6개월 예측 모델 학습용 데이터
      * 총 2526 rows × 125 columns
      
      <br>
      
	   | stock_code | Y-1_총자산(천원) | Y-1_현금및현금성자산(천원) | Y-1_총부채(천원) | Y-1_총자본(천원) | Y-1_매출액(천원) | Y-1_당기순이익(천원) | Y-1_세전계속사업이익(천원) | Y-1_영업이익(천원) | Y-1_매출총이익(천원) | Y-1_차입금의존도(p) | ...  | m6_원달러환율(매매기준율) | m7_원달러환율(매매기준율) | m8_원달러환율(매매기준율) | m9_원달러환율(매매기준율) | m10_원달러환율(매매기준율) | m11_원달러환율(매매기준율) | m12_원달러환율(매매기준율) | y1_gdp_growth_rate | y2_gdp_growth_rate | y3_gdp_growth_rate |
	   | ---------- | ---------------- | -------------------------- | ---------------- | ---------------- | ---------------- | -------------------- | -------------------------- | ------------------ | -------------------- | ------------------- | ---- | ------------------------- | ------------------------- | ------------------------- | ------------------------- | -------------------------- | -------------------------- | -------------------------- | ------------------ | ------------------ | ------------------ |
	   | 008670     | 2.887228e+09     | 1.599800e+07               | 2.197262e+09     | 6.899660e+08     | 2.811410e+08     | 30311000.0           | 37065000.0                 | 4.230700e+07       | 2.811410e+08         | 14.02               | ...  | 1166.34                   | 1166.69                   | 1184.32                   | 1192.95                   | 1184.87                    | 1166.27                    | 1166.17                    | 0.031              | 0.077              | 0.049              |
	   | 035910     | 3.869358e+07     | 4.498010e+05               | 4.206940e+07     | -3.375816e+06    | 5.612976e+07     | -15379698.0          | -15379698.0                | -8.882955e+06      | 3.290716e+06         | 90.42               | ...  | 1150.85                   | 1166.34                   | 1166.69                   | 1184.32                   | 1192.95                    | 1184.87                    | 1166.27                    | 0.031              | 0.077              | 0.049              |
	   | 037640     | 4.960932e+07     | 2.595210e+05               | 4.305133e+07     | 6.557992e+06     | 5.162583e+07     | 469886.0             | 774972.0                   | 2.678560e+06       | 4.504766e+06         | 51.50               | ...  | 1150.85                   | 1166.34                   | 1166.69                   | 1184.32                   | 1192.95                    | 1184.87                    | 1166.27                    | 0.031              | 0.077              | 0.049              |
	   | 007910     | 9.845974e+07     | 2.198753e+06               | 8.763419e+06     | 8.969632e+07     | 6.246431e+07     | 7345991.0            | 9996433.0                  | 5.274090e+05       | 8.468384e+06         | 0.00                | ...  | 1177.37                   | 1150.85                   | 1166.34                   | 1166.69                   | 1184.32                    | 1192.95                    | 1184.87                    | 0.031              | 0.077              | 0.049              |
	   | 054080     | 6.488546e+07     | 8.974588e+06               | 3.043291e+07     | 3.445255e+07     | 3.036421e+07     | 2680136.0            | 2927240.0                  | 3.379793e+06       | 9.497963e+06         | 42.46               | ...  | 1158.65                   | 1177.37                   | 1150.85                   | 1166.34                   | 1166.69                    | 1184.32                    | 1192.95                    | 0.031              | 0.077              | 0.049              |
	   | ...        | ...              | ...                        | ...              | ...              | ...              | ...                  | ...                        | ...                | ...                  | ...                 | ...  | ...                       | ...                       | ...                       | ...                       | ...                        | ...                        | ...                        | ...                | ...                | ...                |
	   | 000150     | 2.888028e+10     | 2.456189e+09               | 2.173524e+10     | 7.145046e+09     | 1.817217e+10     | -340510995.0         | 10553762.0                 | 1.215881e+09       | 3.323509e+09         | 43.43               | ...  | 1130.72                   | 1122.45                   | 1122.00                   | 1122.90                   | 1128.58                    | 1130.81                    | 1120.60                    | 0.032              | 0.029              | 0.028              |
	   | 000120     | 7.868567e+09     | 1.633348e+08               | 4.737829e+09     | 3.130738e+09     | 9.219680e+09     | 66600069.0           | 99818962.0                 | 2.426869e+08       | 8.280729e+08         | 37.12               | ...  | 1130.72                   | 1122.45                   | 1122.00                   | 1122.90                   | 1128.58                    | 1130.81                    | 1120.60                    | 0.032              | 0.029              | 0.028              |
	   | 000100     | 2.173813e+09     | 2.412961e+08               | 5.220771e+08     | 1.651736e+09     | 1.518823e+09     | 58334962.0           | 89391013.0                 | 5.012644e+07       | 4.137920e+08         | 5.46                | ...  | 1130.72                   | 1122.45                   | 1122.00                   | 1122.90                   | 1128.58                    | 1130.81                    | 1120.60                    | 0.032              | 0.029              | 0.028              |
	   | 000060     | 2.047876e+10     | 3.903383e+08               | 1.819556e+10     | 2.283201e+09     | 7.107298e+09     | 234721346.0          | 314793620.0                | 3.127345e+08       | 5.519393e+09         | 1.88                | ...  | 1130.72                   | 1122.45                   | 1122.00                   | 1122.90                   | 1128.58                    | 1130.81                    | 1120.60                    | 0.032              | 0.029              | 0.028              |
	   | 000040     | 1.549011e+08     | 3.080598e+07               | 8.500646e+07     | 6.989460e+07     | 3.656336e+07     | -24442080.0          | -24431117.0                | -1.625702e+07      | -6.310200e+05        | 30.54               | ...  | 1130.72                   | 1122.45                   | 1122.00                   | 1122.90                   | 1128.58                    | 1130.81                    | 1120.60                    | 0.032              | 0.029              | 0.028              |

   

7. 예측기간별로 가장 결과가 좋았던 조합은 아래와 같음
	1. 3개월 예측모델
		1. XGBoost + RandomOverSampling
		2. Train set 과적합은 하이퍼파라미터 튜닝 파트에서 해결 시도

        <br>

        <table>
            <th colspan = "6">3개월 예측모델, XGBoost + RandomOverSampling 평가점수</th>
            <tr>
                <td rowspan = "4">Train</td>
                <td rowspan = "2">생존</td>
                <td>Precision</td>
                <td>Recall</td>
                <td>f1-score</td>
            <td>Accuracy</td>
            </tr>
            <tr>
                <td>1.0</td>
                <td>1.0</td>
                <td>1.0</td>
                <td rowspan = "3">1.0</td>
            </tr>
        <tr>
                <td rowspan = "2">부도</td>
                <td>Precision</td>
                <td>Recall</td>
                <td>f1-score</td>
            </tr>
        <tr>
                <td>1.0</td>
                <td>1.0</td>
                <td>1.0</td>
            </tr>
            <tr>
                <td rowspan = "4">Test</td>
                <td rowspan = "2">생존</td>
                <td>Precision</td>
                <td>Recall</td>
                <td>f1-score</td>
                <td>Accuracy</td>
            </tr>
            <tr>
                <td>0.994</td>
                <td>0.985</td>
                <td>0.989</td>
                <td rowspan = "3">0.982</td>
            </tr>
        <tr>
                <td rowspan = "2">부도</td>
                <td>Precision</td>
                <td>Recall</td>
                <td>f1-score</td>
            </tr>
        <tr>
                <td>0.916</td>
                <td>0.983</td>
                <td>0.938</td>
            </tr>
        </table>

   2. 6개월 예측모델
        1. XGBoost + 오버샘플링 진행하지 않음
        2. Train set 과적합은 하이퍼파라미터 튜닝 파트에서 해결 시도

        <br>

        <table>
        <th colspan = "6">6개월 예측모델, XGBoost + 오버샘플링 진행하지 않음 평가점수</th>
        <tr>
            <td rowspan = "4">Train</td>
            <td rowspan = "2">생존</td>
            <td>Precision</td>
            <td>Recall</td>
            <td>f1-score</td>
            <td>Accuracy</td>
        </tr>
        <tr>
            <td>1.0</td>
            <td>1.0</td>
            <td>1.0</td>
            <td rowspan = "3">1.0</td>
        </tr>
        <tr>
            <td rowspan = "2">부도</td>
            <td>Precision</td>
            <td>Recall</td>
            <td>f1-score</td>
        </tr>
        <tr>
            <td>1.0</td>
            <td>1.0</td>
            <td>1.0</td>
        </tr>
        <tr>
            <td rowspan = "4">Test</td>
            <td rowspan = "2">생존</td>
            <td>Precision</td>
            <td>Recall</td>
            <td>f1-score</td>
            <td>Accuracy</td>
        </tr>
        <tr>
            <td>0.986</td>
            <td>0.984</td>
            <td>0.985</td>
            <td rowspan = "3">0.975</td>
        </tr>
        <tr>
            <td rowspan = "2">부도</td>
            <td>Precision</td>
            <td>Recall</td>
            <td>f1-score</td>
        </tr>
        <tr>
            <td>0.909</td>
            <td>0.919</td>
            <td>0.913</td>
        </tr>
        </table>

   1. 1년 예측모델
   		1. XGBoost + ADASYN
		1. Train set 과적합은 하이퍼파라미터 튜닝 파트에서 해결 시도

        <br>

         <table>
         	<th colspan = "6">1년 예측모델, RandomForest + ADASYN 평가점수</th>
         	<tr>
             	<td rowspan = "4">Train</td>
         	    <td rowspan = "2">생존</td>
         	    <td>Precision</td>
             	<td>Recall</td>
             	<td>f1-score</td>
               <td>Accuracy</td>
         	</tr>
         	<tr>
         	    <td>1.0</td>
         	    <td>1.0</td>
             	<td>1.0</td>
             	<td rowspan = "3">1.0</td>
         	</tr>
           <tr>
         	    <td rowspan = "2">부도</td>
         	    <td>Precision</td>
             	<td>Recall</td>
             	<td>f1-score</td>
         	</tr>
           <tr>
         	    <td>1.0</td>
             	<td>1.0</td>
             	<td>1.0</td>
         	</tr>
         	<tr>
             	<td rowspan = "4">Test</td>
         	    <td rowspan = "2">생존</td>
         	    <td>Precision</td>
             	<td>Recall</td>
             	<td>f1-score</td>
             	<td>Accuracy</td>
         	</tr>
         	<tr>
         	    <td>0.992</td>
         	    <td>0.972</td>
             	<td>0.982</td>
             	<td rowspan = "3">0.97</td>
         	</tr>
           <tr>
         	    <td rowspan = "2">부도</td>
         	    <td>Precision</td>
             	<td>Recall</td>
             	<td>f1-score</td>
         	</tr>
           <tr>
         	    <td>0.858</td>
         	    <td>0.954</td>
             	<td>0.903</td>
         	</tr>
         </table>
		 
   4. 과적합 해소, 더 나은 평가점수를 목표로 하이퍼파라미터 튜닝 진행
8. 각 모델들에 대해 GridSearch 방식으로 하이퍼파라미터 튜닝 진행
   1. 하이퍼파라미터 튜닝 진행 코드 예시

      ```python
      model_3m_randomOver = Pipeline([
              ('sampling', RandomOverSampler(random_state=random_state)),
              ('clf', XGBClassifier(n_estimator = 1000,
                                    learning_rate = 0.1,
                                    max_depth=6,
                                    min_child_weight=12,
                                    random_state=random_state,
                                    n_jobs=-1))])
      
      xgb_param_grid_3m_3 = {'clf__gamma':[i/100 for i in range(1,11)]}
      
      hr_grid_3m = GridSearchCV(estimator=model_3m_randomOver,
                             param_grid=xgb_param_grid_3m_3,
                             scoring='f1_micro',
                             n_jobs=8,
                             cv=4,
                             refit=True, 
                             return_train_score=True)
      
      hr_grid_3m.fit(X_3m, y_3m)
      hr_grid_df_3m = pd.DataFrame(hr_grid_3m.cv_results_)
      hr_grid_df_3m[['params', 'mean_test_score', 'mean_train_score']].sort_values(by=['mean_test_score'], ascending=False)
      
      # 아래 출력된 데이터프레임을 참고하여 하이퍼파라미터 선정
      ```

      | 출력값 | params               | mean_test_score | mean_train_score |
      | ------ | -------------------- | --------------- | ---------------- |
      | 0      | {'clf__gamma': 0.01} | 0.977953        | 0.992388         |
      | 1      | {'clf__gamma': 0.02} | 0.977953        | 0.992388         |
      | 7      | {'clf__gamma': 0.08} | 0.977953        | 0.992388         |
      | 8      | {'clf__gamma': 0.09} | 0.977953        | 0.992388         |
      | 9      | {'clf__gamma': 0.1}  | 0.977953        | 0.992388         |
      | 2      | {'clf__gamma': 0.03} | 0.977559        | 0.992257         |
      | 3      | {'clf__gamma': 0.04} | 0.977559        | 0.992257         |
      | 4      | {'clf__gamma': 0.05} | 0.977559        | 0.992257         |
      | 6      | {'clf__gamma': 0.07} | 0.977165        | 0.992388         |
      | 5      | {'clf__gamma': 0.06} | 0.976772        | 0.992126         |

9. feature importance 측정
   1. importance가 0인 항목들도 존재했으나, 데이터 범위 중간에 위치한 데이터 (예 : 총 12개월의 유가 데이터 중 6개월 째 유가 데이터) 인 경우가 대다수여서, 해당 피쳐들을 제외하는 작업이 부자연스러웠으므로 피쳐 제외 없이 그대로 진행함
10. 최종적으로 사용한 3개월, 6개월, 1년 부도 예측 모델의 평가점수는 아래와 같음

	<table>
		<th colspan = "6">3개월 부도예측 모델 평가점수</th>
		<tr>
		<td rowspan = "4">Train</td>
		    <td rowspan = "2">생존</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
	      <td>Accuracy</td>
		</tr>
		<tr>
		    <td>0.999</td>
		    <td>0.989</td>
		<td>0.994</td>
		<td rowspan = "3">0.994</td>
		</tr>
	  <tr>
		    <td rowspan = "2">부도</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		</tr>
	  <tr>
		    <td>0.989</td>
		<td>0.999</td>
		<td>0.994</td>
		</tr>
		<tr>
		<td rowspan = "4">Test</td>
		    <td rowspan = "2">생존</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		<td>Accuracy</td>
		</tr>
		<tr>
		    <td>0.996</td>
		    <td>0.979</td>
		<td>0.987</td>
		<td rowspan = "3">0.978</td>
		</tr>
	  <tr>
		    <td rowspan = "2">부도</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		</tr>
	  <tr>
		    <td>0.888</td>
		    <td>0.976</td>
		<td>0.929</td>
		</tr>
	</table>


	<table>
		<th colspan = "6">6개월 부도예측 모델 평가점수</th>
		<tr>
		<td rowspan = "4">Train</td>
		    <td rowspan = "2">생존</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
	      <td>Accuracy</td>
		</tr>
		<tr>
		    <td>0.994</td>
		    <td>0.991</td>
		<td>0.993</td>
		<td rowspan = "3">1.0</td>
		</tr>
	  <tr>
		    <td rowspan = "2">부도</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		</tr>
	  <tr>
		    <td>0.948</td>
		<td>0.964</td>
		<td>0.956</td>
		</tr>
		<tr>
		<td rowspan = "4">Test</td>
		    <td rowspan = "2">생존</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		<td>Accuracy</td>
		</tr>
		<tr>
		    <td>0.986</td>
		    <td>0.985</td>
		<td>0.986</td>
		<td rowspan = "3">0.975</td>
		</tr>
	  <tr>
		    <td rowspan = "2">부도</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		</tr>
	  <tr>
		    <td>0.912</td>
		    <td>0.916</td>
		<td>0.913</td>
		</tr>
	</table>


	<table>
		<th colspan = "6">1년 부도예측 모델 평가점수</th>
		<tr>
		<td rowspan = "4">Train</td>
		    <td rowspan = "2">생존</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
	      <td>Accuracy</td>
		</tr>
		<tr>
		    <td>1.0</td>
		    <td>0.998</td>
		<td>0.999</td>
		<td rowspan = "3">0.999</td>
		</tr>
	  <tr>
		    <td rowspan = "2">부도</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		</tr>
	  <tr>
		    <td>0.998</td>
		<td>1.0</td>
		<td>0.999</td>
		</tr>
		<tr>
		<td rowspan = "4">Test</td>
		    <td rowspan = "2">생존</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		<td>Accuracy</td>
		</tr>
		<tr>
		    <td>0.992</td>
		    <td>0.971</td>
		<td>0.982</td>
		<td rowspan = "3">0.969</td>
		</tr>
	  <tr>
		    <td rowspan = "2">부도</td>
		    <td>Precision</td>
		<td>Recall</td>
		<td>f1-score</td>
		</tr>
	  <tr>
		    <td>0.852</td>
		    <td>0.957</td>
		<td>0.901</td>
		</tr>
	</table>


11. 모델을 pickle로 저장하여 사용
12. 기업 하나의 최신 데이터를 모델에 넣어 예측해 본 결과

    ```Python
    model_prediction('LG전자', year=2) # 별도로 제작한 함수
    
    # 출력 결과
    {'result_6m': 'False', # 부도여부
     'proba_6m_false': 97.09, # 생존확률
     'proba_6m_true': 2.91, # 부도확률
     'result_3m': 'False',
     'proba_3m_false': 95.53,
     'proba_3m_true': 4.47,
     'result_1y': 'False',
     'proba_1y_false': 96.49,
     'proba_1y_true': 3.51}
    ```


### 2-5. 데이터 시각화 및 웹 어플리케이션 제작
1. **프로젝트 라이브 URL : http://13.124.187.87:8000**
2. [Django 어플리케이션 폴더 보러 가기](https://github.com/limyj0708/bankruptcy_prediction/tree/master/05_Django_and_Visualization/Django/bankruptcyprediction)
3. Django 프레임워크를 기반으로, [plotly](https://plotly.com/)의 자바스크립트 라이브러리로 데이터 시각화 진행
4. 사용자가 기업 이름을 검색하면, AWS Redshift로 쿼리를 보내 결과를 받아와서 사용하는 구조
   1. 검색 시작 화면
   ![searching_page_main](https://raw.githubusercontent.com/limyj0708/bankruptcy_prediction/master/readme_image/01_searching_page_main.gif)
   <br>
   
   2. 검색 결과 화면
   ![searching_page_result](https://raw.githubusercontent.com/limyj0708/bankruptcy_prediction/master/readme_image/02_searching_result_total_page.gif)
