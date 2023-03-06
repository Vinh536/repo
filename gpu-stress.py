#!/usr/bin/python3
# For running shell commands through Python.
import subprocess
import sys
import time
from datetime import date

# CUDA will need to change the name of the URL filepath to target if the system is ARM64 instead of X86.
def get_cpu_arch():
    processor = subprocess.check_output("uname --processor", shell=True)
    if 'x86_64' in str(processor):
        return 'x86_64'
    else:
        return 'ARM'

def get_distribution_release():
    # Any distribution supporting systemd is guaranteed to have /etc/os-release.
    # This includes Debian, Ubuntu, and RHEL.
    # As such, read the file to determine which OS is installed. This will determine what repository to target.
    os_release   = subprocess.check_output('cat /etc/os-release', shell=True)
    output       = os_release.decode('utf-8').lower()
    if 'ubuntu' in output:
        if '18.04' in output:
            return 'ubuntu1804'
        else:
            return 'ubuntu2004'
    # The CUDA drivers are only supported for Debian 10 currently (no support for Debian 9).
    elif 'debian' in output and 'ubuntu' not in output:
        return 'debian10'
    elif 'rhel' in output or 'centos' in output:
        if '7' in output:
            return 'rhel7'
        else:
            return 'rhel8'
    else:
        print("Unsupported distribution detected. Exiting...")
        sys.exit(1)

    return distribution

def download_cuda(distribution):
    if 'ubuntu' in distribution:
        cuda = cuda_ubuntu(distribution)
        if cuda is None:
            print("Failed to install CUDA successfully. Please try again. Exiting...")
            sys.exit(1)
        else:
            # The cuda metapackage will come with a driver. Make sure to blacklist nouveau, unload nouveau, and then run nvidia-smi to make sure the driver
            # can communicate with CUDA. This is critical for the multi GPU burn utility to actually target the GPUs.
            blacklist_nouveau = subprocess.check_output('sudo echo "blacklist nouveau" > /etc/modprobe.d/blacklist-nouveau.conf; exit 0', shell=True)
            unload_nouveau    = subprocess.check_output('sudo rmmod nouveau; exit 0', shell=True)
            nvidia_smi        = subprocess.check_output('nvidia-smi', shell=True).decode('utf-8').lower()
            if 'mismatch' in nvidia_smi:
                print("Failed to load NVIDIA driver. Please make sure it is installed by running lsmod | grep -i nvidia. Exiting...")
                sys.exit(1)
            else:
                return nvidia_smi
    elif 'rhel' in distribution or 'centos' in distribution:
        add_repo = 'sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/{distribution}/sbsa/cuda-rhel8.repo'
        cleanup  = 'sudo dnf clean all'
        get_dkms_driver = 'sudo dnf -y module install nvidia-driver:latest-dkms'
        get_cuda        = 'sudo dnf -y install cuda'

        subprocess.check_output(add_repo, shell=True)
        subprocess.check_output(cleanup, shell=True)
        subprocess.check_output(get_dkms_driver, shell=True)
        subprocess.check_output(get_cuda, shell=True)

    elif 'debian' in distribution:
        cuda_debian(distribution)
    else:
        print("Currently only Debian 10 is supported for running the GPU burn test. Later implementations for Ubuntu/RHEL systems will be created later.")
        sys.exit(1)

