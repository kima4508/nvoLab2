from novaclient import client
from neutronclient.v2_0 import client as neutron_client
from netmiko import ConnectHandler
import json,time

# OpenStack credentials
auth_url = 'http://198.11.21.41/identity'
username = 'admin'
password = 'password'
project_name = 'admin'
user_domain_name = 'default'
project_domain_name = 'default'

nova = client.Client('2.1', auth_url=auth_url, username=username, password=password,
                     project_name=project_name, user_domain_name=user_domain_name,
                     project_domain_name=project_domain_name)

# neutron = neutron_client.Client(auth_url=auth_url, username=username, password=password,
#                      project_name=project_name, user_domain_name=user_domain_name,
#                      project_domain_name=project_domain_name)
#Get instance details
customerServer = "vm2-kiran"
flavor=None
for instance in nova.servers.list(detailed=True):
   
    if instance.name == customerServer:
        flavor = nova.flavors.get(instance.flavor['id'])

# network = neutron.list_networks()
# print(network)
image = nova.glance.find_image("cirros-0.6.2-x86_64-disk")

jumpHost = {
    'device_type': 'linux',
    'ip': '198.11.21.41',
    'username': 'kirannvo',
    'password': 'password',
}


def createInstance(current_count,image,flavor):
    # Create the server
    server = nova.servers.create(name="vm-kiran-autoscaled_"+str(current_count), image=image, flavor=flavor,\
                                 key_name='kiran-ssh' , nics = [{'net-id': '742b2eef-b169-47d8-a7a3-0aedb597ea6e'}])
    server = nova.servers.get(server.id)
    while server.status != 'ACTIVE':
        time.sleep(5)  # Wait for 5 seconds before checking again
        server = nova.servers.get(server.id)
    # Print server details
    print("Server Details :")
    print(f"  ID: {server.id}")
    print(f"  Name: {server.name}")
    print(f"  Status: {server.status}")
    print(f"  Created: {server.created}")
    print(f"  Updated: {server.updated}")
    print(f"  Addresses: {server.addresses}")


try:
    # Connect to the jump host
    conn = ConnectHandler(**jumpHost)
    print("Gone into dell server")
    output = conn.send_command_timing('ssh cirros@172.24.4.105')
    output = conn.send_command_timing('gocubsgo')
    current_count=1
    while True and current_count<6:
        print("Checking CPU Usage ....")
        output = conn.send_command_timing("top | grep -o '[0-9][0-9]*% idle '")
        idle = ""
        for i in output:
            if i != '%':
                idle += i
            else:
                break
        
        cpuUsage = 100 - int(idle)
        if cpuUsage > 20:
            print("CPU usage greater than 100%. Usage: "+str(cpuUsage)+"%")
            print("Spinning up new instance "+str(current_count))
            createInstance(current_count,image,flavor)
            current_count = current_count+1
        
        time.sleep(40)
    if current_count == 6:
        print("Max limit of autoscaling reached")

finally:
    # Close the connections
    conn.disconnect()

    

