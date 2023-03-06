#!/usr/bin/bash

output_file=serial.tempy.txt

Rack_serial=$1
Order_serial=$2
database="curl -X GET http://10.0.7.170./"

# Create database
for i in $(cat serial); do ${database}$i >> serial.tempy.txt ; done
# Sort order_number into temp file. 
cat serial.tempy.txt | grep -i "order_number" | awk -F ':' '/1/ {print $2}' | awk -F ',' '/1/ {print $1}' | sed 's/"\|,//g' >> Order_serial

for e in $(cat Order_serial); do ${database}$e/$i | jq > $i.json; done 


