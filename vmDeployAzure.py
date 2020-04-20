import os, json, subprocess
from vmDeployAWS import get_key_pair
from sshClient import get_ssh_client, ssh_install_docker_apt, ssh_install_docker_yum, ssh_install_docker_images, load_config_file


def generate_ssh_keys(public_key_filename, private_key_filename):
    if public_key_filename not in os.listdir(".") or private_key_filename not in os.listdir("."):
        pass
        #FIXME
        # create_ssh_keys_command = ['ssh-keygen', '-t', 'rsa', '-b', '2048', '-f', private_key_filename]
        # create_ssh_keys_result = subprocess.Popen(create_ssh_keys_command, stdin=subprocess.PIPE, shell=True)
        # file_selection = bytes("./dimitar\n".encode())
        # newline_input = b'\n'

        # try:
        #     create_ssh_keys_result.communicate(input=file_selection, timeout=5)
        # except subprocess.TimeoutExpired as e:
        #     create_ssh_keys_result.communicate(input=newline_input)

        # print("SSH Keys: {}, {} successfully created.\n".format(public_key_filename, private_key_filename))
    else:
        print("SSH Keys: {}, {} already exist.\n".format(public_key_filename, private_key_filename))


def create_instances(vm_config_list, public_ssh_key_file):
    created_instances = []
    existing_vms = get_vm_names()

    for vm_config in vm_config_list:
        if vm_config['instance_name'] in existing_vms:
            print("Virtual machine instance " + vm_config['instance_name'] + " already exists.")  
        else:
            print("Creating virtual machine instance " + vm_config['instance_name'] + ".", end="")
            create_vm_result = create_instance(vm_config, public_ssh_key_file)
            print(" [DONE]")
            created_instances.append(create_vm_result)
            existing_vms.add(vm_config['instance_name'])
    
    return created_instances


def create_instance(vm_config, public_ssh_key_file):
    created_vm_result = None

    if "storage" in vm_config:
        create_vm_command = ['az', 'vm', 'create', '-n', vm_config['instance_name'], '-g', 'dimitar']
        create_vm_command.extend(['--image', vm_config['vm_image_name']])
        create_vm_command.extend(['--data-disk-sizes-gb', str(vm_config['storage']['size'])])
        create_vm_command.extend(['--size', vm_config['size']])
        create_vm_command.extend(['--ssh-key-value', public_ssh_key_file])
    else:
        create_vm_command = ['az', 'vm', 'create', '-n', vm_config['instance_name'], '-g', 'dimitar']
        create_vm_command.extend(['--image', vm_config['vm_image_name']])
        create_vm_command.extend(['--size', vm_config['size']])
        create_vm_command.extend(['--ssh-key-value', public_ssh_key_file])

    create_vm_result = subprocess.run(create_vm_command, stdout=subprocess.PIPE)
    create_vm_result = json.loads(create_vm_result.stdout)
    create_vm_result['username'] = vm_config['username']
    create_vm_result['package_manager'] = vm_config['package_manager']
    if "docker_images" in vm_config:
        create_vm_result['docker_images'] = vm_config['docker_images']
    else:
        create_vm_result['docker_images'] = None

    return create_vm_result


def get_vm_names():
    list_vms_command = ['az', 'vm', 'list']
    list_vms_result = subprocess.run(list_vms_command, stdout=subprocess.PIPE)
    json_result = json.loads(list_vms_result.stdout)
    vm_names = {json_object['name'] for json_object in json_result}
    return vm_names


if __name__ == "__main__":
    config = load_config_file("./config.json")
    private_key_filename = config['azure_ssh_key']['private_key']
    public_key_filename = config['azure_ssh_key']['public_key']
    azure_vms = config['azure_vms']

    print("--------------------------------")
    print("Getting/constructing key pair...")
    print("--------------------------------")

    generate_ssh_keys(public_key_filename, private_key_filename)

    print("------------------------------------------------")
    print("Creating vm_instances from configuration file...")
    print("------------------------------------------------")

    created_instances = create_instances(azure_vms, public_key_filename)
    
    for instance in created_instances:
        print("\n---------------------------------------------------------------------------------")
        print("Installing docker on virtual machine with IP: " + instance['publicIpAddress'] + "...")
        print("---------------------------------------------------------------------------------")

        ssh_client = get_ssh_client(instance['publicIpAddress'], private_key_filename, instance['username'])
        
        if instance['package_manager'] == "yum":
            ssh_install_docker_yum(ssh_client)
        elif instance['package_manager'] == 'apt':
            ssh_install_docker_apt(ssh_client)

        if instance['docker_images'] is not None:
            ssh_install_docker_images(ssh_client, instance['docker_images'])

        ssh_client.close()
