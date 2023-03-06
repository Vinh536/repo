#!/usr/bin/python3

import subprocess # For running commands from the shell through Python.
import os         # Useful for checking for filepaths.
import re         # For generating and matching regular expressions.

def run(command):
    #print("===============================")
    #print("Command performed: %s" % command)
    #print("===============================")
    # The appended 'exit 0' is because an empty output will cause subprocess to throw an error.
    # This will bypass the CalledProcessError exception.
    output = subprocess.check_output(command + '; exit 0', shell=True)
    return output.decode('utf-8')

def get_manufacturer():
    command = "ipmitool fru print 0 | grep 'Board Mfg  ' | awk '{print $4}'"
    return run(command)

# Depending on the manufacturer we may store the relevant serial number in a different location.
def get_serial(manufacturer):
    serial = ""
    if 'DELL' in manufacturer or 'Supermicro' in manufacturer:
        serial = run("cat /sys/class/dmi/id/product_serial")
    if 'Intel' in manufacturer:
        serial = run("cat /sys/class/dmi/id/chassis_serial")
    return serial

def get_dmesg():
    dmesg = run('dmesg | grep -i error')
    errors = ""
    for error in dmesg.split('\n'):
        errors += error + '\n'
    errs = "No errors detected"
    if errors:
        return errors
    else:
        return errs

def get_var_log_messages():
    messages = run('grep -i error /var/log/messages')
    errors = ""
    for message in messages.split('\n'):
        errors += message + '\n'
    errs = "No errors detected"
    if errors:
        return errors
    else:
        return errs

def get_sel():
    command = 'ipmitool sel elist'
    return run(command)

# Some customers require an asset tag. Since this varies by platform, check the platform manufacturer.
def get_asset_tag(manufacturer):
    asset_tag = ""
    if 'DELL' in manufacturer:
        asset_tag = run("racadm get Bios.MiscSettings.AssetTag | grep 'Asset' | cut -f 2 -d '='")
        if asset_tag == '' or asset_tag == '\n':
            asset_tag = "No asset tag was detected"
    elif 'Supermicro' in manufacturer:
        asset_tag = run('cat /sys/class/dmi/id/board_asset_tag')
        if asset_tag == '' or asset_tag == '\n':
            asset_tag = "No asset tag was detected"
    else:
        asset_tag = "No asset tag was detected"
    return asset_tag

def get_processors():
    processor = run("dmidecode -t processor | grep 'Version' | cut -f 2 -d : | uniq")
    # Check how many lines were returned. This can be useful to determine if it's a single CPU or dual CPU motherboard.
    processor_qty = run("dmidecode -t processor | grep 'Version' | wc -l")
    # In the event we want to analyze if overclocking is leading to symptoms, keep track of the voltage level.
    processor_volt = run("dmidecode -t processor | grep 'Voltage' | cut -f 2 -d : | uniq")
    return "%s x %s, %s" % (processor_qty.strip(), processor.strip(), processor_volt.strip()) 

def get_memory():
    """ This will remove any channels with no DIMMs installed. Then, it will grab the Size field (the ones with a DIMM installed), check the next 11 lines, and
        filter for the Locator (Bank or just the field 'Locator', which will usually contain the channel label [e.g. A1, B1, etc]), Part Number (to help assist RMAs),
        and the relevant Size field (since we want to compute how much total memory is installed in the system).
    """
    command = "dmidecode -t memory | grep -v 'Size: No Module Installed' | grep 'Size' -A 11 | grep 'Size\|Locator\|Part Number' | grep -v 'Not Specified\|Bank\|Cache\|Volatile\|Logical'"
    installed_memory = run(command)
    part_number = ""
    total_memory = 0
    channels_populated = ""
    for line in installed_memory.split('\n'):
        if 'Size' in line:
            # This field contains the amount of MB on that DIMM.
            total_memory += int(line.split(' ')[1])
        elif 'Part Number' in line:
            part_number = line
        else:
            #channels_populated += line.split(':')[0]
            channels_populated += line.strip() + '\n'

    # Take the total memory amount (expressed in MB) and convert to GB or TB.
    if total_memory < 1000:
        convert_to_gb = total_memory
    else:
        convert_to_gb = total_memory / 1024
    # If the length is larger than 3 digits, then round up to the next highest size (in this case, TB).
    #length = len(str(convert_to_gb))
    memory = 0
    if '.0' in str(convert_to_gb):
        memory = round(convert_to_gb)
    else:
        memory = convert_to_gb

    dimms = "Total Memory : " + str(memory).strip() + ' GB' + '\n' + part_number.strip() + '\n' + "Channels Populated: \n" + channels_populated.strip() + '\n'

    return dimms

