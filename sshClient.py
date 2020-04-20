import paramiko, socket, json


def load_config_file(path_to_json):
    config = {}
    with open(path_to_json, "r") as f:
        config = json.load(f)
    return config


def get_ssh_client(vm_ip_address, private_key_filename, username):
    wait_for_port_open(vm_ip_address, 22)
    client = paramiko.SSHClient()
    key = paramiko.RSAKey.from_private_key_file(filename=private_key_filename)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(vm_ip_address, username=username, key_filename=private_key_filename)
    return client


def wait_for_port_open(vm_ip_address, port_number):
    result = -1
    while result != 0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((vm_ip_address, port_number))
        sock.close()


def ssh_install_docker_yum(ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command('sudo yum update -y')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to update packages using yum.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Update all existing packages [DONE]")

    stdin, stdout, stderr = ssh_client.exec_command('sudo yum install -y docker')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to install docker using yum.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Install Docker [DONE]")
    
    stdin, stdout, stderr = ssh_client.exec_command('sudo service docker start')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to start docker service.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Start Docker Service [DONE]")


def ssh_install_docker_apt(ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command('sudo apt-get update -y')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to update packages using apt-get.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Update all existing packages [DONE]")

    stdin, stdout, stderr = ssh_client.exec_command('sudo apt-get install -y docker.io')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to install docker using apt-get.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Install Docker [DONE]")
    
    stdin, stdout, stderr = ssh_client.exec_command('sudo service docker start')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to start docker service.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Start Docker Service [DONE]")  


def ssh_install_docker_images(ssh_client, docker_images):
    for docker_image in docker_images:
        if docker_image['registry'] == "library":
            ssh_install_docker_image_library(ssh_client, docker_image)
        else:
            ssh_install_docker_image_private_repo(ssh_client, docker_image)


def ssh_install_docker_image_library(ssh_client, docker_image):
    docker_command = ""

    if docker_image['background'] == True:
        docker_command = 'sudo docker run {}/{}'.format("registry.hub.docker.com/library", docker_image['name'])
    else:
        docker_command = 'sudo docker pull {}/{}'.format("registry.hub.docker.com/library", docker_image['name'])

    stdin, stdout, stderr = ssh_client.exec_command(docker_command)
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to install/run docker image {}.".format(docker_image['name']))
        for err in stderr:
            print("\t{}".format(err))
    else:
        print("Install docker image {} [DONE]".format(docker_image['name']))


def ssh_install_docker_image_private_repo(ssh_client, docker_image):
    pass


def ssh_list_docker_images(ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command('sudo docker images')
    if stdout.channel.recv_exit_status() != 0:
        print("Error: Failed to list docker images.")
        for err in stderr:
            print("\t{}".format(err))
    else:
        for output in stdout:
            print("\t{}".format(output), end="")

