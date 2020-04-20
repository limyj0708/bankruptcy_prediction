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