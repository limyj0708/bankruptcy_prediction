#!/bin/sh
# 지정된 숫자의 gcloud compute instance들을 만드는 스크립트
start_num=1
last_num=32
instance_num=${start_num}
create_prefix="gcloud compute instances create"
machine_prefix=" cw-machine-"
image=" --image-project ml-practice-261005 --image cw-machine" # 미리 생성해 둔 이미지로 instance 제작
zone_prefix=" --zone"

while (("${instance_num}"<=last_num)); do
    if (("${instance_num}"<=(start_num+7) )); then # zone당 cpu 제한 때문에 zone을 분리함
        zone=" us-east1-b"
    elif (( "${instance_num}">=(start_num+8) && "${instance_num}"<=(start_num+15) )); then
        zone=" us-west1-a"
    elif (( "${instance_num}">=(start_num+16) && "${instance_num}"<=(start_num+23) )); then
        zone=" us-central1-a"
    else
        zone=" northamerica-northeast1-a"
    fi
    machine_name=$machine_prefix$instance_num
    echo $create_prefix$machine_prefix$instance_num$image$zone_prefix$zone
    $create_prefix$machine_prefix$instance_num$image$zone_prefix$zone &
    ((instance_num="${instance_num}"+1))
done

wait
echo "All creating processes are done!"