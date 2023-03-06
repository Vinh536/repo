#!/usr/bin/bash

# Transfer collector.py into github systems and run. 
# Trnasfer bmcip list into root@10.0.8.41:/home/tony/racadm 
    # Run hw & sw inventory 
        # Option 4 ( Github )


IPLIST=$1
USER="root"
PASSWORD="ocptester"
filename=/home/vinh/working/github/collector.py
read BMC_LIST;


SSHPASS="sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@${IPLIST}" 
COPY_FILE="sshpass -p ${PASSWORD} scp -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null ${filename} ${USER}@${IPLIST}"
CHECKING="sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@$IPLIST} "ls | grep -i collector""
PERMISSIONS="chmod +x collector.py"
STORAGE_SERVER="root@10.0.8.41:/home/tony/racadm"


function Transfer() {
# Run for all systems:
# Transfer collector.py into github systems and run.     
    if [${CHECKING} == collector.py ]; then
        # Systems already had the file. Changing permissions only. 
        ${SSHPASS} && ${PERMISSIONS};
        echo "File is present, Changing permissions now."
    elif 
        # Systems did not have the files. Transferring and changing permissions now. 
        ${COPY_FILE} && ${PERMISSIONS};
        echo "Transferring file and changing permissions now."
    else 
        echo "Error: Invalid file"
    fi
}

# Make running Transfer function

# Trnasfer bmcip list into root@10.0.8.41:/home/tony/racadm 
    # Run hw & sw inventory 
        # Option 4 ( Github )
# Run ONCE: 
function inventory () {
    

}
scp $i root@10.0.8.41:/home/tony/
    /home/vinh/scripts/run_commands /home/vinh/scripts/storage
    echo /home/tony/racadm/hw-inventory -f /home/tony/$i/ -u root -p calvin 
        echo 4
    echo /home/tony/racadm/sw-inventory -f /home/tony/$i/ -u root -p calvin 
        echo 4
    

menu(){
echo -ne "
1) Collector script
2) Hw-inventory script
3) Sw-inventory script
"
    read a
    case $a in 
        1) Transfer ; menu ;;
        # Decide on 1 or 2 functions to use here
        2) Hw-inventory ; menu ;;
        3) Sw-inventory ; menu ;;
    0) exit 0 ;;
    *) echo -e $red"Wrong option."$clear; WrongCommand ;;
    esac
}

# Call menu function
menu 
