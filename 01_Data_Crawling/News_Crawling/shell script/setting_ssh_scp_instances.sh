#!/bin/sh
# 처음 생성한 gcloud compute instance들에 바로 scp 접근이 가능하도록 세팅하는 스크립트
start_num=1
last_num=32
instance_num=${start_num}
ssh_prefix="gcloud compute ssh"
machine_prefix=" cw-machine-"
zone_prefix=" --zone"
key_check=" --strict-host-key-checking=no"

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
    echo $ssh_prefix$machine_prefix$instance_num$zone_prefix$zone
    $ssh_prefix$machine_prefix$instance_num$zone_prefix$zone$key_check &
    ((instance_num="${instance_num}"+1))
done


wait
echo "All setting processes are done!"