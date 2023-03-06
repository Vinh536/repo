#!/bin/bash
FAILFLAG=0;
FAILMSG="";
FAILLOG="/root/EZFIO_FAILED.log";

serial="$(cat /sys/class/dmi/id/product_serial)";
logfile_path=/tmp/sda;
server_log_path=/data/customer/cerebras/ezfio_logs;

if [ ! -d "${logfile_path}" ]; then
    mkdir "${logfile_path}"
fi

cd /root/ezfio;

drive="sda";
# Set up the logfile path for each ezfio test; also setup the final ODS file name to expect.
logpath=${logfile_path}/${drive};

if [ ! -d "${logpath}" ]; then
    mkdir "${logpath}";
fi

logfile=${logpath}/${serial}_${drive}_ezfio.ods;
echo "Beginning ezfio test for: /dev/${drive}";
python3 ./ezfio.py --drive /dev/${drive} --output ${logpath}/ --utilization 13 --yes;
ezfio_result=${logpath}/$( ls ${logpath} | grep 'ods' );
# Once the EZFIO test has completed, it will have a unique name. Move it to the expected file name.

if [[ ${ezfio_result} ]]; then
    echo "Discovered: ${ezfio_result}";
    echo "Renaming ${ezfio_result} to ${logfile}";
    mv ${ezfio_result} ${logfile};
    echo "Deleting unnecessary files (to reduce the number of files copied in the recursive scp operation)...";
    rm -rf ${logpath}/details*;

    if [[ -f ${logfile} ]]; then
        echo "Successfully created ${logfile}";
    else
        FAILMSG="ERROR! Failed to create ${logfile}!\n";
        FAILFLAG=1;
	echo ${FAILMSG} >> ${FAILLOG};
    fi
else
    FAILMSG="ODS File for ${drive} was never created. Check if the test ended prematurely!";
    FAILFLAG=1;
    echo ${FAILMSG} >> ${FAILLOG};
fi
