#!/bin/sh
# 분할한 크롤링 대상 url csv 파일을 gcloud compute instnace들에 업로드하는 스크립트.
start_num=1
last_num=32
((instance_num="${start_num}"))
machine_prefix=" cw-machine-"
scp_upload_prefix="gcloud compute scp "
zone_prefix=" --zone"
name_tosend="SeoulK/seoulK_url/seoulK.csv"
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

    name_origin="SeoulK/seoulK_url/seoulK_"$instance_num".csv"
    mv $name_origin $name_tosend

    machine_name=$machine_prefix$instance_num
    echo $scp_upload_prefix$name_tosend$zone_prefix$zone$machine_name$remote_dir
    $scp_upload_prefix$name_tosend$zone_prefix$zone$machine_name$remote_dir

    mv $name_tosend $name_origin
    ((instance_num="${instance_num}"+1))
done

wait
echo "All processes are done!"