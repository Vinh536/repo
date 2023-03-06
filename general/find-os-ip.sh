sshpass -p Kato@101 ssh root@10.0.8.2 dhcp-list > current-dhcp;

for i in $( cat $1 );
do
	sort -k 3 current-dhcp | grep -i  $i | tail -n 1;
done
