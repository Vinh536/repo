#!/bin/bash
SERVICE_TAGS=$1
SERVER="10.0.8.40"
USER="root"
PASSWORD="0cpT3ster"
LOGLIST="./logfile.txt"
sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@${SERVER} "ls -l /data/storage/logs/collector | awk '{print $9}'" > $LOGLIST;
echo "Verifying logs on storage server...";

TOTAL_COUNT=0
SUCCESS_COUNT=0
FAILURE_COUNT=0

for i in $( cat ${SERVICE_TAGS} );
do
	LOGS=$( grep $i $LOGLIST | wc -l);
	if [[ $LOGS -gt 0 ]]; then
		echo "Logs found for $i";
		SUCCESS_COUNT=$(( SUCCESS_COUNT + 1 ));
	else
		echo "ERROR! No logs found for $i";
		FAILURE_COUNT=$(( FAILURE_COUNT + 1 ));
	fi
	TOTAL_COUNT=$((TOTAL_COUNT + 1 ));
done

echo "========================";
echo "|        Summary       |"; 
echo "========================";
echo "Total: ${TOTAL_COUNT}|Success: ${SUCCESS_COUNT}|Failure: ${FAILURE_COUNT}";
rm $LOGLIST;
