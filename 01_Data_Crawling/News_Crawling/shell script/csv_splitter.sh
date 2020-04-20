# 지정한 라인 숫자대로 파일을 분할하는 스크립트

FILENAME=seoulK_dedup.csv # 분할하려고 하는 csv 파일명
HDR=$(head -1 $FILENAME) # 헤더 추출
split -l 15909 $FILENAME xyz # 15909줄씩 분할
n=1
for f in xyz* # 생성된 xyz~ 파일들을 가공
do
     if [ $n -gt 1 ]; then # n이 1보다 크다면, 즉 첫 번째 파일이 아니라면 파일에 헤더를 삽입함
          echo $HDR >> "seoulK_"${n}'.csv'
     fi
     cat $f >> "seoulK_"${n}'.csv' # xyz~ 파일의 내용을 추가함
     rm $f
     ((n++))
done