#!/usr/bin/python
from datetime import date
from fio_configurations import fio_configurations
import os
import sys
import re
import subprocess
import time
# Helper function for scanning /sys/block/ for devices.
def walk(path):
    for (path, block_devices, irrelevant) in os.walk(path,topdown=True):
        devices = [device for device in block_devices if not_filtered(device)]
        return devices
# Helper function for handling the os module from Python.
def parser(command, parent_directory, device_name, additional_arguments):
    device_name = str(device_name)
    parsed = os.popen(command + " " + 
                parent_directory + device_name + additional_arguments).readlines()
    return next(iter(parsed),None).split('\n')[0]
# Filter out loop devices from /sys/block/ output.
def not_filtered(device):
    #Loopback devices like in-memory snap devices.
    if 'loop' in device:
        return False
    #Serial read devices like CD-ROM drives.
    if 'sr' in device:
        return False
    # If all filters passed, then this is not a filtered device.
    return True
# Builds a Dictionary object for each device to pass into fio_configurations.
def device_attributes(device):
    attributes = {
        'name'          : '/dev/' + device,
        'model'         : model(device),
        'size'          : capacity(device),
        'serial'        : serial_number(device),
        'firmware'      : firmware(device),
        'type'          : device_type(device),
        'block_size'    : block_size(device),
        'is_raid_device': is_raid_device(device)
    }
    return attributes
# Captures the human-readable model name of the drive.
def model(device):
    return str(parser("cat", "/sys/block/", device, "/device/model"))
# Captures the size of available space; returns size in GB.
def capacity(device):
    amount_in_bytes = int(parser("cat", "/sys/block/", device, "/size")) * 512
    amount_in_gigabytes = amount_in_bytes / (1024 * 1024 * 1024)
    return str(amount_in_gigabytes)
# WWID includes: device type (e.g. t10.ATA), Model name, Serial Number.

# We can capture the serial number from the WWID.
def serial_number(device):
    # WWID includes: device type (e.g. t10.ATA), Model name, Serial Number.
    # If the device type is t10, then it does not have a WWN.
    wwid = None
    if 'nvme' in device:
        wwid = "".join(parser("cat", "/sys/block/", device, "/device/serial"))
    else:
        wwid = "".join(parser("cat", "/sys/block/", device, "/device/wwid"))
    regex = re.findall(r'\S+', wwid)
    serial = regex[-1]
    return serial

# Captures the last four digits of the device's firmware revision.
def firmware(device):
    if 'nvme' in device:
        return str(parser("cat", "/sys/block/", device, "/device/firmware_rev"))
    else:
        return str(parser("cat", "/sys/block/", device, "/device/rev"))
# Check whether the drive is an HDD, SSD, or NVMe drive.
def device_type(device):
    # If the device reports a rotation of 0, it is an SSD.
    parsed = parser("cat", "/sys/block/", device, "/queue/rotational")
    if int(parsed) == 0:
        # All NVMe drives include the NVMe prefix in their logical name.
        if 'nvme' in str(device):
            return 'NVMe'
        return 'SSD'
    # If the device reports a rotation of 1, it is a spinning device.
    return 'HDD'
def block_size(device):
    parsed = parser("sudo blockdev --getbsz", "/dev/", device, "")
    return str(parsed)

# Get number of CPU cores.
def core_count():
    parsed = os.popen('lscpu -e | wc -l').readlines()
    return str(int(next(iter(parsed),None).split('\n')[0]) -1)

# Check for the presence of a RAID controller.
# If one is found, check if the device is connected to a RAID controller.
# TODO: When RAID device is found, return the model name.
# TODO: Separate out this from device Dictionary; make separate function.
# If RAID controller is found, use storcli/perccli utility to find device information.
def is_raid_device(device):
    output = os.popen('lspci|grep -i "RAID"').readlines()
    if not output:
        return "No"
    return str(next(iter(output),None))

def menu(device):
    print "******************************"
    print "Detected " + device['name']
    print "Available Space: " + device['size'] + ' GB'
    print "Model name: " + device['model']
    print "Serial Number: " + device['serial']
    print "Firmware Revision: " + device['firmware']
    #print "Device type is: " + device['type']
    #print "I/O depth of: " + device['queue_depth']
    #print "Block size: " + device['block_size'] + " bytes"
    #print "Transport model: " + device['interface']
    #print "Connected to RAID?: " + device['is_raid_device']
    print "******************************"

