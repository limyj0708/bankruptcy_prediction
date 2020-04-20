import pandas as pd
import datetime

item_names = ['거래량 (120일 평균)(주)',
 '거래량 (20일 평균)(주)',
 '거래량 (5일 평균)(주)',
 '거래량 (60일 평균)(주)',
 '거래량(주)',
 '매도수량(개인)(주)',
 '매도수량(기관계)(주)',
 '매도수량(외국인계)(주)',
 '매수수량(개인)(주)',
 '매수수량(기관계)(주)',
 '매수수량(외국인계)(주)',
 '변동성 (120일)',
 '변동성 (20일)',
 '변동성 (5일)',
 '변동성 (60일)',
 '변동성 (현금배당반영,20일)',
 '수익률 (1개월)(%)',
 '수익률 (1주)(%)',
 '수익률 (3개월)(%)',
 '수익률 (6개월)(%)',
 '수익률(%)',
 '수정주가 (20일 평균)(원)',
 '수정주가 (5일 평균)(원)',
 '수정주가(원)',
 '순매수수량(개인)(120일합산)(주)',
 '순매수수량(개인)(20일합산)(주)',
 '순매수수량(개인)(5일합산)(주)',
 '순매수수량(개인)(60일합산)(주)',
 '순매수수량(개인)(주)',
 '순매수수량(기관계)(120일합산)(주)',
 '순매수수량(기관계)(20일합산)(주)',
 '순매수수량(기관계)(5일합산)(주)',
 '순매수수량(기관계)(60일합산)(주)',
 '순매수수량(기관계)(주)',
 '순매수수량(외국인계)(120일합산)(주)',
 '순매수수량(외국인계)(20일합산)(주)',
 '순매수수량(외국인계)(5일합산)(주)',
 '순매수수량(외국인계)(60일합산)(주)',
 '순매수수량(외국인계)(주)',
 '시가총액 (52주 평균)(백만원)',
 '시가총액 (52주 평균,보통)(백만원)',
 '종가(원)']

def initialize_df_mold():
    df_mold = pd.DataFrame()
    df_mold['stock_code'] = None
    df_mold['company_name'] = None
    df_mold['date'] = None
    for each_item in item_names:
        df_mold[each_item] = None
    return df_mold

stock_chunk_from_csv_gen = pd.read_csv('2002_2020_stock_data_sorted.csv', dtype={'stock_code':'object'}, chunksize=1)
raw_columns = stock_chunk_from_csv_gen.__next__().columns # csv의 컬럼명 추출

for each_date in raw_column:
    df_mold = initialize_df_mold()
    stock_certain_column = pd.read_csv('2002_2020_stock_data_sorted.csv', dtype={'stock_code':'object', each_date:'object'}, usecols=["stock_code", "company_name", "item_name", each_date])
    # csv의 총 용량이 4GB에 달하기 때문에, 전체 컬럼을 불러올 수가 없어서 필요 컬럼만 하나씩 불러와서 처리 
    stock_code_former = 0
    idx_mold = -1
    for idx in stock_certain_column.index:
        stock_code = stock_certain_column.iloc[idx]['stock_code']
        if stock_code_former != stock_code:
            idx_mold += 1 # 다른 기업이 등장하면 다음 라인으로 넘어감
        df_mold.at[idx_mold, 'stock_code'] = stock_code
        df_mold.at[idx_mold, 'company_name'] = stock_certain_column.iloc[idx]['company_name']
        df_mold.at[idx_mold, 'date'] = datetime.datetime.strptime(each_date, '%Y-%m-%d')
        df_mold.at[idx_mold, stock_certain_column.iloc[idx]['item_name']] = stock_certain_column.iloc[idx][each_date]
        stock_code_former = stock_code
    df_mold.to_csv(each_date+'_stock_data.csv') # 각 날짜별 주가데이터 csv로 저장