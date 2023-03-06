#!/bin/bash

for i in $( cat $1 ); 
do 
	echo $i; 
	ipmitool -I lanplus -H $i -U ADMIN -P Admin123 chassis bootdev pxe;
	ipmitool -I lanplus -H $i -U ADMIN -P Admin123 chassis power reset;
done
