from sklearn.model_selection import StratifiedShuffleSplit
from imblearn.over_sampling import *
from sklearn.metrics import classification_report
import numpy as np

def suffle_and_validation(X, y, model, n_splits=8, random_state=42, test_size=0.25, oversampling=False):
    rs = StratifiedShuffleSplit(n_splits=n_splits, random_state=random_state, test_size=test_size)
    
    accuracy_list_train = []
    precision_list_train_0 = []
    recall_list_train_0 = []
    f1_score_list_train_0 = []
    precision_list_train_1 = []
    recall_list_train_1 = []
    f1_score_list_train_1 = []

    accuracy_list_test = []
    precision_list_test_0 = []
    recall_list_test_0 = []
    f1_score_list_test_0 = []
    precision_list_test_1 = []
    recall_list_test_1 = []
    f1_score_list_test_1 = []
    
    idx = 1

    for train_index, test_index in rs.split(X, y):

        X_train = X.iloc[train_index]
        X_test = X.iloc[test_index]
        y_train = y.iloc[train_index]
        y_test = y.iloc[test_index]
        
        model_cache = model # 테스트용으로 학습되지 않은 모델을 매 반복마다 준비
        
        if oversampling == 'RandomOverSampling':
            ros = RandomOverSampler(random_state=random_state)
            X_train, y_train = ros.fit_resample(X_train,y_train)
        elif oversampling == 'ADASYN':
            X_train, y_train = ADASYN(random_state=random_state).fit_resample(X_train, y_train)
        elif oversampling == 'SMOTE':
            X_train, y_train = SMOTE(random_state=random_state).fit_resample(X_train, y_train)
        
        model_cache.fit(X_train, y_train)
        pred_train = model_cache.predict(X_train)
        pred_test = model_cache.predict(X_test)

        report_train = classification_report(y_train, pred_train, output_dict=True)
        report_test = classification_report(y_test, pred_test, output_dict=True)
        
        accuracy_list_train.append(report_train['accuracy'])
        accuracy_list_test.append(report_test['accuracy'])
        
        precision_list_train_0.append(report_train['False']['precision'])
        recall_list_train_0.append(report_train['False']['recall'])
        f1_score_list_train_0.append(report_train['False']['f1-score'])
        precision_list_train_1.append(report_train['True']['precision'])
        recall_list_train_1.append(report_train['True']['recall'])
        f1_score_list_train_1.append(report_train['True']['f1-score'])

        precision_list_test_0.append(report_test['False']['precision'])
        recall_list_test_0.append(report_test['False']['recall'])
        f1_score_list_test_0.append(report_test['False']['f1-score'])
        precision_list_test_1.append(report_test['True']['precision'])
        recall_list_test_1.append(report_test['True']['recall'])
        f1_score_list_test_1.append(report_test['True']['f1-score'])

        idx += 1
    
    # 각 평가점수들을 모아서 평균
    accuracy_list_train_mean = round(np.mean(accuracy_list_train), 3)
    precision_list_train_0_mean = round(np.mean(precision_list_train_0), 3)
    recall_list_train_0_mean = round(np.mean(recall_list_train_0), 3)
    f1_score_list_train_0_mean = round(np.mean(f1_score_list_train_0), 3)
    precision_list_train_1_mean = round(np.mean(precision_list_train_1), 3)
    recall_list_train_1_mean = round(np.mean(recall_list_train_1), 3)
    f1_score_list_train_1_mean = round(np.mean(f1_score_list_train_1), 3)

    accuracy_list_test_mean = round(np.mean(accuracy_list_test), 3)
    precision_list_test_0_mean = round(np.mean(precision_list_test_0), 3)
    recall_list_test_0_mean = round(np.mean(recall_list_test_0), 3)
    f1_score_list_test_0_mean = round(np.mean(f1_score_list_test_0), 3)
    precision_list_test_1_mean = round(np.mean(precision_list_test_1), 3)
    recall_list_test_1_mean = round(np.mean(recall_list_test_1), 3)
    f1_score_list_test_1_mean = round(np.mean(f1_score_list_test_1), 3)
    
    print(model.__class__)
    if oversampling == 'RandomOverSampling':
        print(f'{n_splits}회 최종평균결과_RandomOverSampling')
    elif oversampling == 'ADASYN':
        print(f'{n_splits}회 최종평균결과_ADASYN')
    elif oversampling == 'SMOTE':
        print(f'{n_splits}회 최종평균결과_SMOTE')
    else:
        print(f'{n_splits}회 최종평균결과')
    
    print('Train')
    print(f'생존 | precision : {precision_list_train_0_mean}, recall : {recall_list_train_0_mean}, f1-score:{f1_score_list_train_0_mean}')
    print(f'부도 | precision : {precision_list_train_1_mean}, recall : {recall_list_train_1_mean}, f1-score:{f1_score_list_train_1_mean}')
    print(f'accuracy : {accuracy_list_train_mean}')
    print('Test')
    print(f'생존 | precision : {precision_list_test_0_mean}, recall : {recall_list_test_0_mean}, f1-score:{f1_score_list_test_0_mean}')
    print(f'부도 | precision : {precision_list_test_1_mean}, recall : {recall_list_test_1_mean}, f1-score:{f1_score_list_test_1_mean}')
    print(f'accuracy : {accuracy_list_test_mean}')
    print('================================================')
    
    return (model, X_train, y_train, X_test, y_test) # 넣었던 모델과 마지막 분할 데이터를 반환함