def get_motherboard(manufacturer):
    # In the case of Dell EMC systems, the file /sys/class/dmi/id/board_serial (which dmidecode consumes the baseboard serial from) is structured: 
    # .SVCTAG.BOARD_SERIAL.
    command = "dmidecode -t baseboard | grep -i 'Product Name\|Serial Number'"
    serial  = run(command)
    if 'DELL' in manufacturer:
        remove_svctag = serial.split('.')[2]
        serial = remove_svctag
    return serial

def get_bios_version():
    command = 'cat /sys/class/dmi/id/bios_version'
    return run(command)

def get_bmc_version():
    command     = "ipmitool bmc info | grep 'Firmware Revision' | cut -f 2 -d ':'"
    bmc_version = run(command)
    # Remove newline character + space at the beginning of string.
    # NOTE: This does not return the full string for some platforms.
    # e.g. Supermicro 1.73.11 would return '1.73'.
    # However this is the most reliable way to get the firmware version (Redfish URI may be blocked by licensing [e.g. no OOB license]).
    return bmc_version.strip()

def get_bmc_sensors():
    command   = 'ipmitool sensor'
    output    = run(command)
    return output

# Because Intel Server uses channel 3 for the dedicated management port, we will need to check the manufacturer to determine if we should use channel 1 or 3.
def get_bmc_lan(manufacturer):
    channel = '1'
    if 'Intel' in manufacturer:
        channel = '3'
    command = "ipmitool lan print %s | grep 'IP Address\|MAC Address' | grep -v 'Source'" % channel
    output = run(command)
    return output

def get_fru():
    command = 'ipmitool fru print'
    return run(command)

def get_dcmi_readings():
    command = 'ipmitool dcmi power reading'
    return run(command)

def get_gpus():
    # First scan lspci to see if any NVIDIA cards are detected. At the current time we almost exclusively use NVIDIA GPUs instead of AMD.
    lspci = run('lspci -knn | grep -i nvidia')
    if lspci:
        # Check that nvidia-smi is installed and loading correctly.
        smi = run('nvidia-smi')
        if 'command not found' in smi:
            return "NVIDIA GPU detected but nvidia-smi not installed.\nPlease install nvidia-smi and try again."
        elif 'NVIDIA-SMI has failed' in smi:
            return 'Nouveau driver is blocking nvidia-smi from loading.\nPlease enter: echo "blacklist nouveau" >> /etc/modprobe.d/blacklist-nouveau.conf'
        else:
            return smi
    else:
        return 'No GPUs were detected.'

# This gets the GPU model, which is NOT guaranteed in nvidia-smi default output.
def get_gpu_model():
    return run('nvidia-smi --list-gpus')

# Consume the manufacturer value to determine the utility to call.
# Currently this is supported for LSI controllers supporting storcli64 and Dell EMC PERC controllers supporting perccli64.
def get_storage(manufacturer):
    # Check for the presence of a hardware RAID controller.
    any_raid_ctrls = run('lspci -knn | grep -i raid')
    if any_raid_ctrls:
        print("RAID Controller Detected.\nChecking Controller Firmware Version...")
        # NOTE: The location of these utilities is inconsistent between our Debian 9 and Debian 10 images.
        # Use /opt/perccli64 for Debian 10.
        utility = "./storcli64"
        if 'DELL' in manufacturer:
            utility = './perccli64'
        ctrl_title      = "=============\nController(s)\n=============\n"
        ctrl_info       = get_ctrl_version(utility)
        virtual_drives  = get_virtual_drives(utility)
        pd_title        = "==============\nPhysical Drives\n==============\n"
        physical_drives = get_physical_drives(utility)

        # Scan /sys/block and check for any additional drives. Specifically ones not connected to a RAID controller.
        # As a useful heuristic, check the /sys/block/<DEV>/device/model file.
        # If this file contains either "MR[0-9]" or 'PERC', then we know that drive is behind a RAID controller.
        # MR = MegaRAID and PERC should be obvious (Dell proprietary name of their RAID controllers).
        onboard_devices = get_onboard_storage()
        onboard_msg     = "\nNo (onboard) storage detected\n"
        if onboard_devices:
            onboard_msg = onboard_devices
        return ctrl_title \
        + ctrl_info \
        + '\n' \
        + virtual_drives \
        + '\n' \
        + pd_title \
        + physical_drives \
        + '\n' \
        + "==============\nOnboard Storage (if any)\n==============" \
        + onboard_msg
    # Assuming no RAID controller was found, scan the detected onboard drives.
    else:
        print("No RAID controllers detected.\nChecking for onboard storage drives...")
        onboard_devices = get_onboard_storage()
        if onboard_devices:
            return "==============\nOnboard Storage (if any)\n==============\n" + onboard_devices + '\n'
        else:
            return "\nNo storage drives detected\n"

