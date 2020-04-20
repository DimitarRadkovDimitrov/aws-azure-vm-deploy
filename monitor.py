import json, boto3, subprocess
from sshClient import get_ssh_client, ssh_list_docker_images, load_config_file


def get_tag_dictionary(tags):
    tag_dict = {}
    for tag in tags:
        tag_dict[tag['Key']] = tag['Value']
    return tag_dict


def get_instances_aws():
    ec2_res = boto3.resource('ec2', 'us-east-1')
    return list(ec2_res.instances.filter())


def get_instances_azure():
    list_vms_command = ['az', 'vm', 'list', '--show-details', '-d']
    list_vms_result = subprocess.run(list_vms_command, stdout=subprocess.PIPE)
    return list(json.loads(list_vms_result.stdout))


def display_instance_aws(instance, tags):
    print("Name: {}".format(tags['Name']))
    print("ID: {}".format(instance.instance_id))
    print("Public IP Address: {}".format(instance.public_ip_address))
    print("Image ID: {}".format(instance.image_id))
    print("Instance Type: {}".format(instance.instance_type))
    print("Status: {}".format(instance.state['Name']))


def display_instance_azure(instance):
    print("Name: {}".format(instance['name']))
    print("ID: {}".format(instance['id']))
    print("Public IP Address: {}".format(instance['publicIps']))
    print("Offer Name: {}".format(instance['storageProfile']['imageReference']['offer']))
    print("Publisher: {}".format(instance['storageProfile']['imageReference']['publisher']))
    print("Sku: {}".format(instance['storageProfile']['imageReference']['sku']))
    print("Instance Type: {}".format(instance['hardwareProfile']['vmSize']))
    print("Status: {}".format(instance['powerState']))


if __name__ == "__main__":
    aws_instances = get_instances_aws()
    azure_instances = get_instances_azure()
    config = load_config_file('./config.json')
    aws_ssh_key = config['aws_ssh_key']['private_key']
    azure_ssh_key = config['azure_ssh_key']['private_key']
    
    print("-----------------")
    print("AWS EC2 Instances")
    print("-----------------")

    if len(aws_instances) == 0:
        print("No AWS EC2 instances found.")
    else:
        for aws_instance in aws_instances:
            tag_dictionary = get_tag_dictionary(aws_instance.tags)

            if aws_instance.state['Name'] == 'running':
                ssh_client = get_ssh_client(aws_instance.public_ip_address, aws_ssh_key, tag_dictionary['AdminUsername'])
                display_instance_aws(aws_instance, tag_dictionary)
                print("Docker Images:")
                ssh_list_docker_images(ssh_client)
                ssh_client.close()
            else:
                display_instance_aws(aws_instance, tag_dictionary)
            print()

    print("\n------------------")
    print("Azure VM Instances")
    print("------------------")

    if len(azure_instances) == 0:
        print("No Azure VM instances found.")
    else:
        for azure_instance in azure_instances:
            if azure_instance['powerState'] == 'VM running':
                ssh_client = get_ssh_client(azure_instance['publicIps'], azure_ssh_key, azure_instance['osProfile']['adminUsername'])
                display_instance_azure(azure_instance)
                print("Docker Images:")
                ssh_list_docker_images(ssh_client)
                ssh_client.close()
            else:
                display_instance_azure(azure_instance)
            print()