# Currently CUDA for Debian 10 only supports x86_64.
def cuda_debian(distribution):
    get_public_key  = "sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/debian10/x86_64/7fa2af80.pub"
    add_repository  = 'sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/debian10/x86_64/ /"'
    other_repository= "sudo add-apt-repository contrib"
    apt_update      = 'sudo apt-get update'
    install_cuda = "sudo apt install cuda -y"
    print("Adding NVIDIA public key")
    subprocess.run(get_public_key, shell=True)
    print("Adding NVIDIA compute repository")
    subprocess.run(add_repository, shell=True)
    print("Adding contrib repository")
    subprocess.run(other_repository, shell=True)
    print("Updating apt database")
    subprocess.run(apt_update, shell=True)
    time.sleep(30)
    print("Downloading CUDA toolkit. This will take a while (expect 10-30 minutes depending on network traffic). Do not terminate the program!")
    try:
        monitor_download = subprocess.check_output(install_cuda, shell=True)
    except subprocess.TimeoutExpired as exception:
        print('Failed to install CUDA. Please try again.')
        sys.exit(1)

   # If CUDA installed successfully, then nvcc should be installed. Check that nvcc is loaded and return a success message if it is found.
    # The 'exit 0' is because if subprocess gets an empty return, it will throw an exception. We could either handle the exception in a try/except block
    # Or just call exit 0. 
    nvcc = subprocess.check_output('ls /usr/local/cuda/bin/nvcc; exit 0', shell=True)
    # A non-empty string from which will give us the path to nvcc if it exists in the $PATH variable (usually it installs to /usr/local/bin/).
    if nvcc:
        download_gpu_burn()
    else:
        print("Failed to load NVCC. Exiting...")
        sys.exit(1)

    return nvcc



def cuda_ubuntu(distribution):
    cpu_arch = get_cpu_arch()
    if cpu_arch == 'ARM':
        wget           = 'wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/sbsa/cuda-ubuntu1804.pin'
        subprocess.run(wget, shell=True)
        pin_file       = 'sudo mv cuda-ubuntu1804.pin /etc/apt/preferences.d/cuda-repository-pin-600'
        subprocess.run(pin_file, shell=True)
        get_public_key = "sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/sbsa/7fa2af80.pub"
        add_repository = 'sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/sbsa/ /"'
        apt_update     = 'sudo apt-get update'
        install_cuda   = 'sudo apt-get -y install cuda'
    else:
        get_public_key  = "sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub"
        add_repository  = 'sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"'
        other_repository= "sudo add-apt-repository contrib"
        apt_update      = 'sudo apt-get update'
        install_cuda = "sudo apt install cuda -y"
    print("Adding NVIDIA public key")
    subprocess.run(get_public_key, shell=True)
    print("Adding NVIDIA compute repository")
    subprocess.run(add_repository, shell=True)
    print("Adding contrib repository")
    if cpu_arch == 'x86_64':
        subprocess.run(other_repository, shell=True)
    print("Updating apt database")
    subprocess.run(apt_update, shell=True)
    print("Setting allow release info flag...")
    subprocess.run("apt-get update --allow-releaseinfo-change")
    time.sleep(30)
    print("Downloading CUDA toolkit. This will take a while (expect 10-30 minutes depending on network traffic). Do not terminate the program!")
    try:
        monitor_download = subprocess.run(install_cuda, shell=True)
    except subprocess.TimeoutExpired as exception:
        print('Failed to install CUDA. Please try again.')
        sys.exit(1)

   # If CUDA installed successfully, then nvcc should be installed. Check that nvcc is loaded and return a success message if it is found.
    # The 'exit 0' is because if subprocess gets an empty return, it will throw an exception. We could either handle the exception in a try/except block
    # Or just call exit 0. 
    nvcc = subprocess.check_output('ls /usr/local/cuda/bin/nvcc; exit 0', shell=True)
    # A non-empty string from which will give us the path to nvcc if it exists in the $PATH variable (usually it installs to /usr/local/bin/).
    if nvcc:
        download_gpu_burn()
    else:
        print("Failed to load NVCC. Exiting...")
        sys.exit(1)

    return nvcc
    
def check_for_gpus():
    lspci_output = subprocess.check_output("lspci -knn", shell=True)
    decoded = lspci_output.decode('utf-8')
    any_gpus = []
    for line in decoded.split('\n'):
        if 'nvidia' in line.lower():
            any_gpus.append(line)
    # No output would indicate nothing was found.
    if not any_gpus:
        return False
    return True

