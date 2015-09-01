from boto.vpc import VPCConnection
import boto.ec2
import boto.vpc
import time

class aws_interface(object):
    def __init__(self, subnet_id, private_ip_address=None):
        self.subnet_id=subnet_id
        self.private_ip_address=private_ip_address

class aws_installer(object):
    def __init__(self, access_key_id, secret_key_id, region, az):
        self.access_key_id=access_key_id
        self.secret_key_id=secret_key_id
        self.region=region
        self.az=az
        self.ec2_conn=boto.ec2.connect_to_region(self.region,
                                                 aws_access_key_id=self.access_key_id,
                                                 aws_secret_access_key=self.secret_key_id)
        self.vpc_conn=boto.vpc.connect_to_region(self.region,
                                                 aws_access_key_id=self.access_key_id,
                                                 aws_secret_access_key=self.secret_key_id)

    def create_vpc(self, cidr_block):
        vpc=self.vpc_conn.create_vpc(cidr_block)
        return vpc

    def delete_vpc(self, vpc_id):
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.vpc_conn.delete_vpc(vpc_id)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break

    def create_subnet(self, vpc_id, cidr_block):
        subnet=self.vpc_conn.create_subnet(vpc_id, cidr_block, availability_zone=self.az)
        return subnet.id

    def delete_subnet(self, subnet_id):
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.vpc_conn.delete_subnet(subnet_id)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break


    def create_vm_test(self, image_id, instance_type, inter):
        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=inter.subnet_id,
                                                                            private_ip_address=inter.private_ip_address,
                                                                            associate_public_ip_address=inter.associate_public_ip_address)
        interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)
        instance=self.ec2_conn.run_instances(image_id, instance_type=instance_type, network_interfaces=interfaces)
        return instance.instances[0].id

    def create_vm(self, image_name, instance_type, interfaces_list):
        if len(interfaces_list) == 4:
            interface1 = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=interfaces_list[0].subnet_id,
                                                                                 private_ip_address=interfaces_list[0].private_ip_address,
                                                                                 device_index=0)
            interface2 = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=interfaces_list[1].subnet_id,
                                                                                 private_ip_address=interfaces_list[1].private_ip_address,
                                                                                 device_index=1)
            interface3 = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=interfaces_list[2].subnet_id,
                                                                                 private_ip_address=interfaces_list[2].private_ip_address, 
                                                                                 device_index=2)
            interface4 = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=interfaces_list[3].subnet_id,
                                                                                 private_ip_address=interfaces_list[3].private_ip_address,
                                                                                 device_index=3)
            interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface1, interface2, interface3, interface4)
        else:
            interface1 = boto.ec2.networkinterface.NetworkInterfaceSpecification(subnet_id=interfaces_list[0].subnet_id,
                                                                                 private_ip_address=interfaces_list[0].private_ip_address,
                                                                                 device_index=0)
            interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface1)
        image_id=self.get_image_id(image_name)
        instance=self.ec2_conn.run_instances(image_id, instance_type=instance_type, network_interfaces=interfaces)
        return instance.instances[0]


    def associate_address(self, instance, dev_no=0):
        eip=self.ec2_conn.allocate_address()
        loop=0
        for loop in range(100):
            try:
                loop=loop+1
                self.ec2_conn.associate_address(public_ip=eip.public_ip, allocation_id=eip.allocation_id, network_interface_id=instance.interfaces[dev_no].id)
            except:
                print "ERROR"
                time.sleep(3)
                continue                
            break
        return eip

    def terminate_instance(self, instance_id):
        instance_ids=[]
        instance_ids.append(instance_id)
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.ec2_conn.terminate_instances(instance_ids)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break

    def disassociate_address(self, public_ip, allocation_id):
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.ec2_conn.disassociate_address(public_ip=public_ip)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break

    def release_address(self, public_ip, allocation_id):
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.ec2_conn.release_address(allocation_id=allocation_id)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break

    def create_internet_gateway(self):
        gateway=self.vpc_conn.create_internet_gateway()
        return gateway.id

    def attach_internet_gateway(self, gateway_id, vpc_id):
        return self.vpc_conn.attach_internet_gateway(gateway_id, vpc_id)

    def detach_internet_gateway(self, gateway_id, vpc_id):
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.vpc_conn.detach_internet_gateway(gateway_id, vpc_id)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break

    def delete_internet_gateway(self, gateway_id):
        loop=0
        for loop in range(100):
            loop=loop+1
            try:
                self.vpc_conn.delete_internet_gateway(gateway_id)
            except:
                print "ERROR"
                time.sleep(3)
                continue
            break

    def get_all_route_tables(self, vpc_id):
        return self.vpc_conn.get_all_route_tables(filters={"vpc_id":vpc_id})

    def create_route_table(self, vpc_id):
        table=self.vpc_conn.create_route_table(vpc_id)
        return table

    def create_route(self, table_id, destination_cidr, interface_id=None, gateway_id=None):
        return self.vpc_conn.create_route(table_id, destination_cidr, interface_id=interface_id, gateway_id=gateway_id)

    def delete_route_table(self, table_id):
        return self.vpc_conn.delete_route_table(table_id)

    def get_image_id(self, image_name):
        image_list=self.ec2_conn.get_all_images(filters={"name":image_name})
        return image_list[0].id

    def create_none_dhcp_options(self):
        return self.vpc_conn.create_dhcp_options()

    def associate_dhcp_options(self, dhcp_options_id, vpc_id):
        return self.vpc_conn.associate_dhcp_options(dhcp_options_id, vpc_id)

    def delete_dhcp_options(self, dhcp_options_id):
        return self.vpc_conn.delete_dhcp_options(dhcp_options_id)

    def disable_sdcheck(self, instance_id):
        return self.ec2_conn.modify_instance_attribute(instance_id, "sourceDestCheck", "false")

    def get_all_security_groups(self, vpc_id):
        return self.ec2_conn.get_all_security_groups(filters={"vpc_id":vpc_id})

