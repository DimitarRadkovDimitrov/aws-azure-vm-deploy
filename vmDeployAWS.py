import boto3, json, os
from sshClient import get_ssh_client, ssh_install_docker_apt, ssh_install_docker_yum, ssh_install_docker_images, load_config_file


def get_key_pair(ec2, private_key_filename):
    if private_key_filename not in os.listdir("."):
        key_pair_name = private_key_filename.rstrip(".pem")
        key_pair_string = ec2.create_key_pair(KeyName=key_pair_name)['KeyMaterial']
        print("Key-Pair: " + private_key_filename + " successfully created.\n")

        with open(private_key_filename, "w") as f:
            f.write(key_pair_string)

        return key_pair_string
    else:
        print("Key-Pair: " + private_key_filename + " already exists.\n")


def create_instances(vm_config_list, private_ssh_key_file):
    vm_instances_created = []
    to_create = [vm['instance_name'] for vm in vm_config_list]
    ec2_res = boto3.resource('ec2', 'us-east-1')
    instances = ec2_res.instances.filter()

    if (len(list(instances)) == 0):
        print("Currently no instances present.")
    else:
        for instance in instances:
            if instance.tags:
                for tag in instance.tags:
                    if tag['Key'] == "Name" and tag['Value'] in to_create:
                        print("Virtual machine instance " + tag['Value'] + " already exists.")
                        to_create.remove(tag['Value'])

    for vm_config in vm_config_list:
        if vm_config['instance_name'] in to_create:
            print("Creating virtual machine instance " + vm_config['instance_name'] + ".", end="")
            print(" [DONE]")
            created_instances = create_instance(ec2_res, vm_config, private_ssh_key_file)
            vm_instances_created.extend([instance for instance in created_instances])
    
    return vm_instances_created


def create_instance(ec2_res, vm_config, private_ssh_key_file):
    key_pair_name = private_ssh_key_file.rstrip(".pem")
    created_instances = None

    if "storage" in vm_config:
        created_instances = ec2_res.create_instances(
            ImageId=vm_config['vm_image_name'],
            MinCount=vm_config['count'],
            MaxCount=vm_config['count'],
            InstanceType=vm_config['size'],
            BlockDeviceMappings=[{
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': vm_config['storage']['size']
                }
            }],
            KeyName=key_pair_name
        )
    else:
        created_instances = ec2_res.create_instances(
            ImageId=vm_config['vm_image_name'],
            MinCount=vm_config['count'],
            MaxCount=vm_config['count'],
            InstanceType=vm_config['size'],
            KeyName=key_pair_name
        )
    
    for instance in created_instances:
        instance.create_tags(Tags=[
            {'Key': 'Name', 'Value': vm_config['instance_name']},
            {'Key': 'AdminUsername', 'Value': vm_config['username']}
        ])
        instance.username = vm_config['username']
        instance.package_manager = vm_config['package_manager']
        if "docker_images" in vm_config:
            instance.docker_images = vm_config['docker_images']
        else:
            instance.docker_images = None
            
    return created_instances


def get_running_vms():
    ec2_res = boto3.resource('ec2', 'us-east-1')
    instances = ec2_res.instances.filter(Filters=[{'Name':'instance-state-name','Values':['running']}])
    instances = {instance.id for instance in instances}
    return instances


if __name__ == "__main__":
    ec2 = boto3.client('ec2', 'us-east-1')
    config = load_config_file("./config.json")
    aws_vms = config['aws_vms']
    private_key_filename = config['aws_ssh_key']['private_key']

    print("--------------------------------")
    print("Getting/constructing key pair...")
    print("--------------------------------")

    get_key_pair(ec2, private_key_filename)

    print("------------------------------------------------")
    print("Creating vm_instances from configuration file...")
    print("------------------------------------------------")

    created_instances = create_instances(aws_vms, private_key_filename)
    
    for instance in created_instances:
        print("\n---------------------------------------------------------------------------------")
        print("Installing docker on virtual machine with id: " + instance.id + "...")
        print("---------------------------------------------------------------------------------")

        print("Waiting for virtual machine with id: " + instance.id + " to instantiate...")
        
        while instance.id not in get_running_vms():
            continue
        
        print("Waiting for port 22 to open on: " + instance.public_dns_name + "...")
        ssh_client = get_ssh_client(instance.public_dns_name, private_key_filename, instance.username)

        if instance.package_manager == "yum":
            ssh_install_docker_yum(ssh_client)
        elif instance.package_manager == 'apt':
            ssh_install_docker_apt(ssh_client)

        if instance.docker_images is not None:
            ssh_install_docker_images(ssh_client, instance.docker_images)
        
        ssh_client.close()