def get_partitions():
    return run('lsblk')
def get_filesystems():
    return run('blkid')

def get_kernel():
    revision = 'uname -r'
    return run(revision)

def get_os_release():
    pretty_name = run('grep -i pretty /etc/os-release | cut -f 2 -d =')
    return pretty_name


def get_onboard_storage():
    command = 'ls /sys/block | grep -v "lo\|sr"'
    onboard_devices = ""
    block_devices = run(command)
    for device in block_devices.split():
        # Now for each drive, check the /sys/block/<DEV>/device/model file.
        dev = 'cat /sys/block/%s/device/model' % (device)
        block_device = run(dev)
        # Avago / LSI / Broadcom controller.
        regexp = re.compile(r'MR[0-9]')
        # if this matches, that device is a virtual drive. We can get more meaningful data from storcli so skip this device.
        if regexp.search(block_device):
            continue
        # Same as above but when checking Dell systems w/ RAID controllers.
        elif 'PERC' in block_device:
            continue
        # If both conditions failed then this device must be connected to the onboard [or this is a RAID controller we hardly work with].
        else:
            command = "smartctl -i /dev/%s | grep 'Device Model\|Serial\|Firmware'" % device
            output  = run(command)
            onboard_devices += device + '\n' + output + '\n' + "===============================\n"
    # Now collate the block_devices into a multiline string.
    if onboard_devices == '':
        return None
    else:
        output = onboard_devices
        return output


def get_ctrl_version(utility):
    command = "%s /cALL show | grep 'Product Name\|FW\|BIOS'" % (utility)
    return run(command)

def get_virtual_drives(utility):
    command = "%s /cALL/vALL show" % (utility)
    return run(command)

def get_physical_drives(utility):
    command = "%s /cALL/eALL/sALL show all | grep 'attributes\|SN\|Model Number\|Firmware Revision\|Coerced size'" % (utility)
    return run(command)

# TODO: Try to determine if the device is a network bond. 
def get_network_devices():
    device_info = ""
    # First scan /sys/class/net for all available network devices. Filter out loopback and any virtual bridges.
    net_devices = run("ls /sys/class/net | grep -v 'lo'")
    # Next use the output to check ethtool. We need to grab the driver name so we can check the driver version via modinfo.
    for device in net_devices.split():
        # Use single quote, NOT double quotes, when calling awk. Otherwise "print $2" will just output the whole line. No idea why.
        driver = run("ethtool -i %s | grep driver | awk '{print $2}'" % device)
        # Now with the driver name, call modinfo and grep for the version.
        # Remove the newline character from driver variable otherwise it will cause subprocess to throw an error.
        driver_version = run("modinfo %s | grep -i version" % driver.strip())
        # Now get the relevant information for the device from ethtool.
        firmware = run("ethtool -i %s | grep -i firmware" % device)
        # Don't forget the MAC address!
        mac = run('cat /sys/class/net/%s/address' % device)

        # Collate it all together.
        dev = "/dev/" + device + '\n'
        device_info += dev + "MAC Address: " + mac  + '\n' + firmware + '\n' + "Driver Name: " + driver + '\n' + driver_version + '\n' + "===============================\n"
    return device_info

