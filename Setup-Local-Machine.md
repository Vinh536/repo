####################################################################
# Github repo setup
####################################################################

Create a folder:
    # This folder will be where you pull all the files from the repo

Install git: 
    sudo apt-get install git -y

Create ssh-keygen and send to Vinh:
    ssh-keygen -t ed25519
        Copy the new sshkey and send it:
            cat ~/.ssh/id_ed<tab>

Change directory into the new folder that you created:
    Initialize git: 
        git init
    
    Add in repo:
        git remote add origin git@github.com/Vinh536/repo.git
        git remote add scripts git@github.com/Vinh536/git-tuorials.git

Pull all files from repo Monday Mornings:
    git pull https://github.com/Vinh536/repo.git master
