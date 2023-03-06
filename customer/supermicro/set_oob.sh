#!/bin/bash
if [ "$#" -eq 0 ]; then
echo "Useage:./rackipmi IP or ip_list.file"
exit
fi
if [ "$#" -eq 3 ]; then
user=$2
password=$3
else
user=ADMIN
password=Qualcomm5G
fi

SUM="smc_sum";
OOB_FILE="oob.license";

TOTAL=0;
SUCCESS_CTR=0;
FAILURE_CTR=0;
UNKNOWN_CTR=0;

# THIS SCRIPT EXPECTS A FILE CALLED "oob.license" IN THE CURRENT WORKING DIRECTORY!
# IF IT IS NOT FOUND, TELL THE USER TO MAKE THE CORRECT FILE NAME!
function check_for_file_name() {
	if [[ ! -e "./oob.license" ]]; then
		echo "THIS SCRIPT REQUIRES THE OOB LICENSE FILE TO BE CALLED: ${OOB_FILE}";
		echo "Exiting...";
		exit 1;
	fi
}
function remove_carriage_return() {
	# Create a backup if something went wrong...
	cp ${OOB_FILE} ${OOB_FILE}.backup;
	sed 's/\r//g' ${OOB_FILE} > temp_file.txt;
	mv temp_file.txt ${OOB_FILE};
}

function activate_license() {
        mac=$(ipmitool -I lanplus -H $i -U $user -P $password lan print| awk '/MAC Address/ {print $4}'| tr '[:lower:]' '[:upper:]' | sed 's/://g');
        oob=$(grep -i ${mac} ${OOB_FILE} | cut -f 3 -d ";");
        license_attempt=$(${SUM} -i ${i} -u ${user} -p ${password} -c ActivateProductKey --key ${oob});
	# Check to see if the OOB License was activated correctly.
	if [[ ${license_attempt} == *"SFT-OOB-LIC"* ]]; then
		echo "${i}: OOB License Activated!";
		SUCCESS_CTR=$((SUCCESS_CTR + 1));
	elif [[ ${license_attempt} == *"Product key format error"* ]]; then
		echo "${i}: License Not Activated! Wrong format for key! Check for \\r characters!";
		FAILURE_CTR=$((FAILURE_CTR + 1));
	else
		echo "${i}: Unknown error! Check with your systems administrator!";
		UNKNOWN_CTR=$((UNKNOWN_CTR + 1));
	fi

}

# ==========
# MAIN BLOCK
# ==========
check_for_file_name;
remove_carriage_return;

for i in $(cat $1)
do
	activate_license;
	TOTAL=$((TOTAL + 1));
done

echo "+===========================================+"
echo "|Total: ${TOTAL}|Success: ${SUCCESS_CTR}|Failure: ${FAILURE_CTR}|Unknown: ${UNKNOWN_CTR}|";
echo "+===========================================+";