def get_system_serial():
    serial = subprocess.check_output("cat /sys/class/dmi/id/product_serial", shell=True)
    return serial.decode('utf-8')

def check_for_errors(logfile):
    # Filter down the log file to just the errors. The JSON ouput is quite terse.
    output = subprocess.check_output('grep "error" %s' % logfile, shell=True)
    errors = output.decode('utf-8')
    err_list = []
    for line in errors.split('\n'):
	# This is the format of the error statements. If we detect the quantity to be zero, skip.
        if '"error" : 0,' in line:
            continue
        else:
            err_list.append(line)
    return err_list

def run_fio(devices_to_test, output_file):
    # Check if the list is empty; if so then skip.
    if devices_to_test:
        print "Performing fio test on " + str(len(devices_to_test)) + " drives."
        print "Skipping fio test for " + str(len(devices_to_skip)) + " drives."
        # Build the configuration file for the test. Output to a file with today's timestamp.
        config_file = fio_configurations(devices_to_test, core_count(), 'libaio')
        serial = get_system_serial()
        output_format = ' --output-format=json --output=' + output_file
        additional_flags = ' --norandommap --refill_buffers --timeout=14400'
        # Run the benchmark
        subprocess.call('sudo fio configs.fio ' + output_format + additional_flags, shell=True)
        return True
    else:
        return False

def run_smartctl_short_test(devices_to_skip, smartctl_output_file):
    if devices_to_skip:
        for device in devices_to_skip:
	        print device['name']
	        command = 'sudo smartctl -t short  -ia %s --log error > %s' % (device['name'], smartctl_output_file)
	        subprocess.check_output(command, shell=True)
	        print "Waiting five minutes for smartctl short tests to complete"
	        print "Saving smartctl attributes output to %s" % smartctl_output_file
        time.sleep(300)
        print "Storage tests completed"
        return True
    return False

# MAIN FUNCTION
if __name__ == '__main__':
    # Storage server IP
    server = "10.0.8.40:/data/storage/logs/disk_test/"

    # Scan for storage devices.
    block_devices = walk('/sys/block/')
    # Pass the results into a list for the test.
    devices = []
    devices_to_test = []
    # This is for SSDs since we won't be stress testing them with fio.
    devices_to_skip = []
    for device in block_devices:
        devices.append(device_attributes(device))
    # Display device information to the user for each device found.
    for device in devices:
        menu(device)
        if device['type'] == 'HDD':
		devices_to_test.append(device)
        else:
        	devices_to_skip.append(device)
    print "Detected " + str(len(devices)) + " amount of drives."
    serial = get_system_serial()
    # For HDD test.
    output_file = str(serial).strip() + "_fio_results_" + str(date.today()) + '.json'
    ran_fio = run_fio(devices_to_test, output_file)
    # Once the fio test is completed, we can grep for any errors from the log.
    if ran_fio:
        errors = check_for_errors(output_file)
        if not errors:
            for error in errors:
                print error
	        print "Please troubleshoot issue and then re-run the disk test. Exiting..."
	        sys.exit(1)
        else:
            print "Uploading %s to storage server" % server
            uploading = subprocess.check_output("sshpass -p 0cpT3ster scp -o StrictHostKeyChecking=no %s root@%s" % (output_file, server), shell=True)
            uploading.decode('utf-8')
    # Use Smartctl to run a short test on any SSDs detected
    smartctl_output_file = str(serial).strip() + "_smartctl_results_" + str(date.today()) + '.txt'
    ran_smartctl = run_smartctl_short_test(devices_to_skip, smartctl_output_file)
    if ran_smartctl:
        # Check for errors.
        any_errors = subprocess.check_output("grep 'No Errors Logged' %s" % smartctl_output_file, shell=True)
	decoded = any_errors.decode('utf-8')
        print(decoded)
        if 'No Errors Logged' in decoded:
            print "Completed smartctl short tests."
            print "Storage tests completed"
            print "Uploading %s to storage server" % smartctl_output_file
            uploading = subprocess.check_output("sshpass -p 0cpT3ster scp -o StrictHostKeyChecking=no %s root@%s" % (smartctl_output_file, server), shell=True)
        else:
            print "Errors detected! Check %s for which drives have errors." % smartctl_output_file
