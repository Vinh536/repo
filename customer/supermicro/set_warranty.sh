#!/bin/bash

if [[ $# -eq 1 ]]; then
    echo "Please enter the shipping date (Month/Day/Year): ";
    read shipping_date;
    IFS="/"
    # Plug the shipping date into a temporary value. Then split by the built-in variable "IFS".
    read -a strarr <<< ${shipping_date};
    month=${strarr[0]};
    day=${strarr[1]};
    year=$( expr ${strarr[2]} + 3 );

    later_shipment_date_flag=1;

else
# This boolean value (can be true or false) is to handle shipment offsets that might overflow to the next month.
# When we are NOT modifying for a later shipment date (i.e. just run this script with NO VARIABLES ADDED)
# then this value will be false (or "zero") and will be used for a variable called "today" later in the script.
later_shipment_date_flag=0;
# Determine the month since every month has a different number of dates.
month=$( date +%m )
day=$(date +%d)
# Add three years to the current year.
year=$( expr $( date +%Y ) + 3)
fi
# Use the number of days in the month to determine the cut off date for the warranty before setting the warranty date.
month_name=$( echo $( date +%B ) );
cut_off_date=0;

# I did not feel like doing a switch statement but that'd be better.
if [[ ${month_name} == 'January' ]]; then
	cut_off_date=31;
fi
if [[ ${month_name} == 'February' ]]; then
	cut_off_date=28;
fi
if [[ ${month_name} == 'March' ]]; then
	cut_off_date=31;
fi
if [[ ${month_name} == 'April' ]]; then
	cut_off_date=30;
fi
if [[ ${month_name} == 'May' ]]; then
	cut_off_date=31;
fi
if [[ ${month_name} == 'June' ]]; then
	cut_off_date=30;
fi
if [[ ${month_name} == 'July' ]]; then
	cut_off_date=31;
fi
if [[ ${month_name} == 'August' ]]; then
	cut_off_date=31;
fi
if [[ ${month_name} == 'September' ]]; then
	cut_off_date=30;
fi
if [[ ${month_name} == 'October' ]]; then
	cut_off_date=31;
fi
if [[ ${month_name} == 'November' ]]; then
	cut_off_date=30;
fi
if [[ ${month_name} == 'December' ]]; then
	cut_off_date=31;
fi

# Now we need to check if adding a week goes beyond the cut off date.
if [[ ${day} -gt ${cut_off_date} ]]; then
        if [[ ${later_shipment_date_flag} -eq 1 ]]; then
            # We might wind up with an edge case such as July 29th (cut off is the 31st).
            # So let's calculate the modulo to figure out the remainder to determine the remaining days
            # To add up to seven days.
            today=$( expr 7 - $( expr ${cut_off_date} % ${strarr[1]} ));
            difference=${today};
        else
	    # Calculate the difference between cut off date and today.
	    today=$( date +%e );
	    # Add one to the date to account for starting the month on the 1st.
	    difference=$( expr $( expr ${cut_off_date} - ${today} ) + 1);
        fi
	month=$( expr $( echo -n ${month} ) + 1);
        if [[ ${month} -gt 12 ]]; then
            offset=$(expr ${month} - 12);
            month=${offset};
            year=$( expr ${year} + 1 );
        fi
	# Accounting for appending a zero in front if the number is less than double digits.
	if [[ ${month} -lt 10 ]]; then
		month=$( echo -e "0${month}");
	fi
	day=${difference}
	# Same as before. Accounting for if less than double digits.
	if [[ ${day} -lt 10 ]]; then
		day=$( echo -e "0${day}");
	fi
fi

# Now compose each of the variables into a string. Use the string to set the warranty through the FRU and the DMI table.
string="Xamount_Warranty_${month}-${day}-${year}";

if [[ $( grep -i 'VERSION_ID' /etc/os-release ) == *"10"* ]]; then
	cd /opt/afulnx64;
	./amidelnx_26_64 /BT ${string};

# Setting warranty under the FRU (Field Replaceable Unit) "Product Asset Tag" field. This is visible from the BMC's web UI.
#ipmi/ipmicfg-linux.x86_64 -fru PAT ${string};
	/root/IPMICFG -fru PAT ${string};
else
	cd /opt/dmi;
	./amidelnx_26_64 /BT ${string};
	/opt/dmi/IPMICFG -fru PAT ${string};
fi
