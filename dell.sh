if [ "$#" -eq 0 ]; then
echo "Useage:./rackipmi IP or ip_list.file"
exit
fi
if [ "$#" -eq 3 ]; then
user=$2
password=$3
else
user=root	
password=calvin
#user=qualys
#password=vmware123
fi
PS3='Please select:'
options=("Boot Bios" "Boot PXE" "Boot HD" "Power On" "Power Off" "Power Reset" "Identify on" "Identify Off" "Check Event Log" "Clear Log" "fw update" "collect inventory" "dell diagnostic test" "enable ipmi over lan" "disable ipmi over lan" "enable bios mode" "enable Uefi mode" "clear pending" "soft reset" "Racadm PXE")
select i in "${options[@]}"
do
case $i in
"Boot Bios")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 chassis bootdev bios

;;

"Boot PXE")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 0 chassis bootdev pxe

;;

"Boot HD")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 chassis bootdev disk

;;


"Power On")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 chassis power on

;;


"Power Off")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 chassis power off

;;


"Power Reset")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 0 chassis power reset

;;

"Identify on")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 chassis identify force

;;

"Identify Off")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 chassis identify 0

;;

"Check Event Log")
echo "----------------------------------------------------------------------------------------------"
echo "Enter a file name for log file"
read file_name
foo () {
	local i=$1
	echo ${i}
	ipmitool -U ${user} -P ${password} -H ${i} -I lanplus sel elist
	racadm -r $i -u root -p calvin getsel
}
	for i in $(cat ${1})
do
	echo ${i}
	foo ${i}|grep -v 'Alternatively\|racadm\|SEC0701\|password\|Security'| tr -d '\r' | grep . | sed -e 's/^ *//' >> ${file_name}&
done


;;

"Clear Log")
cat $1 |xargs -P 200 -I XX ipmitool -U ${user} -P ${password} -H XX -I lanplus -R 1 sel clear

;;

"fw update")
echo "----------------------------------------------------------------------------------------------"
echo "Enter a location with a firmware file name"
read file_name
foo () {
	local i=$1
	echo ${i}
	racadm -r $i -u ${user} -p ${password} update -f $file_name &
}
	for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"collect inventory")
echo "Enter the directory that you wish to store the files."
read Directory

foo () {
	local i=$1
	ST=$(ipmitool -H ${i} -U ${user} -P ${password} -I lanplus fru list | grep 'Product Serial' | uniq | awk '{print $4}')
	racadm -r $i -u ${user} -p ${password} swinventory > ${Directory}${ST}_swinventory.txt
	racadm -r $i -u ${user} -p ${password} hwinventory > ${Directory}${ST}_hwinventory.txt
	ipmitool -H ${i} -U ${user} -P ${password} -I lanplus sel list > ${Directory}${ST}_ipmiLog.txt
	ipmitool -H ${i} -U ${user} -P ${password} -I lanplus sensor >> ${Directory}${ST}_ipmiLog.txt
}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"dell diagnostic test")
foo () {
	local i=$1
	racadm -r $i -u ${user} -p ${password} diagnostics run -m 2 -r pwrcycle
	}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"enable ipmi over lan")
foo () {
	local i=$1
	racadm -r $i -u ${user} -p ${password} set idrac.ipmilan.enable 1  
}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"disable ipmi over lan")
foo () {
	local i=$1
	racadm -r $i -u ${user} -p ${password} set idrac.ipmilan.enable 0  
}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"enable bios mode")
foo () {
	local i=$1
	racadm -r $i -u ${user} -p ${password} set BIOS.BiosBootSettings.BootMode Bios
	racadm -r $i -u ${user} -p ${password} jobqueue create bios.setup.1-1 -r pwrcycle -s TIME_NOW &
}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"enable Uefi mode")
foo () {
	local i=$1
	racadm -r $i -u ${user} -p ${password} set BIOS.BiosBootSettings.BootMode Uefi
	racadm -r $i -u root -p calvin jobqueue create bios.setup.1-1 -r pwrcycle -s TIME_NOW &
}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;

"clear pending")
foo () {
	racadm -r $i -u root -p calvin jobqueue delete --all
	racadm -r $i -u root -p calvin jobqueue delete -i JID_CLEARALL_FORCE 
}
for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done

;;
"soft reset")
cat $1 |xargs -P 200 -I XX racadm -r XX -u ${user} -p ${password} racreset soft

;;

"Racadm PXE")
cat $1 |xargs -P 200 -I XX racadm -r XX -u root -p calvin config -g cfgServerInfo -o cfgServerBootOnce 1
cat $1 |xargs -P 200 -I XX racadm -r XX -u root -p calvin config -g cfgServerInfo -o cfgServerFirstBootDevice PXE
cat $1 |xargs -P 200 -I XX racadm -r XX -u root -p calvin serveraction powercycle

;;

*)
exit
;;






esac
done

