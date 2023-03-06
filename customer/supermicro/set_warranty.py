#!/usr/bin/python3
import json
import requests
import subprocess

""" As of 05/25/2022, we will begin getting the warranty date from TIP instead of manually plugging it in. """
def get_warranty_date(serial):
    response = requests.get(f"http://10.0.7.170:8000/warranty/{serial}")
    if response:
        output = response.json()
        return output
    else:
        return None

""" The date may not be in the right format, so let's re-arrange the warranty date to reflect the expected string."""
def format_date(dictionary):
    warranty_date = dictionary['warranty']
    # Assume the delimiter will be a hyphen. Of course who knows how consistent this will be in the future...
    date_list = warranty_date.split("-")
    if len(date_list[0]) == 4:
        year  = date_list[0]
        month = date_list[1]
        day   = date_list[2]
        return f"{month}-{day}-{year}"
    else:
        return {"status": 403, "message" : "Unexpected date format was handled! Cannot currently support entering date until this format is understood! EXPECTED <YEAR>-<MONTH>-<DAY>"}

""" Path to DMI/FRU utilities will differ based on the release version."""
def get_os():
    with open("/etc/os-release") as os_info:
        info = os_info.readlines()
        for line in info:
            if "VERSION_ID" in line:
                if "10" in line:
                    return "buster"
                elif "11" in line:
                    return "bullseye"
                else:
                    return None

def insert_dmi(warranty):
    warranty = warranty.strip('"')
    os_version  = get_os() 
    dmi_utility = "amidelnx_26_64"
    if os_version == "buster":
        subprocess.run(f"cd /opt/afulnx64; ./{dmi_utility} /BT {warranty}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        return {"status" : 404, "message" : "Currently unsupported operating system detected! Please use Debian 10!"}

def insert_fru(warranty):
    os_version   = get_os()
    fru_utility  = "/root/IPMICFG"
    if os_version == "buster":
        subprocess.run(f"{fru_utility} -fru PAT {warranty}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    warranty_template    = "Xamount_Warranty_"
    serial               = subprocess.check_output("dmidecode -s system-serial-number", shell=True).decode("utf-8").strip()
    warranty_date        = get_warranty_date(serial)
    # Format the date
    expected_date_format = format_date(warranty_date)
    warranty = warranty_template + expected_date_format
    # Now enter the date into the DMI table and FRU.
    insert_dmi(warranty)
    insert_fru(warranty)
    print(json.dumps({
        "status"  : 200,
        "message" : f"Inserted following warranty date: {warranty} into {serial}" 
    }))
