#!/bin/bash

# Create a usage statement. If the required arguments are missing, exit early.
if [[ $# -lt 1  ]]; then
	echo "USAGE: $0 <TEXT FILE OF SERVICE TAGS>";
	exit 1;
fi

FILENAME=$1

# Ask the operator for the customer name of the order. Assume that the operator will have their logs in the following structure:
# /home/$USER/working/$CUSTOMER/logs

#echo -n "Please enter the customer name for these units: ";
#read CUSTOMER_NAME;

# Runs firmware collector
# Change PATH to  your own working directory.
#echo -e "$HOME/working/$CUSTOMER_NAME/logs/" | python3 /home/vinh/scripts/dell_firmware_inventory.py

# ENTER YOUR PATH HERE:
echo -e "/home/vinh/working/github/logs/" | python3 /home/vinh/scripts/dell_firmware_inventory.py

# Sorts inventory file by the sstags list you have.
#for i in $( cat ${FILENAME} ); do grep $i $HOME/working/$CUSTOMER_NAME/logs/dell_firmware_inventory.csv; done > temp.csv

# ENTER YOUR PATH HERE:
for i in $( cat ${FILENAME} ); do grep $i /home/vinh/working/github/logs/dell_firmware_inventory.csv; done > temp.csv

# User_input name.
echo -en "Enter file name below for firmware-inventory: "
read FIRMWARE_FILE_NAME;

# Renames temp file into user_input name.
cp temp.csv temp.csv.backup
mv temp.csv $FIRMWARE_FILE_NAME

# Transfers copy of firmware into storage files.
# DO NOT CHANGE:
sshpass -p ocptester scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $FIRMWARE_FILE_NAME root@10.0.8.41:/home/vinh/firmware-inventory/

# Makes copy to local storage folder.
#cp $FIRMWARE_FILE_NAME $HOME/working/$CUSTOMER_NAME/inventory/

# ENTER YOUR PATH HERE:
cp $FIRMWARE_FILE_NAME /home/vinh/working/github/inventory/


#echo -e
#echo "#############################################################################"
#echo   $user_input has been created. Rename and save into firmware folder. 
#echo "File has been copied to storage server " 
#echo   $user_input has been saved to the inventory folder. 
#echo "#############################################################################"
#echo -e




# Empties LOGS folder.
#rm -rf logs/
#mkdir logs/ 
