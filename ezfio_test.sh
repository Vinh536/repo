#!/bin/bash

apt-get install git fio sdparm -y;
git clone https://github.com/earlephilhower/ezfio;

serial="$(cat /sys/class/dmi/id/product_serial)";
logfile_path=/tmp/sda/;
server_log_path=/data/customer/cerebras/ezfio_logs;

mkdir ${logfile_path};

FAILLOG="/root/EZFIO_FAILED.log";
logfile_nvme0n1=/tmp/sda/${serial}_sda_ezfio.ods;
#logfile_nvme0n1=${logfile_path}/nvme0n1/${serial}_nvme0n1_ezfio.ods;
#logfile_nvme1n1=${logfile_path}/nvme1n1/${serial}_nvme1n1_ezfio.ods;
#logfile_nvme2n1=${logfile_path}/nvme2n1/${serial}_nvme2n1_ezfio.ods;

for device in $( ls /sys/block | grep -v 'lo' ); do
	/root/ezfio_test_${device}.sh &
done

until [[ -f "${logfile_nvme0n1}" ]]; do
	if [[ ! -f ${logfile_nvme0n1} ]]; then
		echo "Still waiting for ${logfile_nvme0n1}...";
        fi

	sleep 300;
done

if [[ ! -f ${FAILLOG} ]]; then
    echo "Copying logs to server"
    /usr/bin/scp -r "${logfile_path}" root@10.0.8.40:${server_log_path}/; echo "Ezfio Testing Complete";
else
    echo "Test did not complete successfully!";
    cat ${FAILLOG};
fi
