for i in $(cat cmc-iplist-test); do 
	echo "CMC IP: $i"; 
	for j in $(racadm -r $i -u root -p calvin getmodinfo | grep 'Server' | awk '{print $1}' ); 
		do echo -n $j "IP: " ; racadm -r $i -u root -p calvin getniccfg -m $j | grep 'IP Address' | awk '{print $4}'; 
	done; 
done
