for i in $( cat $1 );
do
	cat current-dhcp | sed 's/://g' | grep -i  $i | head -n 1;
done
