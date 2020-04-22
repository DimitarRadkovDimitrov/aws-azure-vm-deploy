# AWS/Azure Automated VM Deploy

The scripts vmDeployAWS and vmDeployAzure will create virtual machines in their respective clouds and install docker and any docker images specified in the config.json file.

<br>

## Prerequisites
    
* Install all python project dependencies.
    ```
    pipenv install
    ```

* Make sure your .aws/credentials file is up to date.
* Generate ssh key for azure in the root directory
    ```
    ssh-keygen -t rsa -b 2048 -f cis4010-key-azure
    ```

* Configure [config.json](./config.json) to your liking.

## Run

* Deploy VMs in AWS.
    ```
    pipenv run python3 vmDeployAWS.py
    ```

* Deploy VMs in Azure.
    ```
    pipenv run python3 vmDeployAzure.py
    ```

* Monitor existing VMs in both platforms.
    ```
    pipenv run python3 monitor.py
    ```

<br>

## Known Limitations

* Created vms must have physical storage. If left empty will default to snapshot default.
* Can only create vm with one physical disk at the moment.
* Virtual machines must have either yum or apt package installers.
