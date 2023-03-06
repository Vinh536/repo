# Get VMFS6 GUID.
vmfs=$(partedUtil showGuids | grep 'vmfs' | awk '{print $2}')

# Target all drives.
drives=$(esxcli storage core device list | grep 'naa' | grep 'Devfs' | awk '{print $3}')

# Create a GPT label for each drive.
for i in `echo $drives`; do partedUtil mklabel $i gpt; done

# Create the partition blocks for each drive w/ first usable and last usable sectors.
for i in `echo $drives`; do first_sector=$(partedUtil getUsableSectors $i | awk '{print $1}'); last_sector=$(partedUtil getUsableSectors $i | awk '{print $2}'); partedUtil setptbl "$i" "gpt" "1 $first_sector $last_sector $vmfs 0"; done

# Create the datastore with vmkfstools utility.
for i in `echo $drives`; do vmkfstools -C vmfs6 -b 1m -S datastore$((ctr = ctr + 1)) "$i:1"; done

