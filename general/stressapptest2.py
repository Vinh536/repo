#!/usr/bin/python3
import subprocess
import math
import sys
import argparse
import os
from datetime import date

# Argument Parser
parser=argparse.ArgumentParser(description="Python Stressapptest utility")
# Default to run for 12 hours.
parser.add_argument('-s', '--seconds', help='Number of seconds to run the test for', default=43200)
parser.add_argument('-l','--log', help='Name of the log file to write stressapptest output to')

# Check the passed in arguments from client. Display usage if incorrect.
args=vars(parser.parse_args())

run_for = args['seconds']
logfile = args['log']

# Wrapper function for processing CLI.
def run(command):
	command_performed = subprocess.check_output(
			    command + '; exit 0',
			    shell=True,
			    stderr=subprocess.STDOUT
			)
	# Returns a Byte object; decode to UTF-8 format and use strip to remove outer whitespace.
	return command_performed.decode('utf-8').strip()
# To determine the number of threads to generate for stressapptest.
def get_core_count():
	command = "cat /proc/cpuinfo | grep 'processor' | wc -l"
	core_count = run(command)
	return core_count

def get_coherency_size():
	return run('cat /sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size')

# Also ensures that std::initialize() does not fail which will also kill the processes.
def get_memory_count():
	# Column 4 is where the quantity of free memory is printed.
	command = "free -m | grep 'Mem' | awk '{print $4}'"
	total_mem = run(command)
	# May be unnecessary to remove 2 GB of memory. Needs further investigation.
	mem_in_mb = int(total_mem) - 2048
	return mem_in_mb

if __name__ == '__main__':
	cores    = get_core_count()
	memory   = get_memory_count()
	# Create the log file using touch otherwise this Python script will crash.
	if args['log'] is None:
		logfile  = run("cat /sys/class/dmi/id/product_serial") + '_stressapptest_results_' + str(date.today()) + '.log'
	# Stressapptest will append to the log file so if the file was ran previously, it will not overwrite the log.
	# This can lead to an edge case of the script failing early due to multiple lines of "Found 0 hardware incidents"
	# As such, delete the file if it currently exists and then use touch to create a new file with the previous log name.
	file_exists = os.path.isfile('/root/%s' % logfile)
	#file_exists = os.path.exists(f'/root/{logfile}')
	if file_exists:
		run('rm -f %s' % logfile)

	make_log = run("touch %s" % logfile)
	ip_address= run("ip a | grep 'state UP' --after-context=2 | grep 'inet' | awk '{print $2}' | cut -f 1 -d '/'")
	
	"""
		-W : Runs a more intensive memory copy. This taps into vector instructions for the CPU (when available).
			 This performs a faster copy operation as a result.
			 In cases where the processor does not support the vector instructions flags, the -W flag will utilize
			 floating-point operations instead.
		--cc_test : This flag performs a cache coherency test. The author does not recommend using this flag during a memory test as it will focus more time
					to checking CPU cache and less on validating DRAM.
					As such the test should be split into two phases: an initial memory intensive stress test followed by a cache coherency test.
		--cc_line_count : This determines how many data structures to allocate for the cache coherency threads to work on. The size of the cache line can be
						  determined by checking /sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size.
	"""

	coherency = get_coherency_size()
	# Use an excessively high pause_delay to avoid a power spike causing the test to deadlock.
	# Source: https://github.com/stressapptest/stressapptest/issues/34
	flags     = '-W --cc_test --cc_line_count %s --stop_on_errors -l %s -s %s --pause_delay 100000' % (coherency, logfile, run_for)
	
	subprocess.run('stressapptest %s' % flags, shell=True)

	# Once the stress test completes, there will be a line towards the bottom of the log that indicates how many hardware incidents occurred.
	# So we will use grep to filter for this line and then use awk in order to grab the column containing the value.
	hardware_incidents = run("grep Found %s | grep [0-9]" % logfile)

	# Write the log file to the storage server. Verify that log file has been successfully transferred; verify log file size is not zero.
	if os.stat(logfile).st_size == 0:
		print("Error! Log file is empty. Re-run stress test on this system: %s" % ip_address)
		sys.exit(1)
	elif hardware_incidents != "Stats: Found 0 hardware incidents":
		print("ERROR! %s" % hardware_incidents)
		print("Please troubleshoot the issue and rerun the stress test to see if the errors went away")
		print("Exiting...")
		sys.exit(1)
	# Assuming everything passed and no errors were detected, we will upload the log file to the storage server.
	else:
		secret = "0cpT3ster"
		server = "10.0.8.40"
		# Previously a socket approach was attempted for file transfer but this leads to a deadlock at the beginning of SSH connection.
		# By using sshpass performed through the subprocess module, we can securely copy the log file to the storage server.
		sshpass = "sshpass -p %s scp -o StrictHostKeyChecking=no %s root@%s:/data/storage/logs/stressapptest/" % (secret, logfile, server)
		logged = subprocess.run(sshpass, shell=True)
		# Subprocess.run will return a CompletedProcess object containing the argument(s) passed and a return code.
		# Check that the return code is zero to verify that the file transfer happened successfully.
		if logged.returncode != 0:
			print("Failed to transfer log file to storage server.\nPlease check your network connectivity.")
		else:
			print('Successfully transferred %s to storage server.' % logfile)

