#!/bin/sh
# instance들에서 크롤링 결과물을 한 번에 다운로드 받기 위한 스크립트
start_num=1
last_num=32
instance_num=${start_num}
scp_upload_prefix="gcloud compute scp --recurse "
machine_prefix="cw-machine-"
remote_dir=":~/SeoulK/"
name_todownload="_seoulK_with_body.csv"
local_destination=" /Users/youngjinlim/Downloads/file_from_instances"
zone_prefix=" --zone"

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
    final_file_name=$machine_name$name_todownload
    
    echo $scp_upload_prefix$machine_name$remote_dir$final_file_name$local_destination$zone_prefix$zone
    $scp_upload_prefix$machine_name$remote_dir$final_file_name$local_destination$zone_prefix$zone &

    ((instance_num="${instance_num}"+1))
done

wait
echo "All processes are done!"