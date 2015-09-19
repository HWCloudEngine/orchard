import vm_installer_aws
import cascaded_data

import os
from oslo.config import cfg

CONF = cfg.CONF

cascaded_installer_group = cfg.OptGroup(name='CASCADED_INSTALLER',
                                        title='install a vm in vCenter')
cascaded_installer__opts = [
    cfg.StrOpt("cascaded_image", default=""),
    cfg.StrOpt("cascaded_vm_type", default=""),
    cfg.StrOpt("vpn_image", default=""),
    cfg.StrOpt("vpn_vm_type", default=""),
    cfg.StrOpt("hynode_image", default=""),
    cfg.StrOpt("v2v_image", default=""),
    cfg.StrOpt("v2v_vm_type", default=""),
]
CONF.register_group(cascaded_installer_group)
CONF.register_opts(cascaded_installer__opts, cascaded_installer_group)

#CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
#add_absolute_config_file = os.path.join("/etc/heat/", "add_cloud.ini")
#ADD_CONF(["--config-file=%s" % add_absolute_config_file])

class aws_cascaded_installer(object):
    def __init__(self, access_key_id, secret_key_id, region, az):
        self.region=region
        self.az=az

        self.cascaded_image=CONF.CASCADED_INSTALLER.cascaded_image
        self.cascaded_vm_type=CONF.CASCADED_INSTALLER.cascaded_vm_type
        self.vpn_image=CONF.CASCADED_INSTALLER.vpn_image
        self.vpn_vm_type=CONF.CASCADED_INSTALLER.vpn_vm_type
        self.hynode_image=CONF.CASCADED_INSTALLER.hynode_image
        self.hynode_image_id=None
        self.v2v_image=CONF.CASCADED_INSTALLER.v2v_image
        self.v2v_vm_type=CONF.CASCADED_INSTALLER.v2v_vm_type

        self.vpc_id=None
        self.debug_subnetid=None
        self.base_subnetid=None
        self.api_subnetid=None
        self.tunnel_subnetid=None
        self.gateway_id=None

        self.cascaded_vm=None
        self.cascaded_vm_id=None
        self.cascaded_eip_public_ip=None
        self.cascaded_eip_allocation_id=None
       
        self.v2v_vm_id=None

        self.vpn_api_vm=None
        self.vpn_api_vm_id=None
        self.vpn_api_eip_public_ip=None
        self.vpn_api_eip_allocation_id=None
        self.vpn_api_interface_id=None

        self.vpn_tunnel_vm=None
        self.vpn_tunnel_vm_id=None
        self.vpn_tunnel_eip_public_ip=None
        self.vpn_tunnel_eip_allocation_id=None
        self.vpn_tunnel_interface_id=None

        self.data=cascaded_data.data_handler()

        data_key=self.get_key()
        network=self.data.get_network(data_key)
        if network is not None:
            self.vpc_id=network["vpc_id"]
            self.debug_subnetid=network["debug_subnetid"]
            self.base_subnetid=network["base_subnetid"]
            self.api_subnetid=network["api_subnetid"]
            self.tunnel_subnetid=network["tunnel_subnetid"]
            self.gateway_id=network["gateway_id"]

        cascaded=self.data.get_cascaded(data_key)
        if cascaded is not None:
            self.cascaded_vm_id=cascaded["cascaded_vm_id"]
            self.cascaded_eip_public_ip=cascaded["cascaded_eip_public_ip"]
            self.cascaded_eip_allocation_id=cascaded["cascaded_eip_allocation_id"]

        vpn_api=self.data.get_vpn_api(data_key)
        if vpn_api is not None:
            self.vpn_api_vm_id=vpn_api["vpn_api_vm_id"]
            self.vpn_api_eip_public_ip=vpn_api["vpn_api_eip_public_ip"]
            self.vpn_api_eip_allocation_id=vpn_api["vpn_api_eip_allocation_id"]
            self.vpn_api_interface_id=vpn_api["interface_id"]

        vpn_tunnel=self.data.get_vpn_tunnel(data_key)
        if vpn_tunnel is not None:
            self.vpn_tunnel_vm_id=vpn_tunnel["vpn_tunnel_vm_id"]
            self.vpn_tunnel_eip_public_ip=vpn_tunnel["vpn_tunnel_eip_public_ip"]
            self.vpn_tunnel_eip_allocation_id=vpn_tunnel["vpn_tunnel_eip_allocation_id"]
            self.vpn_tunnel_interface_id=vpn_tunnel["interface_id"]

        self.sg_id=self.data.get_sg_id(data_key)
        self.v2v_vm_id=self.data.get_v2v_id(data_key)
        
        self.installer=vm_installer_aws.aws_installer(access_key_id, secret_key_id, region, az)

    def get_key(self):
        return self.region+"@"+self.az

    def get_ip(self, debug_cidr_block, base_cidr_block, api_cidr_block, tunnel_cidr_block):
        ip_list=debug_cidr_block.split(".")
        self.cascaded_debug_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"12"
        ip_list=base_cidr_block.split(".")
        self.cascaded_base_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"12"
        ip_list=api_cidr_block.split(".")
        self.cascaded_api_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"150"
        self.vpn_api_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"254"
        self.v2v_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"253"
        ip_list=tunnel_cidr_block.split(".")
        self.cascaded_tunnel_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"12"
        self.vpn_tunnel_ip=ip_list[0]+"."+ip_list[1]+"."+ip_list[2]+"."+"254"

    def create_network(self, vpc_cidr_block, debug_cidr_block, base_cidr_block, api_cidr_block, tunnel_cidr_block):
        self.get_ip(debug_cidr_block, base_cidr_block, api_cidr_block, tunnel_cidr_block)
        vpc=self.installer.create_vpc(vpc_cidr_block)
        self.vpc_id=vpc.id

        self.installer.associate_dhcp_options("default", vpc.id)
        self.debug_subnetid=self.installer.create_subnet(self.vpc_id, debug_cidr_block)
        l=self.installer.get_all_route_tables(self.vpc_id)
        self.rtb_id=l[0].id
        self.base_subnetid=self.installer.create_subnet(self.vpc_id, base_cidr_block)
        self.api_subnetid=self.installer.create_subnet(self.vpc_id, api_cidr_block)
        self.tunnel_subnetid=self.installer.create_subnet(self.vpc_id, tunnel_cidr_block)
        self.gateway_id=self.installer.create_internet_gateway()
        self.attach_state=self.installer.attach_internet_gateway(self.gateway_id, self.vpc_id)

        data_key=self.get_key()
        self.data.write_network(data_key, self.vpc_id, self.debug_subnetid, self.base_subnetid, self.api_subnetid, self.tunnel_subnetid, self.gateway_id)

    def cascaded_install(self):
        self.cascaded_debug_en=vm_installer_aws.aws_interface(self.debug_subnetid, self.cascaded_debug_ip)
        self.cascaded_base_en=vm_installer_aws.aws_interface(self.base_subnetid, self.cascaded_base_ip)
        self.cascaded_api_en=vm_installer_aws.aws_interface(self.api_subnetid, self.cascaded_api_ip)
        self.cascaded_tunnel_en=vm_installer_aws.aws_interface(self.tunnel_subnetid, self.cascaded_tunnel_ip)
        self.cascaded_v2v_en=vm_installer_aws.aws_interface(self.api_subnetid, self.v2v_ip)
        en_list=[]
        en_list.append(self.cascaded_debug_en)
        en_list.append(self.cascaded_base_en)
        en_list.append(self.cascaded_api_en)
        en_list.append(self.cascaded_tunnel_en)
        self.cascaded_vm=self.installer.create_vm(self.cascaded_image, self.cascaded_vm_type, en_list)
        self.cascaded_vm_id=self.cascaded_vm.id

        self.vpn_api_en=vm_installer_aws.aws_interface(self.api_subnetid, self.vpn_api_ip)
        self.vpn_tunnel_en=vm_installer_aws.aws_interface(self.tunnel_subnetid, self.vpn_tunnel_ip)
        self.v2v_en=vm_installer_aws.aws_interface(self.api_subnetid, self.v2v_ip)

        en_list_api=[]
        en_list_api.append(self.vpn_api_en)
        self.vpn_api_vm=self.installer.create_vm(self.vpn_image, self.vpn_vm_type, en_list_api)
        self.vpn_api_vm_id=self.vpn_api_vm.id

        en_list_tunnel=[]
        en_list_tunnel.append(self.vpn_tunnel_en)
        self.vpn_tunnel_vm=self.installer.create_vm(self.vpn_image, self.vpn_vm_type, en_list_tunnel)
        self.vpn_tunnel_vm_id=self.vpn_tunnel_vm.id

        if self.v2v_image != "":
            en_list_v2v=[]
            en_list_v2v.append(self.cascaded_v2v_en)
            self.v2v_vm=self.installer.create_vm(self.v2v_image, self.v2v_vm_type, en_list_v2v)
            self.v2v_vm_id=self.v2v_vm.id

        dev_no=0
        for dev_no in range(4):
            if self.cascaded_api_ip==self.cascaded_vm.interfaces[dev_no].private_ip_address:
                break
            dev_no=dev_no+1
        cascaded_eip=self.installer.associate_address(self.cascaded_vm, dev_no)
        self.cascaded_eip_public_ip=cascaded_eip.public_ip
        self.cascaded_eip_allocation_id=cascaded_eip.allocation_id

        vpn_api_eip=self.installer.associate_address(self.vpn_api_vm)
        self.vpn_api_eip_public_ip=vpn_api_eip.public_ip
        self.vpn_api_eip_allocation_id=vpn_api_eip.allocation_id

        vpn_tunnel_eip=self.installer.associate_address(self.vpn_tunnel_vm)
        self.vpn_tunnel_eip_public_ip=vpn_tunnel_eip.public_ip
        self.vpn_tunnel_eip_allocation_id=vpn_tunnel_eip.allocation_id

        self.installer.disable_sdcheck(self.vpn_api_vm_id)
        self.installer.disable_sdcheck(self.vpn_tunnel_vm_id)
        
        """
        sel=self.installer.get_all_security_groups(self.vpc_id)
        self.sg_id=sel[0].id
        """
        self.vpn_api_interface_id=self.vpn_api_vm.interfaces[0].id
        self.vpn_tunnel_interface_id=self.vpn_tunnel_vm.interfaces[0].id
       
        """
        self.installer.create_route(self.rtb_id, "162.3.0.0/16", interface_id=self.vpn_api_vm.interfaces[0].id)
        self.installer.create_route(self.rtb_id, "172.28.48.0/20", interface_id=self.vpn_tunnel_vm.interfaces[0].id)
        """
        self.installer.create_route(self.rtb_id, "0.0.0.0/0", gateway_id=self.gateway_id)

        self.hynode_image_id=self.installer.get_image_id(self.hynode_image)

        data_key=self.get_key()
        self.data.write_cascaded(data_key, self.cascaded_vm_id, self.cascaded_eip_public_ip, self.cascaded_eip_allocation_id)

        self.data.write_vpn_api(data_key, self.vpn_api_vm_id, self.vpn_api_eip_public_ip, self.vpn_api_eip_allocation_id, self.vpn_api_interface_id)
        self.data.write_vpn_tunnel(data_key, self.vpn_tunnel_vm_id, self.vpn_tunnel_eip_public_ip, self.vpn_tunnel_eip_allocation_id, self.vpn_tunnel_interface_id)
        #self.data.write_sg_id(data_key, self.sg_id)
        self.data.write_v2v_id(data_key, self.v2v_vm_id)

    def vpn_install(self):
        self.vpn_api_en=vm_installer_aws.aws_interface(self.api_subnetid, "172.29.0.150")
        self.vpn_tunnel_tunnel_en=vm_installer_aws.aws_interface(self.tunnel_subnetid, "172.29.1.150")
        
        en_list_api=[]
        en_list_api.append(self.vpn_api_en)
        self.vpn_api_vm=self.installer.create_vm(self.vpn_image_id, self.vpn_vm_type, en_list_api)
        self.vpn_api_vm_id=self.vpn_api_vm.id

        en_list_tunnel=[]
        en_list_tunnel.append(self.vpn_tunnel_en)
        self.vpn_tunnel_vm=self.installer.create_vm(self.vpn_image_id, self.vpn_vm_type, en_list_tunnel)
        self.vpn_tunnel_vm_id=self.vpn_tunnel_vm.id

        vpn_api_eip=self.installer.associate_address(self.vpn_api_vm, 2)
        self.vpn_api_eip_public_ip=vpn_api_eip.public_ip
        self.vpn_api_eip_allocation_id=vpn_api_eip.allocation_id

        vpn_tunnel_eip=self.installer.associate_address(self.vpn_tunnel_vm, 2)
        self.vpn_tunnel_eip_public_ip=vpn_tunnel_eip.public_ip
        self.vpn_tunnel_eip_allocation_id=vpn_tunnel_eip.allocation_id

        data_key=self.get_key()
        self.data.write_vpn_api(self.vpn_api_vm_id, self.vpn_api_eip_public_ip, self.vpn_api_eip_allocation_id)
        self.data.write_vpn_tunnel(self.vpn_tunnel_vm_id, self.vpn_tunnel_eip_public_ip, self.vpn_tunnel_eip_allocation_id)

    def rollback(self):
        if self.cascaded_eip_public_ip is not None:
            self.installer.disassociate_address(self.cascaded_eip_public_ip, self.cascaded_eip_allocation_id)
            self.installer.release_address(self.cascaded_eip_public_ip, self.cascaded_eip_allocation_id)
            self.cascaded_eip_public_ip=None
            self.cascaded_eip_allocation_id=None

        if self.vpn_api_eip_public_ip is not None:
            self.installer.disassociate_address(self.vpn_api_eip_public_ip, self.vpn_api_eip_allocation_id)
            self.installer.release_address(self.vpn_api_eip_public_ip, self.vpn_api_eip_allocation_id)
            self.vpn_api_eip_public_ip=None
            self.vpn_api_eip_allocation_id=None

        if self.vpn_tunnel_eip_public_ip is not None:
            self.installer.disassociate_address(self.vpn_tunnel_eip_public_ip, self.vpn_tunnel_eip_allocation_id)
            self.installer.release_address(self.vpn_tunnel_eip_public_ip, self.vpn_tunnel_eip_allocation_id)
            self.vpn_tunnel_eip_public_ip=None
            self.vpn_tunnel_eip_allocation_id=None

        if self.cascaded_vm_id is not None:
            self.installer.terminate_instance(self.cascaded_vm_id)
            self.cascaded_vm_id=None

        if self.vpn_api_vm_id is not None:
            self.installer.terminate_instance(self.vpn_api_vm_id)
            self.vpn_api_vm_id=None

        if self.vpn_tunnel_vm_id is not None:
            self.installer.terminate_instance(self.vpn_tunnel_vm_id)
            self.vpn_tunnel_vm_id=None

        if self.v2v_vm_id is not None:
            self.installer.terminate_instance(self.v2v_vm_id)
            self.v2v_vm_id=None

        if self.gateway_id is not None:
            self.installer.detach_internet_gateway(self.gateway_id, self.vpc_id)
            self.installer.delete_internet_gateway(self.gateway_id)
            self.gateway_id=None

        if self.vpc_id is not None:
            self.installer.delete_subnet(self.debug_subnetid)
            self.installer.delete_subnet(self.base_subnetid)
            self.installer.delete_subnet(self.api_subnetid)
            self.installer.delete_subnet(self.tunnel_subnetid)
            self.installer.delete_vpc(self.vpc_id)
            self.vpc_id=None
            self.debug_subnetid=None
            self.base_subnetid=None
            self.api_subnetid=None
            self.tunnel_subnetid=None

        data_key=self.get_key()
        self.data.remove_all(data_key)

    def uninstall(self):
        self.rollback()

    def add_route(self, type, cidr):
        if type=="api":
            self.installer.create_route(self.rtb_id, cidr, interface_id=self.vpn_api_interface_id)
        else:
            self.installer.create_route(self.rtb_id, cidr, interface_id=self.vpn_tunnel_interface_id)

    def add_security(self, cidr):
        sel=self.installer.get_all_security_groups(self.vpc_id)
        sel[0].authorize(ip_protocol="-1", cidr_ip=cidr)
    
    def remove_security(self, cidr):
        sel=self.installer.get_all_security_groups(self.vpc_id)
        sel[0].revoke(ip_protocol="-1", cidr_ip=cidr)
    