if __name__ == '__main__':
    # Determine the IP address to figure out which subnet to upload the logs to.
    ip = run("ip a | grep 'inet' | grep -v 'inet6\|127.0.0.1' | awk '{print $2}' | cut -f 1 -d '.'")
    server = '10.0.8.40'
    if ip.startswith('172'):
        server = '172.16.8.40'
    # Check the platform to check where to look for the ASA serial / Dell svctag / etc.
    platform = run('cat /sys/class/dmi/id/sys_vendor').strip()
    if 'intel' in platform.lower():
        serial = run('cat /sys/class/dmi/id/chassis_serial').strip()
    # Since we don't do DMI for Mt. Jade platform.
    elif 'wiwynn' in platform.lower():
        serial = run('cat /sys/class/dmi/id/board_serial').strip()
    else:
        serial = run('cat /sys/class/dmi/id/product_serial').strip()
    
    # Setting up logfile names.
    dmi_file       = serial + "_dmi.txt"
    gpu_file       = serial + "_gpu.txt"
    ipmi_file      = serial + "_ipmi.txt"
    storage_file   = serial + "_storage.txt"
    network_file   = serial + "_network.txt"
    os_errors_file = serial + "_errors.txt"
    sel_file       = serial + "_bmc_errors.txt"
    cpu_mem_file   = serial + "_cpu_mem.txt"
    dcmi_file      = serial + '_dcmi.txt'
    with open(storage_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tTesting Environment\n")
        f.write("===============================\n")
        f.write("Operating System: " + get_os_release() + '\n')
        f.write("Kernel Version: " + get_kernel() + '\n')
    with open(dmi_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tManufacturer\n")
        f.write("===============================\n")
        manufacturer    = get_manufacturer()
        f.write("Manufacturer: " + manufacturer + '\n')
        f.write("===============================\n")
        f.write("\tProduct Serial/ASA Serial\n")
        f.write("===============================\n")
        serial          = get_serial(manufacturer)
        f.write("Serial #: " + serial + '\n')
        f.write("===============================\n")
        f.write("\tAsset Tag (if any)\n")
        f.write("===============================\n")
        # Relevant information pertaining to each system
        asset_tag       = get_asset_tag(manufacturer)
        f.write(asset_tag)
    with open(cpu_mem_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tCPUs / Processors\n")
        f.write("===============================\n")
        processors      = get_processors()
        f.write(processors)
        f.write("\n===============================\n")
        f.write("\tMemory\n")
        f.write("===============================\n")
        memory          = get_memory()
        f.write(memory)
        f.write("===============================\n")
        f.write("\tMotherboard\n")
        f.write("===============================\n")
        motherboard     = get_motherboard(manufacturer)
        f.write(motherboard)
        f.write("===============================\n")
        f.write("\tBIOS\n")
        f.write("===============================\n")
        bios_version    = get_bios_version()
        f.write("BIOS Version: " + bios_version)
    with open(ipmi_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tBMC\n")
        f.write("===============================\n")
        bmc_version     = get_bmc_version()
        f.write("BMC Version:" + bmc_version + '\n')
        f.write("==============\n\tBMC LAN Information:\n==============\n")
        bmc_lan_info    = get_bmc_lan(manufacturer)
        f.write(bmc_lan_info)
        f.write("==============\n\tBMC FRU Information:\n==============\n")
        fru = get_fru()
        f.write(fru + '\n')
    with open(dcmi_file, 'a') as f:
        f.write("==============\n\tDCMI Power Readings:\n==============\n")
        dcmi = get_dcmi_readings()
        f.write(dcmi + '\n')
    with open(ipmi_file, 'a') as f:
        f.write("==============\n\tBMC Sensor Readings\n==============\n")
        sensors = get_bmc_sensors()
        f.write(sensors)
    with open(gpu_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tGPUs / Video Cards\n")
        f.write("===============================\n")
        gpus            = get_gpus()
        f.write("GPUs: " + gpus + '\n')
        if 'No GPUs' not in gpus:
            # This will give the GPU model.
            f.write(get_gpu_model())
    with open(storage_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tStorage\n")
        f.write("===============================\n")
        storage         = get_storage(manufacturer)
        f.write(storage)
        f.write("===============================\n")
        f.write("\tPartitions\n")
        f.write("===============================\n")
        partitions = get_partitions()
        f.write(partitions)
        f.write("==================================\n")
        f.write("\tFilesystems\n")
        f.write("==================================\n")
        filesystems = get_filesystems()
        f.write(filesystems)
    with open(network_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tNetwork Devices\n")
        network         = get_network_devices()
        f.write(network)
    with open(os_errors_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tErrors (if any)\n")
        f.write("===============================\n")
    # Checking for errors
        f.write("\tdmesg errors\n")
        f.write("===============================\n")
        dmesg_errors    = get_dmesg()
        f.write(dmesg_errors)
        f.write("===============================\n")
        f.write("\t/var/log/messages errors\n")
        f.write("===============================\n")
        messages_errors = get_var_log_messages()
        f.write(messages_errors)
    with open(sel_file, 'a') as f:
        f.write("===============================\n")
        f.write("\tBMC's System Event Log (SEL)\n")
        f.write("===============================\n")
        f.write(get_sel())
    secret = '0cpT3ster'
    logfiles = [dmi_file, dcmi_file, cpu_mem_file, storage_file, network_file, gpu_file, ipmi_file, os_errors_file, sel_file]
    for log in logfiles:
        sshpass = " sshpass -p %s scp -o StrictHostKeyChecking=no %s root@%s:/data/storage/logs/collector/" % (secret, log, server)
        logged = subprocess.run(sshpass, shell=True)
