#!/usr/bin/python3
import subprocess
import sys
from datetime import datetime
import argparse

parser=argparse.ArgumentParser(description="Dell Diagnostics Helper")
parser.add_argument('-u','--user', help='Username of the BMC/iDRAC systems', required=True)
parser.add_argument('-p','--password', help='Password of the BMC/iDRAC systems', required=True)
parser.add_argument('-l', '--list', help='Text file of the target IP addresses', required=True)

# Make sure the local machine has racadm installed. Otherwise throw an error.
def check_if_racadm_installed():
  output = subprocess.run('which racadm', shell=True)
  #Returncode 1 means an error has occurred. Expecting 0.
  if output.returncode != 0:
    print("racadm required to be installed to run this utility. Exiting...")
    sys.exit(1)

# Get the svctag. This will be used to generate the file name.
def get_svc_tag(ip, username, password):
  # Use the '--nocertwarn' flag to disable those blasted security warning messages.
  # The warning message occurs because racadm uses a self-signed certificate to authenticate with the iDRAC.
  command = f"racadm -r {ip} -u {username} -p {password} getsysinfo | grep 'Service Tag' | grep -v 'Chassis' | cut -f 2 -d '='".strip()
  output = subprocess.check_output(command, shell=True)
  return output.decode('utf-8').strip()

""" 
 The Dell Diagnostic test, by design, is performed in two stages.
 The two stages cannot be combined into one single API for both running and exporting the test results.
 Potentially this *could* be done through a custom implementation by assigning the Job ID of the "remote diagnostic execution" onto a task queue.
 However for the time being, this script will incorporate the two stages independent of one another. A menu interface is provided to give testers a way to upload after the test completes.
"""

def run_diagnostics(ips, username, password):
  print("Beginning diagnostics task for target machines...")
  for ip in ips:
    print(f"Beginning Dell Diagnostics test on: {ip}")
    output = subprocess.run(f'racadm -r {ip} -u {username} -p {password} --nocertwarn diagnostics run -m 2 -r pwrcycle',
          shell=True)

def export_diagnostics(ips, username, password, nfs_share):
  print("Beginning export task for target machines...")
  for ip in ips:
    svctag = get_svc_tag(ip, username, password)
    print(f"Grabbing Diagnostics test results for: {ip} ..., Service Tag: {svctag}")
    file_template = svctag + '-Diagnostics-Results-' + datetime.now().strftime("%d-%b-%Y") + '.txt'
    command = f'racadm -r {ip} -u {username} -p {password} --nocertwarn diagnostics export -f {file_template.strip()} -l {nfs_share.strip()}'
    print("Running: " + command)
    output = subprocess.run(command,
          shell=True)
    print(f"Generating local file for: {ip} ..., Service Tag: {svctag}")
    command = f'racadm -r {ip} -u {username} -p {password} --nocertwarn diagnostics export -f {file_template.strip()}'
    output = subprocess.run(command, shell=True)
    #result = output.stdout

def menu(ips, username, password, nfs_share):
  exit_flag = False
  while  not exit_flag:
    print("Dell Diagnostics Test Script")
    print("0. Exit Script")
    print("1. Run Diagnostics Test")
    print("2. Export Diagnostics Test")
    option = input("Please select an option: ")
    if option == '0':
      exit_flag = True
    elif option == '1':
      run_diagnostics(ips, username, password)
    elif option == '2':
      export_diagnostics(ips, username, password, nfs_share)
    else:
      print("ERROR! Invalid selection chosen. Please select an option from the list...")
  print("Exiting script...")
  sys.exit(0)

if __name__ == '__main__':

  args    = vars(parser.parse_args())
  username      = args['user']
  password      = args['password']
  iplist  = args['list']

  check_if_racadm_installed()
  nfs_share = "10.0.8.40:/data/storage/logs/dell_diagnostics/"

  # Write out the contents of the 'ips' file to a list.
  ips = []
  with open(iplist, 'r') as ipfile:
    for data in ipfile.read().splitlines():
      if data != "":
      	ips.append(data.strip())

  menu(ips, username, password, nfs_share)