def download_gpu_burn():
    repo_url = "sudo git clone https://github.com/wilicc/gpu-burn"
    gpu_burn = subprocess.run(repo_url, shell=True)
    make = subprocess.run('cd gpu-burn; sudo make', shell=True)
    return True

# Use the NVIDIA C/C++ Compiler (nvcc) to check whether CUDA is properly installed.
def is_cuda_installed():
    nvcc_path = subprocess.check_output('ls /usr/local/cuda/bin/nvcc', shell=True)
    if nvcc_path:
        return True
    else:
        return False

def run_gpu_burn(path):
    # Run the GPU burn test for 4 hours.
    # We can also pass in the -d flag to make the test use double floating point calculations.
    test = subprocess.run('cd gpu-burn/; nohup ./gpu_burn 14400 | tee temp', shell=True)

if __name__ == '__main__':
    server = '10.0.8.40'
    secret = '0cpT3ster'

    # Exit early if no video cards were found.
    any_gpus = check_for_gpus()
    if any_gpus:
        # If the nouveau driver is loaded it can cause conflicts with loading the NVIDIA driver.
        # So we will manually remove it via rmmod.
        disable_nouveau = subprocess.run('sudo rmmod nouveau', shell=True)
        distribution = get_distribution_release()

        if 'debian' in distribution or 'ubuntu' in distribution:
            # These packages are REQUIRED to get some of the steps provided by NVIDIA to work for installing the Debian packages through aptitude.
            # apt-get install software-properties-common <- This has utilities like 'add-apt-repository'.
            # git <- To grab the actual gpu_burn test.
            # DEBIAN_FRONTEND=noninteractive keyboard-configuration <- CUDA will ask for what language the keyboard uses. This will make it noninteractive for that stage.
            dialog = subprocess.check_output('sudo apt-get install dialog apt-utils -y', shell=True).decode('utf-8')
            update_pkg_manager = subprocess.check_output('sudo apt update', shell=True).decode('utf-8')
            required_pkgs = subprocess.check_output('sudo apt install software-properties-common git -y', shell=True).decode('utf-8')
            disable_keyboard_config = subprocess.check_output('DEBIAN_FRONTEND=noninteractive sudo apt-get install keyboard-configuration -y', shell=True).decode('utf-8')
        # TODO: See if the same kind of stuff breaks for RHEL-based systems. Does ARM cause any changes? Don't know. Requires further testing.

        get_cuda     = download_cuda(distribution)

        # This is just to handle different file location between Ubuntu and distributions letting you make a root user.
        path = ""
        if 'ubuntu' in distribution:
            path = "/home/ubuntu/gpu-burn/"
        else:
            path = "/root/gpu-burn/"

        if is_cuda_installed():
            get_gpu_burn = download_gpu_burn()
            run_gpu = run_gpu_burn(path)

            # After the test finishes, upload the results to the storage server.
            # However we will also want to modify the filename from nohup.out to one including the system serial number.
            serial  = subprocess.check_output("dmidecode -t system | grep -i serial | awk '{print $3}'", shell=True).decode('utf-8').strip()
            logfile = serial.strip() + '_gpu_results_' + str(date.today()) + '.log'
            moved   = subprocess.check_output('mv %stemp %s' % (path, logfile), shell=True).decode('utf-8')
            # Now attempt to upload the file to the storage server.
            sshpass = "sudo sshpass -p %s scp -o StrictHostKeyChecking=no %s root@%s:/data/storage/logs/gpu_burn/" % (secret, logfile, server)
            logged = subprocess.run(sshpass, shell=True)
            print("Uploaded %s to %s:/data/storage/logs/gpu_burn/" % (logfile, server))
        else:
            print("Failed to download CUDA Toolkit. Please try again")
            sys.exit(1)
    else:
        print("No GPUs detected; exiting GPU test now")
        sys.exit(1)
