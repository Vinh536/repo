for i in $( cat osips ); 
do 
	echo $i; 
	sshpass -p ocptester ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "/root/smc_sum -c ChangeBiosCfg --file cerebras_supermicro.xml --reboot --skip_unknown"; 
done