#    cascaded_openstack=[{"vmid":"", "base_ip":"", "tunnel_ip":"", "api_ip":""}]
#    cascaded_apivpn={"vmid":"", "private_ip":"", "public_ip":""}
#    subnet_info={"api_subnet":"", "tunnel_subnet":""}


def aws_cascaded_intall(region, az, access_key_id, secret_key, vpc_cidr="172.29.0.0/16", debug_cidr="172.29.16.0/20", base_cidr="172.29.124.0/20", api_cidr="172.29.0.0/24", tunnel_cidr="172.29.1.0/24"):
    installer=None
    try:
        # import pdb
        # pdb.set_trace()
        installer=aws_cascaded_installer(access_key_id, secret_key, region, az)
        installer.create_network(vpc_cidr, debug_cidr, base_cidr, api_cidr, tunnel_cidr)
        installer.cascaded_install()
        installer.add_route("api", "162.3.0.0/16")
        installer.add_route("tunnel", "172.28.48.0/20")
        installer.add_security("205.177.226.131/32")
        info={}
        info["cascaded_openstack"]={"vm_id":installer.cascaded_vm_id, "base_ip":installer.cascaded_base_ip, "api_ip":installer.cascaded_api_ip, "tunnel_ip":installer.cascaded_tunnel_ip}
        info["cascaded_apivpn"]={"vm_id":installer.vpn_api_vm_id, "private_ip":installer.vpn_api_ip, "public_ip":installer.vpn_api_eip_public_ip}
        info["cascaded_tunnelvpn"]={"vm_id":installer.vpn_tunnel_vm_id, "private_ip":installer.vpn_tunnel_ip, "public_ip":installer.vpn_tunnel_eip_public_ip}
        info["v2v_gateway"]={"vm_id":installer.v2v_vm_id, "private_ip":installer.v2v_ip}
        info["subnet_info"]={"api_subnet":installer.api_subnetid, "tunnel_subnet":installer.tunnel_subnetid, "base_subnet": installer.base_subnetid}
        info["hynode_ami_id"]=installer.hynode_image_id
        info["vpc_id"]=installer.vpc_id
        return info
    except:
        if installer is not None:
            installer.rollback()


def aws_cascaded_uninstall(region, az, access_key_id, secret_key):
    try:
        installer=aws_cascaded_installer(access_key_id, secret_key, region, az)
        installer.uninstall()
    except:
        if installer is not None:
            installer.rollback()

def aws_cascaded_add_route(region, az, access_key_id, secret_key, type="tunnel", cidr="172.28.48.0/20"):
    installer=aws_cascaded_installer(access_key_id, secret_key, region, az)
    installer.add_route(type, cidr)

def aws_cascaded_add_security(region, az, access_key_id, secret_key, cidr="205.177.226.131/32"):
    installer=aws_cascaded_installer(access_key_id, secret_key, region, az)
    installer.add_security(cidr)

def aws_cascaded_remove_security(region, az, access_key_id, secret_key, cidr="205.177.226.131/32"):
    installer=aws_cascaded_installer(access_key_id, secret_key, region, az)
    installer.remove_security(cidr)

