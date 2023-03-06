#!/bin/bash

unset oc
unset start
unset end
while getopts ":oc:s:e:" opt; do
  case $opt in
    oc) oc=$OPTARG ;;
    s)  start=$OPTARG ;;
    e)  end=$OPTARG ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

if [ -z "$oc" ] || [ -z "$start" ] || [ -z "$end" ]; then
  echo "missing arguments. use flags -oc for oc, -s for start, -e for end"
  echo "start and end are in terms of the leftmost column on TIPS"
  echo "make sure to already be logged in to tips on firefox before running this script"
  exit 1
fi

for i in $(seq $start $end); do 
  firefox http://erp.asasupport.com/tip/burnin.php\?OC\=$oc\&action\=first\&qtyno\=$i; 
done;

for i in $(seq $start $end); do 
  firefox http://erp.asasupport.com/tip/bdone.php\?OC\=$oc\&action\=first\&qtyno\=$i; 
done;
